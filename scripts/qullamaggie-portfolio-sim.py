#!/usr/bin/env python3
"""
Portfolio simulation for bk50d_s20 / s15 / s12 (v1.2_roc100, 366d).

Filters match scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=3.0%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K; tight_range and sma_alignment disabled).

close/high/low are split/dividend-adjusted (scaled by adjusted_close/close) so indicators,
entries, and mark-to-market aren't corrupted by split-day discontinuities; raw (unadjusted)
close is used only for the $5-$250 price band, matching scripts/qullamaggie-backtest-v4.py.

Rules:
  - Period 2020-01-01 .. 2026-06-26, initial equity $30,000.
  - Each signal: buy at the entry-day close, sizing = {3%,4%,5%,6%,7%,8%} of current portfolio
    value (cash + open positions marked to market).
  - If available cash < the target, skip the trade (no liquidity).
  - Exit at the close of the first trading day >= entry + 366 calendar days
    (open positions at period end are marked to market, not force-closed).
  - Fractional shares, no commission/slippage.

Alternative entry compared side-by-side with the EOD baseline: a resting limit buy at
signal_day_close * (1 - LIMIT_DISCOUNT), good for LIMIT_WINDOW_CAL calendar days. It fills on
the first day the low touches the limit price (subject to the same liquidity check, sized off
the portfolio value at the moment of the fill, not the signal day); if the price condition is
never met within the window, the order expires unfilled. Both approaches share the same 366d
time-based exit.

Outputs: monthly portfolio return + transaction-count grid (year x month), Max DD, Calmar,
Sortino, signals taken/skipped, average uninvested capital.
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
EVAL_START = date(2020, 1, 1)
EVAL_END = date(2026, 6, 26)
DATA_START = "2000-01-01"
INIT_EQUITY = 30_000.0
POS_FRACTIONS = [0.03, 0.04, 0.05, 0.06, 0.07, 0.08]  # position-size sweep
HOLD_CAL = 366
BELOW_DAYS = 3  # consecutive days below 200d SMA to trigger trend exit
STOP_DD = 0.30  # fixed stop: close <= (1-STOP_DD) * entry price
TRAIL_DD = 0.25  # trailing stop: close <= (1-TRAIL_DD) * peak-since-entry
RANK_FUNDING = False  # when cash is scarce, fund competing signals by ADR (desc)
LIMIT_DISCOUNT = 0.03  # alternative entry: resting limit at close * (1 - LIMIT_DISCOUNT)
LIMIT_WINDOW_CAL = 30  # limit order stays resting this many calendar days after the signal

EXIT_MODES = ["time"]  # 366d time cap only
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.90
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_FLOOR = 0.03
ADR_CHANGE_CAP = 0.90

CONFIGS = [
    ("s20", 0.20),
    ("s15", 0.15),
    ("s12", 0.12),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-portfolio-v4.md"


def load_spy(engine: sa.Engine) -> pl.DataFrame:
    sql = """
        SELECT date::date, close::float8 FROM turtle.daily_bars
        WHERE symbol = 'SPY.US' AND date >= '1999-01-01' ORDER BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    spy = pl.DataFrame(
        {
            "date": pl.Series([r[0] for r in rows], dtype=pl.Date),
            "close": [float(r[1]) for r in rows],
        }
    )
    return spy.with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))


def load_bars(engine: sa.Engine) -> pl.DataFrame:
    sql = """
        SELECT db.symbol, db.date::date AS date, db.close::float8 AS raw_close,
               db.adjusted_close::float8 AS close,
               db.high::float8 AS high, db.low::float8 AS low, db.volume::int8 AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA' AND t.type = 'Common Stock'
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= :data_start AND db.close > 0 AND db.adjusted_close > 0 AND db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"data_start": DATA_START}).fetchall()
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
            pl.col("_c1").rolling_mean(200, min_samples=200).over("symbol").alias("sma200"),
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
    return df


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
            & (pl.col("adr_pct") >= ADR_FLOOR)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "close", "adr_pct"])
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
    return pl.DataFrame(rows_out).sort("date") if rows_out else cands.clear()


def main() -> None:
    settings = Settings.from_toml()
    print("Loading SPY …", flush=True)
    spy = load_spy(settings.engine)
    bull_dates = set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())
    print("Loading bars …", flush=True)
    df = load_bars(settings.engine)
    valid = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid.to_list()))
    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    # per-symbol arrays for mark-to-market / entry / exit
    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    sym_lows: dict[str, np.ndarray] = {}
    sym_sma200: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_lows[sym] = g["low"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_sma200[sym] = g["sma200"].cast(pl.Float64).to_numpy(allow_copy=True)

    def _idx_on(sym: str, dint: int) -> int:
        d = sym_dates.get(sym)
        if d is None:
            return -1
        return int(np.searchsorted(d, dint, side="right")) - 1

    def price_on(sym: str, dint: int) -> float | None:
        idx = _idx_on(sym, dint)
        return float(sym_closes[sym][idx]) if idx >= 0 else None

    def low_on(sym: str, dint: int) -> float | None:
        idx = _idx_on(sym, dint)
        return float(sym_lows[sym][idx]) if idx >= 0 else None

    def below_sma200(sym: str, dint: int) -> bool:
        idx = _idx_on(sym, dint)
        if idx < 0:
            return False
        sma = sym_sma200[sym][idx]
        return bool(not np.isnan(sma) and sym_closes[sym][idx] < sma)

    # master trading calendar = SPY days within period
    cal = [d for d in spy["date"].to_list() if EVAL_START <= d <= EVAL_END]
    cal_int = [(d - _EPOCH).days for d in cal]

    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    def run_sim(signals_by_day: dict[int, list[dict]], exit_mode: str, pos_fraction: float) -> dict:
        cash = INIT_EQUITY
        positions: list[dict] = []
        equity_curve: list[tuple[date, float]] = []
        cash_curve: list[float] = []
        entry_dates: list[date] = []
        n_taken = n_skipped = n_exit_rule = 0

        for d, dint in zip(cal, cal_int, strict=False):
            still_open = []
            for p in positions:
                px = price_on(p["sym"], dint)
                if dint >= p["exit_int"]:  # 366d time cap (always)
                    if px is not None:
                        cash += p["shares"] * px
                    continue
                rule_hit = False
                if px is not None:
                    if exit_mode == "stop30":
                        rule_hit = px <= (1 - STOP_DD) * p["entry_px"]
                    elif exit_mode == "sma200x3":
                        p["below_cnt"] = p["below_cnt"] + 1 if below_sma200(p["sym"], dint) else 0
                        rule_hit = p["below_cnt"] >= BELOW_DAYS
                    elif exit_mode == "trail25":
                        p["peak"] = max(p["peak"], px)
                        rule_hit = px <= (1 - TRAIL_DD) * p["peak"]
                if rule_hit:
                    cash += p["shares"] * px
                    n_exit_rule += 1
                else:
                    still_open.append(p)
            positions = still_open

            mtm = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)

            day_sigs = signals_by_day.get(dint, [])
            if RANK_FUNDING:
                day_sigs = sorted(day_sigs, key=lambda s: s["adr_pct"], reverse=True)
            for s in day_sigs:
                target = pos_fraction * mtm
                entry_px = price_on(s["symbol"], dint)
                if entry_px is None or entry_px <= 0:
                    continue
                if cash + 1e-9 < target:
                    n_skipped += 1
                    continue
                cash -= target
                positions.append(
                    {
                        "sym": s["symbol"],
                        "shares": target / entry_px,
                        "entry_px": entry_px,
                        "exit_int": dint + HOLD_CAL,
                        "below_cnt": 0,
                        "peak": entry_px,
                    }
                )
                n_taken += 1
                entry_dates.append(d)

            equity = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)
            equity_curve.append((d, equity))
            cash_curve.append(cash)

        dates = [e[0] for e in equity_curve]
        eq = np.array([e[1] for e in equity_curve])
        cash_arr = np.array(cash_curve)
        avg_uninv_pct = float(np.mean(cash_arr / eq) * 100)
        avg_uninv_usd = float(np.mean(cash_arr))
        daily_ret = eq[1:] / eq[:-1] - 1.0
        max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
        n_days = (dates[-1] - dates[0]).days
        cagr = (eq[-1] / eq[0]) ** (365.0 / n_days) - 1.0
        calmar = cagr / abs(max_dd) if max_dd < 0 else float("inf")
        neg = daily_ret[daily_ret < 0]
        dd_daily = float(np.sqrt(np.mean(neg**2))) if len(neg) else float("nan")
        sortino = float(np.mean(daily_ret) * np.sqrt(252) / dd_daily) if dd_daily > 0 else float("nan")

        eq_df = pl.DataFrame({"date": pl.Series(dates, dtype=pl.Date), "eq": eq}).with_columns(
            [
                pl.col("date").dt.year().alias("year"),
                pl.col("date").dt.month().alias("month"),
            ]
        )
        eom = eq_df.group_by(["year", "month"]).agg(pl.col("eq").last().alias("eom")).sort(["year", "month"])
        eom = eom.with_columns((pl.col("eom") / pl.col("eom").shift(1) - 1.0).alias("ret"))
        eom = eom.with_columns(
            pl.when(pl.col("ret").is_null()).then(pl.col("eom") / INIT_EQUITY - 1.0).otherwise(pl.col("ret")).alias("ret")
        )
        return {
            "final": float(eq[-1]),
            "cagr": cagr,
            "max_dd": max_dd,
            "calmar": calmar,
            "sortino": sortino,
            "taken": n_taken,
            "skipped": n_skipped,
            "exit_rule": n_exit_rule,
            "avg_uninv_pct": avg_uninv_pct,
            "avg_uninv_usd": avg_uninv_usd,
            "eom": eom,
            "entries": entry_dates,
        }

    def run_sim_limit(signals_by_day: dict[int, list[dict]], pos_fraction: float) -> dict:
        """Resting limit buy at signal_day_close * (1 - LIMIT_DISCOUNT), good for
        LIMIT_WINDOW_CAL calendar days. Fills on the first day the low touches the limit
        price, sized off the portfolio value at the moment of the fill (not the signal day);
        if cash is short at that moment the order is dropped (liquidity skip, no retry). Same
        366d time-based exit as run_sim."""
        cash = INIT_EQUITY
        positions: list[dict] = []
        pending: list[dict] = []
        equity_curve: list[tuple[date, float]] = []
        cash_curve: list[float] = []
        entry_dates: list[date] = []
        n_taken = n_skipped = 0

        for d, dint in zip(cal, cal_int, strict=False):
            still_open = []
            for p in positions:
                if dint >= p["exit_int"]:
                    px = price_on(p["sym"], dint)
                    if px is not None:
                        cash += p["shares"] * px
                else:
                    still_open.append(p)
            positions = still_open

            still_pending = []
            for o in pending:
                if dint > o["expire_int"]:
                    n_skipped += 1
                    continue
                low = low_on(o["sym"], dint)
                if low is None or low > o["limit_price"]:
                    still_pending.append(o)
                    continue
                mtm = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)
                target = pos_fraction * mtm
                if cash + 1e-9 < target:
                    n_skipped += 1
                    continue
                cash -= target
                positions.append({"sym": o["sym"], "shares": target / o["limit_price"], "exit_int": dint + HOLD_CAL})
                n_taken += 1
                entry_dates.append(d)
            pending = still_pending

            for s in signals_by_day.get(dint, []):
                entry_px = price_on(s["symbol"], dint)
                if entry_px is None or entry_px <= 0:
                    continue
                pending.append(
                    {
                        "sym": s["symbol"],
                        "limit_price": entry_px * (1.0 - LIMIT_DISCOUNT),
                        "expire_int": dint + LIMIT_WINDOW_CAL,
                    }
                )

            equity = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)
            equity_curve.append((d, equity))
            cash_curve.append(cash)

        dates = [e[0] for e in equity_curve]
        eq = np.array([e[1] for e in equity_curve])
        cash_arr = np.array(cash_curve)
        avg_uninv_pct = float(np.mean(cash_arr / eq) * 100)
        avg_uninv_usd = float(np.mean(cash_arr))
        daily_ret = eq[1:] / eq[:-1] - 1.0
        max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
        n_days = (dates[-1] - dates[0]).days
        cagr = (eq[-1] / eq[0]) ** (365.0 / n_days) - 1.0
        calmar = cagr / abs(max_dd) if max_dd < 0 else float("inf")
        neg = daily_ret[daily_ret < 0]
        dd_daily = float(np.sqrt(np.mean(neg**2))) if len(neg) else float("nan")
        sortino = float(np.mean(daily_ret) * np.sqrt(252) / dd_daily) if dd_daily > 0 else float("nan")

        eq_df = pl.DataFrame({"date": pl.Series(dates, dtype=pl.Date), "eq": eq}).with_columns(
            [
                pl.col("date").dt.year().alias("year"),
                pl.col("date").dt.month().alias("month"),
            ]
        )
        eom = eq_df.group_by(["year", "month"]).agg(pl.col("eq").last().alias("eom")).sort(["year", "month"])
        eom = eom.with_columns((pl.col("eom") / pl.col("eom").shift(1) - 1.0).alias("ret"))
        eom = eom.with_columns(
            pl.when(pl.col("ret").is_null()).then(pl.col("eom") / INIT_EQUITY - 1.0).otherwise(pl.col("ret")).alias("ret")
        )
        return {
            "final": float(eq[-1]),
            "cagr": cagr,
            "max_dd": max_dd,
            "calmar": calmar,
            "sortino": sortino,
            "taken": n_taken,
            "skipped": n_skipped,
            "avg_uninv_pct": avg_uninv_pct,
            "avg_uninv_usd": avg_uninv_usd,
            "eom": eom,
            "entries": entry_dates,
        }

    def monthly_grid(eom: pl.DataFrame, entries: list[date]) -> None:
        entry_counts: dict[tuple[int, int], int] = {}
        for ed in entries:
            key = (ed.year, ed.month)
            entry_counts[key] = entry_counts.get(key, 0) + 1

        out("```text")
        header = f"{'Year':>5} | " + " ".join(f"{m:>9}" for m in MONTHS) + f" | {'Year%':>7} {'Txns':>5}"
        out(header)
        out("-" * len(header))
        for yr in sorted(eom["year"].unique().to_list()):
            parts, comp = [], 1.0
            year_txns = 0
            for mo in range(1, 13):
                r = eom.filter((pl.col("year") == yr) & (pl.col("month") == mo))["ret"].to_list()
                cnt = entry_counts.get((yr, mo), 0)
                year_txns += cnt
                if r:
                    cell = f"{r[0] * 100:+.1f}|{cnt}"
                    comp *= 1 + r[0]
                else:
                    cell = "·"
                parts.append(f"{cell:>9}")
            out(f"{yr:>5} | " + " ".join(parts) + f" | {(comp - 1) * 100:>+7.1f} {year_txns:>5}")
        out("```")

    def run_blend(s20_by_day: dict, s15_by_day: dict, pos_fraction: float) -> dict:
        """One cash pool. Each day fund s20 signals first, then s15 with leftover
        liquidity. Same-day same-symbol kept once (s20 priority)."""
        cash = INIT_EQUITY
        positions: list[dict] = []
        equity_curve: list[tuple[date, float]] = []
        cash_curve: list[float] = []
        n_s20 = n_s15 = n_skipped = 0

        for d, dint in zip(cal, cal_int, strict=False):
            still_open = []
            for p in positions:
                if dint >= p["exit_int"]:
                    px = price_on(p["sym"], dint)
                    if px is not None:
                        cash += p["shares"] * px
                else:
                    still_open.append(p)
            positions = still_open

            mtm = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)

            s20_syms = {s["symbol"] for s in s20_by_day.get(dint, [])}
            day_sigs = [{**s, "src": "s20"} for s in s20_by_day.get(dint, [])] + [
                {**s, "src": "s15"} for s in s15_by_day.get(dint, []) if s["symbol"] not in s20_syms
            ]
            for s in day_sigs:
                target = pos_fraction * mtm
                entry_px = price_on(s["symbol"], dint)
                if entry_px is None or entry_px <= 0:
                    continue
                if cash + 1e-9 < target:
                    n_skipped += 1
                    continue
                cash -= target
                positions.append({"sym": s["symbol"], "shares": target / entry_px, "exit_int": dint + HOLD_CAL})
                if s["src"] == "s20":
                    n_s20 += 1
                else:
                    n_s15 += 1

            equity = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)
            equity_curve.append((d, equity))
            cash_curve.append(cash)

        dates = [e[0] for e in equity_curve]
        eq = np.array([e[1] for e in equity_curve])
        cash_arr = np.array(cash_curve)
        daily_ret = eq[1:] / eq[:-1] - 1.0
        max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
        n_days = (dates[-1] - dates[0]).days
        cagr = (eq[-1] / eq[0]) ** (365.0 / n_days) - 1.0
        calmar = cagr / abs(max_dd) if max_dd < 0 else float("inf")
        neg = daily_ret[daily_ret < 0]
        dd_daily = float(np.sqrt(np.mean(neg**2))) if len(neg) else float("nan")
        sortino = float(np.mean(daily_ret) * np.sqrt(252) / dd_daily) if dd_daily > 0 else float("nan")
        eq_df = pl.DataFrame({"date": pl.Series(dates, dtype=pl.Date), "eq": eq}).with_columns(
            [pl.col("date").dt.year().alias("year"), pl.col("date").dt.month().alias("month")]
        )
        eom = eq_df.group_by(["year", "month"]).agg(pl.col("eq").last().alias("eom")).sort(["year", "month"])
        eom = eom.with_columns((pl.col("eom") / pl.col("eom").shift(1) - 1.0).alias("ret"))
        eom = eom.with_columns(
            pl.when(pl.col("ret").is_null()).then(pl.col("eom") / INIT_EQUITY - 1.0).otherwise(pl.col("ret")).alias("ret")
        )
        return {
            "final": float(eq[-1]),
            "cagr": cagr,
            "max_dd": max_dd,
            "calmar": calmar,
            "sortino": sortino,
            "n_s20": n_s20,
            "n_s15": n_s15,
            "skipped": n_skipped,
            "avg_uninv_pct": float(np.mean(cash_arr / eq) * 100),
            "avg_uninv_usd": float(np.mean(cash_arr)),
            "eom": eom,
        }

    out("# Portfolio Simulation — full-cycle size sweep (366d time-only)\n")
    out(f"Run date: {date.today()}")
    out(
        f"Period: {EVAL_START} – {EVAL_END}  |  Initial: ${INIT_EQUITY:,.0f}  |  "
        f"exit: time {HOLD_CAL}d only  |  sizes: {', '.join(f'{f:.0%}' for f in POS_FRACTIONS)}"
    )

    limit_label = f"LIMIT-{LIMIT_DISCOUNT * 100:.0f}%"

    # collect all results first (both approaches), then rank for monthly grids
    all_results: list[tuple[str, str, float, dict]] = []  # (name, approach, pos_fraction, result)

    for name, sma_t in CONFIGS:
        print(f"Simulating {name} …", flush=True)
        sig = get_signals(df, bull_dates, sma_t)
        signals_by_day: dict[int, list[dict]] = {}
        for r in sig.iter_rows(named=True):
            signals_by_day.setdefault((r["date"] - _EPOCH).days, []).append(r)

        out(f"\n\n## {name}  (bk50d_{name}_v1.2_roc100 / 366d)\n")
        hdr = f"{'size':<6} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8} {'taken':>6} {'skip':>6} {'Uninv%':>7}"

        out("### EOD (buy at signal-day close)\n")
        out(hdr)
        out("-" * len(hdr))
        eod_results: dict[float, dict] = {}
        for pf in POS_FRACTIONS:
            r = run_sim(signals_by_day, "time", pf)
            eod_results[pf] = r
            all_results.append((name, "EOD", pf, r))
            out(
                f"{pf:<6.0%} {r['final']:>11,.0f} {r['cagr'] * 100:>+7.2f} {r['max_dd'] * 100:>8.2f} "
                f"{r['calmar']:>7.3f} {r['sortino']:>8.3f} {r['taken']:>6} {r['skipped']:>6} "
                f"{r['avg_uninv_pct']:>6.1f}%"
            )

        out(f"\n### {limit_label} (resting {LIMIT_WINDOW_CAL}d, buy {LIMIT_DISCOUNT * 100:.0f}% below signal-day close)\n")
        out(hdr)
        out("-" * len(hdr))
        limit_results: dict[float, dict] = {}
        for pf in POS_FRACTIONS:
            r = run_sim_limit(signals_by_day, pf)
            limit_results[pf] = r
            all_results.append((name, limit_label, pf, r))
            out(
                f"{pf:<6.0%} {r['final']:>11,.0f} {r['cagr'] * 100:>+7.2f} {r['max_dd'] * 100:>8.2f} "
                f"{r['calmar']:>7.3f} {r['sortino']:>8.3f} {r['taken']:>6} {r['skipped']:>6} "
                f"{r['avg_uninv_pct']:>6.1f}%"
            )

        out(f"\n### EOD vs {limit_label} comparison\n")
        cmp_hdr = (
            f"{'size':<6} {'EOD Calmar':>11} {limit_label + ' Calmar':>16} {'EOD Sortino':>12} "
            f"{limit_label + ' Sortino':>17} {'EOD Final$':>12} {limit_label + ' Final$':>16}"
        )
        out(cmp_hdr)
        out("-" * len(cmp_hdr))
        for pf in POS_FRACTIONS:
            e = eod_results[pf]
            lm = limit_results[pf]
            out(
                f"{pf:<6.0%} {e['calmar']:>11.3f} {lm['calmar']:>16.3f} {e['sortino']:>12.3f} "
                f"{lm['sortino']:>17.3f} {e['final']:>12,.0f} {lm['final']:>16,.0f}"
            )

    # monthly grids for top 5 by Calmar, and separately top 5 by Final$ (both approaches combined)
    ranked_calmar = sorted(all_results, key=lambda x: x[3]["calmar"], reverse=True)
    out("\n\n## Monthly returns/transactions — top 5 by Calmar (EOD + limit combined)\n")
    for rank, (name, approach, pf, r) in enumerate(ranked_calmar[:5], 1):
        out(f"\n### #{rank}  {name} {approach} — size {pf:.0%}  (Calmar {r['calmar']:.3f})")
        monthly_grid(r["eom"], r["entries"])

    ranked_final = sorted(all_results, key=lambda x: x[3]["final"], reverse=True)
    out("\n\n## Monthly returns/transactions — top 5 by Final$ (EOD + limit combined)\n")
    for rank, (name, approach, pf, r) in enumerate(ranked_final[:5], 1):
        out(f"\n### #{rank}  {name} {approach} — size {pf:.0%}  (Final ${r['final']:,.0f})")
        monthly_grid(r["eom"], r["entries"])

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
