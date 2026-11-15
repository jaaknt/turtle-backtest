#!/usr/bin/env python3
"""
Portfolio simulation for bk50d_s20 / s16 / s12 (v2.0, 366d).

Indicators, entries and mark-to-market use split/dividend-adjusted prices; the raw close is used
only for the $5-$250 price band (see turtlex.research.qullamaggie).

Rules:
  - Period 2021-01-01 .. 2026-06-26, initial equity $30,000.
  - Each config's size sweep is one table carrying three ranking treatments: every sizing appears
    three times on adjacent rows — signals scoring below STRICT_RANKING on QullamaggieRanking
    dropped, below MIN_RANKING dropped (matching the portfolio-runner --min-signal-ranking
    default), and no ranking condition at all. Everything else is identical between them, so the
    rows isolate what each gate is worth once position sizing and cash competition are in play.
  - Signals, the 30-day cooldown and the ranking come from turtlex.research.qullamaggie. The
    cooldown runs through the warmup, as in production, so a trigger just before the window
    suppresses an early in-window signal. Until 2026-11-15 this script started the cooldown at
    the window start instead, which admitted ~40 extra early-January-2021 signals at s12.
  - Signals competing for cash on the same day are funded best-ranked first. Entries arrive
    in bursts and cash runs out mid-burst, so this ordering decides which trades exist at all.
  - Each signal: buy at the next trading day's split/dividend-adjusted open (matching
    SignalProcessor.calculate_entry_data), sizing = {3%,4%,5%} of current portfolio
    value (cash + open positions marked to market).
  - If available cash < the target, skip the trade (no liquidity).
  - Exit at the close of the first trading day >= entry + qm.HOLD_CAL calendar days
    (open positions at period end are marked to market, not force-closed). Other exits are
    measured by scripts/qullamaggie-exit-sweep.py.
  - Fractional shares, no commission/slippage.

The simulator itself is turtlex.research.portfolio_sim; this script runs the sweep and writes the
report.

SPY/QQQ buy & hold benchmarks ($INIT_EQUITY lump-sum, first close to last close of the period)
are reported alongside the main sweep. Each taken trade of every config is also scored
with QullamaggieRanking (turtlex/strategy/ranking/qullamaggie.py); trades are split into 10
equal-count ranking deciles and each decile's signal subset is re-simulated in isolation (same
position sizing) to report that decile's own standalone CAGR/MaxDD/Calmar/Sortino. Deciles are
built once per gated signal set — MIN_RANKING and STRICT_RANKING — so each spans only its own
gate..100 and cannot speak to scores below it; the ungated size-sweep rows are what show whether
a gate earns its keep.

Outputs: monthly portfolio return + transaction-count grid (year x month), Max DD, Calmar,
Sortino, signals taken/skipped, average uninvested capital.
"""

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import product
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.common.cli import iso_date_type
from turtlex.common.report import config_table, run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.research.portfolio_sim import SimMarket, SimParams, equity_curve_metrics, gate_signals, resolve_signals, run_sim, year_metrics

EVAL_START = date(2021, 1, 1)
EVAL_END = date(2026, 6, 26)
INIT_EQUITY = 30_000.0
POS_FRACTIONS = [0.03, 0.04, 0.05]  # position-size sweep
DECILE_POS_FRACTION = 0.04  # representative size used for the ranking-decile mini-simulations
N_DECILES = 10
RANK_FUNDING = True  # when cash is scarce, fund competing signals by QullamaggieRanking (desc)

STRICT_RANKING = 55  # tighter comparison gate, reported alongside qm.MIN_RANKING and ungated
# Every ranking treatment, strictest first: the size sweep reports them in this order and the
# decile section walks the gated ones in the same order. A floor of 0 keeps every signal.
GATES: list[tuple[str, int]] = [(f"R>={STRICT_RANKING}", STRICT_RANKING), (f"R>={qm.MIN_RANKING}", qm.MIN_RANKING), ("ungated", 0)]
GATED_LABELS = [label for label, floor in GATES if floor > 0]  # the gates the decile section decomposes
# run_sim result fields only the yearly/monthly focus rows read; dropped from every other result
HEAVY_RESULT_KEYS = ("eom", "entries", "skips", "dates", "eq", "cash", "trades")
FOCUS_NAME = f"s12 R>={qm.MIN_RANKING}"  # the reference algorithm, always in the yearly/monthly sections

CONFIGS = [
    ("s20", 0.20),
    ("s16", 0.16),
    ("s12", 0.12),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-portfolio-v4.md"

# (algorithm label, position fraction, run_sim result)
Result = tuple[str, float, dict]


@dataclass(frozen=True)
class Window:
    """The evaluation window, from the CLI."""

    start: date
    end: date


def config_rows(window: Window) -> list[tuple[str, str]]:
    """Build the run's configuration table rows.

    Args:
        window: The evaluation window

    Returns:
        `(parameter, value)` pairs for `turtlex.common.report.config_table`.
    """
    # Every filter below is identical across s20/s16/s12 — the only difference is the
    # `%abv_SMA50` threshold each config is named for, so it stays on the section headings
    # rather than being repeated here. Same `| Parameter | Value |` shape as the cohort studies.
    return [
        ("Period", f"{window.start} – {window.end}"),
        ("Hold", f"{qm.HOLD_CAL}d (calendar)"),
        ("Algorithms", ", ".join(f"bk50d_{n}_v2.0 (%abv_SMA50>{t * 100:.0f}%)" for n, t in CONFIGS)),
        ("Entry", "next trading day's split/dividend-adjusted open"),
        ("Initial equity", f"${INIT_EQUITY:,.0f}"),
        ("Position sizing", ", ".join(f"{f:.0%}" for f in POS_FRACTIONS) + " of portfolio per trade"),
        (
            "Ranking gate",
            f"QullamaggieRanking >= {STRICT_RANKING} and >= {qm.MIN_RANKING}, reported against an ungated run of the same signals",
        ),
        (
            "Fixed filters",
            f"breakout>50d high, RSI(14)<{qm.RSI_CAP:.0f}, ADR%(20)>={qm.ADR_MIN * 100:.1f}%, "
            f"ADR_change<{qm.ADR_CHANGE_CAP * 100:.0f}%, vol_surge<{qm.VOL_SURGE_MAX:.1f}x, "
            f"roc_12m<{qm.ROC_CAP * 100:.0f}% (no tight_range)",
        ),
        ("Market regime", "SPY close > 200d SMA"),
        ("Price range", f"> ${qm.MIN_PRICE:.0f} and < ${qm.MAX_PRICE:.0f}"),
        ("Min avg vol (20d)", f">= {qm.MIN_AVG_VOL // 1000}K"),
        ("Cooldown", f"{qm.COOLDOWN_DAYS} calendar days"),
        ("Universe", "US common stocks, market_cap >= 1.5B, excl. Comm/RE"),
        ("Cash competition", "same-day signals funded best-ranked first" if RANK_FUNDING else "same-day signals funded in arrival order"),
    ]


def buy_and_hold(bars_history: DailyBarsQueryRepository, symbol: str, window: Window) -> dict:
    """Buy-and-hold benchmark: $INIT_EQUITY at the first close on/after the window start, held to
    the last close on/before its end (raw close, no dividend reinvestment, matching how
    qm.load_spy_regime computes SPY's regime filter).

    Args:
        bars_history: Repository for bar reads
        symbol: Benchmark symbol, in database convention
        window: The evaluation window

    Returns:
        dict with final, cagr, max_dd, calmar and sortino.
    """
    bars = bars_history.get_bars_pl(symbol, window.start, window.end)
    if bars.is_empty():
        raise ValueError(f"no {symbol} bars in {window.start} – {window.end}; the buy-and-hold benchmark cannot be computed")
    closes = bars["close"].cast(pl.Float64).to_numpy()
    return equity_curve_metrics(INIT_EQUITY * (closes / closes[0]))


def parse_args() -> argparse.Namespace:
    """Parse the evaluation window and output path.

    prompts.md asks for this study at three windows (2021-2026 plus 2010-2015 and 2016-2020),
    so the period is a flag rather than an edit. Defaults reproduce the committed baseline run.
    """
    parser = argparse.ArgumentParser(description="Qullamaggie portfolio simulation (size sweep + ranking deciles)")
    parser.add_argument("--start-date", type=iso_date_type, default=EVAL_START, help="evaluation window start (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=iso_date_type, default=EVAL_END, help="evaluation window end (YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, default=RESULT_PATH, help="markdown result path")
    return parser.parse_args()


class Report:
    """The markdown report, echoed to stdout line by line as it is written."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def out(self, s: str = "") -> None:
        """Append one line, and print it.

        Args:
            s: The line
        """
        print(s)
        self.lines.append(s)

    def table(self, hdr: str, rows: list[str]) -> None:
        """Emit a fixed-width table as a fenced ```text block, blank-line-padded on both
        sides so it can't be misread as a setext heading by markdownlint/GitHub."""
        self.out("")
        self.out("```text")
        self.out(hdr)
        self.out("-" * len(hdr))
        for row in rows:
            self.out(row)
        self.out("```")

    def write(self, path: Path) -> None:
        """Save the report to `path`.

        Args:
            path: Markdown output path
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.lines) + "\n")
        print(f"\nSaved to {path}", flush=True)


@dataclass
class Study:
    """What every section of one run shares: the report, the window's market and the sweep's results."""

    rep: Report
    market: SimMarket
    results: list[Result] = field(default_factory=list)


def simulate(market: SimMarket, signals_by_day: dict[int, list[dict]], pos_fraction: float) -> dict:
    """`run_sim` at this study's starting equity and funding order.

    Args:
        market: The window's prices and calendar
        signals_by_day: Signals keyed by the date-int they are funded on
        pos_fraction: Fraction of the portfolio's value per position

    Returns:
        The `run_sim` result.
    """
    return run_sim(market, signals_by_day, SimParams(pos_fraction, INIT_EQUITY, rank_funding=RANK_FUNDING))


def write_preamble(rep: Report, bars_history: DailyBarsQueryRepository, window: Window) -> None:
    """The title, the configuration table and the buy-and-hold benchmarks.

    Args:
        rep: The report
        bars_history: Repository for the benchmarks' bars
        window: The evaluation window
    """
    rep.out("# Portfolio Simulation — size sweep + ranking deciles")
    rep.out("")
    rep.out(f"Run date: {run_timestamp()}")
    rep.out("")
    rep.out("## Configuration")
    rep.out("")
    for line in config_table(config_rows(window)).rstrip("\n").split("\n"):
        rep.out(line)

    rep.out("")
    rep.out("## Buy & Hold Benchmarks")
    rep.out("")
    rep.out(f"${INIT_EQUITY:,.0f} bought on the first trading day of the period, sold on the last.")
    bh_hdr = f"{'symbol':<6} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8}"
    bh_rows: list[str] = []
    for sym in ["SPY.US", "QQQ.US"]:
        bh = buy_and_hold(bars_history, sym, window)
        bh_rows.append(
            f"{sym[:-3]:<6} {bh['final']:>11,.0f} {bh['cagr'] * 100:>+7.2f} {bh['max_dd'] * 100:>8.2f} "
            f"{bh['calmar']:>7.3f} {bh['sortino']:>8.3f}"
        )
    rep.table(bh_hdr, bh_rows)


def prune_results(all_results: list[Result]) -> None:
    """Drop the daily series from results that cannot reach the yearly/monthly focus set.

    That set is the reference algorithm at every sizing plus the two best others by Final$,
    so any other result past the current top two never needs its series. Pruning as the
    sweep goes keeps peak memory near the focus set rather than all 27 results.

    Args:
        all_results: Every result so far, pruned in place
    """
    others = sorted((x for x in all_results if x[0] != FOCUS_NAME), key=lambda x: x[2]["final"], reverse=True)
    for _name, _pf, res in others[2:]:
        for key in HEAVY_RESULT_KEYS:
            res.pop(key, None)


def write_config_sweep(study: Study, sig: pl.DataFrame, config: tuple[str, float]) -> dict[str, dict[int, list[dict]]]:
    """One config's size sweep: every sizing under every ranking treatment, on adjacent rows.

    Args:
        study: The run; this config's results are appended to `study.results` (and it is pruned)
        sig: The config's signals, from `qm.get_signals`
        config: Config name (s20/s16/s12) and its `%abv_SMA50` threshold

    Returns:
        The gated signal sets keyed by gate label, for the decile section; the ungated set is
        left out.
    """
    name, sma_t = config
    rep, market = study.rep, study.market
    rep.out("")
    rep.out(f"## {name}  (bk50d_{name}_v2.0 / {qm.HOLD_CAL}d)")
    rep.out("")
    rep.out(f"`%abv_SMA50 > {sma_t * 100:.0f}%` — every other filter is in the Configuration table above.")
    # Same signals, sized the same way, reported under every ranking treatment on adjacent
    # rows of one table. Reading across is the only way to see what a gate is worth in
    # *portfolio* terms — a gated run alone cannot show whether the signals it removed
    # would have compounded better.
    resolved = resolve_signals(market, sig)
    gate_runs = [(gate_label, *gate_signals(resolved, gate)) for gate_label, gate in GATES]

    rep.out("")
    # Built from each run's own label, so reordering or adding a gate can never pair a label
    # with another gate's counts.
    drops = "; ".join(
        f"`{label}` drops {n_below} signals ({n_no_fill} with no fillable next-day open)" for label, _sigs, n_below, n_no_fill in gate_runs
    )
    rep.out(
        f"**Ranking gate:** {drops}. Each sizing is listed strictest gate first, so the rows read "
        "across — a gated run alone cannot show whether the signals it removed would have "
        "compounded better."
    )
    hdr = (
        f"{'size':<6} {'gate':<8} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} "
        f"{'Sortino':>8} {'taken':>6} {'skip':>6} {'Uninv%':>7}"
    )
    rows: list[str] = []
    for pf, (gate_label, signals_by_day, _n_below, _n_no_fill) in product(POS_FRACTIONS, gate_runs):
        r = simulate(market, signals_by_day, pf)
        study.results.append((f"{name} {gate_label}", pf, r))
        prune_results(study.results)
        rows.append(
            f"{pf:<6.0%} {gate_label:<8} {r['final']:>11,.0f} {r['cagr'] * 100:>+7.2f} "
            f"{r['max_dd'] * 100:>8.2f} {r['calmar']:>7.3f} {r['sortino']:>8.3f} "
            f"{r['taken']:>6} {r['skipped']:>6} {r['avg_uninv_pct']:>6.1f}%"
        )
    rep.table(hdr, rows)
    return {gate_label: signals_by_day for gate_label, signals_by_day, _n_below, _n_no_fill in gate_runs if gate_label in GATED_LABELS}


def write_leaderboard(rep: Report, title: str, ranked: list[Result]) -> None:
    """Top 5 of `ranked`, already sorted by whichever metric the title names.

    Args:
        rep: The report
        title: Section heading
        ranked: Every result, best first
    """
    lb_hdr = (
        f"{'#':>2}  {'algo':<18} {'size':>5} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} "
        f"{'Calmar':>7} {'Sortino':>8} {'taken':>6} {'skip':>6} {'Uninv%':>7}"
    )
    lb_rows = [
        f"{i:>2}  {name:<18} {pf:>5.0%} {r['final']:>11,.0f} {r['cagr'] * 100:>+7.2f} "
        f"{r['max_dd'] * 100:>8.2f} {r['calmar']:>7.3f} {r['sortino']:>8.3f} "
        f"{r['taken']:>6} {r['skipped']:>6} {r['avg_uninv_pct']:>6.1f}%"
        for i, (name, pf, r) in enumerate(ranked[:5], 1)
    ]
    rep.out("")
    rep.out(f"## {title}")
    rep.table(lb_hdr, lb_rows)


def year_rows(name: str, pf: float, r: dict) -> list[str]:
    """One result's yearly table rows; the algorithm label is printed on the first only.

    Args:
        name: Algorithm label
        pf: Position fraction
        r: The `run_sim` result

    Returns:
        One row per calendar year.
    """
    label = f"{name} {pf:.0%}"
    return [
        f"{label if i == 0 else '':<18} {y['year']:>5} {y['final']:>11,.0f} {y['ret'] * 100:>+7.2f} "
        f"{y['max_dd'] * 100:>8.2f} {y['calmar']:>7.3f} {y['sortino']:>8.3f} "
        f"{y['taken']:>6} {y['skipped']:>6} {y['uninv']:>6.1f}%"
        for i, y in enumerate(year_metrics(r))
    ]


def write_yearly(rep: Report, focus: list[Result]) -> None:
    """The per-year table for the focus set.

    Args:
        rep: The report
        focus: The results the yearly and monthly sections cover
    """
    rep.out("")
    rep.out("## Yearly results")
    rep.out("")
    rep.out(
        "Portfolio value at each year end against the previous year end — `Final$` is the equity on "
        "the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, "
        "`Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` "
        "count only that year's signals; none is a slice of the whole-period figure."
    )
    yr_hdr = (
        f"{'algo':<18} {'year':>5} {'Final$':>11} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} "
        f"{'Sortino':>8} {'taken':>6} {'skip':>6} {'Uninv%':>7}"
    )
    rep.table(yr_hdr, [row for name, pf, r in focus for row in year_rows(name, pf, r)])


def month_row(yr: int, rets: dict[tuple[int, int], float], entry_counts: Counter[tuple[int, int]]) -> str:
    """One year of the monthly grid: each month's return and entry count, then the year's.

    Args:
        yr: The year
        rets: Monthly returns keyed by (year, month); a month without equity is missing
        entry_counts: Entries keyed by (year, month)

    Returns:
        The grid row.
    """
    parts: list[str] = []
    comp = 1.0
    year_txns = 0
    for mo in range(1, 13):
        key = (yr, mo)
        year_txns += entry_counts[key]
        cell = "·"
        if key in rets:
            cell = f"{rets[key] * 100:+.1f}|{entry_counts[key]}"
            comp *= 1 + rets[key]
        parts.append(f"{cell:>9}")
    return f"{yr:>5} | " + " ".join(parts) + f" | {(comp - 1) * 100:>+7.1f} {year_txns:>5}"


def monthly_grid(rep: Report, eom: pl.DataFrame, entries: list[date]) -> None:
    """The year x month grid of returns and entry counts for one result.

    Args:
        rep: The report
        eom: Month-end returns (the result's `eom`)
        entries: The date of every funded signal
    """
    entry_counts = Counter((ed.year, ed.month) for ed in entries)
    rets = {(y, m): ret for y, m, ret in eom.select("year", "month", "ret").iter_rows()}
    header = f"{'Year':>5} | " + " ".join(f"{m:>9}" for m in MONTHS) + f" | {'Year%':>7} {'Txns':>5}"
    rep.table(header, [month_row(yr, rets, entry_counts) for yr in sorted(eom["year"].unique().to_list())])


def write_monthly(rep: Report, focus: list[Result]) -> None:
    """The monthly grids for the focus set.

    Args:
        rep: The report
        focus: The results the yearly and monthly sections cover
    """
    rep.out("")
    rep.out(f"## Monthly returns/transactions — s12 R>={qm.MIN_RANKING} at each sizing, plus the top 2 by Final$")
    for name, pf, r in focus:
        rep.out("")
        rep.out(f"### {name} — size {pf:.0%}  (Final ${r['final']:,.0f})")
        monthly_grid(rep, r["eom"], r["entries"])


def ranking_decile_table(study: Study, signals_by_day: dict[int, list[dict]], pos_fraction: float) -> None:
    """Score every taken trade with QullamaggieRanking, split into N_DECILES equal-count
    buckets (D1=lowest ranking .. D10=highest), and re-simulate each decile's own signal
    subset in isolation (same sizing) to report that decile's standalone portfolio metrics.

    Args:
        study: The run
        signals_by_day: One gated signal set
        pos_fraction: Position size for every re-simulation
    """
    rep, market = study.rep, study.market
    base = simulate(market, signals_by_day, pos_fraction)
    trades = sorted(base["trades"], key=lambda t: t["ranking"])
    n = len(trades)
    edges = np.linspace(0, n, N_DECILES + 1).astype(int)
    subsets = [(d, subset) for d in range(N_DECILES) if (subset := trades[edges[d] : edges[d + 1]])]

    hdr = f"{'Decile':<8} {'Ranking':>9} {'N':>5} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8}"
    rows: list[str] = []
    for d, subset in subsets:
        keys = {(t["symbol"], t["sig_date"]) for t in subset}
        sub_by_day = {
            dint: kept for dint, sigs in signals_by_day.items() if (kept := [s for s in sigs if (s["symbol"], s["date"]) in keys])
        }
        res = simulate(market, sub_by_day, pos_fraction)
        rankings = [t["ranking"] for t in subset]
        rows.append(
            f"D{d + 1:<7} {min(rankings):>3}-{max(rankings):<5} {len(subset):>5} {res['cagr'] * 100:>+7.2f} "
            f"{res['max_dd'] * 100:>8.2f} {res['calmar']:>7.3f} {res['sortino']:>8.3f}"
        )
    rep.out(f"Trades scored: {n}  |  size: {pos_fraction:.0%}")
    rep.table(hdr, rows)


def write_deciles(study: Study, gated: dict[tuple[str, str], dict[int, list[dict]]]) -> None:
    """The ranking-decile section: every config under every gate, strictest gate first.

    Args:
        study: The run
        gated: Gated signal sets keyed by (config name, gate label)
    """
    rep = study.rep
    rep.out("")
    rep.out("## Ranking Deciles (QullamaggieRanking)")
    rep.out("")
    rep.out(
        f"Every taken trade of every config (at {DECILE_POS_FRACTION:.0%} sizing, the middle of the "
        f"{'/'.join(f'{f:.0%}' for f in POS_FRACTIONS)} sweep) is scored 0-100 with "
        "turtlex/strategy/ranking/qullamaggie.py at entry, split into "
        f"{N_DECILES} equal-count deciles (D1=lowest score .. D{N_DECILES}=highest), and each "
        "decile's own signal subset is re-simulated in isolation (same sizing, same universe) "
        "to report that decile's standalone portfolio metrics — this tests whether higher-ranked "
        "signals produce a better standalone portfolio, not just a higher per-trade return. Each "
        "config is decomposed once per gated signal set, strictest gate first as in the size sweep: "
        "the deciles split the trades that gate's own run took, so each table "
        "spans only that gate..100 and reads against the matching size-sweep row."
    )
    for (name, _), gate_label in product(CONFIGS, GATED_LABELS):
        print(f"Scoring ranking deciles for {name} {gate_label} …", flush=True)
        rep.out("")
        rep.out(f"### {name} {gate_label}  (bk50d_{name}_v2.0)")
        rep.out("")
        ranking_decile_table(study, gated[(name, gate_label)], DECILE_POS_FRACTION)


def load_window(bars_history: DailyBarsQueryRepository, window: Window) -> tuple[SimMarket, pl.DataFrame, set[date]]:
    """Load the window's calendar, SPY regime, bars and entry indicators.

    Args:
        bars_history: Repository for bar reads
        window: The evaluation window

    Returns:
        (the simulation market, the indicator frame signals are drawn from, SPY's bull dates).
    """
    data_start = window.start - timedelta(days=qm.WARMUP_DAYS)
    print(f"Eval {window.start} – {window.end}  |  bars {data_start} – {window.end}", flush=True)
    print("Loading SPY …", flush=True)
    # SPY's own bars are the master trading calendar run_sim walks; the regime comes from qm.
    cal = qm.load_trading_days(bars_history, window.start, window.end)
    bull_dates = qm.load_spy_regime(bars_history, window.start, window.end)
    # Bars end at the window end: this simulation never requires an exit bar to exist, it marks
    # positions still open on the last day to market. Bounding the load also puts the
    # qm.MIN_BARS count on the window actually being simulated, so a symbol that listed late
    # in it no longer qualifies on bars it had not printed yet.
    print("Loading bars …", flush=True)
    df = qm.load_bars(bars_history, window.start, window.end)
    print("Computing indicators …", flush=True)
    ind = qm.add_indicators(df)
    return SimMarket.from_bars(ind, cal), ind, bull_dates


def main() -> None:
    args = parse_args()
    if args.start_date >= args.end_date:
        raise ValueError(f"--start-date {args.start_date} must be before --end-date {args.end_date}")
    window = Window(args.start_date, args.end_date)
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)
    market, ind, bull_dates = load_window(bars_history, window)

    study = Study(Report(), market)
    write_preamble(study.rep, bars_history, window)

    # Gated signal sets keyed by (config, gate label), for the decile section
    gated: dict[tuple[str, str], dict[int, list[dict]]] = {}
    for name, sma_t in CONFIGS:
        print(f"Simulating {name} …", flush=True)
        # Bars end at the window end, so no window-end bound is needed; only the columns ranking reads are kept.
        sig = qm.get_signals(ind, bull_dates, window.start, sma_t).select("symbol", "date", "raw_close", "adr_pct", "pct_vs_sma50")
        config_gated = write_config_sweep(study, sig, (name, sma_t))
        gated.update({(name, gate_label): sigs for gate_label, sigs in config_gated.items()})
    del ind  # SimMarket holds its own arrays; free the ~7M-row frame before the decile re-simulations

    ranked_final = sorted(study.results, key=lambda x: x[2]["final"], reverse=True)
    write_leaderboard(study.rep, "Top 5 by Final$", ranked_final)
    write_leaderboard(study.rep, "Top 5 by Sortino", sorted(study.results, key=lambda x: x[2]["sortino"], reverse=True))

    # The per-year and monthly sections cover a fixed set: the reference algorithm at every
    # sizing, plus the two best by Final$ (skipped if already present, so the set can be short).
    focus: list[Result] = [r for r in study.results if r[0] == FOCUS_NAME]
    focus += [r for r in ranked_final if r not in focus][:2]
    write_yearly(study.rep, focus)
    write_monthly(study.rep, focus)
    write_deciles(study, gated)
    study.rep.write(args.output)


if __name__ == "__main__":
    main()
