#!/usr/bin/env python3
"""
Qullamaggie-style breakout backtest v4.
Spec: docs/research/qullamaggie-backtest-v4.md

Fixed filters: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%,
               ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=100K
Sweep: SMA_THRESH ∈ {12%,16%,20%}, each held 366 cal days
       (tight_range, sma_alignment and vol_dry_up disabled)
Eval: --start-date .. --end-date, default 2021-01-01 – 2025-12-31; bars are loaded from qm.WARMUP_DAYS
      before the window (burn-in, indicators only) forward to DATA_END, so a trade entered late in
      the window can still reach its 366d exit; entries whose exit falls past DATA_END are skipped.
Entry: next trading day's split/dividend-adjusted open (not the signal-day close).
Every signal is scored 0-100 by the production QullamaggieRanking; results are reported both
without a ranking condition and gated at each threshold in MIN_RANKINGS.

Bars, indicators, the SPY regime, the filter chain, the cooldown and entry resolution come from
turtlex.research.qullamaggie (parity-tested against QullamaggieStrategy); the 366d return comes
from turtlex.research.cohorts.forward_returns.
"""

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.cli import iso_date_type
from turtlex.common.report import REPORT_TIMEZONE, run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

EVAL_START = date(2021, 1, 1)
# Fixed, not date.today(): a trade needs qm.HOLD_CAL days of forward data to reach its exit, so
# scanning up to today only generates signals that are then dropped for want of an exit. Bump this
# as new years complete — or pass --end-date.
EVAL_END = date(2025, 12, 31)
# Last bar date the study may use. Signals stop at EVAL_END, but exits may reach forward to here,
# so a trade entered late in the window can still complete its 366d hold. Capped rather than
# open-ended so the historical windows don't drag in a decade of bars they never look at.
DATA_END = date(2026, 6, 30)
MIN_TRADES = 30
MIN_NEG = 10
MIN_RANKINGS = [qm.MIN_RANKING]  # QullamaggieRanking gates to sweep; qm.MIN_RANKING is the portfolio-runner default
ALGO_VERSION = "2.0"  # version encoded in the bk50d_sX_vN labels — an identity, not a filter value

SMA_THRESHS = [0.12, 0.16, 0.20]
# Only this variant, gated at MIN_RANKINGS[0], gets the monthly Mean%/N grid — it is the
# reference algorithm (see CLAUDE.md), and one grid per combination would be six tables.
MONTHLY_GRID_SMA_THRESH = 0.12
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Monthly-grid cell layout: `<mean>|<n>`, each half padded on its own so the `|` stays in a
# fixed column. 6 fits +1234.5-style means without shifting; 3 fits a 999-trade month.
_MEAN_W = 6
_N_W = 3

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-backtest-v4.md"


# ── Metrics ───────────────────────────────────────────────────────────────────


def compute_metrics(records: list[dict]) -> dict | None:
    """Study-level metrics: the shared trade metrics plus this study's own signal frequency.

    `mean` carries the **annualized** mean return — with a single 366d hold it differs from the
    raw mean only by the 365/366 factor, but reporting one annualized figure keeps the column
    comparable with studies run at other holding periods.
    """
    if len(records) < MIN_TRADES:
        return None
    a = np.array([r["ret"] for r in records])
    m = compute_trade_metrics(a * 100, qm.HOLD_CAL, min_losers=MIN_NEG)
    if m is None or np.isnan(m.sortino) or m.sortino <= 0:
        return None
    months = (EVAL_END.year - EVAL_START.year) * 12 + (EVAL_END.month - EVAL_START.month)
    return {
        "n": m.n,
        "win": m.win_pct,
        "mean": m.ann_mean_pct,
        "med": m.median_pct,
        "pf": m.profit_factor,
        "sr": m.sortino,
        "cvar": m.cvar95_pct,
        "freq": len(a) / max(months, 1),
    }


# ── Output ─────────────────────────────────────────────────────────────────────

# The hold is fixed at qm.HOLD_CAL, so an Exit column would repeat one value on every row; Mean%
# carries the annualized figure directly rather than reporting raw and annualized side by side.
_HDR = (
    f"{'Entry Signal':<16}  {'Gate':<8}  "
    f"{'N':>4}  {'Win%':>5}  {'Mean%':>7}  {'Med%':>7}  {'PF':>5}  {'Sortino':>7}  "
    f"{'CVaR%':>7}  {'F/mo':>5}"
)
_SEP = "─" * len(_HDR)


def fmt_row(label: str, gate_label: str, m: dict) -> str:
    return (
        f"{label:<16}  {gate_label:<8}  "
        f"{m['n']:>4}  {m['win']:>5.1f}  {m['mean']:>+7.2f}  {m['med']:>+7.2f}  "
        f"{m['pf']:>5.2f}  {m['sr']:>7.3f}  "
        f"{m['cvar']:>+7.2f}  {m['freq']:>5.1f}"
    )


def build_rankings(results: list[tuple[str, str, dict]]) -> str:
    """Render one table carrying both ranking treatments.

    `results` arrives already ordered: algorithm groups in SMA-threshold order, and within each
    group the ungated row followed by the gated one, so the pair reads across instead of across
    two separate tables (Step 6 of the spec).

    Args:
        results: `(label, gate_label, metrics)` in display order

    Returns:
        The rendered table.
    """
    lines = [_HDR, _SEP]
    for lbl, gate_label, m in results:
        lines.append(fmt_row(lbl, gate_label, m))
    lines += ["", f"Valid combinations: {len(results)}"]
    return "\n".join(lines)


# History-of-changes row: the ranking table's columns minus `Entry Signal` and `Gate` (the log
# only ever tracks the reference algorithm), with a run timestamp in front. Kept byte-aligned
# with the table in docs/research/qullamaggie-backtest-v4.md so a pasted row lands in column.
_HISTORY_HDR = (
    f"{'Execution':<19} {'N':>4}  {'Win%':>5}  {'Mean%':>7}  {'Med%':>7}  {'PF':>5}  {'Sortino':>7}  {'CVaR%':>7}  {'F/mo':>5}  Comment"
)


def build_history_row(m: dict) -> str:
    """Render the copy-pasteable `### History of changes` row for the reference algorithm.

    The spec keeps that log by hand — the script must not write into the methodology doc, or a
    re-run would erase the history it exists to accumulate — so this is printed to stdout for
    the operator to paste, with `<what changed>` left as a placeholder only they can fill.

    The timestamp is pinned to Tallinn like `run_timestamp`, and for the same reason: runs come
    from more than one host, and the log is ordered by this column. The zone suffix is dropped
    because the column is 19 characters wide in the doc's table.

    Args:
        m: metrics dict for `bk50d_s12_v2.0` gated at `MIN_RANKINGS[0]`

    Returns:
        Two lines — the column header and the row itself.
    """
    stamp = datetime.now(REPORT_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    row = (
        f"{stamp:<19} {m['n']:>4}  {m['win']:>5.1f}  {m['mean']:>+7.2f}  {m['med']:>+7.2f}  "
        f"{m['pf']:>5.2f}  {m['sr']:>7.3f}  {m['cvar']:>+7.2f}  {m['freq']:>5.1f}  <what changed>"
    )
    return f"{_HISTORY_HDR}\n{row}"


def build_monthly_grid(records: list[dict]) -> str:
    """Monthly `Mean%|N` grid, rows = entry year, columns = entry month.

    Each cell is the mean 366d return of the trades *entered* that month and how many there
    were; `·` marks a month with no entries. The right-hand pair is the year's own aggregate
    across all its months, not the mean of the cells.

    The two halves of a cell are padded independently — mean right-aligned in `_MEAN_W`, count
    left-aligned in `_N_W` — so the `|` lands in the same column on every row. Right-aligning
    the joined string instead lets the separator drift with each cell's width, which is what
    makes the numbers impossible to scan down a column.

    Args:
        records: trade records carrying `entry_date` and `ret`

    Returns:
        The rendered fixed-width grid.
    """
    by_ym: dict[tuple[int, int], list[float]] = {}
    for r in records:
        entry = r["entry_date"]
        by_ym.setdefault((entry.year, entry.month), []).append(r["ret"])

    empty = f"{'·':>{_MEAN_W}}{'':{_N_W + 1}}"  # dot sits under the mean column
    hdr = f"{'Year':>5} | " + " ".join(f"{mo:>{_MEAN_W}}{'':{_N_W + 1}}" for mo in MONTHS) + f" | {'Mean%':>7} {'N':>5}"
    lines = [hdr, "-" * len(hdr)]
    if not by_ym:
        return "\n".join([*lines, "(no trades)"])

    for year in sorted({y for y, _m in by_ym}):
        cells: list[str] = []
        year_rets: list[float] = []
        for month_idx in range(1, 13):
            vals = by_ym.get((year, month_idx))
            if vals:
                cells.append(f"{np.mean(vals) * 100:>+{_MEAN_W}.1f}|{len(vals):<{_N_W}}")
                year_rets.extend(vals)
            else:
                cells.append(empty)
        year_mean = float(np.mean(year_rets)) * 100 if year_rets else float("nan")
        lines.append(f"{year:>5} | " + " ".join(cells) + f" | {year_mean:>+6.1f}% {len(year_rets):>5}")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Parse the evaluation window and output path.

    Returns:
        Namespace with start_date, end_date and output.
    """
    parser = argparse.ArgumentParser(description="Qullamaggie breakout backtest v4 (SMA-threshold × ranking-gate sweep)")
    parser.add_argument("--start-date", type=iso_date_type, default=EVAL_START, help="evaluation window start (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=iso_date_type, default=EVAL_END, help="evaluation window end (YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, default=RESULT_PATH, help="markdown result path")
    return parser.parse_args()


def main() -> None:
    global EVAL_START, EVAL_END, RESULT_PATH

    args = parse_args()
    EVAL_START, EVAL_END, RESULT_PATH = args.start_date, args.end_date, args.output
    if EVAL_END <= EVAL_START:
        raise ValueError(f"--end-date {EVAL_END} must be after --start-date {EVAL_START}")

    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)
    data_start = EVAL_START - timedelta(days=qm.WARMUP_DAYS)
    # Forward bars only as far as the last entry could need (EVAL_END + hold + entry search),
    # and never past DATA_END — so a 2010-2015 run loads ~7 years, not ~18.
    data_end = min(DATA_END, EVAL_END + timedelta(days=qm.HOLD_CAL + qm.ENTRY_SEARCH_DAYS))
    print(f"Eval {EVAL_START} – {EVAL_END}  |  bars {data_start} – {data_end}", flush=True)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, data_end)

    df, bars = cohorts.load_universe(bars_history, EVAL_START, end=data_end)

    # Spec Step 6 fixes the output order: algorithms from the widest SMA threshold down
    # (s20, s16, s12), and within each the ungated row before the gated one.
    results: list[tuple[str, str, dict]] = []
    monthly_label = ""
    monthly_records: list[dict] = []
    history_metrics: dict | None = None

    for sma_t in sorted(SMA_THRESHS, reverse=True):
        lbl = f"bk50d_s{round(sma_t * 100)}_v{ALGO_VERSION}"
        print(f"  {lbl} …", flush=True)
        trades = cohorts.cohort_trades(df, bars, bull_dates, sma_t, gated=False, start=EVAL_START, end=EVAL_END)
        trades = trades.sort("symbol", "date")
        m = compute_metrics(trades.select("entry_date", "ret").to_dicts())
        if m is not None:
            results.append((lbl, "ungated", m))
        for min_rank in MIN_RANKINGS:
            gated = trades.filter(pl.col("ranking") >= min_rank)
            if gated.is_empty():
                continue
            records_gated = gated.select("entry_date", "ret").to_dicts()
            m_gated = compute_metrics(records_gated)
            if m_gated is not None:
                results.append((lbl, f"R>={min_rank}", m_gated))
                if sma_t == MONTHLY_GRID_SMA_THRESH and min_rank == MIN_RANKINGS[0]:
                    monthly_label, monthly_records = f"{lbl} R>={min_rank}", records_gated
                    history_metrics = m_gated

    # ── Print tables ───────────────────────────────────────────────────────────

    gates_str = ", ".join(str(r) for r in MIN_RANKINGS)
    output = build_rankings(results)
    print("\n" + output)

    monthly_grid = build_monthly_grid(monthly_records) if monthly_records else ""
    if monthly_grid:
        print(f"\n=== {monthly_label} — Monthly Mean% / N ===\n{monthly_grid}")

    # Printed, never written: the log lives in the methodology doc, which this script must not
    # touch. The eval window is called out because that log tracks the 2021-2025 baseline only,
    # so a row from one of the historical windows must not be pasted into it.
    if history_metrics is not None:
        print(
            f"\n=== History row — {monthly_label}, eval {EVAL_START} – {EVAL_END} ===\n"
            "Paste into docs/research/qullamaggie-backtest-v4.md → History of changes "
            "(baseline window only), then replace <what changed>.\n"
            f"{build_history_row(history_metrics)}"
        )

    # ── Write markdown result ──────────────────────────────────────────────────
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Backtest v4 — Results\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        sma_vals = ", ".join(f"{int(v * 100)}%" for v in SMA_THRESHS)
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Algorithm version | {ALGO_VERSION} (encoded as `_v{ALGO_VERSION}` in the names below) |\n")
        fh.write("| Breakout | 50d high |\n")
        fh.write(f"| Entry | next trading day's adjusted open (within {qm.ENTRY_SEARCH_DAYS} cal days of the signal) |\n")
        fh.write("| Exit | close of the first bar at or after entry + hold |\n")
        fh.write(f"| SMA thresh sweep | {sma_vals} |\n")
        fh.write("| Tight range | disabled (commented out) |\n")
        fh.write(f"| Hold sweep | {qm.HOLD_CAL}d (calendar); entries without {qm.HOLD_CAL}d of forward data are skipped |\n")
        fh.write("| Ranking | QullamaggieRanking (ADR 40 / SMA50 35 / price 25) |\n")
        fh.write(f"| Ranking gate sweep | ungated, ≥ {gates_str} |\n")
        fh.write("| vol_dry_up | disabled (commented out) |\n")
        fh.write(f"| vol_surge | volume/avg_vol_50 < {qm.VOL_SURGE_MAX}× (no lower bound) |\n")
        fh.write(f"| roc_12m_cap | 12m ROC < {int(qm.ROC_CAP * 100)}% |\n")
        fh.write(f"| RSI | RSI(14) < {int(qm.RSI_CAP)} |\n")
        fh.write(f"| ADR | mean((high-low)/low, last 20d, shift-1) ≥ {qm.ADR_MIN * 100:.1f}% |\n")
        fh.write(f"| ADR change | ADR%(10d) / ADR%(50d) < {int(qm.ADR_CHANGE_CAP * 100)}% |\n")
        fh.write("| SMA alignment | disabled (commented out) |\n")
        fh.write("| Market regime | SPY close > 200d SMA |\n")
        fh.write(f"| Price range | > ${qm.MIN_PRICE:.0f} and < ${qm.MAX_PRICE:.0f} |\n")
        fh.write(f"| Min avg vol (20d) | ≥ {qm.MIN_AVG_VOL // 1000}K |\n")
        fh.write(f"| Min history | ≥ {qm.MIN_BARS} trading days |\n")
        fh.write(f"| Cooldown | {qm.COOLDOWN_DAYS} calendar days |\n")
        fh.write(f"| Eval period | {EVAL_START} – {EVAL_END} |\n")
        fh.write(f"| Burn-in (indicators only) | {EVAL_START - timedelta(days=qm.WARMUP_DAYS)} – {EVAL_START} |\n")
        fh.write("| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |\n")
        fh.write(f"| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py) |\n\n")
        fh.write("## Rankings\n\n")
        fh.write(
            "Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: "
            "`ungated` takes every signal that meets the entering condition, "
            f"`R>={gates_str}` takes a trade only if its `QullamaggieRanking` score "
            "(`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. "
            "The two rows come from the same signals, held and exited identically, so the difference "
            "isolates the gate — the drop in `N` between them is how selective it is. The score uses "
            "the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw "
            "signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold "
            "(s20, s16, s12), ungated before gated.\n\n```text\n"
        )
        fh.write(output)
        fh.write("\n```\n\n")
        if monthly_grid:
            fh.write(f"## Monthly Mean% / N — {monthly_label}\n\n")
            fh.write(
                "Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the "
                "full 366 days; `·` marks a month with no entries. The right-hand pair is the year's "
                "own aggregate across all its months, not the mean of the cells. Only this one "
                "combination is shown — it is the reference algorithm, and a grid per combination "
                "would be six tables.\n\n```text\n"
            )
            fh.write(monthly_grid)
            fh.write("\n```\n\n")

        fh.write("## Findings & Caveats\n\n")
        fh.write("### Ideas to improve\n\n")
        ideas = [
            "source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot",
            "source a delisted-ticker history if available to address survivorship",
            "add a slippage/commission assumption on top of the next-day-open fill",
            f"widen the gate sweep past {max(MIN_RANKINGS)} to find where the score stops separating outcomes",
            "report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold",
            "account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence",
            "re-run all three windows (2010-2015, 2016-2020, 2021-present) before accepting any parameter change — "
            "a change that only improves the window it was chosen on is fitted to that window",
            f"pick the ranking gate per SMA threshold rather than one R≥{MIN_RANKINGS[0]} across s12/s16/s20; the same "
            "score rejects a very different share of each, so it is not the same filter at each",
            "report per-year Sortino again — the Yrs+/Consistent columns were dropped from the table, so a "
            "combination that only works in one year is no longer visible at a glance",
        ]
        for idea in ideas:
            fh.write(f"- {idea}\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
