#!/usr/bin/env python3
"""
Market-cap cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

Drops the production `market_cap >= 1.5B` universe floor and buckets every signal by its
company's market cap, so the three sub-floor cohorts exist at all. `>=1.5B (cap)` is the
reference row: the slice the live filter keeps.

**READ THE CAVEAT BEFORE THE TABLE.** `turtle.company.market_cap` is a single snapshot column
with no history, so a 2015 trade is bucketed by its company's market cap *today*. Every other
cohort study measures its variable on the signal date; this one cannot. That inverts the
question being asked: the `(<300M)` bucket is not "small companies", it is "companies that are
small in 2026" — i.e. ones that fell or stagnated over the following decade — and `(>100B)` is
companies that grew into it. Trades are therefore sorted partly by their own outcome, and a
"large caps did better" reading would be look-ahead, not a finding. The study is descriptive
only: it says which of today's size classes the good trades came from, which is a different
question from whether size predicts returns.

The existing `>= 1.5B` *filter* is far less affected, because it applies identically to every
arm of any comparison — it restricts the universe rather than sorting within it.

Memory: the universe is read in market-cap slabs rather than in one query. Dropping the floor
takes the 2013-2026 read from ~5.8M rows to ~11.8M, roughly double the widest existing study,
which already peaks near the 4 GB cap. Market cap is a per-symbol attribute and nothing in the
signal path crosses symbols (the cooldown is per-symbol), so slabbing reproduces a single wide
read exactly while halving peak memory.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import config_table, run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
MIN_AVG_VOL = 100_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
COOLDOWN = 30
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MIN_NEG = 5

# The production universe floor. Not applied here — it is the dimension under study — but
# reported as the `>=1.5B (cap)` row, which is the slice the live filter keeps.
MARKET_CAP_FLOOR = 1_500_000_000

MIN_RANKING = 40  # QullamaggieRanking gate, matching the portfolio-runner default

# Read the universe in these [lo, hi) market-cap slabs. Splitting on a per-symbol attribute is
# lossless here because no part of the signal path crosses symbols.
SLABS: list[tuple[int, int | None]] = [(0, MARKET_CAP_FLOOR), (MARKET_CAP_FLOOR, None)]

STRATEGIES = [
    ("bk50d_s20_v2.0", 0.20),
    ("bk50d_s16_v2.0", 0.16),
    ("bk50d_s12_v2.0", 0.12),
]

_B = 1_000_000_000
_M = 1_000_000
COHORTS: list[tuple[str, float, float]] = [
    ("(<300M)    ", 0, 300 * _M),
    ("[300M-1B)  ", 300 * _M, 1 * _B),
    ("[1B-1.5B)  ", 1 * _B, 1.5 * _B),
    ("[1.5-3B)   ", 1.5 * _B, 3 * _B),
    ("[3-10B)    ", 3 * _B, 10 * _B),
    ("[10-30B)   ", 10 * _B, 30 * _B),
    ("[30-100B)  ", 30 * _B, 100 * _B),
    ("(>100B)    ", 100 * _B, float("inf")),
]

CONFIG_ROWS: list[tuple[str, str]] = [
    ("Period", f"{EVAL_START} – {EVAL_END}"),
    ("Hold", f"{HOLD_CAL}d (calendar)"),
    ("Cohorts", "bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d)"),
    ("Cohort variable", "**`company.market_cap` — a current snapshot, NOT a signal-date value**"),
    ("Entry", "next trading day's split/dividend-adjusted open"),
    (
        "Filter under study",
        "**`market_cap >= 1.5B` — removed, otherwise the three sub-floor cohorts would be empty; returns as the `>=1.5B (cap)` row**",
    ),
    (
        "⚠ Look-ahead",
        "**market_cap has no history, so a 2015 trade is bucketed by its 2026 cap — trades are "
        "sorted partly by their own outcome. Descriptive only; do not read as 'size predicts returns'**",
    ),
    ("Fixed filters", "RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range)"),
    ("Ranking gate", f"QullamaggieRanking >= {MIN_RANKING}"),
    ("Market regime", "SPY close > 200d SMA"),
    ("Price range", f"> ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f}"),
    ("Min avg vol (20d)", f">= {MIN_AVG_VOL // 1000}K"),
    ("Cooldown", f"{COOLDOWN} calendar days"),
    ("Universe", "US common stocks, excl. Comm/RE — **no market-cap floor**"),
    ("Universe read", f"{len(SLABS)} market-cap slabs, lossless vs one wide read (see docstring)"),
    ("Sortino", f"mean / RMS(min(r,0)) over all N x sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py)"),
]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-market-cap.md"


def load_market_caps(engine: sa.Engine) -> dict[str, int]:
    """Map ticker code to its (current) market cap for every US common stock we might load.

    Args:
        engine: SQLAlchemy engine for the trading database

    Returns:
        `{symbol: market_cap}`; symbols missing a cap are absent and get no cohort.
    """
    sql = """
        SELECT t.code, c.market_cap
        FROM   turtle.company c
        JOIN   turtle.ticker  t ON t.code = c.ticker_code
        WHERE  t.country = 'USA' AND t.type = 'Common Stock'
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  c.market_cap > 0
    """
    with engine.connect() as conn:
        return {r[0]: int(r[1]) for r in conn.execute(sa.text(sql)).fetchall()}


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


# ── Signal generation (no market-cap floor; that is the dimension under study) ─


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
    caps: dict[str, int],
) -> list[dict]:
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates or sym not in caps:
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
        records.append({"cap": caps[sym], "ret": float((closes[idx_exit] - entry_px) / entry_px)})
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
        "cvar": m.cvar95_pct,
    }


# ── Output ────────────────────────────────────────────────────────────────────

_COL_HDR = f"{'Cohort':<12}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}  {'CVaR95%':>8}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_cohort_row(label: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return (
        f"{label:<12}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}  {m['cvar']:>+8.2f}"
    )


def build_table(label: str, records: list[dict]) -> list[str]:
    lines = [f"### {label}", "", _COL_HDR, _COL_SEP]
    all_rets = np.array([r["ret"] for r in records])
    for cohort_label, lo, hi in COHORTS:
        cohort_rets = np.array([r["ret"] for r in records if lo <= r["cap"] < hi])
        m = compute_metrics(cohort_rets)
        if m:
            lines.append(fmt_cohort_row(cohort_label, m))
        else:
            n = len(cohort_rets)
            lines.append(f"{cohort_label:<12}  {n:>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}  {'—':>8}")
    lines.append(_COL_SEP)
    m_all = compute_metrics(all_rets)
    if m_all:
        lines.append(fmt_cohort_row("ALL", m_all))
    ref_rets = np.array([r["ret"] for r in records if r["cap"] >= MARKET_CAP_FLOOR])
    m_ref = compute_metrics(ref_rets)
    if m_ref:
        lines.append(fmt_cohort_row(">=1.5B (cap)", m_ref))
    lines.append("")
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading market caps …", flush=True)
    caps = load_market_caps(settings.engine)
    print(f"  {len(caps)} symbols with a market cap", flush=True)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    config = config_table(CONFIG_ROWS)
    print("\n" + config)

    # One record list per algorithm, accumulated across slabs before any metric is computed.
    records_by_strategy: dict[str, list[dict]] = {label: [] for label, _ in STRATEGIES}

    for slab_lo, slab_hi in SLABS:
        hi_txt = "inf" if slab_hi is None else f"{slab_hi / _B:g}B"
        print(f"\n=== slab {slab_lo / _B:g}B – {hi_txt} ===", flush=True)
        print("Loading bars …", flush=True)
        # Bars run past EVAL_END: a 366d hold needs forward data beyond the last signal date.
        # Mirrors qm.load_bars, which cannot be reused because it hardcodes the 1.5B floor.
        raw = bars_history.get_qualified_universe_bars_pl(
            EVAL_START - timedelta(days=qm.WARMUP_DAYS),
            date.today(),
            min_market_cap=slab_lo,
            max_market_cap=slab_hi,
        )
        if raw.is_empty():
            print("  no bars in slab", flush=True)
            continue
        df = qm.prepare_bars(raw.rename({"close": "raw_close"}))
        del raw
        print(f"  {df.height:,} rows, {df['symbol'].n_unique()} symbols", flush=True)

        print("Computing indicators …", flush=True)
        bars = df.select("symbol", "date", "adj_open")
        df = qm.add_indicators(df)

        sym_dates: dict[str, np.ndarray] = {}
        sym_closes: dict[str, np.ndarray] = {}
        for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
            g = grp.sort("date")
            sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
            sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

        for strat_label, sma_t in STRATEGIES:
            print(f"  {strat_label} …", flush=True)
            signals = qm.resolve_entries(get_signals(df, bull_dates, sma_t), bars)
            recs = run_trades(signals, sym_dates, sym_closes, caps)
            records_by_strategy[strat_label].extend(recs)
            print(f"    {len(recs)} trades", flush=True)

        # Free the slab before the next one is read; both do not fit under the memory cap.
        del df, bars, sym_dates, sym_closes

    all_lines: list[str] = []
    for strat_label, _sma_t in STRATEGIES:
        table_lines = build_table(strat_label, records_by_strategy[strat_label])
        all_lines.extend(table_lines)
        for line in table_lines:
            print(line)

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Market-Cap Cohort Analysis\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write(
            "> **⚠ Descriptive only — this cohort variable carries look-ahead.** `company.market_cap` is a "
            "current snapshot with no history, so a 2015 trade is bucketed by its company's market cap *today*. "
            "The `(<300M)` bucket is therefore not 'small companies' but 'companies that are small in 2026' — "
            "ones that fell or stagnated over the following decade — and `(>100B)` is companies that grew into "
            "it. Trades are sorted partly by their own outcome, so a 'large caps did better' reading would be "
            "an artifact, not a finding. Every other cohort study measures its variable on the signal date; "
            "this one cannot until a point-in-time cap (shares outstanding x close) is available.\n\n"
        )
        fh.write("## Configuration\n\n")
        fh.write(config)
        fh.write("\n## Results\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
