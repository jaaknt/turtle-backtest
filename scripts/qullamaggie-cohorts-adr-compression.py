#!/usr/bin/env python3
"""
ADR compression cohort analysis for bk50d_s20_v1.3_roc100, bk50d_s15_v1.3_roc100, bk50d_s12_v1.3_roc100 (366d hold).

New metric, not currently used as a filter — all standard bk50d filters (no tight_range)
apply as-is; compression is only measured, not filtered.

ADR%(N)     = mean((high[-i] - low[-i]) / low[-i] for i in 1..N) * 100  (shift-1, no look-ahead)
compression = ADR%(10) / ADR%(50)

compression < 1 means the last 10 days have been quieter than the last 50 (volatility
contraction ahead of the breakout); > 1 means recent volatility is expanding.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.config.settings import Settings

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.90
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
RSI_REENTRY = 80.0  # spec: RSI(14) < 70 OR RSI(14) > 80 — only the 70-80 band is excluded
ADR_MIN = 0.025
MIN_NEG = 5

STRATEGIES = [
    ("bk50d_s20_v1.3_roc100", 0.20),
    ("bk50d_s15_v1.3_roc100", 0.15),
    ("bk50d_s12_v1.3_roc100", 0.12),
]

COHORTS: list[tuple[str, float, float]] = [
    ("[<0.5)    ", float("-inf"), 0.5),
    ("[0.5-0.7) ", 0.5, 0.7),
    ("[0.7-0.8) ", 0.7, 0.8),
    ("[0.8-0.9) ", 0.8, 0.9),
    ("[0.9-1.0) ", 0.9, 1.0),
    ("[1.0-1.3) ", 1.0, 1.3),
    ("[>1.3)    ", 1.3, float("inf")),
]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-adr-compression.md"


# ── Data loading ─────────────────────────────────────────────────────────────


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= '2012-06-01'
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
          AND  db.date >= '2013-01-01'
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


# ── Indicators ───────────────────────────────────────────────────────────────


def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
            (pl.col("high") - pl.col("low")).shift(1).over("symbol").alias("_dr1"),
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
            pl.col("_dr1").rolling_mean(20, min_samples=20).over("symbol").alias("_adr_num"),
            pl.col("_c1").shift(251).over("symbol").alias("_c_252d"),
            (pl.col("_rp1").rolling_mean(10, min_samples=10).over("symbol") * 100).alias("adr10"),
            (pl.col("_rp1").rolling_mean(50, min_samples=50).over("symbol") * 100).alias("adr50"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr_num") / pl.col("sma50")).alias("adr_pct"),
            (pl.col("close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
            (pl.col("adr10") / pl.col("adr50")).alias("compression"),
        ]
    )
    return df.drop(["_c1", "_v1", "_dr1", "_rp1", "_adr_num", "_c_252d"])


# ── Signal generation ──────────────────────────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("compression").is_not_null()
            & ((pl.col("rsi14") < RSI_CAP) | (pl.col("rsi14") > RSI_REENTRY))
            & (pl.col("close") > MIN_PRICE)
            & (pl.col("close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") >= sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "close", "compression"])
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


# ── Trade runner ──────────────────────────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
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
        ret = float((closes[idx_exit] - closes[idx_entry]) / closes[idx_entry])
        records.append({"comp": row["compression"], "ret": ret})
    return records


# ── Metrics ───────────────────────────────────────────────────────────────────


def compute_metrics(rets: np.ndarray) -> dict | None:
    n = len(rets)
    if n < 5:
        return None
    neg = rets[rets < 0]
    sr = float("nan")
    if len(neg) >= MIN_NEG:
        dd = float(np.sqrt(np.mean(neg**2)))
        if dd > 0:
            sr = float(np.mean(rets) * np.sqrt(365 / HOLD_CAL) / dd)
    gross_win = float(rets[rets > 0].sum())
    gross_loss = float(-rets[rets < 0].sum())
    return {
        "n": n,
        "med": float(np.median(rets) * 100),
        "mean": float(rets.mean() * 100),
        "win": float((rets > 0).mean() * 100),
        "sr": sr,
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
    }


# ── Output ────────────────────────────────────────────────────────────────────

_COL_HDR = f"{'Cohort':<12}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_cohort_row(label: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return f"{label:<12}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}"


def build_table(label: str, records: list[dict]) -> list[str]:
    lines = [f"### {label}", "", _COL_HDR, _COL_SEP]
    all_rets = np.array([r["ret"] for r in records])
    for cohort_label, lo, hi in COHORTS:
        cohort_rets = np.array([r["ret"] for r in records if lo <= r["comp"] < hi])
        m = compute_metrics(cohort_rets)
        if m:
            lines.append(fmt_cohort_row(cohort_label, m))
        else:
            n = len(cohort_rets)
            lines.append(f"{cohort_label:<12}  {n:>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}")
    lines.append(_COL_SEP)
    m_all = compute_metrics(all_rets)
    if m_all:
        lines.append(fmt_cohort_row("ALL", m_all))
    lines.append("")
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


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
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)

    header = (
        f"ADR compression cohort analysis | Hold: {HOLD_CAL}d | "
        f"Period: {EVAL_START} – {EVAL_END}\n"
        f"Filters: all bk50d filters applied as-is (no tight_range);\n"
        f"compression = ADR%(10)/ADR%(50) is measured only, not filtered\n"
    )
    print("\n" + header)

    all_lines: list[str] = [header]

    for strat_label, sma_t in STRATEGIES:
        print(f"  {strat_label} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        print(f"    {len(signals)} signals", flush=True)
        records = run_trades(signals, sym_dates, sym_closes)
        table_lines = build_table(strat_label, records)
        all_lines.extend(table_lines)
        for line in table_lines:
            print(line)

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie ADR Compression Cohort Analysis\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
