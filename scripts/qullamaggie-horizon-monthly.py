#!/usr/bin/env python3
"""Marginal monthly performance of bk50d_s12_v2.0 signals, by signal-generation year.

Every other committed study measures a signal at exactly one horizon — 366 calendar days —
so the repo can say what a signal is worth after a year but not *when* during that year the
return is earned. This one decomposes the year, and runs six months past it: for each signal
it records the return earned **during** each of the 18 months after entry, then averages by
the calendar year the signal was generated in. A row read left to right is that vintage's
decay curve.

The returns are marginal, not cumulative:

    mark[0] = entry_price                      # next day's split/dividend-adjusted open
    mark[M] = adj_close of the first bar on or after entry_date + M calendar months
    ret[M]  = mark[M] / mark[M-1] - 1          # M = 1 .. 18

so month 12 lands within a day or two of the 366-day baseline exit. Chaining a row's means
does *not* reproduce a buy-and-hold return: each cell is an equal-weighted cross-sectional
average over whichever signals have both marks, and that cohort shrinks as M grows. The
gate-comparison table's `N@M18` column reports how much of each sample survives that far.

Results open with a gate-comparison table, then one Mean% matrix per ranking gate (`GATES`,
currently 44/60/70/80) plus the ungated set. All are produced from one signal generation — the
score is carried as a column rather than filtered on — so they share a cooldown chain, entries
and marks, and the differences between them isolate the gate. The gated sets are nested subsets
of the ungated one, and tightening past 60 shrinks the sample faster than it lifts the mean.

close/high/low are split/dividend-adjusted (scaled by adjusted_close/close), the same
convention as qullamaggie-backtest-v4.py. raw_close (unadjusted) is used only for the
MIN_PRICE/MAX_PRICE filter and the ranking's price band, the real tradeable price at entry.

Needs the VPS: the local Docker mirror only holds ~5 years, so run this with
ACTIVE_PROFILE=hetzner-db (see config/settings-hetzner-db.toml) or the early years come back
empty. Loading is chunked to hold peak memory near one chunk rather than the whole span —
see `_chunks` and CHUNK_YEARS.
"""

import argparse
import calendar
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.common.cli import iso_date_type
from turtlex.common.report import config_table, run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)

EVAL_START = date(2015, 1, 1)
EVAL_END = date(2025, 12, 31)

STRATEGY_LABEL = "bk50d_s12_v2.0"
SMA_THRESH = 0.12
MIN_RANKING = 44  # QullamaggieRanking gate, matching the portfolio-runner default
# Gates reported side by side, loosest first after the live one. The live gate leads; the rest
# are progressively stricter cuts, included to show whether the ranking's edge keeps scaling
# with selectivity or flattens out — and at what point the signal count stops filling a book.
GATES: list[int] = [MIN_RANKING, 60, 70, 80]
# A Mean% cell below this many signals prints `·` rather than a number — the same floor the
# cohort studies use (`if len(rets) < 5: return None`). At the tighter gates a thin year can
# fall to one or two names, where a mean is that name's story and reads as a finding. The row's
# `Sig` column still reports the year's true count, so nothing is hidden, only withheld.
MIN_CELL_N = 5

MAX_MONTH = 18
MIN_HISTORY = 300

# Signals are generated in 3-year slices. A single 2013-2026 load of the qualified universe is
# wider than the relax sweep, which already peaks at ~3.5 GB — over the 4 GB cap that keeps an
# OOM from taking the whole WSL distro down. Only the small per-signal record list survives a
# chunk, so peak memory tracks one chunk rather than the span. Boundaries are safe for the
# 30-day cooldown because qm.get_signals runs its cooldown chain over the warmup rows too.
CHUNK_YEARS = 3
# Each chunk's bars run this far past its last signal date so a signal on the final day still
# has a bar 18 months out. 580 > 18 months (~548d) with room for the next trading day.
FORWARD_PAD_DAYS = 580
# A symbol whose last bar is within this many calendar days of the last bar in the data is
# treated as still quoted. Absorbs the odd missing final session without calling the series ended.
STILL_TRADING_DAYS = 7

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-horizon-monthly.md"


# ── Month arithmetic ──────────────────────────────────────────────────────────


def add_months(d: date, months: int) -> date:
    """Return `d` advanced by whole calendar months, clamped to the target month's last day.

    Exact calendar arithmetic rather than a 30.44-day approximation, so month 12 lines up with
    the 366-day baseline exit instead of drifting a week off it. Clamping is what makes
    Jan 31 + 1 month land on Feb 28/29 rather than raising.

    Args:
        d: The anchor date
        months: Whole months to add (non-negative)

    Returns:
        The shifted date.
    """
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


# ── Ranking ──────────────────────────────────────────────────────────────────

_ranker = QullamaggieRanking()


def compute_ranking(row: dict) -> int:
    """Score one signal 0-100 with the production QullamaggieRanking.

    `raw_close` is mapped onto the `close` column the ranking reads: QullamaggieStrategy
    keeps `close` unadjusted and the price bands are dollar-denominated.
    """
    row_df = pl.DataFrame(
        [{"date": row["date"], "close": row["raw_close"], "adr_pct": row["adr_pct"], "pct_vs_sma50": row["pct_vs_sma50"]}]
    )
    return _ranker.ranking(row_df, row["date"])


# ── Marginal monthly returns ──────────────────────────────────────────────────


def monthly_marks(entry_date: date, entry_price: float, dates: np.ndarray, closes: np.ndarray) -> list[float | None]:
    """Return the 19 price marks anchoring a signal's monthly returns: entry, then months 1-18.

    Mark M is the adjusted close of the first bar at or after `entry_date + M months`. A month
    with no such bar — the symbol stopped trading, or the data simply ends — is `None`, and so
    is every month after it.

    Args:
        entry_date: The signal's entry date
        entry_price: Fill price, the entry bar's adjusted open — this is mark 0
        dates: The symbol's bar dates as days since epoch, ascending
        closes: The symbol's adjusted closes, aligned with `dates`

    Returns:
        A list of `MAX_MONTH + 1` marks, `None` past the end of the symbol's data.
    """
    marks: list[float | None] = [entry_price]
    for month in range(1, MAX_MONTH + 1):
        target = (add_months(entry_date, month) - _EPOCH).days
        idx = int(np.searchsorted(dates, target))
        if idx >= len(dates):
            marks.extend([None] * (MAX_MONTH + 1 - len(marks)))
            break
        marks.append(float(closes[idx]))
    return marks


def marginal_returns(marks: list[float | None]) -> list[float | None]:
    """Convert a signal's price marks into the return earned during each month 1-18.

    Args:
        marks: Output of `monthly_marks` — mark 0 is the entry fill

    Returns:
        `MAX_MONTH` returns as fractions, `None` where either end of the month is unmarked.
    """
    out: list[float | None] = []
    for month in range(1, MAX_MONTH + 1):
        prev, curr = marks[month - 1], marks[month]
        out.append(None if prev is None or curr is None or prev <= 0 else curr / prev - 1.0)
    return out


def run_trades(signals: pl.DataFrame, bars: pl.DataFrame) -> tuple[list[dict], int, int]:
    """Expand each signal into its 18 marginal monthly returns.

    A signal whose price series ends mid-horizon contributes the months it does cover and drops
    out of the rest, the same convention the fixed-hold studies apply by skipping a trade without
    a full forward window. The two ways a series can end are counted separately, because they
    mean different things: a symbol still quoted at the end of the loaded bars ran out of
    *window*, while one whose quotes stopped earlier has a halted or zero-volume tail that
    `qm.load_bars` dropped. Note this is **not** a measure of delisting risk — `turtle.daily_bars`
    holds only currently-listed tickers, so companies that were acquired or wound up are absent
    from the data rather than ending early in it. `build_reading` says so in the result.

    The comparison is against the last bar the data actually holds, not today's date: the feed
    lags a day or two, and measuring from today classifies every still-trading symbol as ended.

    Args:
        signals: Signal frame from `qm.resolve_entries`, gated
        bars: Adjusted bars covering the signals and their forward pad — the whole universe,
            so the latest bar in it is the end of the data for this chunk

    Returns:
        `(records, n_short, n_truncated)` — one record per (signal, month) with a return,
        carrying the signal's `ranking` so every gate reads off one pass, plus the counts
        of signals short of 18 months for each of the two reasons. The counts cover every signal,
        gated or not, since ending early is a property of the price series and not of the gate.
    """
    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in bars.group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[str(sym)] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_closes[str(sym)] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    records: list[dict] = []
    n_short = 0
    n_truncated = 0
    universe_end_int = max(int(d[-1]) for d in sym_dates.values())
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        dates, closes = sym_dates.get(sym), sym_closes.get(sym)
        if dates is None or closes is None or len(dates) == 0:
            continue
        marks = monthly_marks(row["entry_date"], float(row["entry_price"]), dates, closes)
        rets = marginal_returns(marks)
        if rets[-1] is None:
            # Still quoted at the end of the loaded bars: the window ran out, not the series.
            if int(dates[-1]) >= universe_end_int - STILL_TRADING_DAYS:
                n_truncated += 1
            else:
                n_short += 1
        year, ranking = row["date"].year, int(row["ranking"])
        for month, ret in enumerate(rets, start=1):
            if ret is not None:
                records.append({"year": year, "month": month, "ret": ret, "ranking": ranking})
    return records, n_short, n_truncated


# ── Output ────────────────────────────────────────────────────────────────────


def _chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split the evaluation window into CHUNK_YEARS-long slices aligned to January 1."""
    out: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        stop = min(date(cursor.year + CHUNK_YEARS, 1, 1) - timedelta(days=1), end)
        out.append((cursor, stop))
        cursor = stop + timedelta(days=1)
    return out


def _matrix(
    trades: pl.DataFrame,
    years: list[int],
    title: str,
    cell: str,
    sig_counts: dict[int, int] | None,
) -> list[str]:
    """Render one year x month-since-entry matrix.

    Args:
        trades: Long frame of (year, month, ret)
        years: Row order
        title: Heading printed above the grid
        cell: Either "mean" or "n" — which statistic each cell carries
        sig_counts: Signals resolved per year, appended as a `Sig` column when given

    Returns:
        The rendered lines, heading included.
    """

    def fmt(rets: list[float]) -> str:
        if not rets:
            return f"{'·':>6}"  # no signals at all
        if cell == "n":
            return f"{len(rets):>6}"
        if len(rets) < MIN_CELL_N:
            return f"{'·':>6}"
        return f"{float(np.mean(rets)) * 100:>+6.1f}"

    tail = f" | {'Sig':>6}" if sig_counts is not None else ""
    header = f"{'Year':>5} | " + " ".join(f"{'M' + str(m):>6}" for m in range(1, MAX_MONTH + 1)) + tail
    sep = "-" * len(header)
    lines = [title, "", header, sep]

    def row(label: str, frame: pl.DataFrame, sig: int | None) -> str:
        cells = " ".join(fmt(frame.filter(pl.col("month") == m)["ret"].to_list()) for m in range(1, MAX_MONTH + 1))
        suffix = f" | {sig:>6}" if sig_counts is not None else ""
        return f"{label:>5} | {cells}{suffix}"

    for yr in years:
        lines.append(row(str(yr), trades.filter(pl.col("year") == yr), (sig_counts or {}).get(yr, 0)))
    lines.append(sep)
    lines.append(row("All", trades, sum((sig_counts or {}).values()) if sig_counts is not None else None))
    return lines


def build_tables(records: list[dict], signal_rows: list[dict]) -> list[str]:
    """Render a Mean% matrix for each ranking gate, plus the ungated set.

    Every treatment comes from one signal generation and differs only by the threshold applied
    to the score each signal already carries: same cooldown chain, same entries, same marks.
    That is what makes the blocks readable as the gate's effect rather than as separate studies.
    The gated sets are nested subsets of the ungated one.

    Args:
        records: One entry per (signal, month) with a return, carrying the signal's `ranking`
        signal_rows: One entry per entered signal, `{year, ranking}`, for the `Sig` column

    The per-cell N matrices this used to carry were dropped as redundant: the `Sig` column gives
    each year's count, and `build_summary` carries the totals and the month-18 attrition. What a
    cell drawn from too few signals looks like is handled by the `MIN_CELL_N` suppression instead.

    Returns:
        The rendered lines for the whole results block.
    """
    schema = {"year": pl.Int64, "month": pl.Int64, "ret": pl.Float64, "ranking": pl.Int64}
    trades = pl.DataFrame(records, schema=schema) if records else pl.DataFrame(schema=schema)
    sig_schema = {"year": pl.Int64, "ranking": pl.Int64}
    signals = pl.DataFrame(signal_rows, schema=sig_schema) if signal_rows else pl.DataFrame(schema=sig_schema)
    years = sorted(set(signals["year"].to_list()))

    def block(banner: str, floor: int) -> list[str]:
        frame = trades.filter(pl.col("ranking") >= floor)
        counts = dict(signals.filter(pl.col("ranking") >= floor).group_by("year").len().rows())
        rule = "─" * 94
        return [rule, banner, rule, ""] + _matrix(frame, years, "Mean% — return earned during month M", "mean", counts)

    lines: list[str] = []
    for gate in GATES:
        note = "  (the live configuration)" if gate == MIN_RANKING else "  (a stricter cut)"
        lines += block(f"R>={gate} — {STRATEGY_LABEL}, QullamaggieRanking >= {gate}{note}", gate)
        lines += ["", ""]
    lines += block(f"UNGATED — {STRATEGY_LABEL}, every signal the filters emit  (no ranking gate)", 0)
    return lines


def build_summary(records: list[dict], signal_rows: list[dict]) -> str:
    """Render the gate-comparison table: one row per treatment, loosest first.

    This is the table that answers "does tightening the gate keep paying?", and it is built so the
    answer cannot be read off the return columns alone. `Signals` and `Thinnest years` sit beside
    the means because a rising Mean% next to a collapsing sample is selectivity eating its own
    evidence, not an improving edge — and a gate leaving single-digit signals in a year cannot fill
    a book whatever its per-signal mean says.

    `N@M18` carries what the removed per-cell N matrices used to show: how much of the sample still
    has eighteen months of forward data. It falls short of the signal count because the most recent
    vintages run into the end of the data, not because those trades failed.

    `Crossover` is the first month whose return drops below `Rebuy` — the M1 rate, which is what
    fresh capital earns. It is the exit-timing read: hold while a month beats redeployment, stop
    when it does not.

    Args:
        records: One entry per (signal, month) with a return, carrying the signal's `ranking`
        signal_rows: One entry per entered signal, `{year, ranking}`

    Returns:
        The markdown table, header included, terminated by a newline.
    """
    schema = {"year": pl.Int64, "month": pl.Int64, "ret": pl.Float64, "ranking": pl.Int64}
    trades = pl.DataFrame(records, schema=schema) if records else pl.DataFrame(schema=schema)
    total = len(signal_rows)

    header = "| Gate | Signals | % of universe | N@M18 | M1–12 | M13–18 | Rebuy (M1) | Crossover | Thinnest years |"
    lines = [header, "|---|---|---|---|---|---|---|---|---|"]

    for label, floor in [("ungated", 0)] + [(f"`R>={g}`", g) for g in GATES]:
        sub = trades.filter(pl.col("ranking") >= floor)
        sigs = [r for r in signal_rows if r["ranking"] >= floor]
        by_month = {m: sub.filter(pl.col("month") == m)["ret"].to_list() for m in range(1, MAX_MONTH + 1)}
        means = [float(np.mean(v)) * 100 if v else None for v in by_month.values()]
        early = [m for m in means[:12] if m is not None]
        late = [m for m in means[12:] if m is not None]
        rebuy = means[0]
        cross = next((i + 1 for i, m in enumerate(means) if i > 0 and m is not None and rebuy is not None and m < rebuy), None)

        per_year: dict[int, int] = {}
        for r in sigs:
            per_year[r["year"]] = per_year.get(r["year"], 0) + 1
        thin = ", ".join(f"{y}: {c}" for y, c in sorted(per_year.items(), key=lambda kv: kv[1])[:2])

        note = " (live)" if floor == MIN_RANKING else ""
        lines.append(
            f"| {label}{note} | {len(sigs)} | {100.0 * len(sigs) / total:.0f}% | {len(by_month[MAX_MONTH])} | "
            f"{sum(early) / len(early):+.2f}% | {sum(late) / len(late):+.2f}% | {rebuy:+.1f}% | "
            f"{'M' + str(cross) if cross else '—'} | {thin} |"
        )
    return "\n".join(lines) + "\n"


def build_reading(n_short: int, n_truncated: int, signal_rows: list[dict]) -> list[str]:
    """Render the `## Reading` narrative, so a re-run regenerates the whole file.

    The script opens the result with "w". Emitting the prose from here rather than hand-writing
    it into the doc is what keeps that safe — see FINDINGS_DOCS in scripts/qullamaggie.sh for
    what happens to a hand-written section otherwise.
    """
    total = len(signal_rows)
    per_year: dict[int, int] = {}
    for r in signal_rows:
        per_year[r["year"]] = per_year.get(r["year"], 0) + 1
    top_year, top_n = max(per_year.items(), key=lambda kv: kv[1])
    passes = ", ".join(
        f"R>={g} keeps {sum(1 for r in signal_rows if r['ranking'] >= g)} "
        f"({100.0 * sum(1 for r in signal_rows if r['ranking'] >= g) / total:.0f}%)"
        for g in GATES
    )
    return [
        "## Reading",
        "",
        "- Cells are **marginal**: month M is the move from month M-1 to month M, not the run from entry. "
        "Chaining a row does not give a buy-and-hold return — each cell is an equal-weighted average over "
        "whichever signals had both marks, and that set shrinks as M grows — see `N@M18` in the gate "
        "comparison for how much of each sample survives to the far columns.",
        "- **The row is the signal's birth year, the column is its age.** Calendar time drifts rightward "
        "along a row: a 2015-vintage M18 cell describes what those positions did in 2016-2017, not what "
        "the 2015 market did. Only the left-hand columns sit mostly inside the row's own year.",
        f"- **Every block comes from one signal generation**, so the treatments differ only by the "
        f"threshold applied to the score each signal already carries — same cooldown chain, same entries, "
        f"same marks. Of {total} signals, {passes}. The gated sets are nested subsets of the ungated one, "
        "so a column where two blocks agree is one the gate is not acting on.",
        f"- **A Mean% cell drawn from fewer than {MIN_CELL_N} signals prints `·`**, the floor the cohort "
        "studies already use. At the tighter gates a thin year falls to one or two names, where an average "
        "is that name's story and reads as a finding. The row's `Sig` column still gives the year's true "
        "count, so a `·` beside a non-zero `Sig` means the cell was withheld rather than empty. **Read the "
        "gate comparison before the grids** — a rising Mean% next to a collapsing sample is selectivity "
        "eating its own evidence, not an improving edge.",
        "- Month 12 lands within a day or two of the 366-day exit the live algorithm uses, so months 13-18 "
        "are the part of the curve the current exit gives up.",
        "- **The last rows are truncated by the data, not by the strategy.** Month 18 is only reachable for "
        "entries roughly 18 months before the final bar; later vintages fall out of the right-hand columns "
        f"first. {n_truncated} signals stop short for that reason. A rising tail in a short row is a smaller, "
        "earlier cohort, not a better one.",
        f"- **The `All` row is pooled, not an average of the year rows.** {top_year} alone contributes "
        f"{top_n} of {total} signals ({100.0 * top_n / total:.0f}%), so it dominates every `All` cell. "
        "Compare year rows with each other, not with `All`.",
        "- **The universe is survivor-only, and this is the caveat that matters most.** Every symbol in "
        "`turtle.daily_bars` still trades today: companies delisted, acquired or wound up during the study "
        "window are absent from the price data entirely and never generate a signal. On top of that, the "
        "`market_cap >= 1.5B` universe filter reads the *current* `turtle.company` snapshot, so a 2015 "
        "signal is admitted only if that company is large today. Both push the same way — every number here "
        "is conditioned on survival and on subsequent growth, and the early years are the most affected. "
        "This is a property of the data layer that every committed study shares, not of this decomposition, "
        "but it means the levels are optimistic even where the shape across months is informative.",
        f"- Only {n_short} signals ({100.0 * n_short / total:.1f}%) end early for a reason other than the "
        "data cutoff — trailing halted or zero-volume stretches, which `qm.load_bars` drops. That number is "
        "small because real delistings cannot appear, not because attrition was low.",
        "- 2025 is reported descriptively. This study fits nothing and selects nothing, so it does not spend "
        "the ranking lab's frozen holdout slice (docs/research/prompts.md, \"Never touch entries on or after "
        '2025-01-01").',
    ]


# ── Main ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Parse the evaluation window and output path.

    Returns:
        Namespace with start_date, end_date and output.
    """
    parser = argparse.ArgumentParser(description="Marginal monthly performance of bk50d_s12_v2.0 signals, by signal year")
    parser.add_argument("--start-date", type=iso_date_type, default=EVAL_START, help="first signal date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=iso_date_type, default=EVAL_END, help="last signal date (YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, default=RESULT_PATH, help="markdown result path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    eval_start, eval_end, result_path = args.start_date, args.end_date, args.output
    if eval_end <= eval_start:
        raise ValueError(f"--end-date {eval_end} must be after --start-date {eval_start}")

    settings = Settings.from_toml()
    repo = DailyBarsQueryRepository(engine=settings.engine)

    records: list[dict] = []
    signal_rows: list[dict] = []
    n_short = n_truncated = 0
    data_end = date.today()

    for chunk_start, chunk_end in _chunks(eval_start, eval_end):
        load_end = min(chunk_end + timedelta(days=FORWARD_PAD_DAYS), data_end)
        print(f"Chunk {chunk_start} – {chunk_end} (bars to {load_end}) …", flush=True)

        bars = qm.load_bars(repo, chunk_start, load_end)
        if bars.is_empty():
            raise ValueError(
                f"No bars for {chunk_start}..{load_end}, so this chunk's years would silently come back "
                "empty rather than failing. Is ACTIVE_PROFILE=hetzner-db set? The local Docker mirror "
                "only holds ~5 years."
            )
        valid_syms = bars.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
        bars = bars.filter(pl.col("symbol").is_in(valid_syms.to_list()))
        bull = qm.load_spy_regime(repo, chunk_start, load_end)

        # Project down to the columns resolve_entries and run_trades read before building the
        # indicator frame, so the full-width bar frame is released rather than held alongside it.
        slim = bars.select("symbol", "date", "adj_open", "adj_close")
        ind = qm.add_indicators(bars)
        del bars

        sig = qm.get_signals(ind, bull, chunk_start, sma_thresh=SMA_THRESH)
        sig = sig.filter(pl.col("date") <= chunk_end)
        del ind
        # Score every signal and carry the score as a column rather than filtering on it, so every
        # gate's table comes from one generation and the blocks differ only by the threshold.
        rankings = [compute_ranking(r) for r in sig.iter_rows(named=True)]
        sig = sig.with_columns(pl.Series("ranking", rankings, dtype=pl.Int64))
        sig = qm.resolve_entries(sig, slim)
        n_live = int((sig["ranking"] >= MIN_RANKING).sum())
        print(f"  {len(sig)} signals with an entry bar, {n_live} at R>={MIN_RANKING}", flush=True)

        signal_rows += [
            {"year": yr, "ranking": rk} for yr, rk in zip(sig["date"].dt.year().to_list(), sig["ranking"].to_list(), strict=True)
        ]
        chunk_records, chunk_short, chunk_truncated = run_trades(sig, slim)
        records += chunk_records
        n_short += chunk_short
        n_truncated += chunk_truncated
        del slim, sig

    n_entered = len(signal_rows)
    gate_summary = ", ".join(f"{sum(1 for r in signal_rows if r['ranking'] >= g)} at R>={g}" for g in GATES)
    print(f"\n{n_entered} signals with an entry bar, {gate_summary}", flush=True)
    if n_entered == 0:
        raise ValueError(f"No {STRATEGY_LABEL} signals with an entry bar in {eval_start}..{eval_end}")

    config_rows: list[tuple[str, str]] = [
        ("Period", f"{eval_start} – {eval_end} (signal dates)"),
        ("Algorithm", f"`{STRATEGY_LABEL}` — 50d breakout, close >= {SMA_THRESH * 100:.0f}% above 50d SMA"),
        ("Horizon", f"**marginal months 1–{MAX_MONTH} after entry** (not the 366d fixed hold)"),
        ("Entry", "next trading day's split/dividend-adjusted open"),
        ("Monthly mark", "adjusted close of the first bar on or after entry + M calendar months"),
        ("Cohort", "**per cell — every signal with a mark at both ends of the month; see `N@M18` above**"),
        ("Ranking gate", f"**all reported** — QullamaggieRanking >= {', >= '.join(str(g) for g in GATES)}, and ungated"),
        (
            "Fixed filters",
            f"RSI<{qm.RSI_CAP:.0f}, ADR>={qm.ADR_MIN * 100:.1f}%, ADR_change<{qm.ADR_CHANGE_CAP * 100:.0f}%, "
            f"roc_12m<{qm.ROC_CAP * 100:.0f}%, vol_surge<{qm.VOL_SURGE_MAX}x",
        ),
        ("Market regime", "SPY close > 200d SMA"),
        ("Price range", f"> ${qm.MIN_PRICE:.0f} and < ${qm.MAX_PRICE:.0f}"),
        ("Min avg vol (20d)", f">= {qm.MIN_AVG_VOL // 1000}K"),
        ("Cooldown", f"{qm.COOLDOWN_DAYS} calendar days"),
        ("Universe", "US common stocks, market_cap >= 1.5B, excl. Comm/RE"),
        ("Signals", f"{n_entered} with an entry bar; {gate_summary}"),
    ]

    output = "\n".join(build_tables(records, signal_rows))
    summary = build_summary(records, signal_rows)
    print("\n" + output)
    reading = "\n".join(build_reading(n_short, n_truncated, signal_rows))

    result_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("w") as fh:
        fh.write(f"# Qullamaggie Marginal Monthly Performance by Signal Year ({eval_start.year}-{eval_end.year})\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("## Configuration\n\n")
        fh.write(config_table(config_rows))
        fh.write("\n## Gate comparison\n\n")
        fh.write(summary)
        fh.write("\n## Results\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n\n")
        fh.write(reading)
        fh.write("\n")
    print(f"\nResults saved to {result_path}", flush=True)


if __name__ == "__main__":
    main()
