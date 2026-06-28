#!/usr/bin/env python3
"""
Monthly mean return by year + yearly statistics for two v4 configs.

Targets:
  bk50d_s25_tr15_v1.2  time_366d
  bk50d_s20_tr10_v1.2  time_366d
"""

import sys
from datetime import date
from pathlib import Path
from typing import TypedDict

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

# Same constants as v4
_EPOCH = date(1970, 1, 1)
EVAL_START = date(2001, 1, 1)
MIN_AVG_VOL = 300_000
MIN_PRICE = 5.0
MIN_HISTORY = 300
COOLDOWN = 30

VOL_DRY_UP_RATIO = 0.85
HOLD_MAX_CAL = 366  # skip entries without 366 calendar days of forward data


class TargetCfg(TypedDict):
    bd: int
    sma: float
    tr: float
    vs: float
    hold_cal: int
    exit: str


TARGETS: list[TargetCfg] = [
    {"bd": 50, "sma": 0.20, "tr": 0.10, "vs": 1.2, "hold_cal": 62, "exit": "time_62d"},
    {"bd": 50, "sma": 0.20, "tr": 0.10, "vs": 1.2, "hold_cal": 366, "exit": "time_366d"},
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def sig_label(bd: int, sma: float, tr: float, vs: float) -> str:
    return f"bk{bd}d_s{int(sma * 100)}_tr{int(tr * 100)}_v{vs}"


def load_spy_regime(engine: sa.Engine) -> tuple[set[date], pl.DataFrame]:
    sql = """
        SELECT date::date AS date, close::float8 AS close
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US'
          AND  date >= '2000-01-01'
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
    spy = spy.with_columns(pl.col("close").shift(1).alias("_c1"))
    spy = spy.with_columns(pl.col("_c1").rolling_mean(window_size=200, min_samples=200).alias("sma200"))
    bull_dates = set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())
    return bull_dates, spy


def load_ticker_bars(engine: sa.Engine, symbol: str) -> pl.DataFrame:
    sql = """
        SELECT date::date AS date, close::float8 AS close
        FROM   turtle.daily_bars
        WHERE  symbol = :symbol
          AND  date >= '2000-01-01'
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol}).fetchall()
    return pl.DataFrame(
        {
            "date": pl.Series([r[0] for r in rows], dtype=pl.Date),
            "close": [float(r[1]) for r in rows],
        }
    )


def compute_spy_monthly(spy: pl.DataFrame) -> pl.DataFrame:
    """Month-over-month SPY return: last close of month / last close of prior month - 1."""
    monthly = (
        spy.sort("date")
        .with_columns(
            [
                pl.col("date").dt.year().alias("year"),
                pl.col("date").dt.month().alias("month"),
            ]
        )
        .group_by(["year", "month"])
        .agg(pl.col("close").last().alias("eom_close"))
        .sort(["year", "month"])
    )
    monthly = monthly.with_columns((pl.col("eom_close") / pl.col("eom_close").shift(1) - 1.0).alias("ret"))
    return monthly.filter(pl.col("ret").is_not_null()).select(["year", "month", "ret"])


def print_spy_monthly_table(spy_monthly: pl.DataFrame, title: str = "SPY Monthly Returns (calendar month close-to-close)") -> None:
    spy_monthly = spy_monthly.filter(pl.col("year") >= EVAL_START.year)
    years = sorted(spy_monthly["year"].unique().to_list())
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")
    header = f"{'Year':>5} | " + " ".join(f"{m:>6}" for m in MONTHS) + f" | {'Ann%':>6}"
    print(header)
    print("-" * len(header))
    for yr in years:
        yr_data = spy_monthly.filter(pl.col("year") == yr)
        row_parts = []
        yr_rets = []
        for mo in range(1, 13):
            mo_data = yr_data.filter(pl.col("month") == mo)["ret"].to_list()
            if mo_data:
                row_parts.append(f"{mo_data[0] * 100:>+6.1f}")
                yr_rets.append(mo_data[0])
            else:
                row_parts.append(f"{'·':>6}")
        if yr_rets:
            ann = (np.prod([1 + r for r in yr_rets]) - 1) * 100
            print(f"{yr:>5} | " + " ".join(row_parts) + f" | {ann:>+6.1f}")
        else:
            print(f"{yr:>5} | " + " ".join(row_parts) + f" | {'·':>6}")
    print("-" * len(header))
    all_rets = spy_monthly["ret"].to_list()
    years_count = len(years)
    avg_ann = ((np.prod([1 + r for r in all_rets]) ** (1 / years_count)) - 1) * 100 if years_count else 0
    print(f"{'CAGR':>5} | " + " " * (len(header) - 14) + f" | {avg_ann:>+6.1f}")


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
          AND  c.market_cap >= 2000000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= '2000-01-01'
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
            (pl.col("high") - pl.col("low")).shift(1).over("symbol").alias("_dr1"),
        ]
    )
    df = df.with_columns([pl.col("_c1").diff(1).over("symbol").alias("_c1_diff")])
    df = df.with_columns(
        [
            pl.when(pl.col("_c1_diff") > 0).then(pl.col("_c1_diff")).otherwise(0.0).alias("_gain"),
            pl.when(pl.col("_c1_diff") < 0).then(-pl.col("_c1_diff")).otherwise(0.0).alias("_loss"),
        ]
    )
    df = df.with_columns(
        [
            pl.col("_gain").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_gain"),
            pl.col("_loss").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_loss"),
        ]
    )
    df = df.with_columns(
        [
            (100.0 - 100.0 / (1.0 + pl.col("_avg_gain") / pl.col("_avg_loss"))).alias("rsi14"),
        ]
    )
    df = df.drop(["_c1_diff", "_gain", "_loss", "_avg_gain", "_avg_loss"])
    df = df.with_columns(
        [
            pl.col("_c1").rolling_mean(window_size=10, min_samples=10).over("symbol").alias("sma10"),
            pl.col("_c1").rolling_mean(window_size=20, min_samples=20).over("symbol").alias("sma20"),
            pl.col("_c1").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("sma50"),
            pl.col("_v1").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(window_size=20, min_samples=20).over("symbol").alias("avg_vol_20"),
            pl.col("_v1").rolling_mean(window_size=10, min_samples=10).over("symbol").alias("avg_vol_10"),
            pl.col("_c1").rolling_max(window_size=50, min_samples=50).over("symbol").alias("max_c_50d"),
            pl.col("_c1").rolling_max(window_size=10, min_samples=10).over("symbol").alias("_tr_max"),
            pl.col("_c1").rolling_min(window_size=10, min_samples=10).over("symbol").alias("_tr_min"),
            pl.col("_c1").rolling_mean(window_size=10, min_samples=10).over("symbol").alias("_tr_mean"),
            pl.col("_dr1").rolling_mean(window_size=20, min_samples=20).over("symbol").alias("_adr_num"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("_tr_max") - pl.col("_tr_min")) / pl.col("_tr_mean")).alias("tight_range_ratio"),
            ((pl.col("close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr_num") / pl.col("sma50")).alias("adr_pct"),
        ]
    )
    return df.drop(["_c1", "_v1", "_dr1", "_tr_max", "_tr_min", "_tr_mean", "_adr_num"])


def get_signals(df: pl.DataFrame, bd: int, sma: float, tr: float, vs: float) -> pl.DataFrame:
    max_col = "max_c_50d"
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & pl.col("sma50").is_not_null()
            & pl.col(max_col).is_not_null()
            & pl.col("tight_range_ratio").is_not_null()
            & pl.col("rsi14").is_not_null()
            & (pl.col("rsi14") < 80.0)
            & (pl.col("close") >= MIN_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= 0.03)
            & (pl.col("sma10") > pl.col("sma20"))
            & (pl.col("sma20") > pl.col("sma50"))
            & (pl.col("close") > pl.col(max_col))
            & (pl.col("pct_vs_sma50") >= sma)
            & (pl.col("tight_range_ratio") <= tr)
            & (pl.col("volume").cast(pl.Float64) > vs * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP_RATIO * pl.col("avg_vol_50"))
            & pl.col("spy_above_200d")
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


def compute_trade_records(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    hold_cal: int,
) -> pl.DataFrame:
    """Return DataFrame with (year, month, ret) for each completed trade.
    Exit at first trading day >= entry + hold_cal calendar days.
    Skip entries without HOLD_MAX_CAL calendar days of forward data."""
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
        idx_exit = int(np.searchsorted(dates, entry_int + hold_cal))
        if idx_exit >= len(dates):
            continue
        window = closes[idx_entry : idx_exit + 1]
        if len(window) < 2:
            continue
        ret = float((window[-1] - window[0]) / window[0])
        records.append({"year": row["date"].year, "month": row["date"].month, "ret": ret})
    if not records:
        return pl.DataFrame(schema={"year": pl.Int32, "month": pl.Int32, "ret": pl.Float64})
    return pl.DataFrame(records)


def print_monthly_table(trades: pl.DataFrame, label: str) -> None:
    years = sorted(trades["year"].unique().to_list())
    print(f"\n{'─' * 70}")
    print(f"  {label}")
    print(f"{'─' * 70}")

    # Header
    header = f"{'Year':>5} | " + " ".join(f"{m:>6}" for m in MONTHS) + f" | {'Mean':>6} {'N':>4}"
    print(header)
    print("-" * len(header))

    for yr in years:
        yr_trades = trades.filter(pl.col("year") == yr)
        row_parts = []
        for mo in range(1, 13):
            mo_rets = yr_trades.filter(pl.col("month") == mo)["ret"].to_list()
            if mo_rets:
                row_parts.append(f"{np.mean(mo_rets) * 100:>+6.1f}")
            else:
                row_parts.append(f"{'·':>6}")
        yr_rets = yr_trades["ret"].to_numpy()
        yr_mean = np.mean(yr_rets) * 100
        n = len(yr_rets)
        print(f"{yr:>5} | " + " ".join(row_parts) + f" | {yr_mean:>+6.1f} {n:>4}")

    # Totals row
    row_parts = []
    for mo in range(1, 13):
        mo_rets = trades.filter(pl.col("month") == mo)["ret"].to_list()
        if mo_rets:
            row_parts.append(f"{np.mean(mo_rets) * 100:>+6.1f}")
        else:
            row_parts.append(f"{'·':>6}")
    all_rets = trades["ret"].to_numpy()
    print("-" * len(header))
    print(f"{'All':>5} | " + " ".join(row_parts) + f" | {np.mean(all_rets) * 100:>+6.1f} {len(all_rets):>4}")


def print_yearly_stats(trades: pl.DataFrame, label: str, hold_cal: int) -> None:
    years = sorted(trades["year"].unique().to_list())
    print(f"\n  Yearly Statistics — {label}")
    print(f"  {'Year':>5} {'N':>5} {'Win%':>6} {'Mean%':>7} {'Med%':>6} {'Sortino':>9} {'CVaR95%':>8}")
    print(f"  {'-' * 5} {'-' * 5} {'-' * 6} {'-' * 7} {'-' * 6} {'-' * 9} {'-' * 8}")

    for yr in years:
        a = trades.filter(pl.col("year") == yr)["ret"].to_numpy()
        n = len(a)
        win_pct = float((a > 0).sum() / n * 100)
        mean_pct = float(np.mean(a) * 100)
        med_pct = float(np.median(a) * 100)
        neg = a[a < 0]
        if len(neg) >= 3:
            dd = float(np.sqrt(np.mean(neg**2)))
            sortino = float(np.mean(a) * np.sqrt(365 / hold_cal) / dd) if dd > 0 else float("nan")
        else:
            sortino = float("nan")
        p5 = max(1, int(np.floor(n * 0.05)))
        cvar = float(np.sort(a)[:p5].mean() * 100)
        sortino_str = f"{sortino:>9.3f}" if not np.isnan(sortino) else f"{'n/a':>9}"
        print(f"  {yr:>5} {n:>5} {win_pct:>6.1f} {mean_pct:>+7.2f} {med_pct:>+6.2f} {sortino_str} {cvar:>8.2f}")

    print(f"  {'-' * 5} {'-' * 5} {'-' * 6} {'-' * 7} {'-' * 6} {'-' * 9} {'-' * 8}")
    a = trades["ret"].to_numpy()
    n = len(a)
    neg = a[a < 0]
    if len(neg) >= 3:
        dd = float(np.sqrt(np.mean(neg**2)))
        sortino = float(np.mean(a) * np.sqrt(365 / hold_cal) / dd) if dd > 0 else float("nan")
    else:
        sortino = float("nan")
    p5 = max(1, int(np.floor(n * 0.05)))
    cvar = float(np.sort(a)[:p5].mean() * 100)
    sortino_str = f"{sortino:>9.3f}" if not np.isnan(sortino) else f"{'n/a':>9}"
    print(
        f"  {'All':>5} {n:>5} {float((a > 0).sum() / n * 100):>6.1f} "
        f"{float(np.mean(a) * 100):>+7.2f} {float(np.median(a) * 100):>+6.2f} "
        f"{sortino_str} {cvar:>8.2f}"
    )


def main() -> None:
    settings = Settings.from_toml()

    print("Loading bars …", flush=True)
    df = load_bars(settings.engine)
    counts = df.group_by("symbol").agg(pl.len().alias("n"))
    valid = counts.filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid.to_list()))

    print("Loading SPY regime …", flush=True)
    spy_bull_dates, spy_df = load_spy_regime(settings.engine)
    df = df.with_columns(pl.col("date").is_in(spy_bull_dates).alias("spy_above_200d"))

    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)

    for cfg in TARGETS:
        label = f"{sig_label(cfg['bd'], cfg['sma'], cfg['tr'], cfg['vs'])}  {cfg['exit']}"
        print(f"\nGenerating signals for {label} …", flush=True)
        sigs = get_signals(df, cfg["bd"], cfg["sma"], cfg["tr"], cfg["vs"])
        trades = compute_trade_records(sigs, sym_dates, sym_closes, cfg["hold_cal"])
        print_monthly_table(trades, label)
        print_yearly_stats(trades, label, cfg["hold_cal"])

    spy_monthly = compute_spy_monthly(spy_df)
    print_spy_monthly_table(spy_monthly, "SPY Monthly Returns (calendar month close-to-close)")

    print("\nLoading QQQ …", flush=True)
    qqq_df = load_ticker_bars(settings.engine, "QQQ.US")
    qqq_monthly = compute_spy_monthly(qqq_df)
    print_spy_monthly_table(qqq_monthly, "QQQ Monthly Returns (calendar month close-to-close)")


if __name__ == "__main__":
    main()
