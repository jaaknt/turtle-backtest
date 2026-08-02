#!/usr/bin/env python3
"""
Long-term monthly analysis for multiple bk50d configs (366d hold).

Same fixed filters as scripts/qullamaggie-backtest-v4.py (RSI<70,
roc_12m<100%, vol_surge<2.0x, ADR>=3.0%, ADR_change<90%,
SPY>200d SMA, close>$5&<$250, avg_vol>=500K), extended back to 2007-01-01 to
cover the 2008 GFC, 2011/2015/2018 corrections, 2020 COVID crash and 2022
bear market.

close/high/low are split/dividend-adjusted (scaled by adjusted_close/close),
same convention as qullamaggie-backtest-v4.py — over a 19-year window this
matters far more than over a 5-year one (many more split events).
raw_close (unadjusted) is used only for the MIN_PRICE/MAX_PRICE filter, the
real tradeable price at entry.

Period: 2007-01-01 – 2026-06-26  (burn-in from 2005-01-01)
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2007, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MIN_NEG = 3

MIN_RANKING = 40  # QullamaggieRanking gate, matching the portfolio-runner default

STRATEGIES = [
    ("bk50d_s20_v2.0", 0.20),
    ("bk50d_s16_v2.0", 0.16),
    ("bk50d_s12_v2.0", 0.12),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-longterm-monthly.md"


# ── Benchmarks (study-specific) ───────────────────────────────────────────────


def load_benchmark_yearly_returns(engine: sa.Engine, symbol: str) -> dict[int, float]:
    """Calendar-year close-to-close return for a benchmark ticker, in percent.

    Kept local: the shared signal layer loads the qualified stock universe, not index proxies.
    """
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = :symbol AND date >= :start AND date <= :end
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol, "start": EVAL_START, "end": EVAL_END}).fetchall()
    by_year: dict[int, list[float]] = {}
    for d, c in rows:
        by_year.setdefault(d.year, []).append(float(c))
    return {y: (v[-1] / v[0] - 1.0) * 100.0 for y, v in by_year.items() if len(v) > 1}


# ── Ranking ──────────────────────────────────────────────────────────────────

_ranker = QullamaggieRanking()


def compute_ranking(row: dict) -> int:
    """Score one signal 0-100 with the production QullamaggieRanking.

    `raw_close` is mapped onto the `close` column the ranking reads: QullamaggieStrategy
    keeps `close` unadjusted and the price bands are dollar-denominated.
    """
    row_df = pl.DataFrame(
        [{"date": row["date"], "close": row["raw_close"], "adr_pct": row["adr_pct"], "pct_vs_sma50": row["pct_vs_sma50"]}]
    )
    return _ranker.ranking(row_df, row["date"])


# ── Signal generation ──────────────────────────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > MIN_PRICE)
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") >= sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "raw_close", "adj_close", "adr_pct", "pct_vs_sma50"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    # Cooldown runs from the warmup window rather than EVAL_START, so a trigger just before
    # the window suppresses an early in-window signal — the ordering qm.get_signals uses.
    # Only accepted triggers on or after EVAL_START are emitted.
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            last_trigger[sym] = d
            if d >= EVAL_START and compute_ranking(row) >= MIN_RANKING:
                rows_out.append(row)
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runner ──────────────────────────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        entry_int = (row["entry_date"] - _EPOCH).days
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        entry_px = float(row["entry_price"])
        ret = float((closes[idx_exit] - entry_px) / entry_px)
        records.append({"year": row["date"].year, "month": row["date"].month, "ret": ret})
    return records


# ── Output ────────────────────────────────────────────────────────────────────


def build_monthly_table(records: list[dict]) -> list[str]:
    trades = pl.DataFrame(records) if records else pl.DataFrame(schema={"year": pl.Int64, "month": pl.Int64, "ret": pl.Float64})
    years = sorted(trades["year"].unique().to_list())

    header = f"{'Year':>5} | " + " ".join(f"{m:>6}" for m in MONTHS) + f" | {'Mean%':>7} {'N':>4}"
    sep = "-" * len(header)
    lines = [header, sep]

    for yr in years:
        yr_trades = trades.filter(pl.col("year") == yr)
        row_parts = []
        for mo in range(1, 13):
            mo_rets = yr_trades.filter(pl.col("month") == mo)["ret"].to_list()
            row_parts.append(f"{np.mean(mo_rets) * 100:>+6.1f}" if mo_rets else f"{'·':>6}")
        yr_rets = yr_trades["ret"].to_numpy()
        lines.append(f"{yr:>5} | " + " ".join(row_parts) + f" | {np.mean(yr_rets) * 100:>+7.1f} {len(yr_rets):>4}")

    row_parts = []
    for mo in range(1, 13):
        mo_rets = trades.filter(pl.col("month") == mo)["ret"].to_list()
        row_parts.append(f"{np.mean(mo_rets) * 100:>+6.1f}" if mo_rets else f"{'·':>6}")
    all_rets = trades["ret"].to_numpy()
    lines.append(sep)
    lines.append(f"{'All':>5} | " + " ".join(row_parts) + f" | {np.mean(all_rets) * 100:>+7.1f} {len(all_rets):>4}")
    return lines


def build_yearly_stats_table(
    records: list[dict],
    qqq_yearly: dict[int, float],
    spy_yearly: dict[int, float],
) -> list[str]:
    trades = pl.DataFrame(records) if records else pl.DataFrame(schema={"year": pl.Int64, "month": pl.Int64, "ret": pl.Float64})
    years = sorted(trades["year"].unique().to_list())

    header = f"{'Year':>5} {'N':>5} {'Win%':>6} {'Mean%':>7} {'QQQ%':>7} {'SPY%':>7} {'Med%':>7} {'Sortino':>8} {'CVaR95%':>8}"
    sep = "-" * len(header)
    lines = [header, sep]

    def fmt_pct(v: float) -> str:
        return f"{v:>+7.1f}" if not np.isnan(v) else f"{'—':>7}"

    def fmt_row(a: np.ndarray, qqq_pct: float, spy_pct: float) -> str:
        m = compute_trade_metrics(a * 100, HOLD_CAL, min_losers=MIN_NEG)
        if m is None:  # unreachable: the years come from the trades themselves
            return f"{0:>5} {'—':>6} {'—':>7} {fmt_pct(qqq_pct)} {fmt_pct(spy_pct)} {'—':>7} {'n/a':>8} {'—':>8}"
        sr_str = f"{m.sortino:>8.3f}" if not np.isnan(m.sortino) else f"{'n/a':>8}"
        return (
            f"{m.n:>5} {m.win_pct:>6.1f} {m.mean_pct:>+7.2f} {fmt_pct(qqq_pct)} {fmt_pct(spy_pct)} "
            f"{m.median_pct:>+7.2f} {sr_str} {m.cvar95_pct:>+8.2f}"
        )

    for yr in years:
        a = trades.filter(pl.col("year") == yr)["ret"].to_numpy()
        lines.append(f"{yr:>5} " + fmt_row(a, qqq_yearly.get(yr, float("nan")), spy_yearly.get(yr, float("nan"))))

    lines.append(sep)
    all_rets = trades["ret"].to_numpy()
    # "All" row's QQQ%/SPY% is the mean of the per-year returns actually covered by trades,
    # comparable to the Mean%/Med% columns (per-trade, ~1yr holds) — not the ~19yr compounded total.
    qqq_covered = [qqq_yearly[yr] for yr in years if yr in qqq_yearly]
    spy_covered = [spy_yearly[yr] for yr in years if yr in spy_yearly]
    qqq_all = float(np.mean(qqq_covered)) if qqq_covered else float("nan")
    spy_all = float(np.mean(spy_covered)) if spy_covered else float("nan")
    lines.append(f"{'All':>5} " + fmt_row(all_rets, qqq_all, spy_all))
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()

    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading benchmark returns …", flush=True)
    qqq_yearly = load_benchmark_yearly_returns(settings.engine, "QQQ.US")
    spy_yearly = load_benchmark_yearly_returns(settings.engine, "SPY.US")

    print("Loading bars …", flush=True)
    # Bars run past EVAL_END: a 366d hold needs forward data beyond the last signal date.
    df = qm.load_bars(bars_history, EVAL_START, date.today())
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    # Project down to the columns qm.resolve_entries reads before building the indicator
    # frame, so the full-width bar frame is released rather than held alongside it.
    bars = df.select("symbol", "date", "adj_open")
    df = qm.add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    fixed_hdr = (
        f"Hold: {HOLD_CAL}d | Period: {EVAL_START} – {EVAL_END}\n"
        f"Fixed: roc_12m<{int(ROC_CAP * 100)}%, "
        f"vol_surge<{VOL_SURGE_MAX}x (no lower bound), RSI<{int(RSI_CAP)}, ADR>={ADR_MIN * 100:.1f}%, "
        f"ADR_change<{int(ADR_CHANGE_CAP * 100)}%, "
        f"SPY>200d SMA, close>${MIN_PRICE:.0f}&<${MAX_PRICE:.0f}, avg_vol>={MIN_AVG_VOL // 1000}K, "
        f"QullamaggieRanking>={MIN_RANKING}\n"
    )
    print("\n" + fixed_hdr)

    all_lines: list[str] = [fixed_hdr]

    for strat_label, sma_t in STRATEGIES:
        print(f"Generating signals for {strat_label} …", flush=True)
        signals = qm.resolve_entries(get_signals(df, bull_dates, sma_t), bars)
        print(f"  {len(signals)} signals", flush=True)
        records = run_trades(signals, sym_dates, sym_closes)

        section = [f"### {strat_label}", ""]
        section += build_monthly_table(records)
        section.append("")
        section += build_yearly_stats_table(records, qqq_yearly, spy_yearly)
        section.append("")

        print("\n".join(section))
        all_lines += section

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Long-Term Monthly Analysis (2007-2026)\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
