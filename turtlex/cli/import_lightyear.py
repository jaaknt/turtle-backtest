#!/usr/bin/env python3
"""Import Lightyear account-statement CSVs into turtle.lightyear_transaction.

Download the statement from Lightyear, drop it into the folder, and run this. Only
Buy/Sell rows in USD whose symbol is in the named ticker group are stored, and the
run is idempotent — re-importing overlapping statements never double-counts.

The ticker group is hand-maintained; seed it with SQL before the first run::

    INSERT INTO turtle.ticker_group (code, ticker_code)
    VALUES ('lightyear', 'DUOL.US') ON CONFLICT DO NOTHING;

Usage:
    uv run lightyear-import [options]

Options:
    --folder PATH          Folder to scan for *.csv statements (default: data/lightyear)
    --ticker-group CODE    turtle.ticker_group code listing held symbols (default: lightyear)
    --verbose              Enable verbose logging
"""

import argparse
import logging
import sys
from pathlib import Path

from turtlex.cli.common import add_logging_args, run_job
from turtlex.config.logging import setup_logging
from turtlex.config.settings import Settings
from turtlex.repository.ingest.lightyear import LightyearRepository
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.lightyear_service import LightyearService, TickerGroupNotSeededError

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Import Lightyear statement CSVs into turtle.lightyear_transaction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--folder", type=Path, default=Path("data/lightyear"), help="Folder to scan for *.csv statements")
    parser.add_argument("--ticker-group", type=str, default="lightyear", help="turtle.ticker_group code listing held symbols")
    add_logging_args(parser)

    return parser


def main() -> int:
    """Parse every statement CSV in the drop folder and store its Buy/Sell rows."""
    args = create_argument_parser().parse_args()

    setup_logging(args.verbose)

    # Checked before Settings.from_toml(): a missing drop folder should report itself, not
    # surface as a config or env-var error from a bootstrap this run never needed. It also means
    # this one failure records no job_runs row — there is no engine yet to write it with.
    if not args.folder.is_dir():
        logger.error("Folder does not exist: %s — create it and drop a Lightyear statement CSV in it", args.folder)
        return 1

    settings = Settings.from_toml()
    return run_job("lightyear-import", args, settings, lambda _recorder: _import_statements(args, settings))


def _import_statements(args: argparse.Namespace, settings: Settings) -> int:
    service = LightyearService(
        repository=LightyearRepository(settings.engine),
        ticker_repo=TickerQueryRepository(settings.engine),
    )

    try:
        summary = service.import_folder(args.folder, args.ticker_group)
    except TickerGroupNotSeededError as e:
        logger.error("%s — seed turtle.ticker_group with the symbols you hold, then re-run", e)
        return 1

    if not summary.files:
        logger.warning("No CSV files found in %s — nothing to import", args.folder)
        return 0

    for f in summary.files:
        if f.failed:
            logger.info("%s: FAILED to parse, nothing stored (see the error above)", f.file_name)
            continue
        logger.info(
            "%s: %d rows, %d buy/sell, %d matched, %d inserted, %d already stored",
            f.file_name,
            f.rows,
            f.buy_sell,
            f.matched,
            f.inserted,
            f.already_stored,
        )
    logger.info(
        "Import complete: %d files, %d rows, %d buy/sell, %d matched, %d inserted, %d already stored",
        len(summary.files),
        summary.rows,
        summary.buy_sell,
        summary.matched,
        summary.inserted,
        summary.already_stored,
    )

    unseeded = summary.unseeded_symbols
    if unseeded:
        logger.warning(
            "skipped %d USD buy/sell rows for symbols not in group '%s': %s — seed them if held",
            summary.skipped_not_in_group,
            args.ticker_group,
            ", ".join(sorted(unseeded)),
        )

    # Reported after the summary, not instead of it: the operator needs to see what the
    # healthy files stored before being told which one to fix.
    if summary.failed_files:
        logger.error(
            "%d of %d files could not be parsed and stored nothing: %s — fix or remove them and re-run",
            len(summary.failed_files),
            len(summary.files),
            ", ".join(summary.failed_files),
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
