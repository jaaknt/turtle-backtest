#!/usr/bin/env python3
"""
Company-sector cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the sector exclusion (Communication Services,
Real Estate), so we can see performance across all GICS sectors including the
two excluded from the baseline universe.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from datetime import date, timedelta
from pathlib import Path

import polars as pl
import sqlalchemy as sa

from turtlex.common.report import config_table
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

UNKNOWN_SECTOR = "(unknown)"
NO_SUCH_SECTOR = "__no_such_sector__"

CONFIG_ROWS = cohorts.config_rows(
    {
        "Cohort variable": "company GICS sector",
        "Filter under study": "**Comm Services / Real Estate universe exclusion — removed; returns as the `excl Comm/RE (cap)` row**",
        "Universe": "**US common stocks, market_cap >= 1.5B — sector exclusion lifted (the cohort variable)**",
    }
)

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-sector.md"


# ── Sector map (study-specific) ───────────────────────────────────────────────


def load_all_sector_bars(bars_history: DailyBarsQueryRepository, start_date: date, end_date: date) -> pl.DataFrame:
    """Load the qualified universe without the sector exclusion, which is this study's whole point.

    `qm.load_bars` hardcodes `EXCLUDED_SECTORS` into the SQL, so it cannot serve a study that
    needs to see Communication Services and Real Estate. Only the universe predicate is widened
    here — adjustment and unusable-bar handling still come from `qm.prepare_bars`, the same path
    `qm.load_bars` uses.

    `NO_SUCH_SECTOR` rather than `[]`: an empty list renders an always-true predicate that
    retains NULL-sector names, which the production universe excludes. The sentinel keeps them
    out, so the only difference from the baseline universe is the two restored sectors.

    Args:
        bars_history: Repository for accessing historical bar data
        start_date: First signal date; bars are fetched from `qm.WARMUP_DAYS` before it
        end_date: Last date to load

    Returns:
        Frame of symbol, date, raw_close, adj_open, adj_close, adj_high, adj_low, volume.
    """
    df = bars_history.get_qualified_universe_bars_pl(
        start_date - timedelta(days=qm.WARMUP_DAYS),
        end_date,
        min_market_cap=qm.MIN_MARKET_CAP,
        excluded_sectors=[NO_SUCH_SECTOR],
    )
    return qm.prepare_bars(df.rename({"close": "raw_close"}))


def load_sector_map(engine: sa.Engine) -> dict[str, str]:
    """Map each qualified ticker to its company sector, the dimension this study cohorts on."""
    sql = """
        SELECT t.code, c.sector
        FROM   turtle.ticker t
        JOIN   turtle.company c ON c.ticker_code = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 1500000000
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    return {r[0]: (r[1] if r[1] else UNKNOWN_SECTOR) for r in rows}


def build_table(label: str, trades: pl.DataFrame) -> list[str]:
    """One row per sector, alphabetical with unknown last, then ALL and the production universe.

    Args:
        label: Table heading, the algorithm variant
        trades: Its completed trades, carrying a `sector` column
    """
    sectors = sorted(set(trades["sector"].to_list()), key=lambda s: (s == UNKNOWN_SECTOR, s))
    groups = [(sector, cohorts.returns(trades, pl.col("sector") == sector)) for sector in sectors]
    footer = [
        ("ALL", cohorts.returns(trades)),
        ("excl Comm/RE (cap)", cohorts.returns(trades, ~pl.col("sector").is_in(qm.EXCLUDED_SECTORS))),
    ]
    return cohorts.render_table(label, groups, footer, label_width=24)


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, cohorts.EVAL_START, cohorts.EVAL_END)

    print("Loading sector map …", flush=True)
    sector_map = load_sector_map(settings.engine)
    df, bars = cohorts.load_universe(bars_history, load=load_all_sector_bars)

    config = config_table(CONFIG_ROWS)
    print("\n" + config)

    lines: list[str] = []
    for arm in cohorts.STANDARD_ARMS:
        print(f"  {arm.label} …", flush=True)
        trades = cohorts.cohort_trades(df, bars, bull_dates, arm.sma_thresh)
        sector = trades["symbol"].replace_strict(sector_map, default=UNKNOWN_SECTOR, return_dtype=pl.String)
        table = build_table(arm.label, trades.with_columns(sector.alias("sector")))
        lines.extend(table)
        print("\n".join(table))

    cohorts.write_result(RESULT_PATH, "Qullamaggie Sector Cohort Analysis", config, lines)


if __name__ == "__main__":
    main()
