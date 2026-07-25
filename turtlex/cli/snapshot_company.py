"""Monthly snapshot of turtle.company into turtle.company_history.

Intended to run on the 1st of each month. The snapshot_date is set to the last
day of the previous month. The operation is idempotent — running it twice on the
same day is safe.
"""

import argparse
import logging
import sys
from datetime import date, timedelta

from sqlalchemy import text

from turtlex.cli.common import add_logging_args
from turtlex.config.logging import setup_logging
from turtlex.config.settings import Settings

logger = logging.getLogger(__name__)

_COLUMNS = [
    "ticker_code",
    "type",
    "name",
    "sector",
    "industry",
    "average_volume",
    "average_price",
    "dividend_yield",
    "market_cap",
    "pe",
    "forward_pe",
]


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="Snapshot turtle.company into turtle.company_history")
    add_logging_args(parser)

    return parser


def main() -> int:
    """Copy current turtle.company rows into turtle.company_history."""
    args = create_argument_parser().parse_args()

    setup_logging(args.verbose)
    settings = Settings.from_toml()

    snapshot_date = date.today().replace(day=1) - timedelta(days=1)
    logger.info("Starting company snapshot for %s", snapshot_date)

    col_list = ", ".join(_COLUMNS)

    with settings.engine.begin() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM turtle.company_history WHERE snapshot_date = :d LIMIT 1"),
            {"d": snapshot_date},
        ).fetchone()

        if existing:
            logger.info("Snapshot for %s already exists — skipping", snapshot_date)
            return 0

        result = conn.execute(
            text(f"INSERT INTO turtle.company_history ({col_list}, snapshot_date) SELECT {col_list}, :d FROM turtle.company"),
            {"d": snapshot_date},
        )

    logger.info("Snapshot complete: %d rows written for %s", result.rowcount, snapshot_date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
