#!/usr/bin/env python3
"""
pct_above_sma50 cohort analysis for bk50d_<X>_v2.0 (366d hold).

All strategy filters applied EXCEPT the pct_vs_sma50 > X threshold itself, so
we can see performance across the full distance-above-SMA50 range. Removing
that filter makes the s12/s15/s17/s20 variants draw from the same candidate
pool, so there is a single cohort table with one reference row per current
threshold cap. pct_above_sma50 = close / mean(close[-51:-1]) - 1

This study runs UNGATED, like the ADR% and entry-price studies. QullamaggieRanking scores
pct_vs_sma50 as its 35-point dimension and awards 0 below 10%, so a >=40 gate filters on the
very variable being cohorted and would empty the low cohorts this study exists to measure.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm

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
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
ROC_CAP = 1.00
MIN_NEG = 5

# Current threshold caps shown as reference rows
SMA_THRESHS = [0.12, 0.15, 0.17, 0.20]

COHORTS: list[tuple[str, float, float]] = [
    ("(<10)    ", float("-inf"), 0.10),
    ("[10-12)  ", 0.10, 0.12),
    ("[12-15)  ", 0.12, 0.15),
    ("[15-17)  ", 0.15, 0.17),
    ("[17-20)  ", 0.17, 0.20),
    ("[20-30)  ", 0.20, 0.30),
    ("(>30)    ", 0.30, float("inf")),
]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-pct-above-sma50.md"


# ── Signal generation (no pct_vs_sma50 threshold) ────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date]) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & pl.col("adr_pct").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > MIN_PRICE)
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("roc_252d") < ROC_CAP)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "raw_close", "adj_close", "adr_pct", "pct_vs_sma50"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    # Cooldown runs from the warmup window rather than EVAL_START, so a trigger just before
    # the window suppresses an early in-window signal — the ordering qm.get_signals uses.
    # Only accepted triggers on or after EVAL_START are emitted.
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            last_trigger[sym] = d
            if d >= EVAL_START:
                rows_out.append(row)
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
        entry_int = (row["entry_date"] - _EPOCH).days
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        entry_px = float(row["entry_price"])
        ret = float((closes[idx_exit] - entry_px) / entry_px)
        records.append({"pct": row["pct_vs_sma50"], "ret": ret})
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

_COL_HDR = f"{'Cohort':<10}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_cohort_row(label: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return f"{label:<10}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}"


def build_table(records: list[dict]) -> list[str]:
    lines = ["### bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)", "", _COL_HDR, _COL_SEP]
    all_rets = np.array([r["ret"] for r in records])
    for cohort_label, lo, hi in COHORTS:
        cohort_rets = np.array([r["ret"] for r in records if lo <= r["pct"] < hi])
        m = compute_metrics(cohort_rets)
        if m:
            lines.append(fmt_cohort_row(cohort_label, m))
        else:
            n = len(cohort_rets)
            lines.append(f"{cohort_label:<10}  {n:>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}")
    lines.append(_COL_SEP)
    m_all = compute_metrics(all_rets)
    if m_all:
        lines.append(fmt_cohort_row("ALL", m_all))
    for sma_t in SMA_THRESHS:
        ref_rets = np.array([r["ret"] for r in records if r["pct"] > sma_t])
        m_ref = compute_metrics(ref_rets)
        if m_ref:
            lines.append(fmt_cohort_row(f">{int(sma_t * 100)}% (s{int(sma_t * 100)})", m_ref))
    lines.append("")
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()

    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading bars …", flush=True)
    # Bars run past EVAL_END: a 366d hold needs forward data beyond the last signal date.
    df = qm.load_bars(bars_history, EVAL_START, date.today())
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    # Project down to the columns qm.resolve_entries reads before building the indicator
    # frame, so the full-width bar frame is released rather than held alongside it.
    bars = df.select("symbol", "date", "adj_open")
    df = qm.add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    header = (
        f"pct_above_sma50 cohort analysis | Hold: {HOLD_CAL}d | "
        f"Period: {EVAL_START} – {EVAL_END}\n"
        f"Filters: RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, "
        f"breakout>50d high, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, "
        f"tight_range disabled; pct_above_sma50>X threshold removed for cohort view "
        f"(reference rows shown for X=12%/15%/17%/20%); ungated (see docstring)\n"
        f"(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)\n"
    )
    print("\n" + header)

    signals = qm.resolve_entries(get_signals(df, bull_dates), bars)
    print(f"  {len(signals)} signals", flush=True)
    records = run_trades(signals, sym_dates, sym_closes)
    table_lines = build_table(records)
    for line in table_lines:
        print(line)

    output = "\n".join([header, *table_lines])

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie pct_above_sma50 Cohort Analysis\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
