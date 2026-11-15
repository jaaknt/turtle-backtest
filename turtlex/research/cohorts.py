"""Shared pipeline for the scripts/qullamaggie-cohorts-*.py studies.

A cohort study drops one production entry filter, raises signals for each algorithm arm,
holds every entry a fixed 366 calendar days (`qm.HOLD_CAL`), and tabulates the returns by
buckets of the variable the dropped filter used to cap. The studies differ only in which
filter they drop, which variable they bucket and how they label the table; everything else
lives here, so a study script is its docstring, its configuration table and a `CohortSpec`.

Signals come from `turtlex.research.qullamaggie`, which is parity-tested against
`QullamaggieStrategy`, and every metric from `turtlex.backtest.metrics`.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import TradeMetrics, compute_trade_metrics
from turtlex.common.report import config_table, run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm

EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
# Below this many losing trades a cohort's Sortino is reported as n/a.
MIN_LOSERS = 5
# Below this many trades a cohort row prints dashes instead of metrics.
MIN_TRADES = 5

# (label, lower bound inclusive, upper bound exclusive)
Bucket = tuple[str, float, float]
# (label, condition over the trade frame)
Reference = tuple[str, pl.Expr]


@dataclass(frozen=True)
class Arm:
    """One algorithm variant a study tabulates, e.g. `bk50d_s12_v2.0`.

    Attributes:
        label: Table heading
        sma_thresh: Minimum fraction above the 50-day SMA for the breakout to count
    """

    label: str
    sma_thresh: float


STANDARD_ARMS = (
    Arm("bk50d_s20_v2.0", 0.20),
    Arm("bk50d_s16_v2.0", 0.16),
    Arm("bk50d_s12_v2.0", 0.12),
)


@dataclass(frozen=True)
class CohortSpec:
    """Everything that distinguishes one cohort study from another.

    Attributes:
        title: Markdown H1 of the result document, without the leading `# `
        result_path: Where the result document is written
        config_rows: Rows of the document's configuration table
        tables: Renders one arm's trade frame (from `cohort_trades`) as table lines
        arms: The algorithm variants to run, one table block each
        drop: Names from `qm.entry_filters` the study removes
        require: Columns that must be non-null for a bar to be a candidate — the cohort
            variable, when it is not already guarded by a production filter
        gated: Apply the `qm.MIN_RANKING` gate. Off for studies whose cohort variable is a
            ranking input, where the gate would filter on the variable being measured
        add_indicators: Adds the study's own cohort column to the indicator frame
        preamble: Markdown placed between the run date and the configuration table
    """

    title: str
    result_path: Path
    config_rows: Sequence[tuple[str, str]]
    tables: Callable[[Arm, pl.DataFrame], list[str]]
    arms: Sequence[Arm] = STANDARD_ARMS
    drop: Sequence[str] = ()
    require: Sequence[str] = ()
    gated: bool = True
    add_indicators: Callable[[pl.DataFrame], pl.DataFrame] | None = None
    preamble: str = ""


def config_rows(rows: dict[str, str | None]) -> list[tuple[str, str]]:
    """Build a study's configuration table rows from the standard set.

    Every cohort study reports the same parameters in the same order, so result documents
    diff cleanly against each other. A study supplies what is its own — at least
    `Cohort variable` — and overrides any standard row; None omits one.
    A parameter the standard set lacks goes right after the one listed before it in `rows`
    (first, when it leads).

    Args:
        rows: Parameter -> value, merged over the standard rows

    Returns:
        (parameter, value) pairs in the standard order.
    """
    standard: dict[str, str | None] = {
        "Period": f"{EVAL_START} – {EVAL_END}",
        "Hold": f"{qm.HOLD_CAL}d (calendar)",
        "Cohorts": ", ".join(arm.label for arm in STANDARD_ARMS) + f" ({qm.HOLD_CAL}d)",
        "Cohort variable": None,
        "Entry": "next trading day's split/dividend-adjusted open",
        "Filter under study": None,
        "Fixed filters": "RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range)",
        "Ranking gate": f"QullamaggieRanking >= {qm.MIN_RANKING}",
        "Market regime": "SPY close > 200d SMA",
        "Price range": f"> ${qm.MIN_PRICE:.0f} and < ${qm.MAX_PRICE:.0f}",
        "Min avg vol (20d)": f">= {qm.MIN_AVG_VOL // 1000}K",
        "Cooldown": f"{qm.COOLDOWN_DAYS} calendar days",
        "Universe": "US common stocks, market_cap >= 1.5B, excl. Comm/RE",
        "Sortino": f"mean / RMS(min(r,0)) over all N x sqrt(365/hold), min {MIN_LOSERS} losers (turtlex/backtest/metrics.py)",
    }
    order = list(standard)
    previous: str | None = None
    for name in rows:
        if name not in standard:
            order.insert(0 if previous is None else order.index(previous) + 1, name)
        previous = name
    merged = standard | rows
    return [(name, value) for name in order if (value := merged[name]) is not None]


def forward_returns(signals: pl.DataFrame, df: pl.DataFrame) -> pl.DataFrame:
    """Attach each entered signal's return over a fixed calendar-day hold.

    The exit is the first bar on or after `entry_date + qm.HOLD_CAL`. A signal whose symbol's
    data ends before that date is dropped rather than exited early, so every return covers
    the full hold.

    Args:
        signals: Signals carrying `entry_date` and `entry_price`, from `qm.resolve_entries`
        df: Bar frame with symbol, date and adj_close running past the last exit

    Returns:
        The signals that complete the hold, in their input order, with `ret` (a fraction) added.
    """
    target = signals.with_row_index("_row").with_columns((pl.col("entry_date") + pl.duration(days=qm.HOLD_CAL)).alias("_exit_target"))
    # Project before filtering, so the filter copies three columns rather than the whole indicator frame.
    closes = df.select("symbol", pl.col("date").alias("_exit_date"), pl.col("adj_close").cast(pl.Float64).alias("_exit_price")).filter(
        pl.col("symbol").is_in(target["symbol"].unique().implode())
    )
    last = closes.group_by("symbol").agg(pl.col("_exit_date").max().alias("_last_date"))
    target = target.join(last, on="symbol").filter(pl.col("_last_date") >= pl.col("_exit_target"))
    exited = target.sort("_exit_target").join_asof(
        closes.sort("_exit_date"), left_on="_exit_target", right_on="_exit_date", by="symbol", strategy="forward", check_sortedness=False
    )
    return (
        exited.with_columns(((pl.col("_exit_price") - pl.col("entry_price")) / pl.col("entry_price")).alias("ret"))
        .sort("_row")
        .drop("_row", "_exit_target", "_last_date", "_exit_date", "_exit_price")
    )


def cohort_trades(
    df: pl.DataFrame,
    bars: pl.DataFrame,
    bull_dates: set[date],
    sma_thresh: float,
    *,
    drop: Sequence[str] = (),
    require: Sequence[str] = (),
    gated: bool = True,
    start: date = EVAL_START,
    end: date = EVAL_END,
) -> pl.DataFrame:
    """Raise one arm's signals, enter them next bar and attach their fixed-hold returns.

    The window end and the `require` guards join the candidate filter, ahead of the cooldown,
    as production's would. The ranking gate follows the cooldown: a trigger the gate rejects
    still starts its symbol's cooldown, as in `QullamaggieStrategy`.

    Args:
        df: Indicator frame from `qm.add_indicators`, running past `end` by the hold
        bars: Frame of symbol, date, adj_open for entry resolution
        bull_dates: Dates passing the SPY regime gate
        sma_thresh: Minimum fraction above the 50-day SMA
        drop: Names from `qm.entry_filters` to remove
        require: Columns that must be non-null on a candidate bar
        gated: Keep only signals ranked at or above `qm.MIN_RANKING`
        start: First signal date
        end: Last signal date

    Returns:
        One row per completed trade, sorted by (date, symbol), with the indicator columns,
        `ranking`, `entry_date`, `entry_price` and `ret`.
    """
    extra = [pl.col("date") <= end, *(pl.col(c).is_not_null() for c in require)]
    signals = qm.add_ranking(qm.get_signals(df, bull_dates, start, sma_thresh, drop=drop, extra=extra))
    if gated:
        signals = signals.filter(pl.col("ranking") >= qm.MIN_RANKING)
    return forward_returns(qm.resolve_entries(signals, bars), df)


def returns(trades: pl.DataFrame, condition: pl.Expr | None = None) -> np.ndarray:
    """Return the `ret` values of the matching trades.

    Args:
        trades: Trade frame from `cohort_trades`
        condition: Filter over the trade frame; None keeps every trade
    """
    selected = trades if condition is None else trades.filter(condition)
    return selected["ret"].to_numpy()


def bucket_groups(trades: pl.DataFrame, column: str | pl.Expr, buckets: Sequence[Bucket]) -> list[tuple[str, np.ndarray]]:
    """Split trade returns into half-open `[lo, hi)` buckets of `column`.

    Args:
        trades: Trade frame from `cohort_trades`
        column: Cohort variable, as a column name or an expression over the trade frame
        buckets: (label, lo, hi) per row, in display order

    Returns:
        (label, returns) per bucket.
    """
    value = pl.col(column) if isinstance(column, str) else column
    return [(label, returns(trades, (value >= lo) & (value < hi))) for label, lo, hi in buckets]


def _metrics(rets: np.ndarray) -> TradeMetrics | None:
    if len(rets) < MIN_TRADES:
        return None
    return compute_trade_metrics(rets * 100, qm.HOLD_CAL, min_losers=MIN_LOSERS)


def render_table(
    heading: str,
    groups: Sequence[tuple[str, np.ndarray]],
    footer: Sequence[tuple[str, np.ndarray]],
    label_width: int = 16,
    label_header: str = "Cohort",
) -> list[str]:
    """Render one cohort table as plain-text lines.

    Args:
        heading: Text of the `###` heading
        groups: (label, returns) per cohort row; a row too small for metrics prints dashes
        footer: (label, returns) per summary row below a closing rule; a row too small is
            omitted. Empty for a table with no summary, which then has no closing rule either
        label_width: Width of the label column
        label_header: Header of the label column

    Returns:
        The heading, header, rows and a trailing blank line.
    """
    header = f"{label_header:<{label_width}}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}  {'CVaR95%':>8}"
    rule = "─" * len(header)

    def row(label: str, m: TradeMetrics) -> str:
        sortino = "     n/a" if np.isnan(m.sortino) else f"{m.sortino:>8.3f}"
        return (
            f"{label:<{label_width}}  {m.n:>5}  {m.median_pct:>+7.2f}  {m.mean_pct:>+7.2f}  {m.win_pct:>6.1f}  "
            f"{sortino}  {m.profit_factor:>6.2f}  {m.cvar95_pct:>+8.2f}"
        )

    lines = [f"### {heading}", "", header, rule]
    for label, rets in groups:
        m = _metrics(rets)
        dashes = f"{label:<{label_width}}  {len(rets):>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}  {'—':>8}"
        lines.append(row(label, m) if m else dashes)
    if footer:
        lines.append(rule)
    for label, rets in footer:
        m = _metrics(rets)
        if m:
            lines.append(row(label, m))
    lines.append("")
    return lines


def bucket_table(
    heading: str,
    trades: pl.DataFrame,
    column: str | pl.Expr,
    buckets: Sequence[Bucket],
    references: Sequence[Reference],
    label_width: int = 16,
) -> list[str]:
    """Render the standard table: one row per bucket, then `ALL` and the reference rows.

    Args:
        heading: Text of the `###` heading
        trades: Trade frame from `cohort_trades`
        column: Cohort variable, as a column name or an expression over the trade frame
        buckets: (label, lo, hi) per row
        references: (label, condition) per footer row — typically what the dropped
            production filter would have kept
        label_width: Width of the label column

    Returns:
        The rendered table lines.
    """
    footer = [("ALL", returns(trades)), *((label, returns(trades, cond)) for label, cond in references)]
    return render_table(heading, bucket_groups(trades, column, buckets), footer, label_width)


def write_result(path: Path, title: str, config: str, lines: Sequence[str], preamble: str = "", results_intro: str = "") -> None:
    """Write a cohort study's result document.

    Args:
        path: Destination markdown file
        title: H1 text, without the leading `# `
        config: Rendered configuration table, from `config_table`
        lines: Result lines, placed in one `text` code block
        preamble: Markdown placed between the run date and the configuration
        results_intro: Markdown placed between the results heading and the tables
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines)
    path.write_text(
        f"# {title}\n\nRun date: {run_timestamp()}\n\n{preamble}"
        f"## Configuration\n\n{config}\n## Results\n\n{results_intro}```text\n{body}\n```\n"
    )
    print(f"\nResults saved to {path}", flush=True)


def load_universe(
    bars_history: DailyBarsQueryRepository,
    start: date = EVAL_START,
    add_indicators: Callable[[pl.DataFrame], pl.DataFrame] | None = None,
    load: Callable[[DailyBarsQueryRepository, date, date], pl.DataFrame] = qm.load_bars,
    end: date | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load the qualified universe from `start` to `end` and compute its indicators.

    Bars run to today by default rather than to the window end: a 366d hold needs forward
    data beyond the last signal date.

    Args:
        bars_history: Repository for accessing historical bar data
        start: First signal date; `qm.load_bars` adds the indicator warmup before it
        add_indicators: The study's own indicator step, run after `qm.add_indicators`
        load: Bar loader with `qm.load_bars`'s signature, for a study that widens the universe
        end: Last bar date to load; today when None

    Returns:
        (indicator frame, entry-resolution frame of symbol, date, adj_open).
    """
    print("Loading bars …", flush=True)
    df = load(bars_history, start, end or date.today())
    print("Computing indicators …", flush=True)
    # Project down to the columns qm.resolve_entries reads before building the indicator
    # frame, so the full-width bar frame is released rather than held alongside it.
    bars = df.select("symbol", "date", "adj_open")
    df = qm.add_indicators(df)
    if add_indicators is not None:
        df = add_indicators(df)
    return df, bars


def run_cohort_study(spec: CohortSpec) -> None:
    """Run a standard cohort study end to end and write its result document.

    Args:
        spec: The study's definition
    """
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)
    df, bars = load_universe(bars_history, add_indicators=spec.add_indicators)

    config = config_table(spec.config_rows)
    print("\n" + config)

    lines: list[str] = []
    for arm in spec.arms:
        print(f"  {arm.label} …", flush=True)
        trades = cohort_trades(df, bars, bull_dates, arm.sma_thresh, drop=spec.drop, require=spec.require, gated=spec.gated)
        print(f"    {trades.height} trades", flush=True)
        table = spec.tables(arm, trades)
        lines.extend(table)
        print("\n".join(table))

    write_result(spec.result_path, spec.title, config, lines, spec.preamble)
