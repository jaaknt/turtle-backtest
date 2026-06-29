#!/usr/bin/env python3
"""
Limit-order fill sensitivity test for bk50d_s15_tr15_v1.2_roc100 / 366d.

Baseline: buy at signal-day close (EOD, current behaviour).
Limit sweep: place limit buy on the NEXT trading day at
             close * (1 - limit_pct) for limit_pct ∈ {0%, 0.5%, 1%, 1.5%, 2%, 3%}.
A limit order fills when next-day low ≤ limit_price; entry price = limit_price.

Period: 2010-01-01 – 2026-06-30  (burn-in data from 2008-01-01)
"""

import datetime
import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2010, 1, 1)
EVAL_END = date(2026, 6, 30)
HOLD_CAL = 366
HOLD_MAX_CAL = 366  # require this many cal days of fwd data
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.80
VOL_SURGE = 1.0
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
SMA_T = 0.15
TR_T = 0.15
MIN_TRADES = 30
MIN_NEG = 10

LIMIT_PCTS = [0.000, 0.005, 0.010, 0.015, 0.020, 0.030]


# ── Data loading ────────────────────────────────────────────────────────────────


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= '2007-06-01'
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
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
               db.open::float8  AS open,
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
          AND  db.date >= '2008-01-01'
          AND  db.close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    return pl.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "date": pl.Series([r[1] for r in rows], dtype=pl.Date),
            "open": [float(r[2]) for r in rows],
            "close": [float(r[3]) for r in rows],
            "high": [float(r[4]) for r in rows],
            "low": [float(r[5]) for r in rows],
            "volume": [int(r[6]) for r in rows],
        }
    )


# ── Indicators ──────────────────────────────────────────────────────────────────


def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
            (pl.col("high") - pl.col("low")).shift(1).over("symbol").alias("_dr1"),
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
            pl.col("_c1").rolling_mean(10, min_samples=10).over("symbol").alias("sma10"),
            pl.col("_c1").rolling_mean(20, min_samples=20).over("symbol").alias("sma20"),
            pl.col("_c1").rolling_mean(50, min_samples=50).over("symbol").alias("sma50"),
            pl.col("_v1").rolling_mean(50, min_samples=50).over("symbol").alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(20, min_samples=20).over("symbol").alias("avg_vol_20"),
            pl.col("_v1").rolling_mean(10, min_samples=10).over("symbol").alias("avg_vol_10"),
            pl.col("_c1").rolling_max(50, min_samples=50).over("symbol").alias("max_c_50d"),
            pl.col("_c1").rolling_max(10, min_samples=10).over("symbol").alias("_tr_max"),
            pl.col("_c1").rolling_min(10, min_samples=10).over("symbol").alias("_tr_min"),
            pl.col("_c1").rolling_mean(10, min_samples=10).over("symbol").alias("_tr_mean"),
            pl.col("_dr1").rolling_mean(20, min_samples=20).over("symbol").alias("_adr_num"),
            pl.col("_c1").shift(251).over("symbol").alias("_c_252d"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("_tr_max") - pl.col("_tr_min")) / pl.col("_tr_mean")).alias("tight_range_ratio"),
            ((pl.col("close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr_num") / pl.col("sma50")).alias("adr_pct"),
            (pl.col("close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
        ]
    )
    return df.drop(["_c1", "_v1", "_dr1", "_tr_max", "_tr_min", "_tr_mean", "_adr_num", "_c_252d"])


# ── Signal generation ────────────────────────────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date]) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("tight_range_ratio").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & (pl.col("rsi14") < 80.0)
            & (pl.col("close") > MIN_PRICE)
            & (pl.col("close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= 0.025)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") >= SMA_T)
            & (pl.col("tight_range_ratio") <= TR_T)
            & (pl.col("volume").cast(pl.Float64) > VOL_SURGE * pl.col("avg_vol_50"))
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "close"])
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


# ── Trade runners ────────────────────────────────────────────────────────────────


def run_trades_next_open(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_opens: dict[str, np.ndarray],
) -> list[dict]:
    """Buy at next trading day's open price (always fills)."""
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        opens = sym_opens[sym]
        signal_int = (row["date"] - _EPOCH).days
        idx_signal = int(np.searchsorted(dates, signal_int))
        if idx_signal >= len(dates) or dates[idx_signal] != signal_int:
            continue
        idx_entry = idx_signal + 1
        if idx_entry >= len(dates):
            continue
        entry_day_int = int(dates[idx_entry])
        if dates[-1] < entry_day_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_day_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        entry_price = opens[idx_entry]
        exit_price = closes[idx_exit]
        ret = float((exit_price - entry_price) / entry_price)
        records.append({"year": row["date"].year, "ret": ret})
    return records


def run_trades_eod(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
    """Buy at signal-day close (baseline)."""
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        entry_int = (row["date"] - _EPOCH).days
        idx_entry = int(np.searchsorted(dates, entry_int))
        if idx_entry >= len(dates) or dates[idx_entry] != entry_int:
            continue
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        entry_price = closes[idx_entry]
        exit_price = closes[idx_exit]
        ret = float((exit_price - entry_price) / entry_price)
        records.append({"year": row["date"].year, "ret": ret})
    return records


def run_trades_limit(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_lows: dict[str, np.ndarray],
    limit_pct: float,
) -> tuple[list[dict], int, int]:
    """
    Buy via limit order on next trading day.
    Returns (records, n_signals_attempted, n_filled).
    """
    records: list[dict] = []
    n_attempted = 0
    n_filled = 0
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

        # Next trading day for limit order
        idx_limit_day = idx_signal + 1
        if idx_limit_day >= len(dates):
            continue

        n_attempted += 1

        limit_price = closes[idx_signal] * (1.0 - limit_pct)

        # Fill if next day's low touches the limit price
        if lows[idx_limit_day] > limit_price:
            continue  # order didn't fill

        n_filled += 1

        # Require enough forward data from limit day
        limit_day_int = int(dates[idx_limit_day])
        if dates[-1] < limit_day_int + HOLD_MAX_CAL:
            continue

        idx_exit = int(np.searchsorted(dates, limit_day_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue

        entry_price = limit_price
        exit_price = closes[idx_exit]
        ret = float((exit_price - entry_price) / entry_price)
        limit_date_obj = datetime.date.fromordinal(_EPOCH.toordinal() + limit_day_int)
        records.append({"year": limit_date_obj.year, "ret": ret})
    return records, n_attempted, n_filled


# ── Metrics ──────────────────────────────────────────────────────────────────────


def sortino(a: np.ndarray) -> float:
    neg = a[a < 0]
    if len(neg) < MIN_NEG:
        return float("nan")
    dd = float(np.sqrt(np.mean(neg**2)))
    return float(np.mean(a) * np.sqrt(365 / HOLD_CAL) / dd) if dd > 0 else float("nan")


def compute_metrics(records: list[dict]) -> dict | None:
    if len(records) < MIN_TRADES:
        return None
    a = np.array([r["ret"] for r in records])
    sr = sortino(a)
    if np.isnan(sr) or sr <= 0:
        return None
    p5 = max(1, int(np.floor(len(a) * 0.05)))
    gross_win = float(a[a > 0].sum())
    gross_loss = float(-a[a < 0].sum())
    return {
        "n": len(a),
        "win": float((a > 0).mean() * 100),
        "mean": float(a.mean() * 100),
        "med": float(np.median(a) * 100),
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
        "sr": sr,
        "cvar": float(np.sort(a)[:p5].mean() * 100),
    }


# ── Output ────────────────────────────────────────────────────────────────────────

_HDR = (
    f"{'Entry mode':<22}  {'Fill%':>6}  {'N':>4}  "
    f"{'Win%':>5}  {'Mean%':>7}  {'Med%':>7}  {'PF':>5}  {'Sortino':>7}  {'CVaR%':>7}"
)
_SEP = "─" * len(_HDR)


def fmt_row(label: str, fill_pct: str, m: dict) -> str:
    return (
        f"{label:<22}  {fill_pct:>6}  {m['n']:>4}  "
        f"{m['win']:>5.1f}  {m['mean']:>+7.2f}  {m['med']:>+7.2f}  {m['pf']:>5.2f}  "
        f"{m['sr']:>7.3f}  {m['cvar']:>+7.2f}"
    )


# ── Main ──────────────────────────────────────────────────────────────────────────


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
    sym_opens: dict[str, np.ndarray] = {}
    sym_lows: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_opens[sym] = g["open"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_lows[sym] = g["low"].cast(pl.Float64).to_numpy(allow_copy=True)

    print("Generating signals …", flush=True)
    signals = get_signals(df, bull_dates)
    print(f"  {len(signals)} raw signals", flush=True)

    lines = [
        f"Strategy : bk50d_s{int(SMA_T * 100)}_tr{int(TR_T * 100)}_v1.2_roc100 | Hold: {HOLD_CAL}d",
        f"Period   : {EVAL_START} – {EVAL_END}",
        f"Signals  : {len(signals)} (after {COOLDOWN}d cooldown)",
        "",
        _HDR,
        _SEP,
    ]

    # Baseline: EOD buy
    eod_records = run_trades_eod(signals, sym_dates, sym_closes)
    eod_m = compute_metrics(eod_records)
    if eod_m:
        lines.append(fmt_row("EOD (baseline)", "100%", eod_m))
    else:
        lines.append(f"{'EOD (baseline)':<22}  {'100%':>6}  insufficient trades")

    # Next-day open
    open_records = run_trades_next_open(signals, sym_dates, sym_closes, sym_opens)
    open_m = compute_metrics(open_records)
    if open_m:
        lines.append(fmt_row("next-day open", "100%", open_m))
    else:
        lines.append(f"{'next-day open':<22}  {'100%':>6}  insufficient trades")

    lines.append(_SEP)

    # Limit order sweep
    for lp in LIMIT_PCTS:
        label = f"limit -{lp * 100:.1f}%"
        records, n_att, n_fill = run_trades_limit(signals, sym_dates, sym_closes, sym_lows, lp)
        fill_pct = f"{n_fill / n_att * 100:.1f}%" if n_att > 0 else "n/a"
        m = compute_metrics(records)
        if m:
            lines.append(fmt_row(label, fill_pct, m))
        else:
            lines.append(f"{label:<22}  {fill_pct:>6}  {len(records):>4}  insufficient trades")

    output = "\n".join(lines)
    print("\n" + output)

    result_path = Path(__file__).parent.parent / "docs" / "research" / "result-limit-order-test.md"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("w") as fh:
        fh.write("# Limit Order Fill Sensitivity — bk50d_s15_tr15_v1.2_roc100 / 366d\n\n")
        fh.write(f"Run date: {datetime.date.today()}\n\n")
        fh.write("```\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {result_path}", flush=True)


if __name__ == "__main__":
    main()
