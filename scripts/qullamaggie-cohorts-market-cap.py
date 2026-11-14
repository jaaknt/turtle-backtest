#!/usr/bin/env python3
"""
Market-cap cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

Drops the production `market_cap >= 1.5B` universe floor and buckets every signal by its
company's market cap, so the three sub-floor cohorts exist at all. `>=1.5B (cap)` is the
reference row: the slice the live filter keeps.

**READ THE CAVEAT BEFORE THE TABLE.** `turtle.company.market_cap` is a single snapshot column
with no history, so a 2015 trade is bucketed by its company's market cap *today*. Every other
cohort study measures its variable on the signal date; this one cannot. That inverts the
question being asked: the `(<300M)` bucket is not "small companies", it is "companies that are
small in 2026" — i.e. ones that fell or stagnated over the following decade — and `(>100B)` is
companies that grew into it. Trades are therefore sorted partly by their own outcome, and a
"large caps did better" reading would be look-ahead, not a finding. The study is descriptive
only: it says which of today's size classes the good trades came from, which is a different
question from whether size predicts returns.

The existing `>= 1.5B` *filter* is far less affected, because it applies identically to every
arm of any comparison — it restricts the universe rather than sorting within it.

Memory: the universe is read in market-cap slabs rather than in one query. Dropping the floor
takes the 2013-2026 read from ~5.8M rows to ~11.8M, roughly double the widest existing study,
which already peaks near the 4 GB cap. Market cap is a per-symbol attribute and nothing in the
signal path crosses symbols (the cooldown is per-symbol), so slabbing reproduces a single wide
read exactly while halving peak memory.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from datetime import date, timedelta
from functools import partial
from pathlib import Path

import polars as pl
import sqlalchemy as sa

from turtlex.common.report import config_table
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

# The production universe floor. Not applied here — it is the dimension under study — but
# reported as the `>=1.5B (cap)` row, which is the slice the live filter keeps.
MARKET_CAP_FLOOR = 1_500_000_000

# Read the universe in these [lo, hi) market-cap slabs. Splitting on a per-symbol attribute is
# lossless here because no part of the signal path crosses symbols.
SLABS: list[tuple[int, int | None]] = [(0, MARKET_CAP_FLOOR), (MARKET_CAP_FLOOR, None)]

_B = 1_000_000_000
_M = 1_000_000
COHORTS: list[cohorts.Bucket] = [
    ("(<300M)    ", 0, 300 * _M),
    ("[300M-1B)  ", 300 * _M, 1 * _B),
    ("[1B-1.5B)  ", 1 * _B, 1.5 * _B),
    ("[1.5-3B)   ", 1.5 * _B, 3 * _B),
    ("[3-10B)    ", 3 * _B, 10 * _B),
    ("[10-30B)   ", 10 * _B, 30 * _B),
    ("[30-100B)  ", 30 * _B, 100 * _B),
    ("(>100B)    ", 100 * _B, float("inf")),
]

CONFIG_ROWS = cohorts.config_rows(
    {
        "Cohort variable": "**`company.market_cap` — a current snapshot, NOT a signal-date value**",
        "Filter under study": (
            "**`market_cap >= 1.5B` — removed, otherwise the three sub-floor cohorts would be empty; returns as the `>=1.5B (cap)` row**"
        ),
        "⚠ Look-ahead": (
            "**market_cap has no history, so a 2015 trade is bucketed by its 2026 cap — trades are "
            "sorted partly by their own outcome. Descriptive only; do not read as 'size predicts returns'**"
        ),
        "Universe": "US common stocks, excl. Comm/RE — **no market-cap floor**",
        "Universe read": f"{len(SLABS)} market-cap slabs, lossless vs one wide read (see docstring)",
    }
)

PREAMBLE = (
    "> **⚠ Descriptive only — this cohort variable carries look-ahead.** `company.market_cap` is a "
    "current snapshot with no history, so a 2015 trade is bucketed by its company's market cap *today*. "
    "The `(<300M)` bucket is therefore not 'small companies' but 'companies that are small in 2026' — "
    "ones that fell or stagnated over the following decade — and `(>100B)` is companies that grew into "
    "it. Trades are sorted partly by their own outcome, so a 'large caps did better' reading would be "
    "an artifact, not a finding. Every other cohort study measures its variable on the signal date; "
    "this one cannot until a point-in-time cap (shares outstanding x close) is available.\n\n"
)

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-market-cap.md"


def load_market_caps(engine: sa.Engine) -> dict[str, int]:
    """Map ticker code to its (current) market cap for every US common stock we might load.

    Args:
        engine: SQLAlchemy engine for the trading database

    Returns:
        `{symbol: market_cap}`; symbols missing a cap are absent and get no cohort.
    """
    sql = """
        SELECT t.code, c.market_cap
        FROM   turtle.company c
        JOIN   turtle.ticker  t ON t.code = c.ticker_code
        WHERE  t.country = 'USA' AND t.type = 'Common Stock'
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  c.market_cap > 0
    """
    with engine.connect() as conn:
        return {r[0]: int(r[1]) for r in conn.execute(sa.text(sql)).fetchall()}


def load_slab(bars_history: DailyBarsQueryRepository, start_date: date, end_date: date, *, lo: int, hi: int | None) -> pl.DataFrame:
    """Load one market-cap slab of the universe, with no market-cap floor.

    Mirrors `qm.load_bars`, which cannot be reused because it hardcodes the 1.5B floor.

    Args:
        bars_history: Repository for accessing historical bar data
        start_date: First signal date; bars are fetched from `qm.WARMUP_DAYS` before it
        end_date: Last date to load
        lo: Smallest market cap in the slab
        hi: Market cap the slab stops below, or None for no ceiling

    Returns:
        The slab's prepared bars, as `qm.load_bars` returns them.
    """
    raw = bars_history.get_qualified_universe_bars_pl(
        start_date - timedelta(days=qm.WARMUP_DAYS),
        end_date,
        min_market_cap=lo,
        max_market_cap=hi,
    )
    return qm.prepare_bars(raw.rename({"close": "raw_close"}))


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading market caps …", flush=True)
    caps = load_market_caps(settings.engine)
    print(f"  {len(caps)} symbols with a market cap", flush=True)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, cohorts.EVAL_START, cohorts.EVAL_END)

    config = config_table(CONFIG_ROWS)
    print("\n" + config)

    capped = list(caps)
    # One trade frame per algorithm per slab, combined before any metric is computed.
    trades_by_arm: dict[str, list[pl.DataFrame]] = {arm.label: [] for arm in cohorts.STANDARD_ARMS}

    for slab_lo, slab_hi in SLABS:
        hi_txt = "inf" if slab_hi is None else f"{slab_hi / _B:g}B"
        print(f"\n=== slab {slab_lo / _B:g}B – {hi_txt} ===", flush=True)
        df, bars = cohorts.load_universe(bars_history, load=partial(load_slab, lo=slab_lo, hi=slab_hi))
        if df.is_empty():
            print("  no bars in slab", flush=True)
            continue
        print(f"  {df.height:,} rows, {df['symbol'].n_unique()} symbols", flush=True)

        for arm in cohorts.STANDARD_ARMS:
            print(f"  {arm.label} …", flush=True)
            # A symbol without a market cap has no cohort, so it is left out of every row.
            trades = cohorts.cohort_trades(df, bars, bull_dates, arm.sma_thresh).filter(pl.col("symbol").is_in(capped))
            trades_by_arm[arm.label].append(
                trades.with_columns(pl.col("symbol").replace_strict(caps, return_dtype=pl.Int64).alias("market_cap"))
            )
            print(f"    {trades.height} trades", flush=True)

        # Free the slab before the next one is read; both do not fit under the memory cap.
        del df, bars

    lines: list[str] = []
    for arm in cohorts.STANDARD_ARMS:
        frames = trades_by_arm[arm.label]
        trades = pl.concat(frames) if frames else pl.DataFrame(schema={"market_cap": pl.Int64, "ret": pl.Float64})
        references = [(">=1.5B (cap)", pl.col("market_cap") >= MARKET_CAP_FLOOR)]
        table = cohorts.bucket_table(arm.label, trades, "market_cap", COHORTS, references, label_width=12)
        lines.extend(table)
        print("\n".join(table))

    cohorts.write_result(RESULT_PATH, "Qullamaggie Market-Cap Cohort Analysis", config, lines, PREAMBLE)


if __name__ == "__main__":
    main()
