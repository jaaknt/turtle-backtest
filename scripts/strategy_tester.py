#!/usr/bin/env python3
"""
Strategy Performance Testing Script

This script tests trading strategies by analyzing historical signals and calculating
returns over various time periods.

Usage:
    python scripts/strategy_tester.py [options]

Examples:
    # Test DarvasBox strategy for January 2024
    python scripts/strategy_tester.py --strategy darvas_box --start-date 2024-01-01 --end-date 2024-01-31

    # Test Mars strategy with custom periods
    python scripts/strategy_tester.py --strategy mars --start-date 2024-01-01 --end-date 2024-03-31 --periods 5d,2W,3M

    # Test with limited symbols and save to CSV
    python scripts/strategy_tester.py --strategy momentum --start-date 2024-01-01 --end-date 2024-02-29 --max-symbols 50 --output csv --save results.csv

Options:
    --strategy NAME          Strategy to test (darvas_box, mars, momentum) [required]
    --start-date YYYY-MM-DD  Start date for signal generation [required]
    --end-date YYYY-MM-DD    End date for signal generation [required]
    --periods LIST           Test periods (default: 3d,1W,2W,1M,3M,6M)
    --symbols LIST           Comma-separated list of specific symbols to test
    --max-symbols NUM        Maximum number of symbols to test
    --time-frame FRAME       Time frame (DAY, WEEK) [default: DAY]
    --output FORMAT          Output format (console, csv, json) [default: console]
    --save FILENAME          Save results to file
    --verbose                Enable verbose logging
    --dry-run               Show what would be tested without running
    --help                  Show this help message
"""

import argparse
import json
import logging.config
import pathlib
import sys
from datetime import datetime
from typing import List

import pandas as pd
from dotenv import load_dotenv

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.service.strategy_tester import StrategyTesterService
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
            for handler in config.get("handlers", {}).values():
                if isinstance(handler, dict) and "level" in handler:
                    handler["level"] = "DEBUG"

        logging.config.dictConfig(config)
    else:
        # Fallback logging configuration
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


def parse_periods(periods_str: str) -> List[pd.Timedelta]:
    """
    Parse period string into list of pandas Timedelta objects.

    Args:
        periods_str: Comma-separated periods (e.g., "3d,1W,2W,1M")

    Returns:
        List of pandas Timedelta objects
    """
    periods = []

    for period_str in periods_str.split(","):
        period_str = period_str.strip()

        if period_str.endswith("d"):
            days = int(period_str[:-1])
            periods.append(pd.Timedelta(days=days))
        elif period_str.endswith("w") or period_str.endswith("W"):
            weeks = int(period_str[:-1])
            periods.append(pd.Timedelta(weeks=weeks))
        elif period_str.endswith("m") or period_str.endswith("M"):
            months = int(period_str[:-1])
            periods.append(
                pd.Timedelta(days=months * 30)
            )  # Approximate month as 30 days
        else:
            raise ValueError(
                f"Invalid period format: {period_str}. Use format like '3d', '1W', '2W', '1M'"
            )

    return periods


def parse_symbols(symbols_str: str) -> List[str]:
    """Parse comma-separated symbols string."""
    return [symbol.strip().upper() for symbol in symbols_str.split(",")]


def parse_time_frame(time_frame_str: str) -> TimeFrameUnit:
    """Parse time frame string."""
    time_frame_map = {
        "DAY": TimeFrameUnit.DAY,
        "WEEK": TimeFrameUnit.WEEK,
    }

    time_frame_upper = time_frame_str.upper()
    if time_frame_upper not in time_frame_map:
        raise ValueError(f"Invalid time frame: {time_frame_str}. Use DAY or WEEK")

    return time_frame_map[time_frame_upper]


def validate_date(date_str: str) -> datetime:
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test trading strategy performance by analyzing historical signals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Required arguments
    parser.add_argument(
        "--strategy",
        required=True,
        choices=list(StrategyTesterService.AVAILABLE_STRATEGIES.keys()),
        help="Strategy to test",
    )
    parser.add_argument(
        "--start-date",
        required=True,
        type=validate_date,
        help="Start date for signal generation (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        type=validate_date,
        help="End date for signal generation (YYYY-MM-DD)",
    )

    # Optional arguments
    parser.add_argument(
        "--periods", default="3d,1W,2W,1M,3M,6M", help="Test periods (default: 3d,1W,2W,1M,3M,6M)"
    )
    parser.add_argument(
        "--symbols", help="Comma-separated list of specific symbols to test"
    )
    parser.add_argument(
        "--max-symbols", type=int, help="Maximum number of symbols to test"
    )
    parser.add_argument(
        "--time-frame", default="DAY", help="Time frame for analysis (default: DAY)"
    )
    parser.add_argument(
        "--output",
        choices=["console", "csv", "json"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument("--save", help="Save results to file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tested without running",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load environment variables
    load_dotenv()

    try:
        # Parse arguments
        test_periods = parse_periods(args.periods)
        time_frame = parse_time_frame(args.time_frame)
        symbols = parse_symbols(args.symbols) if args.symbols else None

        # Validate date range
        if args.start_date > args.end_date:
            logger.error("Start date must be before or equal to end date")
            sys.exit(1)

        logger.info("Strategy Performance Test Configuration:")
        logger.info(f"  Strategy: {args.strategy}")
        logger.info(
            f"  Signal period: {args.start_date.strftime('%Y-%m-%d')} to {args.end_date.strftime('%Y-%m-%d')}"
        )
        logger.info(f"  Test periods: {[str(p) for p in test_periods]}")
        logger.info(f"  Time frame: {time_frame}")
        if symbols:
            logger.info(f"  Specific symbols: {symbols}")
        if args.max_symbols:
            logger.info(f"  Max symbols: {args.max_symbols}")
        logger.info(f"  Output format: {args.output}")
        if args.save:
            logger.info(f"  Save to: {args.save}")

        if args.dry_run:
            logger.info("Dry run completed - no actual testing performed")
            return

        # Create strategy tester service
        service = StrategyTesterService.from_strategy_name(
            strategy_name=args.strategy,
            signal_start_date=args.start_date,
            signal_end_date=args.end_date,
            test_periods=test_periods,
            time_frame_unit=time_frame,
        )

        # Run the test
        test_summary = service.run_test(symbols=symbols, max_symbols=args.max_symbols)

        # Output results
        if args.save:
            service.save_results(test_summary, args.save, args.output)
        else:
            service.print_results(test_summary, args.output)

        logger.info("Strategy testing completed successfully")

    except KeyboardInterrupt:
        logger.info("Strategy testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Strategy testing failed: {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
