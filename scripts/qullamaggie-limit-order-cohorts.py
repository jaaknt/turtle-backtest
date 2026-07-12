#!/usr/bin/env python3
"""
Limit-order fill sensitivity test for the 366d-hold cohorts of qullamaggie-backtest-v4.

Cohorts: bk50d_s20_tr20_v1.2_roc100, bk50d_s15_tr20_v1.2_roc100, bk50d_s12_tr20_v1.2_roc100 (all 366d hold).
Filters/indicators match scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=3.0%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<80%, tight_range<20%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K). close/high/low are split/dividend-adjusted.

Baseline: buy at signal-day close (EOD, current backtest-v4 behaviour).
Limit sweep: place a resting limit buy at signal_day_close * (1 - X%) for X% in {0, 1, 2, 3, 4, 5},
             good for 30 calendar days from the signal day. It fills on the first trading day within
             that window whose low <= limit price (entry price = limit price); if no day in the
             window touches the limit, the order expires unfilled. Hold 366 calendar days from the
             fill day (same HOLD_MAX_CAL forward-data requirement as the backtest).

Also reports monthly seasonality (Mean%/N by entry year x month) for the EOD baseline of each cohort.

Period: 2010-01-01 - 2026-06-26  |  Burn-in data from 2008-01-01.

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
EVAL_START = date(2010, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
LIMIT_WINDOW_CAL = 30  # limit order stays resting this many calendar days after the signal

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
MIN_NEG = 10

LIMIT_PCTS = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
SMA_THRESHS = [(0.20, "bk50d_s20_tr20_v1.2_roc100"), (0.15, "bk50d_s15_tr20_v1.2_roc100"), (0.12, "bk50d_s12_tr20_v1.2_roc100")]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-limit-order-cohorts.md"


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


# ── Signal generation (identical to qullamaggie-backtest-v4.py) ───────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
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


# ── Trade runners ──────────────────────────────────────────────────────────────


def run_trades_eod(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
    """Buy at signal-day close (backtest-v4 baseline). Records entry year/month for the monthly breakdown."""
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
        ret = float(closes[idx_exit] / closes[idx_entry] - 1.0)
        records.append({"year": row["date"].year, "month": row["date"].month, "ret": ret})
    return records


def run_trades_limit(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_lows: dict[str, np.ndarray],
    limit_pct: float,
) -> tuple[list[dict], int, int]:
    """Buy via a resting limit order, good for LIMIT_WINDOW_CAL calendar days after the signal.

    Fills on the first trading day in that window whose low <= limit price; entry price = limit
    price. Returns (records, n_attempted, n_filled).
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

        idx_start = idx_signal + 1
        if idx_start >= len(dates):
            continue

        n_attempted += 1
        limit_price = closes[idx_signal] * (1.0 - limit_pct)
        idx_end = int(np.searchsorted(dates, signal_int + LIMIT_WINDOW_CAL, side="right")) - 1
        idx_end = min(idx_end, len(dates) - 1)

        fill_idx: int | None = None
        for idx in range(idx_start, idx_end + 1):
            if lows[idx] <= limit_price:
                fill_idx = idx
                break
        if fill_idx is None:
            continue  # order expired unfilled
        n_filled += 1

        fill_day_int = int(dates[fill_idx])
        if dates[-1] < fill_day_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, fill_day_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue

        ret = float(closes[idx_exit] / limit_price - 1.0)
        records.append({"ret": ret})
    return records, n_attempted, n_filled


# ── Metrics ────────────────────────────────────────────────────────────────────


def sortino(a: np.ndarray) -> float:
    neg = a[a < 0]
    if len(neg) < MIN_NEG:
        return float("nan")
    dd = float(np.sqrt(np.mean(neg**2)))
    return float(np.mean(a) * np.sqrt(365 / HOLD_CAL) / dd) if dd > 0 else float("nan")


def compute_metrics(records: list[dict]) -> dict:
    if not records:
        return {"n": 0, "win": float("nan"), "mean": float("nan"), "med": float("nan"), "pf": float("nan"), "sr": float("nan")}
    a = np.array([r["ret"] for r in records])
    gross_win = float(a[a > 0].sum())
    gross_loss = float(-a[a < 0].sum())
    return {
        "n": len(a),
        "win": float((a > 0).mean() * 100),
        "mean": float(a.mean() * 100),
        "med": float(np.median(a) * 100),
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
        "sr": sortino(a),
    }


# ── Output ─────────────────────────────────────────────────────────────────────

_HDR = f"{'Cohort':<16} {'Fill%':>7} {'N':>5} {'Med%':>8} {'Mean%':>8} {'Win%':>7} {'Sortino':>8} {'PF':>7}"
_SEP = "-" * len(_HDR)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_calendar_table(records: list[dict], label: str) -> str:
    """Monthly Mean%/N grid (rows=year, cols=month) grouped by each trade's entry year/month."""
    by_ym: dict[tuple[int, int], list[float]] = {}
    for r in records:
        by_ym.setdefault((r["year"], r["month"]), []).append(r["ret"])

    hdr = f"{'Year':>5} |" + "".join(f"{m:>8}" for m in MONTHS) + f" | {'Mean%':>7} {'N':>5}"
    sep = "-" * len(hdr)
    lines = [f"### {label} — Monthly Mean% / N (EOD, entry month/year)\n", "```", hdr, sep]

    if not by_ym:
        lines += ["(no trades)", "```\n"]
        return "\n".join(lines)

    for year in sorted({y for y, _m in by_ym}):
        cells: list[str] = []
        year_rets: list[float] = []
        for month_idx in range(1, 13):
            vals = by_ym.get((year, month_idx))
            if vals:
                cell = f"{np.mean(vals) * 100:+.1f}|{len(vals)}"
                year_rets.extend(vals)
            else:
                cell = "·"
            cells.append(f"{cell:>8}")
        year_mean_pct = float(np.mean(year_rets)) * 100 if year_rets else float("nan")
        lines.append(f"{year:>5} |" + "".join(cells) + f" | {year_mean_pct:>+6.1f}% {len(year_rets):>4}")

    lines.append("```\n")
    return "\n".join(lines)


def fmt_row(label: str, fill_pct: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not np.isnan(m["sr"]) else f"{'n/a':>8}"
    pf_str = f"{m['pf']:>7.2f}" if np.isfinite(m["pf"]) else f"{'inf':>7}"
    if m["n"] == 0:
        return f"{label:<16} {fill_pct:>7} {0:>5}      --       --      --      n/a      --"
    return f"{label:<16} {fill_pct:>7} {m['n']:>5} {m['med']:>+7.1f}% {m['mean']:>+7.1f}% {m['win']:>6.1f}% {sr_str} {pf_str}"


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

    report_sections: list[str] = []
    calendar_sections: list[str] = []
    for sma_t, label in SMA_THRESHS:
        print(f"Generating signals for {label} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        print(f"  {len(signals)} raw signals", flush=True)

        lines = [f"### {label} — 366d\n", "```", _HDR, _SEP]

        eod_records = run_trades_eod(signals, sym_dates, sym_closes)
        eod_m = compute_metrics(eod_records)
        lines.append(fmt_row("EOD (baseline)", "100.0%", eod_m))
        lines.append(_SEP)

        for lp in LIMIT_PCTS:
            records, n_att, n_fill = run_trades_limit(signals, sym_dates, sym_closes, sym_lows, lp)
            fill_pct = f"{n_fill / n_att * 100:.1f}%" if n_att > 0 else "n/a"
            m = compute_metrics(records)
            lines.append(fmt_row(f"{lp * 100:.0f}%", fill_pct, m))

        lines.append("```\n")
        section = "\n".join(lines)
        report_sections.append(section)
        print("\n" + section)

        calendar_section = build_calendar_table(eod_records, label)
        calendar_sections.append(calendar_section)
        print("\n" + calendar_section)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write(f"Period: {EVAL_START} – {EVAL_END}  |  Hold: {HOLD_CAL}d (calendar)\n\n")
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write("| Cohorts | bk50d_s20_tr20_v1.2_roc100, bk50d_s15_tr20_v1.2_roc100, bk50d_s12_tr20_v1.2_roc100 (366d) |\n")
        fh.write(f"| Limit sweep | X% = {', '.join(f'{int(lp * 100)}%' for lp in LIMIT_PCTS)} |\n")
        fh.write(
            f"| Limit order rule | resting limit at signal_day_close x (1 - X%), good for {LIMIT_WINDOW_CAL} calendar days; "
            "fills on the first day in that window whose low <= limit price, else expires unfilled |\n"
        )
        fh.write("| Baseline | EOD — buy at signal-day close (backtest-v4 default) |\n")
        fh.write("| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<80%, tight_range<20% |\n")
        fh.write("| Market regime | SPY close > 200d SMA |\n")
        fh.write(f"| Price range | > ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f} |\n")
        fh.write(f"| Min avg vol (20d) | >= {MIN_AVG_VOL // 1000}K |\n")
        fh.write(f"| Cooldown | {COOLDOWN} calendar days |\n")
        fh.write("| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |\n\n")
        fh.write("## Results\n\n")
        for section in report_sections:
            fh.write(section)
            fh.write("\n")
        fh.write("## Monthly Seasonality (EOD baseline)\n\n")
        fh.write(
            "Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the "
            "EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The "
            "Mean%/N columns on the right are the year's aggregate across all its months.\n\n"
        )
        for section in calendar_sections:
            fh.write(section)
            fh.write("\n")
        fh.write("## Findings & Caveats\n\n")
        fh.write(
            f"- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for "
            f"{LIMIT_WINDOW_CAL} calendar days and fills on the *first* day the low touches the limit price. This "
            "raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are "
            "increasingly dominated by trades that took most of the window to retrace that far — those signals "
            "have effectively already spent part of their 366d hold going nowhere (or down) before the position "
            "even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the "
            "signal day).\n\n"
        )
        fh.write(
            "- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering "
            "the breakout signal — this is not a neutral resampling of the same trade population as the EOD "
            "baseline; it systematically selects for breakouts that gave back some of the signal-day gain before "
            "continuing (or failing), which can bias mean/median returns in either direction depending on regime.\n\n"
        )
        fh.write(
            "- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under "
            "30 are not statistically reliable, even if the ratios look attractive.\n\n"
        )
        fh.write(
            "- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are "
            "split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the "
            "modeled discount), and hold length is measured in calendar days from the fill day, not the original "
            "signal day.\n\n"
        )
        fh.write(
            "- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit "
            "order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the "
            "limit price would fill better than modeled).\n"
        )
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
