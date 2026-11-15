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
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TypeGuard

import numpy as np
import polars as pl

from turtlex.backtest.metrics import TradeMetrics, compute_trade_metrics
from turtlex.common.cli import iso_date_type
from turtlex.common.report import REPORT_TIMEZONE, config_table, run_timestamp
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
GATES_STR = ", ".join(str(r) for r in MIN_RANKINGS)  # the gate sweep, as the result doc prints it
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


@dataclass(frozen=True)
class Window:
    """The evaluation window, from the CLI."""

    start: date
    end: date

    @property
    def months(self) -> int:
        """Whole calendar months from start to end, the base of the signal frequency."""
        return (self.end.year - self.start.year) * 12 + (self.end.month - self.start.month)


# ── Metrics ───────────────────────────────────────────────────────────────────


def has_positive_sortino(m: TradeMetrics | None) -> TypeGuard[TradeMetrics]:
    """Whether the trade metrics exist and carry a finite, positive Sortino.

    Args:
        m: Trade metrics, or None when there were too few trades or losers

    Returns:
        True if `m` can be reported.
    """
    return m is not None and not np.isnan(m.sortino) and m.sortino > 0


def compute_metrics(records: list[dict], window: Window) -> dict | None:
    """Study-level metrics: the shared trade metrics plus this study's own signal frequency.

    `mean` carries the **annualized** mean return — with a single 366d hold it differs from the
    raw mean only by the 365/366 factor, but reporting one annualized figure keeps the column
    comparable with studies run at other holding periods.

    Args:
        records: Trade records carrying `ret`
        window: The evaluation window, for the per-month frequency

    Returns:
        The metrics dict, or None below MIN_TRADES trades or without a positive Sortino.
    """
    if len(records) < MIN_TRADES:
        return None
    a = np.array([r["ret"] for r in records])
    m = compute_trade_metrics(a * 100, qm.HOLD_CAL, min_losers=MIN_NEG)
    if not has_positive_sortino(m):
        return None
    return {
        "n": m.n,
        "win": m.win_pct,
        "mean": m.ann_mean_pct,
        "med": m.median_pct,
        "pf": m.profit_factor,
        "sr": m.sortino,
        "cvar": m.cvar95_pct,
        "freq": len(a) / max(window.months, 1),
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

    hdr = f"{'Year':>5} | " + " ".join(f"{mo:>{_MEAN_W}}{'':{_N_W + 1}}" for mo in MONTHS) + f" | {'Mean%':>7} {'N':>5}"
    lines = [hdr, "-" * len(hdr)]
    if not by_ym:
        return "\n".join([*lines, "(no trades)"])

    lines.extend(_grid_row(year, by_ym) for year in sorted({y for y, _m in by_ym}))
    return "\n".join(lines)


def _grid_row(year: int, by_ym: dict[tuple[int, int], list[float]]) -> str:
    """One year of the monthly grid: a `Mean%|N` cell per month, then the year's own aggregate.

    Args:
        year: Entry year
        by_ym: Trade returns keyed by (entry year, entry month)

    Returns:
        The grid row.
    """
    empty = f"{'·':>{_MEAN_W}}{'':{_N_W + 1}}"  # dot sits under the mean column
    month_vals = [by_ym.get((year, month_idx)) for month_idx in range(1, 13)]
    cells = [f"{np.mean(vals) * 100:>+{_MEAN_W}.1f}|{len(vals):<{_N_W}}" if vals else empty for vals in month_vals]
    year_rets = [v for vals in month_vals if vals for v in vals]
    year_mean = float(np.mean(year_rets)) * 100 if year_rets else float("nan")
    return f"{year:>5} | " + " ".join(cells) + f" | {year_mean:>+6.1f}% {len(year_rets):>5}"


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


@dataclass(frozen=True)
class Reference:
    """The reference algorithm's cell, which also gets the monthly grid and the history row."""

    label: str
    records: list[dict]
    metrics: dict


@dataclass
class Sweep:
    """The sweep's output: the ranking rows, plus the reference cell when it has enough trades."""

    results: list[tuple[str, str, dict]] = field(default_factory=list)
    reference: Reference | None = None


def algo_label(sma_t: float) -> str:
    """The `bk50d_sX_vN` name of the algorithm at SMA threshold `sma_t`."""
    return f"bk50d_s{round(sma_t * 100)}_v{ALGO_VERSION}"


def add_gated_rows(sweep: Sweep, trades: pl.DataFrame, sma_t: float, window: Window) -> None:
    """Append one algorithm's gated rows, and capture the reference cell for the grid and history row.

    Args:
        sweep: Accumulates the rows
        trades: The algorithm's ungated trades, carrying `ranking`
        sma_t: The algorithm's SMA threshold
        window: The evaluation window
    """
    lbl = algo_label(sma_t)
    for min_rank in MIN_RANKINGS:
        records_gated = trades.filter(pl.col("ranking") >= min_rank).select("entry_date", "ret").to_dicts()
        m_gated = compute_metrics(records_gated, window)
        if m_gated is None:
            continue
        sweep.results.append((lbl, f"R>={min_rank}", m_gated))
        if sma_t == MONTHLY_GRID_SMA_THRESH and min_rank == MIN_RANKINGS[0]:
            sweep.reference = Reference(f"{lbl} R>={min_rank}", records_gated, m_gated)


def run_sweep(df: pl.DataFrame, bars: pl.DataFrame, bull_dates: set[date], window: Window) -> Sweep:
    """Every SMA threshold, ungated and at each ranking gate.

    Spec Step 6 fixes the output order: algorithms from the widest SMA threshold down
    (s20, s16, s12), and within each the ungated row before the gated one.

    Args:
        df: Indicator frame, from `cohorts.load_universe`
        bars: Adjusted bars, for the forward returns
        bull_dates: Dates passing the SPY regime gate
        window: The evaluation window

    Returns:
        The sweep's rows, grid records and history metrics.
    """
    sweep = Sweep()
    for sma_t in sorted(SMA_THRESHS, reverse=True):
        lbl = algo_label(sma_t)
        print(f"  {lbl} …", flush=True)
        trades = cohorts.cohort_trades(df, bars, bull_dates, sma_t, gated=False, start=window.start, end=window.end)
        trades = trades.sort("symbol", "date")
        m = compute_metrics(trades.select("entry_date", "ret").to_dicts(), window)
        if m is not None:
            sweep.results.append((lbl, "ungated", m))
        add_gated_rows(sweep, trades, sma_t, window)
    return sweep


def config_rows(window: Window) -> list[tuple[str, str]]:
    """The result doc's configuration table rows.

    Args:
        window: The evaluation window

    Returns:
        `(parameter, value)` pairs for `turtlex.common.report.config_table`.
    """
    sma_vals = ", ".join(f"{int(v * 100)}%" for v in SMA_THRESHS)
    return [
        ("Algorithm version", f"{ALGO_VERSION} (encoded as `_v{ALGO_VERSION}` in the names below)"),
        ("Breakout", "50d high"),
        ("Entry", f"next trading day's adjusted open (within {qm.ENTRY_SEARCH_DAYS} cal days of the signal)"),
        ("Exit", "close of the first bar at or after entry + hold"),
        ("SMA thresh sweep", sma_vals),
        ("Tight range", "disabled (commented out)"),
        ("Hold sweep", f"{qm.HOLD_CAL}d (calendar); entries without {qm.HOLD_CAL}d of forward data are skipped"),
        ("Ranking", "QullamaggieRanking (ADR 40 / SMA50 35 / price 25)"),
        ("Ranking gate sweep", f"ungated, ≥ {GATES_STR}"),
        ("vol_dry_up", "disabled (commented out)"),
        ("vol_surge", f"volume/avg_vol_50 < {qm.VOL_SURGE_MAX}× (no lower bound)"),
        ("roc_12m_cap", f"12m ROC < {int(qm.ROC_CAP * 100)}%"),
        ("RSI", f"RSI(14) < {int(qm.RSI_CAP)}"),
        ("ADR", f"mean((high-low)/low, last 20d, shift-1) ≥ {qm.ADR_MIN * 100:.1f}%"),
        ("ADR change", f"ADR%(10d) / ADR%(50d) < {int(qm.ADR_CHANGE_CAP * 100)}%"),
        ("SMA alignment", "disabled (commented out)"),
        ("Market regime", "SPY close > 200d SMA"),
        ("Price range", f"> ${qm.MIN_PRICE:.0f} and < ${qm.MAX_PRICE:.0f}"),
        ("Min avg vol (20d)", f"≥ {qm.MIN_AVG_VOL // 1000}K"),
        ("Min history", f"≥ {qm.MIN_BARS} trading days"),
        ("Cooldown", f"{qm.COOLDOWN_DAYS} calendar days"),
        ("Eval period", f"{window.start} – {window.end}"),
        ("Burn-in (indicators only)", f"{window.start - timedelta(days=qm.WARMUP_DAYS)} – {window.start}"),
        ("Universe", "US common stocks, market_cap ≥ 1.5B, excl. Comm/RE"),
        ("Sortino", f"mean / RMS(min(r,0)) over all N × sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py)"),
    ]


def ideas() -> list[str]:
    """The `### Ideas to improve` bullets."""
    return [
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


def render_markdown(window: Window, rankings: str, monthly_label: str, monthly_grid: str) -> str:
    """The result doc.

    Args:
        window: The evaluation window
        rankings: The rendered ranking table
        monthly_label: The reference algorithm's label, heading its grid
        monthly_grid: The rendered monthly grid, or "" when there is none

    Returns:
        The markdown document.
    """
    parts = [
        "# Qullamaggie Backtest v4 — Results\n\n",
        f"Run date: {run_timestamp()}\n\n",
        "## Configuration\n\n",
        config_table(config_rows(window)) + "\n",
        "## Rankings\n\n",
        "Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: "
        "`ungated` takes every signal that meets the entering condition, "
        f"`R>={GATES_STR}` takes a trade only if its `QullamaggieRanking` score "
        "(`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. "
        "The two rows come from the same signals, held and exited identically, so the difference "
        "isolates the gate — the drop in `N` between them is how selective it is. The score uses "
        "the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw "
        "signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold "
        "(s20, s16, s12), ungated before gated.\n\n```text\n",
        rankings,
        "\n```\n\n",
    ]
    if monthly_grid:
        parts += [
            f"## Monthly Mean% / N — {monthly_label}\n\n",
            "Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the "
            "full 366 days; `·` marks a month with no entries. The right-hand pair is the year's "
            "own aggregate across all its months, not the mean of the cells. Only this one "
            "combination is shown — it is the reference algorithm, and a grid per combination "
            "would be six tables.\n\n```text\n",
            monthly_grid,
            "\n```\n\n",
        ]
    parts += ["## Findings & Caveats\n\n", "### Ideas to improve\n\n", *(f"- {idea}\n" for idea in ideas())]
    return "".join(parts)


def print_history_row(ref: Reference | None, window: Window) -> None:
    """Print the reference algorithm's copy-pasteable history row, when it has one.

    Printed, never written: the log lives in the methodology doc, which this script must not
    touch. The eval window is called out because that log tracks the 2021-2025 baseline only,
    so a row from one of the historical windows must not be pasted into it.

    Args:
        ref: The reference cell, or None when it had too few trades
        window: The evaluation window
    """
    if ref is None:
        return
    print(
        f"\n=== History row — {ref.label}, eval {window.start} – {window.end} ===\n"
        "Paste into docs/research/qullamaggie-backtest-v4.md → History of changes "
        "(baseline window only), then replace <what changed>.\n"
        f"{build_history_row(ref.metrics)}"
    )


def main() -> None:
    args = parse_args()
    window = Window(args.start_date, args.end_date)
    if window.end <= window.start:
        raise ValueError(f"--end-date {window.end} must be after --start-date {window.start}")

    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)
    data_start = window.start - timedelta(days=qm.WARMUP_DAYS)
    # Forward bars only as far as the last entry could need (the window end + hold + entry
    # search), and never past DATA_END — so a 2010-2015 run loads ~7 years, not ~18.
    data_end = min(DATA_END, window.end + timedelta(days=qm.HOLD_CAL + qm.ENTRY_SEARCH_DAYS))
    print(f"Eval {window.start} – {window.end}  |  bars {data_start} – {data_end}", flush=True)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, window.start, data_end)
    df, bars = cohorts.load_universe(bars_history, window.start, end=data_end)
    sweep = run_sweep(df, bars, bull_dates, window)
    del df, bars  # nothing below reads the bars; free them before rendering

    rankings = build_rankings(sweep.results)
    print("\n" + rankings)
    ref = sweep.reference
    monthly_label, monthly_grid = (ref.label, build_monthly_grid(ref.records)) if ref is not None else ("", "")
    if monthly_grid:
        print(f"\n=== {monthly_label} — Monthly Mean% / N ===\n{monthly_grid}")
    print_history_row(ref, window)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(window, rankings, monthly_label, monthly_grid))
    print(f"\nResults saved to {args.output}", flush=True)


if __name__ == "__main__":
    main()
