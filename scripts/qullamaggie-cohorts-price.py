#!/usr/bin/env python3
"""
Entry-price cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the close>$5&<$250 price bounds, so we can see
performance across the full entry-price range including sub-$5 and $250+ cohorts.

This study runs UNGATED, like the ADR% study. QullamaggieRanking scores the raw close as its
25-point dimension and awards 0 above $100, so a >=40 gate filters on the very variable being
cohorted and would thin the expensive cohorts this study exists to measure.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import config_table, run_timestamp
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
VOL_SURGE_MAX = 2.0
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
ROC_CAP = 1.00
MIN_NEG = 5

STRATEGIES = [
    ("bk50d_s20_v2.0", 0.20),
    ("bk50d_s16_v2.0", 0.16),
    ("bk50d_s12_v2.0", 0.12),
]

COHORTS: list[tuple[str, float, float]] = [
    ("[0-5)      ", 0.0, 5.0),
    ("[5-10)     ", 5.0, 10.0),
    ("[10-20)    ", 10.0, 20.0),
    ("[20-50)    ", 20.0, 50.0),
    ("[50-100)   ", 50.0, 100.0),
    ("[100-250)  ", 100.0, 250.0),
    ("[250-700)  ", 250.0, 700.0),
    ("[700-2000) ", 700.0, 2000.0),
    ("[>2000]    ", 2000.0, float("inf")),
]

CONFIG_ROWS: list[tuple[str, str]] = [
    ("Period", f"{EVAL_START} – {EVAL_END}"),
    ("Hold", f"{HOLD_CAL}d (calendar)"),
    ("Cohorts", "bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d)"),
    ("Cohort variable", "raw close on the signal date, in dollars"),
    ("Entry", "next trading day's split/dividend-adjusted open"),
    ("Filter under study", "**close > $5 & < $250 — removed; returns as the `$5-$250 (cap)` row**"),
    ("Fixed filters", "RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range)"),
    ("Ranking gate", "**not applied — price is the score's 25-point dimension and the cohort variable (ungated)**"),
    ("Market regime", "SPY close > 200d SMA"),
    ("Price range", "**removed — this is the cohort variable**"),
    ("Min avg vol (20d)", f">= {MIN_AVG_VOL // 1000}K"),
    ("Cooldown", f"{COOLDOWN} calendar days"),
    ("Universe", "US common stocks, market_cap >= 1.5B, excl. Comm/RE"),
    ("Sortino", f"mean / RMS(min(r,0)) over all N x sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py)"),
]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-price.md"


# ── Signal generation (no price bounds) ───────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
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
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") >= sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
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
        records.append({"price": row["raw_close"], "ret": ret})
    return records


# ── Metrics ───────────────────────────────────────────────────────────────────


def compute_metrics(rets: np.ndarray) -> dict | None:
    if len(rets) < 5:
        return None
    m = compute_trade_metrics(rets * 100, HOLD_CAL, min_losers=MIN_NEG)
    if m is None:
        return None
    return {
        "n": m.n,
        "med": m.median_pct,
        "mean": m.mean_pct,
        "win": m.win_pct,
        "sr": m.sortino,
        "pf": m.profit_factor,
        "cvar": m.cvar95_pct,
    }


# ── Output ────────────────────────────────────────────────────────────────────

_COL_HDR = f"{'Cohort':<12}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}  {'CVaR95%':>8}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_cohort_row(label: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return (
        f"{label:<12}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}  {m['cvar']:>+8.2f}"
    )


def build_table(label: str, records: list[dict]) -> list[str]:
    lines = [f"### {label}", "", _COL_HDR, _COL_SEP]
    all_rets = np.array([r["ret"] for r in records])
    for cohort_label, lo, hi in COHORTS:
        cohort_rets = np.array([r["ret"] for r in records if lo <= r["price"] < hi])
        m = compute_metrics(cohort_rets)
        if m:
            lines.append(fmt_cohort_row(cohort_label, m))
        else:
            n = len(cohort_rets)
            lines.append(f"{cohort_label:<12}  {n:>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}  {'—':>8}")
    lines.append(_COL_SEP)
    m_all = compute_metrics(all_rets)
    if m_all:
        lines.append(fmt_cohort_row("ALL", m_all))
    ref_rets = np.array([r["ret"] for r in records if MIN_PRICE < r["price"] < MAX_PRICE])
    m_ref = compute_metrics(ref_rets)
    if m_ref:
        lines.append(fmt_cohort_row("$5-$250 (cap)", m_ref))
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

    config = config_table(CONFIG_ROWS)
    print("\n" + config)

    all_lines: list[str] = []
    for strat_label, sma_t in STRATEGIES:
        print(f"  {strat_label} …", flush=True)
        signals = qm.resolve_entries(get_signals(df, bull_dates, sma_t), bars)
        print(f"    {len(signals)} signals", flush=True)
        records = run_trades(signals, sym_dates, sym_closes)
        table_lines = build_table(strat_label, records)
        all_lines.extend(table_lines)
        for line in table_lines:
            print(line)

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Entry-Price Cohort Analysis\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("## Configuration\n\n")
        fh.write(config)
        fh.write("\n## Results\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
