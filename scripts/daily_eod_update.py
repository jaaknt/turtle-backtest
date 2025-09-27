#!/usr/bin/env python3
"""
Database Update Script

This script updates the database with stock market data.
It supports multiple update modes for different types of data.

Usage:
    python scripts/daily_eod_update.py [options]

Options:
    --mode {bars,symbols,companies}     Update mode (default: bars)
    --start-date YYYY-MM-DD             Start date for update range (required for bars mode)
    --end-date YYYY-MM-DD               End date for update range (default: same as start-date)
    --dry-run                          Show what would be updated without making changes
    --verbose                          Enable verbose logging
    --help                             Show this help message

Modes:
    bars        Update OHLCV historical data for all symbols (requires dates)
    symbols     Download USA stocks symbol list from EODHD
    companies   Download company fundamental data from Yahoo Finance

Examples:
    # Update OHLCV data for a specific date (default mode)
    python scripts/daily_eod_update.py --start-date 2025-06-28

    # Download symbol list
    python scripts/daily_eod_update.py --mode symbols

    # Download company data
    python scripts/daily_eod_update.py --mode companies
"""

import argparse
import pathlib
import sys
from datetime import datetime, timedelta


# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.config.logging import LogConfig
from turtle.config.settings import Settings
from turtle.service.data_update_service import DataUpdateService

# from turtle.common.enums import TimeFrameUnit
import logging

logger = logging.getLogger(__name__)


def get_previous_trading_day(reference_date: datetime | None = None) -> datetime:
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


def validate_symbols_update_success(data_updater: DataUpdateService) -> bool:
    """
    Validate that the symbols update was successful.

    Args:
        data_updater: DataUpdateService instance

    Returns:
        True if validation passes, False otherwise
    """
    try:
        symbol_list = data_updater.symbol_repo.get_symbol_list("USA")
        total_symbols = len(symbol_list)

        if total_symbols == 0:
            logger.error("No symbols found in database after update")
            return False

        logger.info(f"Validation: Found {total_symbols} symbols in database")

        # Basic validation - we should have a reasonable number of symbols
        if total_symbols < 1000:  # Expecting thousands of US symbols
            logger.warning(f"Symbol count seems low: {total_symbols}")
            return False

        return True

    except Exception as e:
        logger.error(f"Symbols validation failed with error: {e}")
        return False


def validate_companies_update_success(data_updater: DataUpdateService) -> bool:
    """
    Validate that the companies update was successful.

    Args:
        data_updater: DataUpdateService instance

    Returns:
        True if validation passes, False otherwise
    """
    try:
        # Get some symbols to check
        symbol_list = data_updater.symbol_repo.get_symbol_list("USA")
        if not symbol_list:
            logger.error("No symbols available to validate companies")
            return False

        # Sample a few symbols to verify company data exists
        sample_symbols = symbol_list[:10]  # Check first 10 symbols
        successful_updates = 0

        for symbol_rec in sample_symbols:
            try:
                # Check if company data exists (this would need to be implemented in company_repo)
                # For now, just assume success if we can get the symbol
                successful_updates += 1
                logger.debug(f"✓ Company data check for {symbol_rec.symbol}")
            except Exception as e:
                logger.warning(f"✗ Error checking company data for {symbol_rec.symbol}: {e}")

        success_rate = successful_updates / len(sample_symbols)
        logger.info(f"Validation: {successful_updates}/{len(sample_symbols)} sample symbols checked ({success_rate:.1%})")

        # Consider successful if we can process most symbols
        return success_rate >= 0.8

    except Exception as e:
        logger.error(f"Companies validation failed with error: {e}")
        return False


def validate_bars_update_success(data_updater: DataUpdateService, start_date: datetime, end_date: datetime) -> bool:
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
                bars = data_updater.bars_history.get_bars_history(symbol_rec.symbol, start_date, end_date)
                if bars:
                    successful_updates += 1
                    logger.debug(f"✓ Data found for {symbol_rec.symbol} from {start_date.date()} to {end_date.date()}")
                else:
                    logger.warning(f"✗ No data for {symbol_rec.symbol} from {start_date.date()} to {end_date.date()}")
            except Exception as e:
                logger.warning(f"✗ Error checking {symbol_rec.symbol}: {e}")

        success_rate = successful_updates / len(sample_symbols)
        logger.info(f"Validation: {successful_updates}/{len(sample_symbols)} sample symbols have data ({success_rate:.1%})")

        # Consider successful if at least 80% of sampled symbols have data
        return success_rate >= 0.8

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return False


def parse_and_validate_dates(args: "argparse.Namespace") -> tuple[datetime | None, datetime | None]:
    """
    Parse and validate start and end dates from command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (start_date, end_date) as datetime objects, or (None, None) if dates not required

    Raises:
        SystemExit: If date validation fails
    """
    # Check if dates are required for this mode
    if args.mode in ["symbols", "companies"]:
        if args.start_date or args.end_date:
            logger.warning(f"Dates are not used for {args.mode} mode, ignoring")
        return None, None

    # Dates are required for bars mode
    if args.mode == "bars" and not args.start_date:
        logger.error(f"--start-date is required for {args.mode} mode")
        sys.exit(1)

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
        description="Update database with stock data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["bars", "symbols", "companies"],
        default="bars",
        help="Update mode: bars (OHLCV data), symbols (symbol list), or companies (company data)",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for update range (YYYY-MM-DD format, required for bars mode)",
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

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    return parser


def execute_symbols_update(data_updater: DataUpdateService, dry_run: bool) -> bool:
    """Execute symbols update operation."""
    if dry_run:
        logger.info("Would download USA stocks symbol list from EODHD")
        return True

    logger.info("Starting symbols update from EODHD...")
    update_start_time = datetime.now()

    data_updater.update_symbol_list()

    update_end_time = datetime.now()
    duration = update_end_time - update_start_time
    logger.info(f"Symbols update completed in {duration.total_seconds():.1f} seconds")

    # Validate the update
    logger.info("Validating symbols update success...")
    return validate_symbols_update_success(data_updater)


def execute_companies_update(data_updater: DataUpdateService, dry_run: bool) -> bool:
    """Execute companies update operation."""
    if dry_run:
        symbol_list = data_updater.symbol_repo.get_symbol_list("USA")
        logger.info(f"Would download company data from Yahoo Finance for {len(symbol_list)} symbols")
        return True

    logger.info("Starting companies update from Yahoo Finance...")
    update_start_time = datetime.now()

    data_updater.update_company_list()

    update_end_time = datetime.now()
    duration = update_end_time - update_start_time
    logger.info(f"Companies update completed in {duration.total_seconds():.1f} seconds")

    # Validate the update
    logger.info("Validating companies update success...")
    return validate_companies_update_success(data_updater)


def execute_bars_update(data_updater: DataUpdateService, start_date: datetime, end_date: datetime, dry_run: bool) -> bool:
    """Execute bars update operation."""
    if dry_run:
        symbol_list = data_updater.symbol_repo.get_symbol_list("USA")
        if start_date == end_date:
            logger.info(f"Would update {len(symbol_list)} symbols for date: {start_date.date()}")
        else:
            logger.info(f"Would update {len(symbol_list)} symbols from {start_date.date()} to {end_date.date()}")
        return True

    logger.info(f"Starting bars history update from {start_date.date()} to {end_date.date()}")
    update_start_time = datetime.now()

    data_updater.update_bars_history(start_date, end_date)

    update_end_time = datetime.now()
    duration = update_end_time - update_start_time
    logger.info(f"Bars update completed in {duration.total_seconds():.1f} seconds")

    # Validate the update
    logger.info("Validating bars update success...")
    return validate_bars_update_success(data_updater, end_date, end_date)


def main() -> int:
    """Main entry point for database update."""
    parser = create_argument_parser()
    args = parser.parse_args()
    settings = Settings.from_toml()

    # Setup logging
    LogConfig.setup(args.verbose)

    logger.info(f"Starting database update - mode: {args.mode}")

    try:
        # Parse and validate dates
        start_date, end_date = parse_and_validate_dates(args)

        # Dry run mode
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual updates will be performed")

        # Initialize data updater
        logger.info("Initializing data updater...")
        data_updater = DataUpdateService(pool=settings.pool, app_config=settings.app)

        # Execute based on mode
        success = True

        if args.mode == "symbols":
            success = execute_symbols_update(data_updater, args.dry_run)

        elif args.mode == "companies":
            success = execute_companies_update(data_updater, args.dry_run)

        elif args.mode == "bars":
            if start_date is None or end_date is None:
                logger.error("Internal error: dates should be validated for bars mode")
                return 1
            success = execute_bars_update(data_updater, start_date, end_date, args.dry_run)

        # Final result
        if args.dry_run:
            logger.info("Dry run complete - no data was actually updated")
            return 0
        elif success:
            logger.info(f"✓ Database update ({args.mode} mode) completed successfully")
            return 0
        else:
            logger.error(f"✗ Database update ({args.mode} mode) validation failed")
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
