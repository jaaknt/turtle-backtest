#!/usr/bin/env python3
"""
Strategy Runner Script

This script runs trading strategy analysis using the StrategyRunnerService class.
It can get ticker lists, ticker counts, check individual ticker signals, or count signals for specific tickers using different trading strategies.

Usage:
    python scripts/strategy_runner.py [options]

Options:
    --start-date YYYY-MM-DD  Start date for analysis (required for count mode)
    --end-date YYYY-MM-DD    End date for analysis (required for count mode)
    --date YYYY-MM-DD        Single date for ticker list analysis or signal check
    --ticker TICKER          Stock ticker symbol (required for signal and signal_count modes)
    --strategy STRATEGY      Trading strategy: darvas_box, mars, momentum (default: darvas_box)
    --mode MODE              Analysis mode: list, count, signal, or signal_count (default: list)
    --verbose                Enable verbose logging
    --help                   Show this help message
"""

import argparse
import json
import logging.config
import logging.handlers
import pathlib
import sys
from datetime import datetime
from typing import Optional, Tuple

from dotenv import load_dotenv

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.service.strategy_runner import StrategyRunnerService
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


def get_trading_strategy(strategy_runner: StrategyRunnerService, strategy_name: str):
    """Create and return a trading strategy instance by name."""
    from turtle.strategy.darvas_box import DarvasBoxStrategy
    from turtle.strategy.mars import MarsStrategy
    from turtle.strategy.momentum import MomentumStrategy

    strategy_classes = {
        "darvas_box": DarvasBoxStrategy,
        "mars": MarsStrategy,
        "momentum": MomentumStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available_strategies = ", ".join(strategy_classes.keys())
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. Available strategies: {available_strategies}"
        )

    # Create strategy instance with common parameters
    return strategy_class(
        bars_history=strategy_runner.bars_history,
        time_frame_unit=strategy_runner.time_frame_unit,
        warmup_period=strategy_runner.warmup_period,
    )


def parse_and_validate_dates(
    args,
) -> Tuple[Optional[datetime], Optional[datetime], Optional[datetime]]:
    """
    Parse and validate dates from command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (date, start_date, end_date) as datetime objects

    Raises:
        SystemExit: If date validation fails
    """
    date = None
    start_date = None
    end_date = None

    # Parse single date for list mode
    if args.date:
        try:
            date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Parse start and end dates for count mode
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            logger.error(
                f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD"
            )
            sys.exit(1)

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Validate based on mode
    if args.mode == "list":
        if not date:
            logger.error("List mode requires --date parameter")
            sys.exit(1)
        logger.info(f"List mode: analyzing date {date.date()}")
    elif args.mode == "count":
        if not start_date or not end_date:
            logger.error(
                "Count mode requires both --start-date and --end-date parameters"
            )
            sys.exit(1)
        if start_date > end_date:
            logger.error("Start date cannot be after end date")
            sys.exit(1)
        logger.info(
            f"Count mode: analyzing range {start_date.date()} to {end_date.date()}"
        )
    elif args.mode == "signal":
        if not date:
            logger.error("Signal mode requires --date parameter")
            sys.exit(1)
        if not args.ticker:
            logger.error("Signal mode requires --ticker parameter")
            sys.exit(1)
        logger.info(f"Signal mode: checking {args.ticker} on {date.date()}")
    elif args.mode == "signal_count":
        if not start_date or not end_date:
            logger.error(
                "Signal count mode requires both --start-date and --end-date parameters"
            )
            sys.exit(1)
        if start_date > end_date:
            logger.error("Start date cannot be after end date")
            sys.exit(1)
        if not args.ticker:
            logger.error("Signal count mode requires --ticker parameter")
            sys.exit(1)
        logger.info(
            f"Signal count mode: analyzing {args.ticker} from {start_date.date()} to {end_date.date()}"
        )

    return date, start_date, end_date


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Run trading strategy analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--date",
        type=str,
        help="Single date for ticker list analysis (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for ticker count analysis (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for ticker count analysis (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker symbol (required for signal and signal_count modes)",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default="darvas_box",
        choices=["darvas_box", "mars", "momentum"],
        help="Trading strategy to use (default: darvas_box)",
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="list",
        choices=["list", "count", "signal", "signal_count"],
        help="Analysis mode: list (get tickers for date), count (get ticker counts for range), signal (check single ticker signal), signal_count (get signal count for single ticker) (default: list)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    return parser


def main():
    """Main entry point for strategy runner."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load environment variables
    load_dotenv()

    logger.info(f"Starting strategy analysis with {args.strategy} strategy")

    try:
        # Parse and validate dates
        date, start_date, end_date = parse_and_validate_dates(args)

        # Initialize strategy runner
        logger.info("Initializing strategy runner...")
        strategy_runner = StrategyRunnerService(time_frame_unit=TimeFrameUnit.DAY)

        # Get the trading strategy
        try:
            trading_strategy = get_trading_strategy(strategy_runner, args.strategy)
        except ValueError as e:
            logger.error(str(e))
            return 1

        # Run analysis based on mode
        if args.mode == "list":
            if not date:
                logger.error("List mode requires a valid date")
                return 1

            logger.info(
                f"Getting ticker list for {date.date()} using {args.strategy} strategy"
            )
            ticker_list = strategy_runner.get_tickers_list(date, trading_strategy)

            print(f"\nTicker list for {date.date()} ({args.strategy} strategy):")
            print(f"Found {len(ticker_list)} tickers:")
            for ticker in ticker_list:
                print(f" {ticker['symbol']} (Ranking: {ticker['ranking']})")

            if not ticker_list:
                print("  No tickers found for the specified date and strategy")

        elif args.mode == "count":
            if not start_date or not end_date:
                logger.error("Count mode requires valid start and end dates")
                return 1
            logger.info(
                f"Getting ticker counts from {start_date.date()} to {end_date.date()} using {args.strategy} strategy"
            )
            ticker_counts = strategy_runner.get_tickers_count(
                start_date, end_date, trading_strategy
            )

            print(
                f"\nTicker counts from {start_date.date()} to {end_date.date()} ({args.strategy} strategy):"
            )
            print(f"Found {len(ticker_counts)} tickers with signals:")

            # Sort by count (descending) and display
            sorted_counts = sorted(ticker_counts, key=lambda x: x[1], reverse=True)
            for ticker, count in sorted_counts:
                print(f"  {ticker}: {count} signals")

            if not ticker_counts:
                print(
                    "  No ticker signals found for the specified date range and strategy"
                )

        elif args.mode == "signal":
            if not date or not args.ticker:
                logger.error("Signal mode requires valid date and ticker")
                return 1

            logger.info(
                f"Checking trading signal for {args.ticker} on {date.date()} using {args.strategy} strategy"
            )
            has_signal = strategy_runner.is_trading_signal(
                args.ticker, date, trading_strategy
            )

            print(
                f"\nTrading signal check for {args.ticker} on {date.date()} ({args.strategy} strategy):"
            )
            if has_signal:
                print(f"  ✓ {args.ticker} has a trading signal on {date.date()}")
            else:
                print(
                    f"  ✗ {args.ticker} does NOT have a trading signal on {date.date()}"
                )

        elif args.mode == "signal_count":
            if not start_date or not end_date or not args.ticker:
                logger.error(
                    "Signal count mode requires valid start date, end date, and ticker"
                )
                return 1

            logger.info(
                f"Getting signal count for {args.ticker} from {start_date.date()} to {end_date.date()} using {args.strategy} strategy"
            )
            signal_count = strategy_runner.trading_signals_count(
                args.ticker, start_date, end_date, trading_strategy
            )

            print(
                f"\nSignal count for {args.ticker} from {start_date.date()} to {end_date.date()} ({args.strategy} strategy):"
            )
            print(f"  {args.ticker}: {signal_count} signals")

            if signal_count == 0:
                print(
                    f"  No signals found for {args.ticker} in the specified date range"
                )

        logger.info("Strategy analysis completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Analysis failed with error: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
