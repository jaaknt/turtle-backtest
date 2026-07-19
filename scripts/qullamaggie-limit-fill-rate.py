#!/usr/bin/env python3
"""
Limit-order fill-rate grid for bk50d_s12_v1.2_roc100 signals (pure fill-probability
study — no hold/return computation).

For each signal, a resting limit buy is placed at signal_day_close * (1 - X%) for
X% in {0, 1, 2, 3, 4, 5}, eligible from the day after the signal. The order fills on
the first trading day whose low <= limit price within Y calendar days of the signal
day (Y in {30, 60, 90}), else expires unfilled. Reports Fill% plus median/mean
trading days from signal to fill (filled orders only) per X x Y cell.

Filters match scripts/qullamaggie-signals-v4.py exactly (RSI<70, ADR mean-of-ratios
>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K, no tight_range, cooldown 30d, mcap>=1.5B excl Comm/RE).
close/high/low are split/dividend-adjusted; the fill test uses adjusted prices — same
convention as scripts/qullamaggie-limit-order-cohorts.py's run_trades_limit.

Period: 2010-06-01 - today  |  Burn-in data from 2008-01-01.

References: docs/research/qullamaggie-backtest-v4.md, docs/research/result-qullamaggie-backtest-v4.md
"""

import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

_EPOCH = date(1970, 1, 1)
BAR_LOAD_START = date(2008, 1, 1)
EVAL_START = date(2010, 6, 1)
EVAL_END = date.today()

MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.90
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90

SMA_T = 0.12
LABEL = "bk50d_s12_v1.2_roc100"

LIMIT_PCTS = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
WINDOWS_CAL = [30, 60, 90]  # limit order stays resting this many calendar days after the signal

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-limit-fill-rate.md"


# ── Data loading (identical to qullamaggie-backtest-v4.py) ────────────────────


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


# ── Indicators (identical to qullamaggie-backtest-v4.py) ──────────────────────


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
            pl.col("_rp1").rolling_mean(20, min_samples=20).over("symbol").alias("adr_pct"),
            pl.col("_rp1").rolling_mean(10, min_samples=10).over("symbol").alias("_adr10"),
            pl.col("_rp1").rolling_mean(50, min_samples=50).over("symbol").alias("_adr50"),
            pl.col("_c1").shift(251).over("symbol").alias("_c_252d"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr10") / pl.col("_adr50")).alias("adr_pct_change"),
            (pl.col("close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
        ]
    )
    return df.drop(["_c1", "_v1", "_rp1", "_adr10", "_adr50", "_c_252d"])


# ── Signal generation (identical to qullamaggie-signals-v4.py: no tight_range) ─


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
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > MIN_PRICE)
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date"])
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


# ── Fill analysis ──────────────────────────────────────────────────────────────


def run_fill_analysis(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_lows: dict[str, np.ndarray],
) -> tuple[int, int, dict[tuple[float, int], list[int]]]:
    """Sweep the X% x Y-day fill grid over all signals.

    For each signal and each limit discount X%, finds the first trading day (starting
    the day after the signal) whose low <= signal_day_close * (1 - X%); the fill counts
    toward every window Y that the touch falls inside (calendar days from the signal).

    Returns (n_attempted, n_full_window, fills) where n_attempted counts signals with at
    least one following bar, n_full_window counts those with data covering the longest
    window, and fills maps (limit_pct, window_cal) -> list of trading-days-to-fill.
    """
    max_window = max(WINDOWS_CAL)
    fills: dict[tuple[float, int], list[int]] = {(lp, w): [] for lp in LIMIT_PCTS for w in WINDOWS_CAL}
    n_attempted = 0
    n_full_window = 0
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        lows = sym_lows[sym]
        signal_int = (row["date"] - _EPOCH).days
        idx_signal = int(np.searchsorted(dates, signal_int))
        if idx_signal >= len(dates) or dates[idx_signal] != signal_int:
            continue

        idx_start = idx_signal + 1
        if idx_start >= len(dates):
            continue

        n_attempted += 1
        if dates[-1] >= signal_int + max_window:
            n_full_window += 1
        idx_end = int(np.searchsorted(dates, signal_int + max_window, side="right")) - 1
        idx_end = min(idx_end, len(dates) - 1)

        for lp in LIMIT_PCTS:
            limit_price = closes[idx_signal] * (1.0 - lp)
            for idx in range(idx_start, idx_end + 1):
                if lows[idx] <= limit_price:
                    days_cal = int(dates[idx]) - signal_int
                    days_trading = idx - idx_signal
                    for w in WINDOWS_CAL:
                        if days_cal <= w:
                            fills[(lp, w)].append(days_trading)
                    break
    return n_attempted, n_full_window, fills


# ── Output ─────────────────────────────────────────────────────────────────────


def build_grid(n_attempted: int, fills: dict[tuple[float, int], list[int]]) -> str:
    blocks = [f"{f'Y={w}d':^22}" for w in WINDOWS_CAL]
    hdr1 = f"{'X%':>4}  | " + " | ".join(blocks)
    hdr2 = f"{'':>4}  | " + " | ".join(f"{'Fill%':>7} {'MedD':>6} {'MeanD':>6}" for _ in WINDOWS_CAL)
    sep = "-" * len(hdr2)
    lines = [hdr1, hdr2, sep]
    for lp in LIMIT_PCTS:
        cells = []
        for w in WINDOWS_CAL:
            d = fills[(lp, w)]
            if d:
                fill_pct = len(d) / n_attempted * 100
                cells.append(f"{fill_pct:>6.1f}% {float(np.median(d)):>6.1f} {float(np.mean(d)):>6.1f}")
            else:
                cells.append(f"{'--':>7} {'--':>6} {'--':>6}")
        lines.append(f"{lp * 100:>3.0f}%  | " + " | ".join(cells))
    return "\n".join(lines)


def build_counts(n_attempted: int, fills: dict[tuple[float, int], list[int]]) -> str:
    hdr = f"{'X%':>4}  | " + " | ".join(f"{f'n_filled Y={w}d':>14}" for w in WINDOWS_CAL)
    sep = "-" * len(hdr)
    lines = [hdr, sep]
    for lp in LIMIT_PCTS:
        cells = [f"{len(fills[(lp, w)]):>14}" for w in WINDOWS_CAL]
        lines.append(f"{lp * 100:>3.0f}%  | " + " | ".join(cells))
    return "\n".join(lines)


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

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    sym_lows: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_lows[sym] = g["low"].cast(pl.Float64).to_numpy(allow_copy=True)

    print(f"Generating signals for {LABEL} …", flush=True)
    signals = get_signals(df, bull_dates, SMA_T)
    print(f"  {len(signals)} raw signals", flush=True)

    print("Running fill analysis …", flush=True)
    n_attempted, n_full_window, fills = run_fill_analysis(signals, sym_dates, sym_closes, sym_lows)

    grid = build_grid(n_attempted, fills)
    counts = build_counts(n_attempted, fills)
    summary = (
        f"N signals: {len(signals)}  |  N attempted (>=1 bar after signal): {n_attempted}  |  "
        f"N with full {max(WINDOWS_CAL)}d window of data: {n_full_window}"
    )

    print("\n" + summary)
    print("\n" + grid)
    print("\n" + counts)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write(f"# Limit-Order Fill Rate — {LABEL}\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write(f"Period: {EVAL_START} – {EVAL_END}\n\n")
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Signal | {LABEL}: 50d-high breakout, close >12% above SMA50, 12m ROC < 100% |\n")
        fh.write(f"| Limit sweep | X% = {', '.join(f'{lp * 100:.0f}%' for lp in LIMIT_PCTS)} |\n")
        fh.write(f"| Window sweep | Y = {', '.join(f'{w}d' for w in WINDOWS_CAL)} (calendar days after the signal day) |\n")
        fh.write(
            "| Fill rule | resting limit at signal_day_close x (1 - X%), eligible from the day after the signal; "
            "fills on the first trading day whose low <= limit price within Y calendar days, else expires unfilled "
            "(adjusted prices, same convention as scripts/qullamaggie-limit-order-cohorts.py) |\n"
        )
        fh.write("| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, no tight_range |\n")
        fh.write("| Market regime | SPY close > 200d SMA |\n")
        fh.write(f"| Price range | > ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f} |\n")
        fh.write(f"| Min avg vol (20d) | >= {MIN_AVG_VOL // 1000}K |\n")
        fh.write(f"| Cooldown | {COOLDOWN} calendar days |\n")
        fh.write("| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |\n\n")
        fh.write("## Results\n\n")
        fh.write(f"{summary}\n\n")
        fh.write(
            "Fill% = n_filled / N attempted. MedD/MeanD = median/mean trading days from the signal day to the "
            "fill day, filled orders only (1 = fills on the first trading day after the signal).\n\n"
        )
        fh.write("```text\n")
        fh.write(grid)
        fh.write("\n```\n\n")
        fh.write("### n_filled per cell\n\n")
        fh.write("```text\n")
        fh.write(counts)
        fh.write("\n```\n\n")
        fh.write("## Findings & Caveats\n\n")
        fh.write(
            "- **Truncated windows near the end of data**: signals in the last 90 calendar days of the period "
            "have fewer forward bars than the window nominally allows, so Fill% for the longer windows is "
            "slightly understated for those signals (denominator counts every signal with at least one "
            "following bar, matching scripts/qullamaggie-limit-order-cohorts.py).\n\n"
        )
        fh.write(
            "- **First-touch convention**: a fill is the first day the low touches the limit; MedD/MeanD "
            "therefore measure time to the *first* touch, not how long the price stayed below the limit.\n\n"
        )
        fh.write(
            "- **No execution costs or queue effects**: touching the limit is assumed to fill in full; a real "
            "resting order carries queue-priority risk at exactly-touched prices, and a gap-down open below the "
            "limit would fill at the open (better than modeled).\n"
        )
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
