#!/usr/bin/env python3
"""
Does capping new positions per month pay for itself?

At $30,000 with 4% positions the portfolio holds 25 names, while s12 raises roughly 36 gated
signals a month against the two or three the book can actually fund once it is full. Supply
outruns fundable capacity by more than an order of magnitude, so the book fills first-come
and every slot can be consumed by a single month's signals — one entry vintage carrying the whole
year, with no capacity left for anything better that appears later. Capping intake per month is
the obvious fix. This study asks whether it actually buys anything.

**It does not.** The cap diversifies entry vintages exactly as intended and delivers no gain in
return, drawdown or dispersion at any horizon tested. The result is committed because the
negative is the useful part: it closes off an intuitively appealing change to the live portfolio.

Method, and the two traps it is built around:

1. **Vintage concentration is a variance problem, so a single backtest cannot see it.** One
   ten-year run says nothing about whether outcomes depend on *when you started*. Every horizon
   here is therefore replayed from many quarterly start dates, each beginning with fresh cash,
   and the spread across those starts is reported alongside the average. A cap that helps on one
   start date proves nothing; one that narrows the distribution is doing what it claims.
2. **A monthly cap must not peek.** `run_sim`'s `max_new_per_month` takes signals as they arrive
   within a month, best-scored first on any given day, until the cap is hit. Choosing "the best
   N signals of the month" would need the month in advance and would flatter the cap.

Read the dispersion columns with the overlap caveat in mind: quarterly starts drawn from one
ten-year window share most of their data, so the runs are not independent samples. At the
five-year horizon the effective sample size is nearer two than twenty. This can rule out a large
effect; it cannot resolve a small one.

Signals come from the ranking-lab parquet cache rather than the database, so this runs in seconds
and scores the identical signal set the ranking studies use. Build it first:

    ACTIVE_PROFILE=hetzner-db DB_APP_PASSWORD="$DB_CLAUDE_PASSWORD" \
      systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 \
      uv run scripts/qullamaggie-ranking-lab.py --build-cache
"""

import statistics
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from turtlex.common.report import config_table, run_timestamp
from turtlex.research import ranking_lab as rl
from turtlex.research.portfolio_replay import HOLD_CAL, INIT_EQUITY, POS_FRACTION, Market, run_sim

_EPOCH = date(1970, 1, 1)

CONFIG = "s12"  # the live reference algorithm (CLAUDE.md)
GATE = 44  # MIN_RANKING, held fixed: this study varies pacing, not selection
BASELINE_SPEC = Path(__file__).parent.parent / "docs" / "research" / "ranking-lab" / "candidates" / "c000-production.json"
RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-pacing.md"

# Windows are capped at the holdout boundary: this is a portfolio question, and opening the
# frozen slice for it would spend it a second time.
WINDOW_START = rl.EVAL_START
WINDOW_END = rl.HOLDOUT_START - timedelta(days=1)
HORIZONS = [(548, "18 months"), (1096, "3 years"), (1826, "5 years")]
CAPS: list[int | None] = [None, 5, 4, 3, 2]
MIN_CALENDAR_DAYS = 200  # a horizon shorter than this has too few bars to replay


def start_dates(horizon_days: int) -> list[date]:
    """Quarterly start dates whose full horizon fits inside the study window.

    Args:
        horizon_days: Length of each replay in calendar days
    """
    every_quarter = [date(y, m, 1) for y in range(WINDOW_START.year, WINDOW_END.year + 1) for m in (1, 4, 7, 10)]
    return [s for s in every_quarter if s >= WINDOW_START and s + timedelta(days=horizon_days) <= WINDOW_END]


def vintage_stats(entries: list[date]) -> tuple[int, float]:
    """How spread out a book's entry dates are.

    Args:
        entries: The date each funded position was opened

    Returns:
        `(distinct entry months, share of positions in the single busiest month)`. The second
        is the number the cap exists to reduce.
    """
    if not entries:
        return 0, 0.0
    months = [(e.year, e.month) for e in entries]
    busiest = max(months.count(m) for m in set(months))
    return len(set(months)), 100.0 * busiest / len(months)


def main() -> None:
    """Sweep the monthly intake cap across horizons and start dates, and write the report."""
    signals, prices, calendar = rl.load_cache()
    sig = signals[CONFIG].sort(["date", "symbol"])
    scores = rl.raw_scores(sig, rl.load_spec(BASELINE_SPEC))

    market = Market(prices)
    cal_days = {(d - _EPOCH).days for d in calendar}
    rows = [
        {
            "symbol": r["symbol"],
            "entry_dint": (r["entry_date"] - _EPOCH).days,
            "entry_px": float(r["entry_price"]),
            "score": float(scores[i]),
        }
        for i, r in enumerate(sig.iter_rows(named=True))
        if (r["entry_date"] - _EPOCH).days in cal_days and r["entry_date"] < rl.HOLDOUT_START and scores[i] >= GATE
    ]

    lines: list[str] = []

    def out(text: str = "") -> None:
        print(text)
        lines.append(text)

    out("# Qullamaggie Portfolio Pacing — does a monthly intake cap help?")
    out("")
    out(f"Run date: {run_timestamp()}")
    out("")
    out(
        config_table(
            [
                ("Algorithm", f"bk50d_{CONFIG}_v2.0, {HOLD_CAL}d calendar hold"),
                ("Ranking gate", f"QullamaggieRanking >= {GATE} (held fixed)"),
                ("Window", f"{WINDOW_START} – {WINDOW_END} (holdout excluded)"),
                ("Gated signals", str(len(rows))),
                ("Sizing", f"{POS_FRACTION:.0%} of portfolio value, ${INIT_EQUITY:,.0f} fresh at each start"),
                ("Starts", "quarterly, every horizon replayed from each"),
                ("Cap", "**the variable under study** — new positions per calendar month"),
            ]
        )
    )
    out(
        "`sd`, `p10` and `min` are taken across start dates, not across trades: vintage "
        "concentration is a claim about start-date dependence, so the spread is the point. "
        "Quarterly starts overlap heavily, so treat those columns as ruling out a large effect "
        "rather than resolving a small one."
    )

    for horizon_days, label in HORIZONS:
        starts = start_dates(horizon_days)
        out("")
        out(f"## Horizon {label} — {len(starts)} start dates")
        out("")
        out("```text")
        hdr = (
            f"{'cap/mo':>7} {'mean':>7} {'median':>7} {'sd':>6} {'p10':>7} {'min':>7} "
            f"{'meanDD':>7} {'Sortino':>8} {'taken':>6} {'vintages':>9} {'top-mo%':>8}"
        )
        out(hdr)
        out("-" * len(hdr))
        for cap in CAPS:
            results = []
            for start in starts:
                end = start + timedelta(days=horizon_days)
                cal = [d for d in calendar if start <= d <= end]
                if len(cal) < MIN_CALENDAR_DAYS:
                    continue
                lo, hi = (start - _EPOCH).days, (end - _EPOCH).days
                window_rows = [r for r in rows if lo <= r["entry_dint"] <= hi]
                results.append(run_sim(market, cal, window_rows, "score", max_new_per_month=cap))
            if not results:
                continue
            cagrs = np.array([r["cagr"] for r in results])
            vintages = [vintage_stats(r["entries"]) for r in results]
            out(
                f"{'none' if cap is None else cap:>7} {cagrs.mean():>+7.2f} {np.median(cagrs):>+7.2f} {cagrs.std():>6.2f} "
                f"{np.percentile(cagrs, 10):>+7.2f} {cagrs.min():>+7.2f} "
                f"{statistics.fmean([r['max_dd'] for r in results]):>7.2f} "
                f"{statistics.fmean([r['sortino'] for r in results]):>8.3f} "
                f"{statistics.fmean([r['taken'] for r in results]):>6.0f} "
                f"{statistics.fmean([v[0] for v in vintages]):>9.1f} "
                f"{statistics.fmean([v[1] for v in vintages]):>7.1f}%"
            )
        out("```")

    out("")
    out("## Reading")
    out("")
    out(
        "The cap works mechanically — `top-mo%` and `vintages` move sharply in the intended "
        "direction at every horizon — and buys nothing. At 18 months it cuts dispersion and the "
        "mean in the same proportion, which is what holding less exposure does rather than what "
        "managing risk does, and it leaves the worst start date worse off. At 3 years there is "
        "no effect at all. At 5 years the p10 and Sortino edge is inside what overlapping start "
        "dates can produce by chance, and mean drawdown moves the wrong way."
    )
    out("")
    out(
        "So an intake cap is a preference, not an edge. It is a reasonable thing to want if "
        "committing a year of capacity on one month's signals is uncomfortable to hold — it "
        "just should not be adopted expecting better returns."
    )

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
