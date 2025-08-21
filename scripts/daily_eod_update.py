#!/usr/bin/env python3
"""
Daily EOD Database Update Script

This script updates the database with OHLCV data for all symbols.
It's designed to be run manually to keep the database current with market data.

Usage:
    python scripts/daily_eod_update.py [options]

Options:
    --start-date YYYY-MM-DD  Start date for update range (required)
    --end-date YYYY-MM-DD    End date for update range (default: same as start-date)
    --dry-run               Show what would be updated without making changes
    --verbose               Enable verbose logging
    --help                  Show this help message
"""

import argparse
import json
import logging.config
import logging.handlers
import pathlib
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple

from dotenv import load_dotenv

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.service.data_update_service import DataUpdateService
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    config_file = pathlib.Path(__file__).parent.parent / "config" / "stdout.json"

    if config_file.exists():
        with open(config_file) as f_in:
            config = json.load(f_in)

        # Adjust log level if verbose
        if verbose:
            if "root" in config:
                config["root"]["level"] = "DEBUG"
            if "loggers" in config and "root" in config["loggers"]:
                config["loggers"]["root"]["level"] = "DEBUG"
            for handler in config["handlers"].values():
                if "level" in handler:
                    handler["level"] = "DEBUG"

        logging.config.dictConfig(config)
    else:
        # Fallback to basic config if json config not found
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


def get_previous_trading_day(reference_date: Optional[datetime] = None) -> datetime:
    """
    Get the previous trading day from the reference date.

    Trading days are Monday-Friday, excluding weekends.
    TODO: Add holiday handling for US market holidays.

    Args:
        reference_date: Date to calculate from (default: today)

    Returns:
        Previous trading day as datetime
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Start with yesterday
    target_date = reference_date - timedelta(days=1)

    # If it's a weekend, go back to Friday
    while target_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
        target_date -= timedelta(days=1)

    return target_date


def validate_update_success(
    data_updater: DataUpdateService, start_date: datetime, end_date: datetime
) -> bool:
    """
    Validate that the data update was successful.

    Args:
        data_updater: DataUpdateService instance
        start_date: Start date that was updated
        end_date: End date that was updated

    Returns:
        True if validation passes, False otherwise
    """
    try:
        # Get symbol count
        symbol_list = data_updater.symbol_repo.get_symbol_list("USA")
        total_symbols = len(symbol_list)

        if total_symbols == 0:
            logger.error("No symbols found in database")
            return False

        logger.info(f"Validation: Found {total_symbols} symbols to check")

        # Sample a few symbols to verify data exists for date range
        sample_symbols = symbol_list[:5]  # Check first 5 symbols
        successful_updates = 0

        for symbol_rec in sample_symbols:
            try:
                bars = data_updater.bars_history.get_bars_history(
                    symbol_rec.symbol, start_date, end_date
                )
                if bars:
                    successful_updates += 1
                    logger.debug(
                        f"✓ Data found for {symbol_rec.symbol} from {start_date.date()} to {end_date.date()}"
                    )
                else:
                    logger.warning(
                        f"✗ No data for {symbol_rec.symbol} from {start_date.date()} to {end_date.date()}"
                    )
            except Exception as e:
                logger.warning(f"✗ Error checking {symbol_rec.symbol}: {e}")

        success_rate = successful_updates / len(sample_symbols)
        logger.info(
            f"Validation: {successful_updates}/{len(sample_symbols)} sample symbols have data ({success_rate:.1%})"
        )

        # Consider successful if at least 80% of sampled symbols have data
        return success_rate >= 0.8

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return False


def parse_and_validate_dates(args: 'argparse.Namespace') -> Tuple[datetime, datetime]:
    """
    Parse and validate start and end dates from command line arguments.

    Args:
        args: Parsed command line arguments with required start_date

    Returns:
        Tuple of (start_date, end_date) as datetime objects

    Raises:
        SystemExit: If date validation fails
    """
    start_date = None
    end_date = None

    # Parse required start-date parameter
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD")
        sys.exit(1)

    # Parse optional end-date parameter
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        end_date = start_date
        logger.info(f"Using same date as end date: {end_date.date()}")

    # Validate date range
    if start_date > end_date:
        logger.error("Start date cannot be after end date")
        sys.exit(1)

    if start_date == end_date:
        logger.info(f"Updating single date: {start_date.date()}")
    else:
        logger.info(f"Updating date range: {start_date.date()} to {end_date.date()}")

    return start_date, end_date


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Update database with daily EOD stock data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date for update range (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for update range (YYYY-MM-DD format). Default: same as start-date",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    return parser


def main() -> int:
    """Main entry point for daily EOD update."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load environment variables
    load_dotenv()

    logger.info("Starting daily EOD database update")

    try:
        # Parse and validate dates
        start_date, end_date = parse_and_validate_dates(args)

        # Dry run mode
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual updates will be performed")

            # Initialize data updater to get symbol count
            data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
            symbol_list = data_updater.symbol_repo.get_symbol_list("USA")

            if start_date == end_date:
                logger.info(
                    f"Would update {len(symbol_list)} symbols for date: {start_date.date()}"
                )
            else:
                logger.info(
                    f"Would update {len(symbol_list)} symbols from {start_date.date()} to {end_date.date()}"
                )
            logger.info("Dry run complete - no data was actually updated")
            return 0

        # Actual update
        logger.info("Initializing data updater...")
        data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)

        logger.info(
            f"Starting bars history update from {start_date.date()} to {end_date.date()}"
        )

        update_start_time = datetime.now()

        # Update bars history for the date range
        data_updater.update_bars_history(start_date, end_date)

        update_end_time = datetime.now()
        duration = update_end_time - update_start_time

        logger.info(f"Update completed in {duration.total_seconds():.1f} seconds")

        # Validate the update
        logger.info("Validating update success...")
        if validate_update_success(data_updater, end_date, end_date):
            logger.info("✓ Daily EOD update completed successfully")
            return 0
        else:
            logger.error("✗ Daily EOD update validation failed")
            return 1

    except KeyboardInterrupt:
        logger.warning("Update interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Update failed with error: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
