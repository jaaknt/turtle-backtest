#!/usr/bin/env python3
"""
Current-period signal report for bk50d_s12_tr20_v1.2_roc100 vs bk50d_s20_tr20_v1.2_roc100.

Filters match scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=3.0%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<80%, tight_range<20%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K). Display window: 2025-07-01 - today.
Candidate window starts earlier so the 30-day cooldown state is correct at the start of the
display window.

close/high/low are split/dividend-adjusted (scaled by adjusted_close/close) so indicators
match the backtest's methodology; Entry $/Curr Price/Change % use raw (unadjusted) close,
the real tradeable price, matching scripts/qullamaggie-backtest-v4.py's MIN_PRICE/MAX_PRICE
convention.

References: docs/research/qullamaggie-backtest-v4.md, docs/research/result-qullamaggie-backtest-v4.md
"""

import sys
from bisect import bisect_left
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

DISPLAY_START = date(2025, 7, 1)
DISPLAY_END = date.today()
CANDIDATE_START = date(2025, 1, 1)
BAR_LOAD_START = date(2023, 1, 1)

MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.80
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
TR_FIXED = 0.20

BASE_LABEL = "bk50d_s12_tr20_v1.2_roc100"
BASE_SMA_T = 0.12
COMPARE_LABEL = "bk50d_s20_tr20_v1.2_roc100"
COMPARE_SMA_T = 0.20

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-signals-v4.md"

COHORTS = [
    (12.0, 15.0, "[12-15)"),
    (15.0, 17.5, "[15-17.5)"),
    (17.5, 20.0, "[17.5-20)"),
    (20.0, float("inf"), "[>=20)"),
]


def cohort_label(pct: float) -> str:
    for lo, hi, label in COHORTS:
        if lo <= pct < hi:
            return label
    return COHORTS[-1][2]


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
            "high": [float(r[4]) * f for r, f in zip(rows, factor)],
            "low": [float(r[5]) * f for r, f in zip(rows, factor)],
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
            pl.col("_v1").rolling_mean(10, min_samples=10).over("symbol").alias("avg_vol_10"),
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
            & (pl.col("tight_range_ratio") < TR_FIXED)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
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
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        d_list = g["date"].to_list()
        c_list = [float(c) for c in g["raw_close"].to_list()]
        sym_dates[sym] = d_list
        sym_raw_closes[sym] = c_list
        latest_date[sym] = d_list[-1]
        latest_raw_close[sym] = c_list[-1]

    print(f"Generating signals for {BASE_LABEL} …", flush=True)
    base_sig = get_signals(df, bull_dates, BASE_SMA_T)
    base_sig = base_sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END)).sort(["date", "symbol"])
    print(f"  {len(base_sig)} signals in display window", flush=True)

    print(f"Generating signals for {COMPARE_LABEL} …", flush=True)
    compare_sig = get_signals(df, bull_dates, COMPARE_SMA_T)
    compare_sig = compare_sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END))
    print(f"  {len(compare_sig)} signals in display window", flush=True)

    compare_keys = {(r["symbol"], r["date"]) for r in compare_sig.iter_rows(named=True)}

    hdr = (
        f"{'Date':<11}│ {'Symbol':<7}│ {'Entry $':>8} │ {'Curr Price':>10} │ {'Change %':>9} │ "
        f"{'%abv SMA50':>10} │ {'ADR%':>6} │ {'ADR_CHG':>7} │ {'RSI14':>6} │ {'TR%':>6} │ {'ROC252%':>8} │ "
        f"{'In s20?':>7} │ {'Last date':>11}"
    )
    sep = "─" * len(hdr)

    lines: list[str] = [hdr, sep]
    missing_rows: list[dict] = []
    cohort_returns: dict[str, list[float]] = {label: [] for _, _, label in COHORTS}
    cohort_mdds: dict[str, list[float]] = {label: [] for _, _, label in COHORTS}
    for row in base_sig.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        entry = row["raw_close"]
        curr = latest_raw_close.get(sym, float("nan"))
        chg = (curr / entry - 1.0) * 100 if entry else float("nan")
        in_compare = (sym, d) in compare_keys
        mark = "✓" if in_compare else " "
        ld = latest_date.get(sym)
        sma_pct = row["pct_vs_sma50"] * 100
        lines.append(
            f"{str(d):<11}│ {sym:<7}│ {entry:>8.2f} │ {curr:>10.2f} │ {chg:>+8.1f}% │ "
            f"{sma_pct:>+9.1f}% │ {row['adr_pct'] * 100:>5.1f}% │ {row['adr_pct_change']:>7.2f} │ "
            f"{row['rsi14']:>6.1f} │ {row['tight_range_ratio'] * 100:>5.1f}% │ {row['roc_252d'] * 100:>+7.1f}% │ "
            f"{mark:>7} │ {str(ld):>11}"
        )
        if not in_compare:
            missing_rows.append(row)
        label = cohort_label(sma_pct)
        cohort_returns[label].append(chg)
        idx_entry = bisect_left(sym_dates[sym], d)
        window = np.array(sym_raw_closes[sym][idx_entry:])
        running_max = np.maximum.accumulate(window)
        cohort_mdds[label].append(float((1.0 - window / running_max).max()))

    lines.append(sep)
    also_in_compare = len(base_sig) - len(missing_rows)
    summary = f"Total {BASE_LABEL} signals in window: {len(base_sig)}  |  Also in {COMPARE_LABEL}: {also_in_compare}"
    lines.append(summary)

    output = "\n".join(lines)
    print("\n" + output)

    reason_lines: list[str] = []
    if missing_rows:
        reason_lines.append(f"=== {BASE_LABEL} signals NOT in {COMPARE_LABEL} (N={len(missing_rows)}) — what's missing ===\n")
        for row in missing_rows:
            sym, d = row["symbol"], row["date"]
            pct = row["pct_vs_sma50"] * 100
            threshold_pct = COMPARE_SMA_T * 100
            if pct < threshold_pct:
                reason = f"%abv SMA50={pct:+.1f}% < {threshold_pct:.0f}% threshold — short by {threshold_pct - pct:.1f}pp"
            else:
                reason = (
                    f"%abv SMA50={pct:+.1f}% already clears {threshold_pct:.0f}%, but this exact entry date was "
                    f"suppressed by {COMPARE_LABEL}'s own 30-day cooldown (a different date for {sym} was selected "
                    "as its trigger instead)"
                )
            reason_lines.append(f"  {d} {sym:<7} {reason}")
    else:
        reason_lines.append(f"All {BASE_LABEL} signals in the display window are also in {COMPARE_LABEL}.")

    reasons_text = "\n".join(reason_lines)
    print("\n" + reasons_text)

    cohort_hdr = f"{'Cohort':<10} {'N':>4} {'Med%':>8} {'Mean%':>8} {'Win%':>7} {'PF':>6} {'Sortino':>8} {'MaxDD%':>7}"
    cohort_sep = "-" * len(cohort_hdr)
    cohort_lines = [cohort_hdr, cohort_sep]
    cohort_means: list[float] = []
    for _, _, label in COHORTS:
        vals = cohort_returns[label]
        if not vals:
            cohort_lines.append(f"{label:<10} {0:>4} {'--':>8} {'--':>8} {'--':>7} {'--':>6} {'--':>8} {'--':>7}")
            continue
        arr = np.array(vals)
        med = float(np.median(arr))
        mean = float(arr.mean())
        win = float((arr > 0).mean() * 100)
        cohort_means.append(mean)
        gross_win = float(arr[arr > 0].sum())
        gross_loss = float(-arr[arr < 0].sum())
        pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
        downside = np.where(arr < 0, arr, 0.0)
        downside_dev = float(np.sqrt(np.mean(downside**2)))
        sortino = mean / downside_dev if downside_dev > 0 else float("nan")
        mdd_pct = float(np.mean(cohort_mdds[label]) * 100)
        pf_str = f"{pf:>6.2f}" if np.isfinite(pf) else f"{'inf':>6}"
        sortino_str = f"{sortino:>8.2f}" if not np.isnan(sortino) else f"{'n/a':>8}"
        cohort_lines.append(f"{label:<10} {len(vals):>4} {med:>+7.1f}% {mean:>+7.1f}% {win:>6.1f}% {pf_str} {sortino_str} {mdd_pct:>6.1f}%")
    cohort_output = "\n".join(cohort_lines)
    print(f"\n=== {BASE_LABEL} — Change % by %abv SMA50 cohort (mark-to-latest-price) ===")
    print(cohort_output)

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

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write(f"# {BASE_LABEL} vs {COMPARE_LABEL} — Signal Report\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write(f"Period: {DISPLAY_START} – {DISPLAY_END}\n\n")
        fh.write(
            "Entry $/Curr Price/Change % use raw (unadjusted) close — the real tradeable price. "
            "%abv SMA50/ADR%/ADR_CHG/RSI14/TR%/ROC252% are computed on the entry date, using the "
            "same split/dividend-adjusted series as scripts/qullamaggie-backtest-v4.py. Last date is "
            "the latest date with data available for that symbol in turtle.daily_bars.\n\n"
        )
        fh.write("```\n")
        fh.write(output)
        fh.write("\n```\n\n")
        fh.write("## Signals not in bk50d_s20_tr20_v1.2_roc100\n\n")
        fh.write("```\n")
        fh.write(reasons_text)
        fh.write("\n```\n\n")
        fh.write(f"## Cohort Analysis — {BASE_LABEL} by %abv SMA50 at entry\n\n")
        fh.write(
            "Med%/Mean%/Win%/PF/Sortino are computed on the mark-to-latest-price Change % (same as the "
            "Change % column above) grouped by each signal's %abv SMA50 value at entry. Unlike the backtest's "
            "Sortino, these are **not annualized** (positions have no fixed holding period here — each is "
            "still open, marked at whatever elapsed time has passed since entry), but downside_dev keeps the "
            "backtest's convention (RMS of negative returns over all N, positives count as 0). MaxDD% is the "
            "mean of each signal's own peak-to-trough decline (raw close) from entry through its latest "
            "available date.\n\n```\n"
        )
        fh.write(cohort_output)
        fh.write("\n```\n\n")
        fh.write("### mean(Mean%) vs benchmarks\n\n")
        fh.write(
            "`mean(Mean%)` is the unweighted average of the four cohort Mean% values above (not weighted "
            "by N per cohort). SPY.US/QQQ.US are raw-close buy-and-hold over the same window, no dividend "
            "reinvestment — same convention as Entry $/Curr Price/Change %.\n\n```\n"
        )
        fh.write(bench_output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
