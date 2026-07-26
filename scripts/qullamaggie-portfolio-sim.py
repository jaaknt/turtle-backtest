#!/usr/bin/env python3
"""
Portfolio simulation for bk50d_s20 / s17 / s15 / s12 (v1.3_roc100, 366d).

Filters match scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=3.0%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K; tight_range and sma_alignment disabled).

open/close/high/low are split/dividend-adjusted (scaled by adjusted_close/close) so indicators,
entries, and mark-to-market aren't corrupted by split-day discontinuities; raw (unadjusted)
close is used only for the $5-$250 price band, matching scripts/qullamaggie-backtest-v4.py.

Rules:
  - Period 2020-01-01 .. 2026-06-26, initial equity $30,000.
  - Signals scoring below MIN_RANKING on QullamaggieRanking are dropped before the
    simulation, matching the portfolio-runner --min-signal-ranking default.
  - Each signal: buy at the next trading day's split/dividend-adjusted open (matching
    SignalProcessor.calculate_entry_data), sizing = {3%,4%,5%} of current portfolio
    value (cash + open positions marked to market).
  - If available cash < the target, skip the trade (no liquidity).
  - Exit at the close of the first trading day >= entry + HOLD_CAL calendar days
    (open positions at period end are marked to market, not force-closed).
  - Fractional shares, no commission/slippage.

SPY/QQQ buy & hold benchmarks ($INIT_EQUITY lump-sum, first close to last close of the period)
are reported alongside the main sweep. Each taken trade for the s20/s12 configs is also scored
with QullamaggieRanking (turtlex/strategy/ranking/qullamaggie.py); trades are split into 10
equal-count ranking deciles and each decile's signal subset is re-simulated in isolation (same
position sizing) to report that decile's own standalone CAGR/MaxDD/Calmar/Sortino. Note the
deciles only span MIN_RANKING..100: the entry gate removes the low end of the evidence for
whether ranking predicts outcome, so these tables no longer speak to scores below it.

Outputs: monthly portfolio return + transaction-count grid (year x month), Max DD, Calmar,
Sortino, signals taken/skipped, average uninvested capital.
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.config.settings import Settings
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2020, 1, 1)
EVAL_END = date(2026, 6, 26)
DATA_START = "2000-01-01"
INIT_EQUITY = 30_000.0
POS_FRACTIONS = [0.03, 0.04, 0.05]  # position-size sweep
HOLD_CAL = 366
DECILE_POS_FRACTION = 0.04  # representative size used for the ranking-decile mini-simulations
N_DECILES = 10
BELOW_DAYS = 3  # consecutive days below 200d SMA to trigger trend exit
STOP_DD = 0.30  # fixed stop: close <= (1-STOP_DD) * entry price
TRAIL_DD = 0.25  # trailing stop: close <= (1-TRAIL_DD) * peak-since-entry
RANK_FUNDING = False  # when cash is scarce, fund competing signals by ADR (desc)

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
MIN_RANKING = 40  # QullamaggieRanking entry gate, matching the portfolio-runner default

CONFIGS = [
    ("s20", 0.20),
    ("s17", 0.17),
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
               db.adjusted_close::float8 AS close, db.open::float8 AS open,
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
            "open": [float(r[4]) * f for r, f in zip(rows, factor, strict=True)],
            "high": [float(r[5]) * f for r, f in zip(rows, factor, strict=True)],
            "low": [float(r[6]) * f for r, f in zip(rows, factor, strict=True)],
            "volume": [int(r[7]) for r in rows],
        }
    )


def buy_and_hold(engine: sa.Engine, symbol: str) -> dict:
    """Buy-and-hold benchmark: $INIT_EQUITY at the first close on/after EVAL_START, held to
    the last close on/before EVAL_END (raw close, no dividend reinvestment, matching how SPY's
    regime filter is computed above)."""
    sql = """
        SELECT date::date, close::float8 FROM turtle.daily_bars
        WHERE symbol = :symbol AND date >= :start AND date <= :end ORDER BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol, "start": EVAL_START, "end": EVAL_END}).fetchall()
    dates = [r[0] for r in rows]
    eq = INIT_EQUITY * (np.array([float(r[1]) for r in rows]) / float(rows[0][1]))
    daily_ret = eq[1:] / eq[:-1] - 1.0
    max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
    n_days = (dates[-1] - dates[0]).days
    cagr = (eq[-1] / eq[0]) ** (365.0 / n_days) - 1.0
    calmar = cagr / abs(max_dd) if max_dd < 0 else float("inf")
    neg = daily_ret[daily_ret < 0]
    dd_daily = float(np.sqrt(np.mean(neg**2))) if len(neg) else float("nan")
    sortino = float(np.mean(daily_ret) * np.sqrt(252) / dd_daily) if dd_daily > 0 else float("nan")
    return {"final": float(eq[-1]), "cagr": cagr, "max_dd": max_dd, "calmar": calmar, "sortino": sortino}


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
        .select(["symbol", "date", "close", "raw_close", "adr_pct", "adr_pct_change", "pct_vs_sma50", "roc_252d", "rsi14"])
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


_ranker = QullamaggieRanking()


def compute_ranking(s: dict) -> int:
    """Score a signal row with QullamaggieRanking. Uses raw_close (not the adjusted close
    used for position sizing elsewhere in this script) since that's the column the live
    QullamaggieStrategy/QullamaggieRanking pairing scores against."""
    row_df = pl.DataFrame(
        [
            {
                "date": s["date"],
                "close": s["raw_close"],
                "adr_pct": s["adr_pct"],
                "adr_pct_change": s["adr_pct_change"],
                "pct_vs_sma50": s["pct_vs_sma50"],
                "roc_252d": s["roc_252d"],
                "rsi14": s["rsi14"],
            }
        ]
    )
    return _ranker.ranking(row_df, s["date"])


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
    sym_opens: dict[str, np.ndarray] = {}
    sym_sma200: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_opens[sym] = g["open"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_sma200[sym] = g["sma200"].cast(pl.Float64).to_numpy(allow_copy=True)

    def _idx_on(sym: str, dint: int) -> int:
        d = sym_dates.get(sym)
        if d is None:
            return -1
        return int(np.searchsorted(d, dint, side="right")) - 1

    def price_on(sym: str, dint: int) -> float | None:
        idx = _idx_on(sym, dint)
        return float(sym_closes[sym][idx]) if idx >= 0 else None

    def next_open(sym: str, dint: int) -> tuple[int, float] | None:
        """First tradeable bar strictly after `dint`, as (date_int, adjusted open).

        Mirrors SignalProcessor.calculate_entry_data: the search skips bars with a
        non-positive open and gives up after 7 calendar days, and the open is already
        scaled by that bar's own adjustment factor in load_bars.
        """
        dates = sym_dates.get(sym)
        if dates is None:
            return None
        idx = int(np.searchsorted(dates, dint, side="right"))
        opens = sym_opens[sym]
        while idx < len(dates) and dates[idx] <= dint + 7:
            if opens[idx] > 0 and not np.isnan(opens[idx]):
                return int(dates[idx]), float(opens[idx])
            idx += 1
        return None

    def below_sma200(sym: str, dint: int) -> bool:
        idx = _idx_on(sym, dint)
        if idx < 0:
            return False
        sma = sym_sma200[sym][idx]
        return bool(not np.isnan(sma) and sym_closes[sym][idx] < sma)

    # master trading calendar = SPY days within period
    cal = [d for d in spy["date"].to_list() if EVAL_START <= d <= EVAL_END]
    cal_int = [(d - _EPOCH).days for d in cal]
    cal_set = set(cal_int)  # entries must land on a day run_sim actually visits

    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    def table(hdr: str, rows: list[str]) -> None:
        """Emit a fixed-width table as a fenced ```text block, blank-line-padded on both
        sides so it can't be misread as a setext heading by markdownlint/GitHub."""
        out("")
        out("```text")
        out(hdr)
        out("-" * len(hdr))
        for row in rows:
            out(row)
        out("```")

    def run_sim(signals_by_day: dict[int, list[dict]], exit_mode: str, pos_fraction: float, hold_cal: int = HOLD_CAL) -> dict:
        cash = INIT_EQUITY
        positions: list[dict] = []
        equity_curve: list[tuple[date, float]] = []
        cash_curve: list[float] = []
        entry_dates: list[date] = []
        trades: list[dict] = []
        n_taken = n_skipped = n_exit_rule = 0

        for d, dint in zip(cal, cal_int, strict=False):
            still_open = []
            for p in positions:
                px = price_on(p["sym"], dint)
                if dint >= p["exit_int"]:  # time cap (always)
                    if px is not None:
                        cash += p["shares"] * px
                        trades.append(
                            {
                                "entry_date": p["entry_date"],
                                "sig_date": p["sig_date"],
                                "symbol": p["sym"],
                                "ret": px / p["entry_px"] - 1.0,
                                "ranking": p["ranking"],
                            }
                        )
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
                    trades.append(
                        {
                            "entry_date": p["entry_date"],
                            "sig_date": p["sig_date"],
                            "symbol": p["sym"],
                            "ret": px / p["entry_px"] - 1.0,
                            "ranking": p["ranking"],
                        }
                    )
                else:
                    still_open.append(p)
            positions = still_open

            mtm = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)

            day_sigs = signals_by_day.get(dint, [])
            if RANK_FUNDING:
                day_sigs = sorted(day_sigs, key=lambda s: s["adr_pct"], reverse=True)
            for s in day_sigs:
                target = pos_fraction * mtm
                entry_px = s["entry_px"]  # next trading day's adjusted open, resolved once in main()
                if cash + 1e-9 < target:
                    n_skipped += 1
                    continue
                cash -= target
                positions.append(
                    {
                        "sym": s["symbol"],
                        "shares": target / entry_px,
                        "entry_px": entry_px,
                        "entry_date": d,
                        "sig_date": s["date"],
                        "exit_int": dint + hold_cal,
                        "below_cnt": 0,
                        "peak": entry_px,
                        "ranking": s["ranking"],
                    }
                )
                n_taken += 1
                entry_dates.append(d)

            equity = cash + sum(p["shares"] * (price_on(p["sym"], dint) or 0.0) for p in positions)
            equity_curve.append((d, equity))
            cash_curve.append(cash)

        for p in positions:  # still open at period end -- mark-to-market, not force-closed
            px = price_on(p["sym"], cal_int[-1])
            if px is not None:
                trades.append(
                    {
                        "entry_date": p["entry_date"],
                        "sig_date": p["sig_date"],
                        "symbol": p["sym"],
                        "ret": px / p["entry_px"] - 1.0,
                        "ranking": p["ranking"],
                    }
                )

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
            "trades": trades,
        }

    def monthly_grid(eom: pl.DataFrame, entries: list[date]) -> None:
        entry_counts: dict[tuple[int, int], int] = {}
        for ed in entries:
            key = (ed.year, ed.month)
            entry_counts[key] = entry_counts.get(key, 0) + 1

        header = f"{'Year':>5} | " + " ".join(f"{m:>9}" for m in MONTHS) + f" | {'Year%':>7} {'Txns':>5}"
        rows: list[str] = []
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
            rows.append(f"{yr:>5} | " + " ".join(parts) + f" | {(comp - 1) * 100:>+7.1f} {year_txns:>5}")
        table(header, rows)

    def ranking_decile_table(name: str, signals_by_day: dict[int, list[dict]], pos_fraction: float) -> None:
        """Score every taken trade with QullamaggieRanking, split into N_DECILES equal-count
        buckets (D1=lowest ranking .. D10=highest), and re-simulate each decile's own signal
        subset in isolation (same sizing) to report that decile's standalone portfolio metrics."""
        base = run_sim(signals_by_day, "time", pos_fraction)
        trades = sorted(base["trades"], key=lambda t: t["ranking"])
        n = len(trades)
        edges = np.linspace(0, n, N_DECILES + 1).astype(int)

        hdr = f"{'Decile':<8} {'Ranking':>9} {'N':>5} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8}"
        rows: list[str] = []
        for d in range(N_DECILES):
            subset = trades[edges[d] : edges[d + 1]]
            if not subset:
                continue
            keys = {(t["symbol"], t["sig_date"]) for t in subset}
            sub_by_day: dict[int, list[dict]] = {}
            for dint, sigs in signals_by_day.items():
                kept = [s for s in sigs if (s["symbol"], s["date"]) in keys]
                if kept:
                    sub_by_day[dint] = kept
            res = run_sim(sub_by_day, "time", pos_fraction)
            rankings = [t["ranking"] for t in subset]
            rows.append(
                f"D{d + 1:<7} {min(rankings):>3}-{max(rankings):<5} {len(subset):>5} {res['cagr'] * 100:>+7.2f} "
                f"{res['max_dd'] * 100:>8.2f} {res['calmar']:>7.3f} {res['sortino']:>8.3f}"
            )
        out(f"Trades scored: {n}  |  size: {pos_fraction:.0%}")
        table(hdr, rows)

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
                entry_px = s["entry_px"]
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

    out("# Portfolio Simulation — size sweep + ranking deciles")
    out("")
    out(f"Run date: {date.today()}")
    out(
        f"Period: {EVAL_START} – {EVAL_END}  |  Initial: ${INIT_EQUITY:,.0f}  |  "
        f"algorithm: RSI<70  |  sizes: {', '.join(f'{f:.0%}' for f in POS_FRACTIONS)}  |  "
        f"hold: {HOLD_CAL}d  |  min ranking: {MIN_RANKING}"
    )

    out("")
    out("## Buy & Hold Benchmarks")
    out("")
    out(f"${INIT_EQUITY:,.0f} bought on the first trading day of the period, sold on the last.")
    bh_hdr = f"{'symbol':<6} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8}"
    bh_rows: list[str] = []
    for sym in ["SPY.US", "QQQ.US"]:
        bh = buy_and_hold(settings.engine, sym)
        bh_rows.append(
            f"{sym[:-3]:<6} {bh['final']:>11,.0f} {bh['cagr'] * 100:>+7.2f} {bh['max_dd'] * 100:>8.2f} "
            f"{bh['calmar']:>7.3f} {bh['sortino']:>8.3f}"
        )
    table(bh_hdr, bh_rows)

    # collect all baseline (366d) results first, then rank for monthly grids
    all_results: list[tuple[str, float, dict]] = []  # (name, pos_fraction, result)
    signals_by_day_by_config: dict[str, dict[int, list[dict]]] = {}
    hdr = f"{'size':<6} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8} {'taken':>6} {'skip':>6} {'Uninv%':>7}"

    for name, sma_t in CONFIGS:
        print(f"Simulating {name} …", flush=True)
        sig = get_signals(df, bull_dates, sma_t)
        # Score and resolve the fill once here, not per entry inside run_sim: the sweep and
        # the decile re-simulations replay the same signals many times over. Signals are
        # keyed by their *entry* day (the next trading day), so run_sim funds a position on
        # the day it is actually filled.
        signals_by_day: dict[int, list[dict]] = {}
        n_below_rank = n_no_fill = 0
        for r in sig.iter_rows(named=True):
            r["ranking"] = compute_ranking(r)
            if r["ranking"] < MIN_RANKING:
                n_below_rank += 1
                continue
            fill = next_open(r["symbol"], (r["date"] - _EPOCH).days)
            if fill is None or fill[0] not in cal_set:
                n_no_fill += 1  # no tradeable open, or the fill lands past EVAL_END
                continue
            entry_dint, r["entry_px"] = fill
            signals_by_day.setdefault(entry_dint, []).append(r)
        signals_by_day_by_config[name] = signals_by_day

        out("")
        out(f"## {name}  (bk50d_{name}_v1.3_roc100 / {HOLD_CAL}d)")
        out("")
        out(
            f"Parameters: %abv_SMA50>{sma_t * 100:.0f}%, breakout>50d high, RSI(14)<{RSI_CAP:.0f}, "
            f"ADR%(20)>={ADR_FLOOR * 100:.1f}%, ADR_change<{ADR_CHANGE_CAP * 100:.0f}%, "
            f"vol_surge<{VOL_SURGE_MAX:.1f}x, vol_dry_up<{VOL_DRY_UP * 100:.0f}%, roc_12m<{ROC_CAP * 100:.0f}%, "
            f"SPY>200d SMA, close>${MIN_PRICE:.0f}&<${MAX_PRICE:.0f}, avg_vol>={MIN_AVG_VOL // 1000}K, "
            f"cooldown={COOLDOWN}d, hold={HOLD_CAL}d cal, QullamaggieRanking>={MIN_RANKING} "
            f"({n_below_rank} signals dropped below it, {n_no_fill} with no fillable next-day open in period)"
        )
        results: dict[float, dict] = {}
        rows: list[str] = []
        for pf in POS_FRACTIONS:
            r = run_sim(signals_by_day, "time", pf)
            results[pf] = r
            all_results.append((name, pf, r))
            rows.append(
                f"{pf:<6.0%} {r['final']:>11,.0f} {r['cagr'] * 100:>+7.2f} {r['max_dd'] * 100:>8.2f} "
                f"{r['calmar']:>7.3f} {r['sortino']:>8.3f} {r['taken']:>6} {r['skipped']:>6} "
                f"{r['avg_uninv_pct']:>6.1f}%"
            )
        table(hdr, rows)

    # monthly grids for top 5 by Calmar, and separately top 5 by Final$ (366d baseline, RSI<70)
    ranked_calmar = sorted(all_results, key=lambda x: x[2]["calmar"], reverse=True)
    out("")
    out("## Monthly returns/transactions — top 5 by Calmar")
    for rank, (name, pf, r) in enumerate(ranked_calmar[:5], 1):
        out("")
        out(f"### #{rank}  {name} — size {pf:.0%}  (Calmar {r['calmar']:.3f})")
        monthly_grid(r["eom"], r["entries"])

    ranked_final = sorted(all_results, key=lambda x: x[2]["final"], reverse=True)
    out("")
    out("## Monthly returns/transactions — top 5 by Final$")
    for rank, (name, pf, r) in enumerate(ranked_final[:5], 1):
        out("")
        out(f"### #{rank}  {name} — size {pf:.0%}  (Final ${r['final']:,.0f})")
        monthly_grid(r["eom"], r["entries"])

    out("")
    out("## Ranking Deciles (QullamaggieRanking)")
    out("")
    out(
        f"Every taken trade for s20/s12 (at {DECILE_POS_FRACTION:.0%} sizing, the middle of the "
        f"{'/'.join(f'{f:.0%}' for f in POS_FRACTIONS)} sweep) is scored 0-100 with "
        "turtlex/strategy/ranking/qullamaggie.py at entry, split into "
        f"{N_DECILES} equal-count deciles (D1=lowest score .. D{N_DECILES}=highest), and each "
        "decile's own signal subset is re-simulated in isolation (same sizing, same universe) "
        "to report that decile's standalone portfolio metrics — this tests whether higher-ranked "
        "signals produce a better standalone portfolio, not just a higher per-trade return."
    )
    for name in ["s20", "s12"]:
        print(f"Scoring ranking deciles for {name} …", flush=True)
        out("")
        out(f"### {name}  (bk50d_{name}_v1.3_roc100)")
        out("")
        ranking_decile_table(name, signals_by_day_by_config[name], DECILE_POS_FRACTION)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
