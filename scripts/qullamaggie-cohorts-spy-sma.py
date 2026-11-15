#!/usr/bin/env python3
"""
SPY market-regime cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

The production regime gate is `spy_close > mean(spy_close[-201:-1])` — SPY above its prior-day
200-day SMA. This study sweeps that lookback: N in {150, 200, 250, 300, 350}, plus a `regime off`
row that applies no market filter at all.

Unlike the other cohort studies this is a **variant sweep, not a partition**. The cohort variable
is a parameter of the filter rather than a property of a signal, so a signal that clears SMA150
usually clears SMA350 as well. Each row is therefore the *full* signal population under that
regime setting and the rows overlap; they do not sum to the `regime off` row. Read it as "what
would this algorithm have produced with that lookback", not as a decomposition.

The regime gate is applied before the 30-day cooldown, exactly as in production, so a different N
changes which triggers win the cooldown slot. That is why every variant regenerates signals from
scratch instead of re-filtering one shared candidate set.

Periods are chosen for this question rather than the usual 2015-2026 cohort window: a regime
filter only earns its keep in a downturn, so both windows straddle one — 2006-2010 covers the
2008 crash, 2018-2023 covers 2018 Q4, the 2020 Covid crash and 2022. Each window is loaded and
simulated on its own so neither drags in the other's bars.
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.common.report import config_table
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

# Both windows straddle a bear market, which is the only condition under which a regime filter
# can pay for itself. Each is loaded separately — a single span would pull 20 years of the
# universe and OOM the host.
PERIODS: list[tuple[date, date]] = [
    (date(2006, 1, 1), date(2010, 12, 31)),
    (date(2018, 1, 1), date(2023, 12, 31)),
]

MARKET_TICKER = "SPY.US"
# Extra SPY history so the longest lookback in the sweep is warm on the window's first day.
SPY_WARMUP_DAYS = 900
# The production lookback is 200; the others are the sweep. `None` is the no-regime reference row.
SMA_LOOKBACKS: list[int | None] = [150, 200, 250, 300, 350, None]
PRODUCTION_LOOKBACK = 200

CONFIG_ROWS = cohorts.config_rows(
    {
        "Period": None,
        "Periods": "**" + ", ".join(f"{s} – {e}" for s, e in PERIODS) + "** — each straddles a bear market",
        "Cohort variable": "**the regime lookback N in `spy_close > mean(spy_close[-(N+1):-1])`**",
        "Filter under study": (
            "**SPY > 200d SMA — swept over N = "
            + "/".join(str(lb) for lb in SMA_LOOKBACKS if lb is not None)
            + " and switched off entirely; `SMA200 *` is the production setting and `regime off` the "
            "dropped-filter reference**"
        ),
        "Rows overlap": "**variant sweep, not a partition — rows do not sum to `regime off`**",
        "Market regime": None,
        "Cooldown": f"{qm.COOLDOWN_DAYS} calendar days, applied after the regime gate as in production",
    }
)

RESULTS_INTRO = (
    "Each row is the **whole** signal population under that regime setting, so the rows overlap and do "
    "not sum to `regime off` — a signal clearing SMA150 usually clears SMA350 too. `SMA200 *` is the "
    "production setting; `regime off` applies no market filter at all. The gate runs before the 30-day "
    "cooldown, as in production, so a different lookback also changes which triggers win the cooldown "
    "slot — the row counts are not a pure subset relationship either.\n\n"
    "Both windows deliberately straddle a bear market, since that is the only condition under which a "
    "regime filter can pay for itself: 2006-2010 covers the 2008 crash, 2018-2023 covers 2018 Q4, the "
    "2020 Covid crash and 2022. They are **not** comparable with the other cohort studies, which all "
    "run 2015-2026.\n\n"
)

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-spy-sma.md"


def regime_dates(spy: pl.DataFrame, lookback: int | None) -> set[date] | None:
    """Dates on which SPY closed above its prior-day `lookback`-day SMA.

    `None` means no regime filter, and is signalled back as `None` rather than "every date" so
    the caller can skip the membership test entirely instead of building a set of the calendar.

    Args:
        spy: SPY bars covering the window plus enough lead-in to warm the longest lookback
        lookback: SMA window in trading days, or None for no filter

    Returns:
        The qualifying dates, or None when no filter applies.
    """
    if lookback is None:
        return None
    warm = spy.with_columns(pl.col("close").shift(1).rolling_mean(lookback, min_samples=lookback).alias("_sma"))
    return set(warm.filter(pl.col("close") > pl.col("_sma"))["date"].to_list())


def regime_label(lookback: int | None) -> str:
    if lookback is None:
        return "regime off"
    return f"SMA{lookback}" + (" *" if lookback == PRODUCTION_LOOKBACK else "")


# ── One evaluation window ─────────────────────────────────────────────────────


def run_window(bars_history: DailyBarsQueryRepository, eval_start: date, eval_end: date) -> list[str]:
    """Load one window's bars and sweep every regime lookback across all three algorithms.

    Bars are fetched per window rather than once for the whole study: a single span covering
    2006-2023 would pull ~20 years of the qualified universe and exhaust the memory cap.

    Args:
        bars_history: Repository for accessing historical bar data
        eval_start: First date a signal may be emitted for
        eval_end: Last date a signal may be emitted for

    Returns:
        Rendered markdown lines for this window, one table per algorithm.
    """
    label = f"{eval_start} – {eval_end}"
    print(f"\n=== {label} ===", flush=True)

    print("Loading SPY …", flush=True)
    spy_start = eval_start - timedelta(days=qm.WARMUP_DAYS + SPY_WARMUP_DAYS)
    spy = bars_history.get_bars_pl(MARKET_TICKER, spy_start, eval_end).sort("date")
    regimes = {lb: regime_dates(spy, lb) for lb in SMA_LOOKBACKS}
    for lb in SMA_LOOKBACKS:
        d = regimes[lb]
        n_days = "all" if d is None else str(len({x for x in d if eval_start <= x <= eval_end}))
        print(f"  {regime_label(lb):<12} qualifying days in window: {n_days}", flush=True)

    # Forward bars past eval_end so a signal on the last day can still reach its 366d exit.
    df, bars = cohorts.load_universe(bars_history, eval_start, end=eval_end + timedelta(days=qm.HOLD_CAL + 30))

    lines: list[str] = []
    for arm in cohorts.STANDARD_ARMS:
        print(f"  {arm.label} …", flush=True)
        groups: list[tuple[str, np.ndarray]] = []
        for lb in SMA_LOOKBACKS:
            trades = cohorts.cohort_trades(
                df,
                bars,
                regimes[lb] or set(),
                arm.sma_thresh,
                drop=("regime",) if lb is None else (),
                start=eval_start,
                end=eval_end,
            )
            groups.append((regime_label(lb), cohorts.returns(trades)))
            print(f"    {regime_label(lb):<12} {trades.height} trades", flush=True)
        table = cohorts.render_table(f"{label} — {arm.label}", groups, [], label_width=12, label_header="Regime")
        lines.extend(table)
        print("\n".join(table))
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    config = config_table(CONFIG_ROWS)
    print("\n" + config)

    lines: list[str] = []
    for eval_start, eval_end in PERIODS:
        lines += run_window(bars_history, eval_start, eval_end)

    cohorts.write_result(RESULT_PATH, "Qullamaggie SPY Regime (market SMA) Cohort Analysis", config, lines, results_intro=RESULTS_INTRO)


if __name__ == "__main__":
    main()
