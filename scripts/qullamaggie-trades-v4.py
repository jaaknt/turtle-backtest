#!/usr/bin/env python3
"""
Current-period trade report for bk50d_s20_tr20_v1.2_roc100.

Filters match scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=2.5%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<80%, tight_range<20%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K). Display window: 2025-07-01 - today.
Candidate window starts earlier so the 30-day cooldown state is correct at the start of the
display window.
"""

import sys
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
ADR_MIN = 0.025
ADR_CHANGE_CAP = 0.90
TR_FIXED = 0.20
SMA_T = 0.20

STRATEGY_LABEL = "bk50d_s20_tr20_v1.2_roc100"

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-trades-v4.md"


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
               db.date::date    AS date,
               db.close::float8 AS close,
               db.high::float8  AS high,
               db.low::float8   AS low,
               db.volume::int8  AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= :start
          AND  db.close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"start": BAR_LOAD_START}).fetchall()
    return pl.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "date": pl.Series([r[1] for r in rows], dtype=pl.Date),
            "close": [float(r[2]) for r in rows],
            "high": [float(r[3]) for r in rows],
            "low": [float(r[4]) for r in rows],
            "volume": [int(r[5]) for r in rows],
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


def get_signals(df: pl.DataFrame, bull_dates: set[date]) -> pl.DataFrame:
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
            & (pl.col("close") > MIN_PRICE)
            & (pl.col("close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > SMA_T)
            & (pl.col("tight_range_ratio") < TR_FIXED)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "close", "pct_vs_sma50", "adr_pct", "adr_pct_change", "rsi14", "tight_range_ratio", "roc_252d"])
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
    latest_close: dict[str, float] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        latest_date[sym] = g["date"][-1]
        latest_close[sym] = float(g["close"][-1])

    print(f"Generating signals for {STRATEGY_LABEL} …", flush=True)
    sig = get_signals(df, bull_dates)
    sig = sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END)).sort(["date", "symbol"])
    print(f"  {len(sig)} signals in display window", flush=True)

    hdr = (
        f"{'Date':<11}│ {'Symbol':<7}│ {'Entry $':>8} │ {'Curr Price':>10} │ {'Change %':>9} │ "
        f"{'%abv SMA50':>10} │ {'ADR%':>6} │ {'ADR_CHG':>7} │ {'RSI14':>6} │ {'TR%':>6} │ {'ROC252%':>8} │ {'Latest Data':>11}"
    )
    sep = "─" * len(hdr)

    lines: list[str] = [hdr, sep]
    rets: list[float] = []
    for row in sig.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        entry = row["close"]
        curr = latest_close.get(sym, float("nan"))
        chg = (curr / entry - 1.0) * 100 if entry else float("nan")
        rets.append(chg)
        ld = latest_date.get(sym)
        lines.append(
            f"{str(d):<11}│ {sym:<7}│ {entry:>8.2f} │ {curr:>10.2f} │ {chg:>+8.1f}% │ "
            f"{row['pct_vs_sma50'] * 100:>+9.1f}% │ {row['adr_pct'] * 100:>5.1f}% │ {row['adr_pct_change']:>7.2f} │ "
            f"{row['rsi14']:>6.1f} │ {row['tight_range_ratio'] * 100:>5.1f}% │ {row['roc_252d'] * 100:>+7.1f}% │ {str(ld):>11}"
        )

    lines.append(sep)
    n = len(rets)
    mean_ret = float(np.mean(rets)) if n else float("nan")
    summary = (
        f"\nIf every open trade were closed at its symbol's latest available price:\n"
        f"  Trade count (N): {n}\n"
        f"  Mean trade performance: {mean_ret:+.2f}%"
    )
    lines.append(summary)

    output = "\n".join(lines)
    print("\n" + output)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write(f"# {STRATEGY_LABEL} — Trade Report\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write(f"Period: {DISPLAY_START} – {DISPLAY_END}\n\n")
        fh.write("```\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
