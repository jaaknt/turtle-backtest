#!/usr/bin/env python3
"""
SPY market-regime cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

The production regime gate is `spy_close > mean(spy_close[-201:-1])` — SPY above its prior-day
200-day SMA. This study sweeps that lookback: N in {150, 200, 250, 300, 350}, plus a `regime off`
row that applies no market filter at all.

Unlike the other cohort studies this is a **variant sweep, not a partition**. The cohort variable
is a parameter of the filter rather than a property of a signal, so a signal that clears SMA150
usually clears SMA350 as well. Each row is therefore the *full* signal population under that
regime setting and the rows overlap; they do not sum to the `regime off` row. Read it as "what
would this algorithm have produced with that lookback", not as a decomposition.

The regime gate is applied before the 30-day cooldown, exactly as in production, so a different N
changes which triggers win the cooldown slot. That is why every variant regenerates signals from
scratch instead of re-filtering one shared candidate set.

Periods are chosen for this question rather than the usual 2015-2026 cohort window: a regime
filter only earns its keep in a downturn, so both windows straddle one — 2006-2010 covers the
2008 crash, 2018-2023 covers 2018 Q4, the 2020 Covid crash and 2022. Each window is loaded and
simulated on its own so neither drags in the other's bars.
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import config_table, run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
MIN_AVG_VOL = 100_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MIN_NEG = 5

# Both windows straddle a bear market, which is the only condition under which a regime filter
# can pay for itself. Each is loaded separately — a single span would pull 20 years of the
# universe and OOM the host.
PERIODS: list[tuple[date, date]] = [
    (date(2006, 1, 1), date(2010, 12, 31)),
    (date(2018, 1, 1), date(2023, 12, 31)),
]

MARKET_TICKER = "SPY.US"
# Extra SPY history so the longest lookback in the sweep is warm on the window's first day.
SPY_WARMUP_DAYS = 900
# The production lookback is 200; the others are the sweep. `None` is the no-regime reference row.
SMA_LOOKBACKS: list[int | None] = [150, 200, 250, 300, 350, None]
PRODUCTION_LOOKBACK = 200

MIN_RANKING = 44  # QullamaggieRanking gate, matching the portfolio-runner default

STRATEGIES = [
    ("bk50d_s20_v2.0", 0.20),
    ("bk50d_s16_v2.0", 0.16),
    ("bk50d_s12_v2.0", 0.12),
]

CONFIG_ROWS: list[tuple[str, str]] = [
    ("Periods", "**" + ", ".join(f"{s} – {e}" for s, e in PERIODS) + "** — each straddles a bear market"),
    ("Hold", f"{HOLD_CAL}d (calendar)"),
    ("Cohorts", "bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d)"),
    ("Cohort variable", "**the regime lookback N in `spy_close > mean(spy_close[-(N+1):-1])`**"),
    ("Entry", "next trading day's split/dividend-adjusted open"),
    (
        "Filter under study",
        "**SPY > 200d SMA — swept over N = "
        + "/".join(str(lb) for lb in SMA_LOOKBACKS if lb is not None)
        + " and switched off entirely; `SMA200 *` is the production setting and `regime off` the "
        "dropped-filter reference**",
    ),
    ("Rows overlap", "**variant sweep, not a partition — rows do not sum to `regime off`**"),
    ("Fixed filters", "RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range)"),
    ("Ranking gate", f"QullamaggieRanking >= {MIN_RANKING}"),
    ("Price range", f"> ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f}"),
    ("Min avg vol (20d)", f">= {MIN_AVG_VOL // 1000}K"),
    ("Cooldown", f"{COOLDOWN} calendar days, applied after the regime gate as in production"),
    ("Universe", "US common stocks, market_cap >= 1.5B, excl. Comm/RE"),
    ("Sortino", f"mean / RMS(min(r,0)) over all N x sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py)"),
]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-spy-sma.md"


def regime_dates(spy: pl.DataFrame, lookback: int | None) -> set[date] | None:
    """Dates on which SPY closed above its prior-day `lookback`-day SMA.

    `None` means no regime filter, and is signalled back as `None` rather than "every date" so
    the caller can skip the membership test entirely instead of building a set of the calendar.

    Args:
        spy: SPY bars covering the window plus enough lead-in to warm the longest lookback
        lookback: SMA window in trading days, or None for no filter

    Returns:
        The qualifying dates, or None when no filter applies.
    """
    if lookback is None:
        return None
    warm = spy.with_columns(pl.col("close").shift(1).rolling_mean(lookback, min_samples=lookback).alias("_sma"))
    return set(warm.filter(pl.col("close") > pl.col("_sma"))["date"].to_list())


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


# ── Signal generation (regime gate is the swept dimension) ───────────────────


def get_signals(
    df: pl.DataFrame,
    bull_dates: set[date] | None,
    sma_t: float,
    eval_start: date,
    eval_end: date,
) -> pl.DataFrame:
    cond = (
        (pl.col("date") <= eval_end)
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
    )
    if bull_dates is not None:
        cond = cond & pl.col("date").is_in(bull_dates)
    cands = df.filter(cond).select(["symbol", "date", "raw_close", "adj_close", "adr_pct", "pct_vs_sma50"]).sort(["symbol", "date"])
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    # Cooldown runs from the warmup window rather than eval_start, so a trigger just before
    # the window suppresses an early in-window signal — the ordering qm.get_signals uses.
    # Only accepted triggers on or after eval_start are emitted.
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            last_trigger[sym] = d
            if d >= eval_start and compute_ranking(row) >= MIN_RANKING:
                rows_out.append(row)
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runner ──────────────────────────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[float]:
    rets: list[float] = []
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
        rets.append(float((closes[idx_exit] - entry_px) / entry_px))
    return rets


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

_COL_HDR = f"{'Regime':<12}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}  {'CVaR95%':>8}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_cohort_row(label: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return (
        f"{label:<12}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}  {m['cvar']:>+8.2f}"
    )


def regime_label(lookback: int | None) -> str:
    if lookback is None:
        return "regime off"
    return f"SMA{lookback}" + (" *" if lookback == PRODUCTION_LOOKBACK else "")


# ── One evaluation window ─────────────────────────────────────────────────────


def run_window(bars_history: DailyBarsQueryRepository, eval_start: date, eval_end: date) -> list[str]:
    """Load one window's bars and sweep every regime lookback across all three algorithms.

    Bars are fetched per window rather than once for the whole study: a single span covering
    2006-2023 would pull ~20 years of the qualified universe and exhaust the memory cap.

    Args:
        bars_history: Repository for accessing historical bar data
        eval_start: First date a signal may be emitted for
        eval_end: Last date a signal may be emitted for

    Returns:
        Rendered markdown lines for this window, one table per algorithm.
    """
    label = f"{eval_start} – {eval_end}"
    print(f"\n=== {label} ===", flush=True)

    print("Loading SPY …", flush=True)
    spy_start = eval_start - timedelta(days=qm.WARMUP_DAYS + SPY_WARMUP_DAYS)
    spy = bars_history.get_bars_pl(MARKET_TICKER, spy_start, eval_end).sort("date")
    regimes = {lb: regime_dates(spy, lb) for lb in SMA_LOOKBACKS}
    for lb in SMA_LOOKBACKS:
        d = regimes[lb]
        n_days = "all" if d is None else str(len({x for x in d if eval_start <= x <= eval_end}))
        print(f"  {regime_label(lb):<12} qualifying days in window: {n_days}", flush=True)

    print("Loading bars …", flush=True)
    # Forward bars past eval_end so a signal on the last day can still reach its 366d exit.
    df = qm.load_bars(bars_history, eval_start, eval_end + timedelta(days=HOLD_MAX_CAL + 30))
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    bars = df.select("symbol", "date", "adj_open")
    df = qm.add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    lines: list[str] = []
    for strat_label, sma_t in STRATEGIES:
        print(f"  {strat_label} …", flush=True)
        lines += [f"### {label} — {strat_label}", "", _COL_HDR, _COL_SEP]
        for lb in SMA_LOOKBACKS:
            signals = qm.resolve_entries(get_signals(df, regimes[lb], sma_t, eval_start, eval_end), bars)
            rets = np.array(run_trades(signals, sym_dates, sym_closes))
            m = compute_metrics(rets)
            row_label = regime_label(lb)
            if m:
                lines.append(fmt_cohort_row(row_label, m))
            else:
                lines.append(f"{row_label:<12}  {len(rets):>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}  {'—':>8}")
            print(f"    {row_label:<12} {len(rets)} trades", flush=True)
        lines.append("")
        for line in lines[-(len(SMA_LOOKBACKS) + 5) :]:
            print(line)
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    config = config_table(CONFIG_ROWS)
    print("\n" + config)

    all_lines: list[str] = []
    for eval_start, eval_end in PERIODS:
        all_lines += run_window(bars_history, eval_start, eval_end)

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie SPY Regime (market SMA) Cohort Analysis\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("## Configuration\n\n")
        fh.write(config)
        fh.write("\n## Results\n\n")
        fh.write(
            "Each row is the **whole** signal population under that regime setting, so the rows overlap and do "
            "not sum to `regime off` — a signal clearing SMA150 usually clears SMA350 too. `SMA200 *` is the "
            "production setting; `regime off` applies no market filter at all. The gate runs before the 30-day "
            "cooldown, as in production, so a different lookback also changes which triggers win the cooldown "
            "slot — the row counts are not a pure subset relationship either.\n\n"
            "Both windows deliberately straddle a bear market, since that is the only condition under which a "
            "regime filter can pay for itself: 2006-2010 covers the 2008 crash, 2018-2023 covers 2018 Q4, the "
            "2020 Covid crash and 2022. They are **not** comparable with the other cohort studies, which all "
            "run 2015-2026.\n\n"
        )
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
