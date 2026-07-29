#!/usr/bin/env python3
"""
ADR% cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the adr_pct >= 3.0% floor, so we can see
performance across the full ADR% range including the sub-3% cohorts.
adr_pct = mean((high_i - low_i) / low_i, i in last 20 days, shift-1)

Bars, indicators and entry resolution come from turtlex.research.qullamaggie, which is
parity-tested against QullamaggieStrategy. That gives this study split/dividend-adjusted
prices (the local copy this replaced used raw closes, so a split showed as a fake ~90%
one-day move) and next-trading-day open entries. Only the cohort filter is local, because
`qm.get_signals` hardcodes the full production filter set and this study must drop one of
its conditions.

Signals are gated at QullamaggieRanking >= MIN_RANKING. Note the gate reads adr_pct as its
highest-weighted dimension, so on this particular study it is partly a function of the
variable being cohorted -- the sub-3% cohorts are thinned by the gate, not only by the market.

Period: 2015-01-01 - 2026-06-26  (warmup handled by qm.load_bars)
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.90
VOL_SURGE_MAX = 2.0
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
ROC_CAP = 1.00
MIN_NEG = 5
MIN_RANKING = 40  # QullamaggieRanking gate, matching the portfolio-runner default

STRATEGIES = [
    ("bk50d_s20_v2.0", 0.20),
    ("bk50d_s16_v2.0", 0.16),
    ("bk50d_s12_v2.0", 0.12),
]

COHORTS: list[tuple[str, float, float]] = [
    ("[0-1.0)  ", 0.000, 0.010),
    ("[1.0-2.0)", 0.010, 0.020),
    ("[2.0-2.5)", 0.020, 0.025),
    ("[2.5-3.0)", 0.025, 0.030),
    ("[3.0-3.5)", 0.030, 0.035),
    ("[3.5-4.0)", 0.035, 0.040),
    ("[4.0-4.5)", 0.040, 0.045),
    ("[4.5-5.0)", 0.045, 0.050),
    ("[5.0-7.0)", 0.050, 0.070),
    ("(>8.0)   ", 0.080, float("inf")),
]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-adr.md"


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


# ── Signal generation (no adr_pct floor) ─────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & pl.col("adr_pct").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > MIN_PRICE)
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("roc_252d") < ROC_CAP)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "raw_close", "adj_close", "adr_pct", "pct_vs_sma50"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            last_trigger[sym] = d
            if compute_ranking(row) >= MIN_RANKING:
                rows_out.append(row)
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runner ──────────────────────────────────────────────────────────────


def run_trades(signals: pl.DataFrame, sym_dates: dict[str, np.ndarray], sym_closes: dict[str, np.ndarray]) -> list[dict]:
    """Hold each resolved entry HOLD_CAL calendar days, exiting at the adjusted close.

    `signals` must already carry `entry_date`/`entry_price` from `qm.resolve_entries`, so the
    buy is the next trading day's adjusted open rather than the close that fired the signal.
    """
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
        records.append({"adr": row["adr_pct"], "ret": ret})
    return records


# ── Metrics ───────────────────────────────────────────────────────────────────


def compute_metrics(rets: np.ndarray) -> dict | None:
    if len(rets) < 5:
        return None
    m = compute_trade_metrics(rets * 100, HOLD_CAL, min_losers=MIN_NEG)
    if m is None:
        return None
    return {
        "n": m.n,
        "med": m.median_pct,
        "mean": m.mean_pct,
        "win": m.win_pct,
        "sr": m.sortino,
        "pf": m.profit_factor,
    }


# ── Output ────────────────────────────────────────────────────────────────────

_COL_HDR = f"{'Cohort':<10}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_cohort_row(label: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return f"{label:<10}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}"


def build_table(label: str, records: list[dict]) -> list[str]:
    lines = [f"### {label}", "", _COL_HDR, _COL_SEP]
    all_rets = np.array([r["ret"] for r in records])
    for cohort_label, lo, hi in COHORTS:
        cohort_rets = np.array([r["ret"] for r in records if lo <= r["adr"] < hi])
        m = compute_metrics(cohort_rets)
        if m:
            lines.append(fmt_cohort_row(cohort_label, m))
        else:
            n = len(cohort_rets)
            lines.append(f"{cohort_label:<10}  {n:>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}")
    lines.append(_COL_SEP)
    m_all = compute_metrics(all_rets)
    if m_all:
        lines.append(fmt_cohort_row("ALL", m_all))
    ref_rets = np.array([r["ret"] for r in records if r["adr"] >= ADR_MIN])
    m_ref = compute_metrics(ref_rets)
    if m_ref:
        lines.append(fmt_cohort_row(">=3% (min)", m_ref))
    lines.append("")
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading bars …", flush=True)
    bars = qm.load_bars(bars_history, EVAL_START, EVAL_END)
    valid_syms = bars.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    bars = bars.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    df = qm.add_indicators(bars)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    header = (
        f"ADR% cohort analysis | Hold: {HOLD_CAL}d | "
        f"Period: {EVAL_START} – {EVAL_END}\n"
        f"Filters: RSI(14)<70, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, breakout>50d high, "
        f"%abv_sma50>12%/16%/20% (swept), SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, "
        f"tight_range disabled; adr_pct>=3.0% floor removed for cohort view; ranking>=40 gate; next-day-open entry\n"
        f"Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min {MIN_NEG} losers "
        f"(turtlex/backtest/metrics.py)\n"
    )
    print("\n" + header)

    all_lines: list[str] = [header]
    for strat_label, sma_t in STRATEGIES:
        print(f"  {strat_label} …", flush=True)
        signals = qm.resolve_entries(get_signals(df, bull_dates, sma_t), bars)
        print(f"    {len(signals)} signals", flush=True)
        records = run_trades(signals, sym_dates, sym_closes)
        table_lines = build_table(strat_label, records)
        all_lines.extend(table_lines)
        for line in table_lines:
            print(line)

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie ADR% Cohort Analysis\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
