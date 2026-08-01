#!/usr/bin/env python3
"""
Current-period signal report for bk50d_s12_v2.0 vs bk50d_s16_v2.0 and
bk50d_s20_v2.0 (signals marked when also present in the stricter variants).

The reported signal list is gated at QullamaggieRanking >= MIN_RANKING, matching the
portfolio-runner --min-signal-ranking default. Both cohort tables are deliberately computed
over the *ungated* s12 signals: their job is to show whether ranking and %abv SMA50 separate
outcomes, which a table containing only scores >= 40 could not do (the [0-20) and [20-40)
ranking buckets would always be empty).
0.97*Entry is the 3%-below-entry-close resting-limit level from the portfolio study;
"Reached?" marks whether any daily low touched that level within LIMIT_WINDOW_CAL calendar
days after the signal (fill eligible from the day after the signal, adjusted-price space —
same convention as scripts/qullamaggie-portfolio-sim.py's run_sim_limit).

Filters match scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=3.0%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K; tight_range and sma_alignment disabled — TR% is shown for
information only, not filtered). Display window: 2026-06-01 - today.
Candidate window starts earlier so the 30-day cooldown state is correct at the start of the
display window.

close/high/low are split/dividend-adjusted (scaled by adjusted_close/close) so indicators
match the backtest's methodology; Entry $/Curr Price/Change % use raw (unadjusted) close,
the real tradeable price, matching scripts/qullamaggie-backtest-v4.py's MIN_PRICE/MAX_PRICE
convention.

Ranking is the 0-100 QullamaggieRanking score (turtlex/strategy/ranking/qullamaggie.py) on the
entry date's indicators. Two cohort tables are reported: Change % by %abv SMA50 bucket, and
Change % by Ranking bucket -- both mark-to-latest-price, not annualized (see cohort_stats()).

The whole report — signal table, exclusions, both cohort tables and the benchmark
comparison — is printed to stdout; no result doc is written.

References: docs/research/qullamaggie-backtest-v4.md, docs/research/result-qullamaggie-backtest-v4.md,
turtlex/strategy/ranking/qullamaggie.py
"""

import time
from bisect import bisect_left
from datetime import date

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

DISPLAY_START = date(2026, 6, 1)
DISPLAY_END = date.today()
CANDIDATE_START = date(2025, 1, 1)
BAR_LOAD_START = date(2023, 1, 1)

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
SUSPICIOUS_DAY_MOVE = 0.50  # exclude signals with a >50% single-day raw-close move between entry and latest date

MIN_RANKING = 40  # QullamaggieRanking gate on the reported list (portfolio-runner default)

BASE_LABEL = "bk50d_s12_v2.0"
BASE_SMA_T = 0.12
COMPARE_LABEL = "bk50d_s20_v2.0"
COMPARE_SMA_T = 0.20
COMPARE16_LABEL = "bk50d_s16_v2.0"
COMPARE16_SMA_T = 0.16
LIMIT_DISCOUNT = 0.03  # 0.97*Entry column: resting-limit level 3% below the entry-day close
LIMIT_WINDOW_CAL = 30  # "Reached?" checks lows for this many calendar days after the signal

COHORTS = [
    (12.0, 15.0, "[12-15)"),
    (15.0, 17.5, "[15-17.5)"),
    (17.5, 20.0, "[17.5-20)"),
    (20.0, float("inf"), "[>=20)"),
]

RANKING_COHORTS = [
    (0.0, 20.0, "[0-20)"),
    (20.0, 40.0, "[20-40)"),
    (40.0, 60.0, "[40-60)"),
    (60.0, 80.0, "[60-80)"),
    (80.0, float("inf"), "[>=80)"),
]


def cohort_label(value: float, cohorts: list[tuple[float, float, str]]) -> str:
    for lo, hi, label in cohorts:
        if lo <= value < hi:
            return label
    return cohorts[-1][2]


def cohort_stats(returns: list[float], mdds: list[float]) -> dict | None:
    """Med%/Mean%/Win%/PF/Sortino/MaxDD% for one cohort's Change % values.

    Sortino here is **not annualized** -- passing holding_days=0 skips the
    sqrt(365/hold) factor, because these positions have no fixed holding period
    (each is still open, marked at whatever elapsed time has passed since entry).
    """
    m = compute_trade_metrics(returns, 0, trade_drawdowns_pct=[d * 100 for d in mdds])
    if m is None:
        return None
    return {
        "n": m.n,
        "med": m.median_pct,
        "mean": m.mean_pct,
        "win": m.win_pct,
        "pf": m.profit_factor,
        "sortino": m.sortino,
        "mdd": m.mean_trade_mdd_pct if m.mean_trade_mdd_pct is not None else float("nan"),
    }


def format_cohort_row(label: str, stats: dict | None) -> str:
    if stats is None:
        return f"{label:<10} {0:>4} {'--':>8} {'--':>8} {'--':>7} {'--':>6} {'--':>8} {'--':>7}"
    pf_str = f"{stats['pf']:>6.2f}" if np.isfinite(stats["pf"]) else f"{'inf':>6}"
    sortino_str = f"{stats['sortino']:>8.2f}" if not np.isnan(stats["sortino"]) else f"{'n/a':>8}"
    return (
        f"{label:<10} {stats['n']:>4} {stats['med']:>+7.1f}% {stats['mean']:>+7.1f}% "
        f"{stats['win']:>6.1f}% {pf_str} {sortino_str} {stats['mdd']:>6.1f}%"
    )


def build_cohort_table(
    cohorts: list[tuple[float, float, str]], returns_by_label: dict[str, list[float]], mdds_by_label: dict[str, list[float]]
) -> tuple[str, list[float]]:
    hdr = f"{'Cohort':<10} {'N':>4} {'Med%':>8} {'Mean%':>8} {'Win%':>7} {'PF':>6} {'Sortino':>8} {'MaxDD%':>7}"
    lines = [hdr, "-" * len(hdr)]
    means: list[float] = []
    for _, _, label in cohorts:
        stats = cohort_stats(returns_by_label[label], mdds_by_label[label])
        lines.append(format_cohort_row(label, stats))
        if stats:
            means.append(stats["mean"])
    return "\n".join(lines), means


def load_benchmark_return(engine: sa.Engine, symbol: str) -> tuple[float, date, date]:
    """Raw-close buy-and-hold return for `symbol` from the first available date >= DISPLAY_START
    through the latest available date <= DISPLAY_END (no dividend reinvestment, matching how
    Entry $/Curr Price/Change % are computed for the signal tickers)."""
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = :symbol AND date >= :start AND date <= :end
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol, "start": DISPLAY_START, "end": DISPLAY_END}).fetchall()
    start_date, start_close = rows[0][0], float(rows[0][1])
    end_date, end_close = rows[-1][0], float(rows[-1][1])
    ret = (end_close / start_close - 1.0) * 100.0
    return ret, start_date, end_date


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= :start
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"start": BAR_LOAD_START}).fetchall()
    spy = pl.DataFrame(
        {
            "date": pl.Series([r[0] for r in rows], dtype=pl.Date),
            "close": [float(r[1]) for r in rows],
        }
    )
    spy = spy.with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
    return set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())


def load_bars(engine: sa.Engine) -> pl.DataFrame:
    sql = """
        SELECT db.symbol,
               db.date::date             AS date,
               db.close::float8          AS raw_close,
               db.adjusted_close::float8 AS close,
               db.high::float8           AS high,
               db.low::float8            AS low,
               db.volume::int8           AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= :start
          AND  db.close > 0
          AND  db.adjusted_close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"start": BAR_LOAD_START}).fetchall()
    factor = [float(r[3]) / float(r[2]) for r in rows]  # adjusted_close / raw_close
    return pl.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "date": pl.Series([r[1] for r in rows], dtype=pl.Date),
            "raw_close": [float(r[2]) for r in rows],
            "close": [float(r[3]) for r in rows],
            "high": [float(r[4]) * f for r, f in zip(rows, factor, strict=True)],
            "low": [float(r[5]) * f for r, f in zip(rows, factor, strict=True)],
            "volume": [int(r[6]) for r in rows],
        }
    )


def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
            ((pl.col("high") - pl.col("low")) / pl.col("low")).shift(1).over("symbol").alias("_rp1"),
        ]
    )
    df = df.with_columns(pl.col("_c1").diff(1).over("symbol").alias("_diff"))
    df = df.with_columns(
        [
            pl.when(pl.col("_diff") > 0).then(pl.col("_diff")).otherwise(0.0).alias("_gain"),
            pl.when(pl.col("_diff") < 0).then(-pl.col("_diff")).otherwise(0.0).alias("_loss"),
        ]
    )
    df = df.with_columns(
        [
            pl.col("_gain").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_gain"),
            pl.col("_loss").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_loss"),
        ]
    )
    df = df.with_columns((100.0 - 100.0 / (1.0 + pl.col("_avg_gain") / pl.col("_avg_loss"))).alias("rsi14"))
    df = df.drop(["_diff", "_gain", "_loss", "_avg_gain", "_avg_loss"])
    df = df.with_columns(
        [
            pl.col("_c1").rolling_mean(50, min_samples=50).over("symbol").alias("sma50"),
            pl.col("_v1").rolling_mean(50, min_samples=50).over("symbol").alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(20, min_samples=20).over("symbol").alias("avg_vol_20"),
            pl.col("_c1").rolling_max(50, min_samples=50).over("symbol").alias("max_c_50d"),
            pl.col("_c1").rolling_max(10, min_samples=10).over("symbol").alias("_tr_max"),
            pl.col("_c1").rolling_min(10, min_samples=10).over("symbol").alias("_tr_min"),
            pl.col("_c1").rolling_mean(10, min_samples=10).over("symbol").alias("_tr_mean"),
            pl.col("_rp1").rolling_mean(20, min_samples=20).over("symbol").alias("adr_pct"),
            pl.col("_rp1").rolling_mean(10, min_samples=10).over("symbol").alias("_adr10"),
            pl.col("_rp1").rolling_mean(50, min_samples=50).over("symbol").alias("_adr50"),
            pl.col("_c1").shift(251).over("symbol").alias("_c_252d"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("_tr_max") - pl.col("_tr_min")) / pl.col("_tr_mean")).alias("tight_range_ratio"),
            ((pl.col("close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr10") / pl.col("_adr50")).alias("adr_pct_change"),
            (pl.col("close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
        ]
    )
    return df.drop(["_c1", "_v1", "_rp1", "_tr_max", "_tr_min", "_tr_mean", "_adr10", "_adr50", "_c_252d"])


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= CANDIDATE_START)
            & (pl.col("date") <= DISPLAY_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("tight_range_ratio").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > MIN_PRICE)
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(
            [
                "symbol",
                "date",
                "raw_close",
                "pct_vs_sma50",
                "adr_pct",
                "adr_pct_change",
                "rsi14",
                "tight_range_ratio",
                "roc_252d",
            ]
        )
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
            rows_out.append(row)
            last_trigger[sym] = d
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


def main() -> None:
    run_start = time.perf_counter()
    settings = Settings.from_toml()

    print("Loading SPY regime …", flush=True)
    bull_dates = load_spy_regime(settings.engine)

    print("Loading bars …", flush=True)
    df = load_bars(settings.engine)
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    latest_date: dict[str, date] = {}
    latest_raw_close: dict[str, float] = {}
    sym_dates: dict[str, list[date]] = {}
    sym_raw_closes: dict[str, list[float]] = {}
    sym_adj_closes: dict[str, list[float]] = {}
    sym_adj_lows: dict[str, list[float]] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        d_list = g["date"].to_list()
        c_list = [float(c) for c in g["raw_close"].to_list()]
        sym_dates[sym] = d_list
        sym_raw_closes[sym] = c_list
        sym_adj_closes[sym] = [float(c) for c in g["close"].to_list()]
        sym_adj_lows[sym] = [float(v) for v in g["low"].to_list()]
        latest_date[sym] = d_list[-1]
        latest_raw_close[sym] = c_list[-1]

    def limit_reached(sym: str, idx_entry: int, entry_date: date) -> bool:
        """True if any adjusted low within LIMIT_WINDOW_CAL calendar days after the signal
        (starting the day after) touched adjusted_entry_close * (1 - LIMIT_DISCOUNT)."""
        limit_adj = sym_adj_closes[sym][idx_entry] * (1.0 - LIMIT_DISCOUNT)
        dates = sym_dates[sym]
        lows = sym_adj_lows[sym]
        for i in range(idx_entry + 1, len(dates)):
            if (dates[i] - entry_date).days > LIMIT_WINDOW_CAL:
                break
            if lows[i] <= limit_adj:
                return True
        return False

    ranker = QullamaggieRanking()

    def compute_ranking(row: dict) -> int:
        row_df = pl.DataFrame(
            [
                {
                    "date": row["date"],
                    "close": row["raw_close"],
                    "adr_pct": row["adr_pct"],
                    "adr_pct_change": row["adr_pct_change"],
                    "pct_vs_sma50": row["pct_vs_sma50"],
                    "roc_252d": row["roc_252d"],
                    "rsi14": row["rsi14"],
                }
            ]
        )
        return ranker.ranking(row_df, row["date"])

    print(f"Generating signals for {BASE_LABEL} …", flush=True)
    base_sig = get_signals(df, bull_dates, BASE_SMA_T)
    base_sig = base_sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END)).sort(["date", "symbol"])
    rankings = [compute_ranking(r) for r in base_sig.iter_rows(named=True)]
    base_sig = base_sig.with_columns(pl.Series("ranking", rankings, dtype=pl.Int64))
    n_gated = int(base_sig.filter(pl.col("ranking") >= MIN_RANKING).height)
    print(f"  {len(base_sig)} signals in display window, {n_gated} at ranking >= {MIN_RANKING}", flush=True)

    print(f"Generating signals for {COMPARE_LABEL} …", flush=True)
    compare_sig = get_signals(df, bull_dates, COMPARE_SMA_T)
    compare_sig = compare_sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END))
    print(f"  {len(compare_sig)} signals in display window", flush=True)

    compare_keys = {(r["symbol"], r["date"]) for r in compare_sig.iter_rows(named=True)}

    print(f"Generating signals for {COMPARE16_LABEL} …", flush=True)
    compare16_sig = get_signals(df, bull_dates, COMPARE16_SMA_T)
    compare16_sig = compare16_sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END))
    print(f"  {len(compare16_sig)} signals in display window", flush=True)
    compare16_keys = {(r["symbol"], r["date"]) for r in compare16_sig.iter_rows(named=True)}

    hdr = (
        f"{'Date':<11}│ {'Symbol':<7}│ {'Entry $':>8} │ {'Curr Price':>10} │ {'0.97*Entry':>10} │ {'Change %':>9} │ "
        f"{'%abv SMA50':>10} │ {'ADR%':>6} │ {'ADR_CHG':>7} │ {'RSI14':>6} │ {'TR%':>6} │ {'ROC252%':>8} │ "
        f"{'In s16?':>7} │ {'In s20?':>7} │ {'Reached?':>8} │ {'Ranking':>7} │ {'Last date':>11}"
    )
    sep = "─" * len(hdr)

    lines: list[str] = [hdr, sep]
    excluded_rows: list[dict] = []
    also_in_compare = 0
    reached_count = 0
    cohort_returns: dict[str, list[float]] = {label: [] for _, _, label in COHORTS}
    cohort_mdds: dict[str, list[float]] = {label: [] for _, _, label in COHORTS}
    ranking_returns: dict[str, list[float]] = {label: [] for _, _, label in RANKING_COHORTS}
    ranking_mdds: dict[str, list[float]] = {label: [] for _, _, label in RANKING_COHORTS}
    shown = 0
    also_in_16 = 0
    n_below_gate = 0
    for row in base_sig.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        idx_entry = bisect_left(sym_dates[sym], d)
        window = np.array(sym_raw_closes[sym][idx_entry:])
        max_day_chg = float(np.abs(window[1:] / window[:-1] - 1.0).max()) if len(window) > 1 else 0.0
        if max_day_chg > SUSPICIOUS_DAY_MOVE:
            excluded_rows.append({**row, "max_day_chg": max_day_chg})
            continue
        entry = row["raw_close"]
        curr = latest_raw_close.get(sym, float("nan"))
        chg = (curr / entry - 1.0) * 100 if entry else float("nan")
        ranking = row["ranking"]
        sma_pct = row["pct_vs_sma50"] * 100
        running_max = np.maximum.accumulate(window)
        mdd = float((1.0 - window / running_max).max())
        # cohort tables cover every non-suspicious signal, gated or not — see module docstring
        cohort_returns[cohort_label(sma_pct, COHORTS)].append(chg)
        cohort_mdds[cohort_label(sma_pct, COHORTS)].append(mdd)
        ranking_returns[cohort_label(float(ranking), RANKING_COHORTS)].append(chg)
        ranking_mdds[cohort_label(float(ranking), RANKING_COHORTS)].append(mdd)
        if ranking < MIN_RANKING:
            n_below_gate += 1
            continue
        limit_px = entry * (1.0 - LIMIT_DISCOUNT)
        in_compare = (sym, d) in compare_keys
        mark = "✓" if in_compare else " "
        in_compare16 = (sym, d) in compare16_keys
        mark16 = "✓" if in_compare16 else " "
        reached = limit_reached(sym, idx_entry, d)
        mark_reached = "✓" if reached else " "
        ld = latest_date.get(sym)
        lines.append(
            f"{str(d):<11}│ {sym:<7}│ {entry:>8.2f} │ {curr:>10.2f} │ {limit_px:>10.2f} │ {chg:>+8.1f}% │ "
            f"{sma_pct:>+9.1f}% │ {row['adr_pct'] * 100:>5.1f}% │ {row['adr_pct_change']:>7.2f} │ "
            f"{row['rsi14']:>6.1f} │ {row['tight_range_ratio'] * 100:>5.1f}% │ {row['roc_252d'] * 100:>+7.1f}% │ "
            f"{mark16:>7} │ {mark:>7} │ {mark_reached:>8} │ {ranking:>7} │ {str(ld):>11}"
        )
        shown += 1
        if in_compare:
            also_in_compare += 1
        if in_compare16:
            also_in_16 += 1
        if reached:
            reached_count += 1

    lines.append(sep)
    reached_pct = reached_count / shown * 100 if shown else 0.0
    summary = (
        f"{BASE_LABEL} signals at ranking >= {MIN_RANKING}: {shown}  |  Also in {COMPARE16_LABEL}: {also_in_16}  |  "
        f"Also in {COMPARE_LABEL}: {also_in_compare}  |  "
        f"0.97*Entry reached: {reached_count}/{shown} ({reached_pct:.1f}%)"
    )
    summary += f"  |  Dropped below gate: {n_below_gate}"
    if excluded_rows:
        summary += f"  |  Excluded as suspicious: {len(excluded_rows)}"
    lines.append(summary)

    output = "\n".join(lines)
    print(f"\n=== {BASE_LABEL} vs {COMPARE_LABEL} — Signal Report ===")
    print(f"Run date: {run_timestamp()}  |  Period: {DISPLAY_START} – {DISPLAY_END}")
    print("\n" + output)

    excluded_lines: list[str] = []
    if excluded_rows:
        excluded_lines.append(
            f"=== Excluded as suspicious data — single-day |Δraw_close| > {SUSPICIOUS_DAY_MOVE * 100:.0f}% "
            f"between entry and latest available date (N={len(excluded_rows)}) ===\n"
        )
        for row in excluded_rows:
            excluded_lines.append(
                f"  {row['date']} {row['symbol']:<7} max 1-day move {row['max_day_chg'] * 100:.1f}% "
                "— likely a data anomaly or delisting/halt-type event, not organic price action"
            )
    else:
        excluded_lines.append("No signals excluded as suspicious.")
    excluded_text = "\n".join(excluded_lines)
    print("\n" + excluded_text)

    cohort_output, cohort_means = build_cohort_table(COHORTS, cohort_returns, cohort_mdds)
    print(f"\n=== {BASE_LABEL} — Change % by %abv SMA50 cohort (mark-to-latest-price, ungated) ===")
    print(cohort_output)

    ranking_output, _ranking_means = build_cohort_table(RANKING_COHORTS, ranking_returns, ranking_mdds)
    print(f"\n=== {BASE_LABEL} — Change % by Ranking cohort (mark-to-latest-price, ungated) ===")
    print(f"All s12 signals, including those below the ranking >= {MIN_RANKING} gate, so the gate can be judged.")
    print(ranking_output)

    print("Loading benchmark returns …", flush=True)
    mean_of_means = float(np.mean(cohort_means)) if cohort_means else float("nan")
    spy_ret, spy_start_d, spy_end_d = load_benchmark_return(settings.engine, "SPY.US")
    qqq_ret, qqq_start_d, qqq_end_d = load_benchmark_return(settings.engine, "QQQ.US")
    bench_lines = [
        f"mean(Mean%) across cohorts:  {mean_of_means:>+7.1f}%",
        f"SPY.US buy-and-hold:         {spy_ret:>+7.1f}%   ({spy_start_d} → {spy_end_d})",
        f"QQQ.US buy-and-hold:         {qqq_ret:>+7.1f}%   ({qqq_start_d} → {qqq_end_d})",
    ]
    bench_output = "\n".join(bench_lines)
    print(f"\n=== mean(Mean%) vs SPY/QQQ buy-and-hold, {DISPLAY_START} – {DISPLAY_END} ===")
    print(bench_output)

    print(f"\nSignal report completed in {time.perf_counter() - run_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
