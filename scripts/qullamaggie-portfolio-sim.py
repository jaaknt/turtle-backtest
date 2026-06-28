#!/usr/bin/env python3
"""
Portfolio simulation for bk50d_s20_tr10_v1.2_roc100 / 366d.

Rules:
  - Period 2021-01-01 .. 2026-06-26, initial equity $30,000.
  - Each signal: buy at the entry-day close, sizing = 10% of current portfolio
    value (cash + open positions marked to market).
  - If available cash < the 10% target, skip the trade (no liquidity).
  - Exit at the close of the first trading day >= entry + 366 calendar days
    (open positions at period end are marked to market, not force-closed).
  - Fractional shares, no commission/slippage.

Outputs: monthly portfolio return grid (year x month), Max DD, Calmar, Sortino.
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
EVAL_START = date(2001, 1, 1)
EVAL_END = date(2026, 6, 26)
DATA_START = "2000-01-01"
INIT_EQUITY = 30_000.0
POS_FRACTIONS = [0.03, 0.04, 0.05]  # position-size sweep
HOLD_CAL = 366
BELOW_DAYS = 3  # consecutive days below 200d SMA to trigger trend exit
STOP_DD = 0.30  # fixed stop: close <= (1-STOP_DD) * entry price
TRAIL_DD = 0.25  # trailing stop: close <= (1-TRAIL_DD) * peak-since-entry
RANK_FUNDING = False  # when cash is scarce, fund competing signals by ADR (desc)

EXIT_MODES = ["time"]  # each runs the full 366d time cap too
MIN_AVG_VOL = 500_000
MIN_PRICE = 10.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.80
VOL_SURGE = 1.0
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
ADR_FLOOR = 0.025

CONFIGS = [
    ("s20_tr10", 0.20, 0.10),
    ("s15_tr15", 0.15, 0.15),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-portfolio.md"


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
        SELECT db.symbol, db.date::date AS date, db.close::float8 AS close,
               db.high::float8 AS high, db.low::float8 AS low, db.volume::int8 AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA' AND t.type = 'Common Stock'
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= :data_start AND db.close > 0 AND db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"data_start": DATA_START}).fetchall()
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
    return df


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float, tr_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("tight_range_ratio").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & (pl.col("rsi14") < 72.0)
            & (pl.col("close") >= MIN_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_FLOOR)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") >= sma_t)
            & (pl.col("tight_range_ratio") <= tr_t)
            & (pl.col("volume").cast(pl.Float64) > VOL_SURGE * pl.col("avg_vol_50"))
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
    sym_sma200: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_sma200[sym] = g["sma200"].cast(pl.Float64).to_numpy(allow_copy=True)

    def _idx_on(sym: str, dint: int) -> int:
        d = sym_dates.get(sym)
        if d is None:
            return -1
        return int(np.searchsorted(d, dint, side="right")) - 1

    def price_on(sym: str, dint: int) -> float | None:
        idx = _idx_on(sym, dint)
        return float(sym_closes[sym][idx]) if idx >= 0 else None

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
        }

    def monthly_grid(eom: pl.DataFrame) -> None:
        out("```")
        header = f"{'Year':>5} | " + " ".join(f"{m:>6}" for m in MONTHS) + f" | {'Year%':>7}"
        out(header)
        out("-" * len(header))
        for yr in sorted(eom["year"].unique().to_list()):
            parts, comp = [], 1.0
            for mo in range(1, 13):
                r = eom.filter((pl.col("year") == yr) & (pl.col("month") == mo))["ret"].to_list()
                if r:
                    parts.append(f"{r[0] * 100:>+6.1f}")
                    comp *= 1 + r[0]
                else:
                    parts.append(f"{'·':>6}")
            out(f"{yr:>5} | " + " ".join(parts) + f" | {(comp - 1) * 100:>+7.1f}")
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

    for name, sma_t, tr_t in CONFIGS:
        print(f"Simulating {name} …", flush=True)
        sig = get_signals(df, bull_dates, sma_t, tr_t)
        signals_by_day: dict[int, list[dict]] = {}
        for r in sig.iter_rows(named=True):
            signals_by_day.setdefault((r["date"] - _EPOCH).days, []).append(r)

        out(f"\n\n## {name}  (bk50d_{name}_v1.2_roc100 / 366d)\n")
        hdr = f"{'size':<6} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8} {'taken':>6} {'skip':>6} {'Uninv%':>7}"
        out(hdr)
        out("-" * len(hdr))
        results = {}
        for pf in POS_FRACTIONS:
            r = run_sim(signals_by_day, "time", pf)
            results[pf] = r
            out(
                f"{pf:<6.0%} {r['final']:>11,.0f} {r['cagr'] * 100:>+7.2f} {r['max_dd'] * 100:>8.2f} "
                f"{r['calmar']:>7.3f} {r['sortino']:>8.3f} {r['taken']:>6} {r['skipped']:>6} "
                f"{r['avg_uninv_pct']:>6.1f}%"
            )
        for pf in POS_FRACTIONS:
            out(f"\n### {name} — size {pf:.0%}  (monthly % by year)")
            monthly_grid(results[pf]["eom"])

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
