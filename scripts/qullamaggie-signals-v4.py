#!/usr/bin/env python3
"""
Current-period signal report for bk50d_s12_v2.0.

The reported signal list is gated at QullamaggieRanking >= qm.MIN_RANKING, matching the
portfolio-runner --min-signal-ranking default. Both cohort tables are deliberately computed
over the *ungated* s12 signals: their job is to show whether ranking and %abv SMA50 separate
outcomes, which a table containing only scores >= 44 could not do (the [20-30) and [30-40)
buckets would always be empty; [0-10) and [10-20) are empty regardless, since a signal clearing
the entry filters scores at least 20).
Sector is turtle.company.sector; the signal universe excludes Communication Services and Real
Estate, so neither ever appears there — the current-investments table reads the same column but
over whatever is actually held, so both sectors can show up in it.

Two columns are informational only, not filtered on: TR% (tight_range) and VOL_DRY
(`mean(volume[-11:-1]) / mean(volume[-51:-1])`, both shift-1). VOL_DRY was the `vol_dry_up < 0.90`
filter until it was retired on 2026-08-01 — see docs/research/result-qullamaggie-cohorts-vol-dry-up.md
— so values at or above 0.90 now appear where they previously could not.
Display window: 2026-06-01 - today.
Candidate window starts earlier so the 30-day cooldown state is correct at the start of the
display window.

Bars, indicators, the SPY regime, the filter chain, the cooldown and the ranking come from
turtlex.research.qullamaggie (parity-tested against QullamaggieStrategy); TR% and VOL_DRY are
added on top, since only this report shows them.

Entry $/Curr Price/Change % use the raw (unadjusted) close, the real tradeable price, matching
the qm.MIN_PRICE/MAX_PRICE convention; indicators run on adjusted prices.

Ranking is the 0-100 QullamaggieRanking score (turtlex/strategy/ranking/qullamaggie.py) on the
entry date's indicators. Two cohort tables are reported: Change % by %abv SMA50 bucket, and
Change % by Ranking bucket -- both mark-to-latest-price, not annualized (see cohort_stats()).

Current investments come from turtle.lightyear_transaction (real Buy/Sell executions imported
by lightyear-import), netted per ticker and marked to the latest raw close. Their Signal date /
Ranking are the newest s12 signal in the SIGNAL_LOOKBACK_CAL calendar days strictly before the
buy, scored *ungated* — unlike the signal table above, a position bought off a sub-qm.MIN_RANKING
signal shows that score rather than a "--", which here means only that no signal precedes the buy
inside the window.

The whole report — signal table, exclusions, both cohort tables, current investments and the
benchmark comparison — is printed to stdout; no result doc is written.

References: docs/research/qullamaggie-backtest-v4.md, docs/research/result-qullamaggie-backtest-v4.md,
turtlex/strategy/ranking/qullamaggie.py
"""

import time
from bisect import bisect_left
from datetime import date, timedelta

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm

DISPLAY_START = date(2026, 6, 1)
DISPLAY_END = date.today()
CANDIDATE_START = date(2025, 1, 1)  # bars load from qm.WARMUP_DAYS before this

SUSPICIOUS_DAY_MOVE = 0.50  # exclude signals with a >50% single-day raw-close move between entry and latest date

BASE_LABEL = "bk50d_s12_v2.0"
BASE_SMA_T = 0.12
SIGNAL_LOOKBACK_CAL = 50  # holdings table: how far back before a buy its matching signal may sit

COHORTS = [
    (12.0, 15.0, "[12-15)"),
    (15.0, 17.5, "[15-17.5)"),
    (17.5, 20.0, "[17.5-20)"),
    (20.0, float("inf"), "[>=20)"),
]

RANKING_COHORTS = [
    (0.0, 10.0, "[0-10)"),
    (10.0, 20.0, "[10-20)"),
    (20.0, 30.0, "[20-30)"),
    (30.0, 40.0, "[30-40)"),
    (40.0, 50.0, "[40-50)"),
    (50.0, 60.0, "[50-60)"),
    (60.0, 70.0, "[60-70)"),
    (70.0, 80.0, "[70-80)"),
    (80.0, 90.0, "[80-90)"),
    (90.0, float("inf"), "[>=90)"),
]


def cohort_label(value: float, cohorts: list[tuple[float, float, str]]) -> str:
    for lo, hi, label in cohorts:
        if lo <= value < hi:
            return label
    return cohorts[-1][2]


def cohort_stats(returns: list[float], mdds: list[float]) -> dict | None:
    """Med%/Mean%/Win%/PF/Sortino/MaxDD% for one cohort's Change % values.

    Sortino here is **not annualized** -- passing holding_days=0 skips the
    sqrt(365/hold) factor, because these positions have no fixed holding period
    (each is still open, marked at whatever elapsed time has passed since entry).
    """
    m = compute_trade_metrics(returns, 0, trade_drawdowns_pct=[d * 100 for d in mdds])
    if m is None:
        return None
    return {
        "n": m.n,
        "med": m.median_pct,
        "mean": m.mean_pct,
        "win": m.win_pct,
        "pf": m.profit_factor,
        "sortino": m.sortino,
        "mdd": m.mean_trade_mdd_pct if m.mean_trade_mdd_pct is not None else float("nan"),
    }


def format_cohort_row(label: str, stats: dict | None) -> str:
    if stats is None:
        return f"{label:<10} {0:>4} {'--':>8} {'--':>8} {'--':>7} {'--':>6} {'--':>8} {'--':>7}"
    pf_str = f"{stats['pf']:>6.2f}" if np.isfinite(stats["pf"]) else f"{'inf':>6}"
    sortino_str = f"{stats['sortino']:>8.2f}" if not np.isnan(stats["sortino"]) else f"{'n/a':>8}"
    return (
        f"{label:<10} {stats['n']:>4} {stats['med']:>+7.1f}% {stats['mean']:>+7.1f}% "
        f"{stats['win']:>6.1f}% {pf_str} {sortino_str} {stats['mdd']:>6.1f}%"
    )


def build_cohort_table(
    cohorts: list[tuple[float, float, str]], returns_by_label: dict[str, list[float]], mdds_by_label: dict[str, list[float]]
) -> tuple[str, list[float]]:
    hdr = f"{'Cohort':<10} {'N':>4} {'Med%':>8} {'Mean%':>8} {'Win%':>7} {'PF':>6} {'Sortino':>8} {'MaxDD%':>7}"
    lines = [hdr, "-" * len(hdr)]
    means: list[float] = []
    for _, _, label in cohorts:
        stats = cohort_stats(returns_by_label[label], mdds_by_label[label])
        lines.append(format_cohort_row(label, stats))
        if stats:
            means.append(stats["mean"])
    return "\n".join(lines), means


def load_holdings(engine: sa.Engine) -> list[dict]:
    """Open Lightyear positions, marked to each symbol's latest raw close.

    Buys and sells are netted per ticker and only open positions (Shares > 0) are kept.
    Avg Price is the quantity-weighted mean over *buys* only, so a partial sell leaves the
    cost basis unmoved, and it is the per-share `price` — the statement's fee and tax sit in
    their own columns and are deliberately not folded in, so PL reads slightly better than
    the realised result.

    Curr Price is the raw close, not the adjusted one: the statement records the actual
    fill price, so only the unadjusted series is comparable with it.

    Args:
        engine: Sync engine used for the read

    Returns:
        list[dict]: One row per open position, ordered by ticker code. `curr_price` is None
            when the symbol has no usable bar in turtle.daily_bars.
    """
    sql = """
        WITH holding AS (
            SELECT ticker_code,
                   SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) AS shares,
                   MIN(transacted_at) FILTER (WHERE transaction_type = 'buy')               AS entry_date,
                   SUM(price * quantity) FILTER (WHERE transaction_type = 'buy')
                     / SUM(quantity) FILTER (WHERE transaction_type = 'buy')                AS avg_price
            FROM   turtle.lightyear_transaction
            GROUP  BY ticker_code
            HAVING SUM(CASE WHEN transaction_type = 'buy' THEN quantity ELSE -quantity END) > 0
        ),
        latest AS (
            SELECT DISTINCT ON (symbol) symbol, close::float8 AS curr_price, date::date AS last_date
            FROM   turtle.daily_bars
            WHERE  symbol IN (SELECT ticker_code FROM holding) AND close > 0 AND volume > 0
            ORDER  BY symbol, date DESC
        )
        SELECT h.ticker_code, h.entry_date::date, h.avg_price::float8, h.shares::float8, l.curr_price, l.last_date
        FROM   holding h
        LEFT   JOIN latest l ON l.symbol = h.ticker_code
        ORDER  BY h.ticker_code
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    return [
        {
            "symbol": r[0],
            "entry_date": r[1],
            "avg_price": float(r[2]),
            "shares": float(r[3]),
            "curr_price": r[4],
            # Calendar days held. The prompt writes this as `Entry date - Last date`, which is
            # negative; a holding period reads as a positive count, so the operands are swapped.
            "days": (r[5] - r[1]).days if r[5] is not None else None,
        }
        for r in rows
    ]


def holding_signal(signals: pl.DataFrame, symbol: str, entry_date: date) -> tuple[date, int] | None:
    """The signal a held position was most plausibly bought off, with its ranking.

    Only signals strictly before `entry_date` and no more than SIGNAL_LOOKBACK_CAL calendar
    days earlier count, so a stale trigger from months back cannot attach itself to an unrelated
    buy. The window is wider than the 30-day cooldown on purpose — a buy placed weeks after the
    breakout still finds its trigger — which also means two signals can fall inside it rather
    than the at most one a cooldown-width window allows. The newest wins and qm.MIN_RANKING is
    deliberately not applied: a position bought off a signal the gate would have dropped shows
    that score, which "--" could not be told apart from having no signal at all.

    Args:
        signals: Ungated, ranked s12 signals over the whole candidate window
        symbol: Ticker code in "TICKER.US" format
        entry_date: First buy date for the position

    Returns:
        tuple[date, int] | None: (signal date, 0-100 score), or None when no signal precedes the
            buy within the lookback window — the symbol may also sit outside the universe
            `qm.load_bars` selects, in which case it never had signals computed at all
    """
    window = (
        signals.filter(
            (pl.col("symbol") == symbol)
            & (pl.col("date") < entry_date)
            & (pl.col("date") >= entry_date - timedelta(days=SIGNAL_LOOKBACK_CAL))
        )
        .sort("date", descending=True)
        .head(1)
    )
    if window.is_empty():
        return None
    row = window.row(0, named=True)
    return row["date"], row["ranking"]


def format_holdings_table(rows: list[dict]) -> str:
    """Render open positions as a fixed-width table with a portfolio total line.

    Args:
        rows: Output of `load_holdings`, each row extended with `sector`, `signal_date` and
            `ranking`

    Returns:
        str: The rendered table, or a single line when no position is open
    """
    if not rows:
        return "No open positions in turtle.lightyear_transaction."
    hdr = (
        f"{'Symbol':<7}│ {'Sector':<23}│ {'Signal date':<12}│ {'Entry date':<11}│ {'Days':>5} │ {'Ranking':>7} │ "
        f"{'Avg Price':>10} │ {'Shares':>10} │ {'Curr Price':>10} │ {'Change %':>9} │ {'PL':>12}"
    )
    lines = [hdr, "─" * len(hdr)]
    total_cost = total_value = 0.0
    for r in rows:
        total_cost += r["avg_price"] * r["shares"]
        signal_date = f"{str(r['signal_date']):<12}" if r["signal_date"] is not None else f"{'--':<12}"
        days = f"{r['days']:>5}" if r["days"] is not None else f"{'--':>5}"
        ranking = f"{r['ranking']:>7}" if r.get("ranking") is not None else f"{'--':>7}"
        sector = f"{r['sector'] or '--':<23}"
        head = (
            f"{r['symbol']:<7}│ {sector}│ {signal_date}│ {str(r['entry_date']):<11}│ {days} │ {ranking} │ "
            f"{r['avg_price']:>10.2f} │ {r['shares']:>10.4f} │ "
        )
        if r["curr_price"] is None:
            lines.append(head + f"{'--':>10} │ {'--':>9} │ {'--':>12}")
            continue
        curr = float(r["curr_price"])
        total_value += curr * r["shares"]
        chg = (curr / r["avg_price"] - 1.0) * 100.0
        pl = (curr - r["avg_price"]) * r["shares"]
        lines.append(head + f"{curr:>10.2f} │ {chg:>+8.1f}% │ {pl:>+12.2f}")
    lines.append("─" * len(hdr))
    total_chg = (total_value / total_cost - 1.0) * 100.0 if total_cost else float("nan")
    lines.append(
        f"{'TOTAL':<7}│ {'':<23}│ {'':<12}│ {'':<11}│ {'':>5} │ {'':>7} │ "
        f"{total_cost:>10.2f} │ {'':>10} │ {total_value:>10.2f} │ {total_chg:>+8.1f}% │ {total_value - total_cost:>+12.2f}"
    )
    return "\n".join(lines)


def load_benchmark_return(engine: sa.Engine, symbol: str) -> tuple[float, date, date]:
    """Raw-close buy-and-hold return for `symbol` from the first available date >= DISPLAY_START
    through the latest available date <= DISPLAY_END (no dividend reinvestment, matching how
    Entry $/Curr Price/Change % are computed for the signal tickers)."""
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = :symbol AND date >= :start AND date <= :end
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol, "start": DISPLAY_START, "end": DISPLAY_END}).fetchall()
    start_date, start_close = rows[0][0], float(rows[0][1])
    end_date, end_close = rows[-1][0], float(rows[-1][1])
    ret = (end_close / start_close - 1.0) * 100.0
    return ret, start_date, end_date


def load_sectors(engine: sa.Engine) -> dict[str, str]:
    """Sector per ticker, for the Sector column of the signal and holdings tables.

    Args:
        engine: Sync engine used for the read

    Returns:
        dict[str, str]: Ticker code -> sector name. `qm.load_bars` joins turtle.company and filters
            on sector, so its symbols are normally all present — but that is a second read on a
            second connection, so a concurrent snapshot-company refresh can drop one. A held
            ticker outside the bars universe may be missing too. Both render as "--".
    """
    sql = "SELECT ticker_code, sector FROM turtle.company WHERE sector IS NOT NULL"
    with engine.connect() as conn:
        return {r[0]: r[1] for r in conn.execute(sa.text(sql)).fetchall()}


def add_report_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Add the two informational columns only this report shows, on top of `qm.add_indicators`.

    Both read the same shift-1 inputs the entry filters do, so neither adds look-ahead.

    Args:
        df: Indicator frame from `qm.add_indicators`

    Returns:
        The frame with tight_range_ratio (10-day close range over its mean) and
        vol_dry_up_ratio (avg_vol_10 / avg_vol_50) added.
    """
    c1 = pl.col("adj_close").shift(1)
    tr_max = c1.rolling_max(10, min_samples=10).over("symbol")
    tr_min = c1.rolling_min(10, min_samples=10).over("symbol")
    tr_mean = c1.rolling_mean(10, min_samples=10).over("symbol")
    return df.with_columns(
        ((tr_max - tr_min) / tr_mean).alias("tight_range_ratio"),
        (pl.col("avg_vol_10") / pl.col("avg_vol_50")).alias("vol_dry_up_ratio"),
    )


def main() -> None:
    run_start = time.perf_counter()
    settings = Settings.from_toml()

    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, CANDIDATE_START, DISPLAY_END)

    print("Loading bars …", flush=True)
    sectors = load_sectors(settings.engine)
    df = qm.load_bars(bars_history, CANDIDATE_START, DISPLAY_END)

    print("Computing indicators …", flush=True)
    df = add_report_columns(qm.add_indicators(df))

    latest_date: dict[str, date] = {}
    latest_raw_close: dict[str, float] = {}
    sym_dates: dict[str, list[date]] = {}
    sym_raw_closes: dict[str, list[float]] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        d_list = g["date"].to_list()
        c_list = [float(c) for c in g["raw_close"].to_list()]
        sym_dates[sym] = d_list
        sym_raw_closes[sym] = c_list
        latest_date[sym] = d_list[-1]
        latest_raw_close[sym] = c_list[-1]

    print(f"Generating signals for {BASE_LABEL} …", flush=True)
    # kept over the whole candidate window, not just the display one: a position bought early in
    # the display window was triggered by a signal that precedes it
    candidate_sig = qm.add_ranking(
        qm.get_signals(df, bull_dates, CANDIDATE_START, BASE_SMA_T)  # bars end at DISPLAY_END
    )
    base_sig = candidate_sig.filter((pl.col("date") >= DISPLAY_START) & (pl.col("date") <= DISPLAY_END)).sort(["date", "symbol"])
    n_gated = int(base_sig.filter(pl.col("ranking") >= qm.MIN_RANKING).height)
    print(f"  {len(base_sig)} signals in display window, {n_gated} at ranking >= {qm.MIN_RANKING}", flush=True)

    hdr = (
        f"{'Date':<11}│ {'Symbol':<7}│ {'Sector':<23}│ {'%abv SMA50':>10} │ {'ADR%':>6} │ {'ADR_CHG':>7} │ "
        f"{'VOL_DRY':>7} │ {'RSI14':>6} │ {'TR%':>6} │ {'ROC252%':>8} │ {'Last date':>11} │ "
        f"{'Ranking':>7} │ {'Entry $':>8} │ {'Curr Price':>10} │ {'Change %':>9}"
    )
    sep = "─" * len(hdr)

    lines: list[str] = [hdr, sep]
    excluded_rows: list[dict] = []
    cohort_returns: dict[str, list[float]] = {label: [] for _, _, label in COHORTS}
    cohort_mdds: dict[str, list[float]] = {label: [] for _, _, label in COHORTS}
    ranking_returns: dict[str, list[float]] = {label: [] for _, _, label in RANKING_COHORTS}
    ranking_mdds: dict[str, list[float]] = {label: [] for _, _, label in RANKING_COHORTS}
    shown = 0
    n_below_gate = 0
    for row in base_sig.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        idx_entry = bisect_left(sym_dates[sym], d)
        window = np.array(sym_raw_closes[sym][idx_entry:])
        max_day_chg = float(np.abs(window[1:] / window[:-1] - 1.0).max()) if len(window) > 1 else 0.0
        if max_day_chg > SUSPICIOUS_DAY_MOVE:
            excluded_rows.append({**row, "max_day_chg": max_day_chg})
            continue
        entry = row["raw_close"]
        curr = latest_raw_close.get(sym, float("nan"))
        chg = (curr / entry - 1.0) * 100 if entry else float("nan")
        ranking = row["ranking"]
        sma_pct = row["pct_vs_sma50"] * 100
        running_max = np.maximum.accumulate(window)
        mdd = float((1.0 - window / running_max).max())
        # cohort tables cover every non-suspicious signal, gated or not — see module docstring
        cohort_returns[cohort_label(sma_pct, COHORTS)].append(chg)
        cohort_mdds[cohort_label(sma_pct, COHORTS)].append(mdd)
        ranking_returns[cohort_label(float(ranking), RANKING_COHORTS)].append(chg)
        ranking_mdds[cohort_label(float(ranking), RANKING_COHORTS)].append(mdd)
        if ranking < qm.MIN_RANKING:
            n_below_gate += 1
            continue
        ld = latest_date.get(sym)
        lines.append(
            f"{str(d):<11}│ {sym:<7}│ {sectors.get(sym) or '--':<23}│ {sma_pct:>+9.1f}% │ "
            f"{row['adr_pct'] * 100:>5.1f}% │ {row['adr_pct_change']:>7.2f} │ "
            f"{row['vol_dry_up_ratio']:>7.2f} │ {row['rsi14']:>6.1f} │ {row['tight_range_ratio'] * 100:>5.1f}% │ "
            f"{row['roc_252d'] * 100:>+7.1f}% │ {str(ld):>11} │ "
            f"{ranking:>7} │ {entry:>8.2f} │ {curr:>10.2f} │ {chg:>+8.1f}%"
        )
        shown += 1

    lines.append(sep)
    summary = f"{BASE_LABEL} signals at ranking >= {qm.MIN_RANKING}: {shown}  |  Dropped below gate: {n_below_gate}"
    if excluded_rows:
        summary += f"  |  Excluded as suspicious: {len(excluded_rows)}"
    lines.append(summary)

    output = "\n".join(lines)
    print(f"\n=== {BASE_LABEL} — Signal Report ===")
    print(f"Run date: {run_timestamp()}  |  Period: {DISPLAY_START} – {DISPLAY_END}")
    print("\n" + output)

    excluded_lines: list[str] = []
    if excluded_rows:
        excluded_lines.append(
            f"=== Excluded as suspicious data — single-day |Δraw_close| > {SUSPICIOUS_DAY_MOVE * 100:.0f}% "
            f"between entry and latest available date (N={len(excluded_rows)}) ===\n"
        )
        for row in excluded_rows:
            excluded_lines.append(
                f"  {row['date']} {row['symbol']:<7} max 1-day move {row['max_day_chg'] * 100:.1f}% "
                "— likely a data anomaly or delisting/halt-type event, not organic price action"
            )
    else:
        excluded_lines.append("No signals excluded as suspicious.")
    excluded_text = "\n".join(excluded_lines)
    print("\n" + excluded_text)

    cohort_output, cohort_means = build_cohort_table(COHORTS, cohort_returns, cohort_mdds)
    print(f"\n=== {BASE_LABEL} — Change % by %abv SMA50 cohort (mark-to-latest-price, ungated) ===")
    print(cohort_output)

    ranking_output, _ranking_means = build_cohort_table(RANKING_COHORTS, ranking_returns, ranking_mdds)
    print(f"\n=== {BASE_LABEL} — Change % by Ranking cohort (mark-to-latest-price, ungated) ===")
    print(f"All s12 signals, including those below the ranking >= {qm.MIN_RANKING} gate, so the gate can be judged.")
    print(ranking_output)

    print("Loading current investments …", flush=True)
    holdings = load_holdings(settings.engine)
    for h in holdings:
        h["sector"] = sectors.get(h["symbol"])
        match = holding_signal(candidate_sig, h["symbol"], h["entry_date"])
        h["signal_date"], h["ranking"] = match if match is not None else (None, None)
    holdings_output = format_holdings_table(holdings)
    print("\n=== Current investments (turtle.lightyear_transaction, marked to latest raw close) ===")
    print(holdings_output)

    print("Loading benchmark returns …", flush=True)
    mean_of_means = float(np.mean(cohort_means)) if cohort_means else float("nan")
    spy_ret, spy_start_d, spy_end_d = load_benchmark_return(settings.engine, "SPY.US")
    qqq_ret, qqq_start_d, qqq_end_d = load_benchmark_return(settings.engine, "QQQ.US")
    bench_lines = [
        f"mean(Mean%) across cohorts:  {mean_of_means:>+7.1f}%",
        f"SPY.US buy-and-hold:         {spy_ret:>+7.1f}%   ({spy_start_d} → {spy_end_d})",
        f"QQQ.US buy-and-hold:         {qqq_ret:>+7.1f}%   ({qqq_start_d} → {qqq_end_d})",
    ]
    bench_output = "\n".join(bench_lines)
    print(f"\n=== mean(Mean%) vs SPY/QQQ buy-and-hold, {DISPLAY_START} – {DISPLAY_END} ===")
    print(bench_output)

    print(f"\nSignal report completed in {time.perf_counter() - run_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
