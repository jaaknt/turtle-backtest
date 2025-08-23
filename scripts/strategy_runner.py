#!/usr/bin/env python3
"""
Strategy Runner Script

This script runs trading strategy analysis using the StrategyRunnerService class.
It can get ticker lists, ticker counts, check individual ticker signals, or count signals
for specific tickers using different trading strategies.

Usage:
    python scripts/strategy_runner.py [options]

Options:
    --start-date YYYY-MM-DD  Start date for analysis (required for count mode)
    --end-date YYYY-MM-DD    End date for analysis (required for count mode)
    --tickers TICKER         Comma-separated list of specific tickers to test
    --trading_strategy STRATEGY      Trading strategy: darvas_box, mars, momentum (default: darvas_box)
    --max-tickers NUM        Maximum number of tickers to test (default: 10000)
    --mode MODE              Analysis mode: signal, list, top (default: signal)
    --verbose                Enable verbose logging
    --help                   Show this help message
"""

import argparse
import json
import logging.config
import logging.handlers
import os
import pathlib
import sys
from datetime import datetime

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from psycopg import Connection
from psycopg.rows import TupleRow

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.service.strategy_runner_service import StrategyRunnerService
from turtle.common.enums import TimeFrameUnit
from turtle.data.bars_history import BarsHistoryRepo
from turtle.strategy.trading_strategy import TradingStrategy
from turtle.ranking.momentum import MomentumRanking

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
        logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_trading_strategy_instance(strategy_name: str) -> TradingStrategy:
    """Create and return a trading strategy instance by name."""
    from turtle.strategy.darvas_box import DarvasBoxStrategy
    from turtle.strategy.mars import MarsStrategy
    from turtle.strategy.momentum import MomentumStrategy

    strategy_classes: dict[str, type[TradingStrategy]] = {
        "darvas_box": DarvasBoxStrategy,
        "mars": MarsStrategy,
        "momentum": MomentumStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available_strategies = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available strategies: {available_strategies}")

    # Create database connection and bars_history for strategy
    pool: ConnectionPool[Connection[TupleRow]] = ConnectionPool(
        conninfo="host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres", min_size=5, max_size=50, max_idle=600
    )
    bars_history = BarsHistoryRepo(
        pool,
        str(os.getenv("ALPACA_API_KEY")),
        str(os.getenv("ALPACA_SECRET_KEY")),
    )

    # Create strategy instance with common parameters
    return strategy_class(
        bars_history=bars_history,
        ranking_strategy=MomentumRanking(),
        time_frame_unit=TimeFrameUnit.DAY,
        warmup_period=730,
    )


def get_trading_strategy(strategy_runner: StrategyRunnerService, strategy_name: str) -> TradingStrategy:
    """Create and return a trading strategy instance by name (deprecated - kept for compatibility)."""
    return get_trading_strategy_instance(strategy_name)


def iso_date_type(date_string: str) -> datetime:
    """Custom argparse type for ISO date validation"""
    try:
        return datetime.fromisoformat(date_string)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Expected ISO format (YYYY-MM-DD)") from err


def parse_symbols(symbols_str: str) -> list[str]:
    """Parse comma-separated symbols string."""
    return [symbol.strip().upper() for symbol in symbols_str.split(",")]


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Run trading strategy analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--start-date",
        type=iso_date_type,
        required=True,
        help="Start date for ticker count analysis (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--end-date",
        type=iso_date_type,
        required=True,
        help="End date for ticker count analysis (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--tickers",
        nargs="*",  # Zero or more arguments
        help="Stock ticker symbols (required for signal mode)",
    )

    parser.add_argument(
        "--trading_strategy",
        type=str,
        default="darvas_box",
        choices=["darvas_box", "mars", "momentum"],
        help="Trading strategy to use (default: darvas_box)",
    )

    parser.add_argument("--max-tickers", type=int, default=10000, help="Maximum number of tickers to test")

    parser.add_argument(
        "--mode",
        type=str,
        default="list",
        choices=["list", "signal", "top"],
        help="Analysis mode: list (get tickers list signals), signal (check single ticker signal), "
        "top (get top 20 signals) (default: list)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    return parser


def main() -> int:
    """Main entry point for strategy runner."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load environment variables
    load_dotenv()

    logger.info(f"Starting strategy analysis with {args.trading_strategy} strategy")

    try:
        # Parse and validate dates
        start_date, end_date = (args.start_date, args.end_date)

        # Get the trading strategy first (we need it for service initialization)
        try:
            trading_strategy = get_trading_strategy_instance(args.trading_strategy)
        except ValueError as e:
            logger.error(str(e))
            return 1

        # Initialize strategy runner with the trading strategy
        logger.info("Initializing strategy runner...")
        strategy_runner = StrategyRunnerService(trading_strategy=trading_strategy, time_frame_unit=TimeFrameUnit.DAY)

        # Run analysis based on mode
        if args.mode == "list":
            if args.tickers:
                logger.warning("Tickers parameter is ignored in list mode")
            for ticker in strategy_runner.get_symbol_list(max_symbols=args.max_tickers):
                signals = strategy_runner.get_trading_signals(ticker, start_date, end_date)

                if len(signals) > 0:
                    for signal in signals:
                        print(f"  ✓ Signal {ticker} on {signal.date.date()} ranking: {signal.ranking} ")

        elif args.mode == "top":
            logger.info("Getting top 20 signals...")
            signal_list = []
            for ticker in strategy_runner.get_symbol_list(max_symbols=args.max_tickers):
                signal_list.extend(strategy_runner.get_trading_signals(ticker, start_date, end_date))

            # Flatten the list and get top 20 signals
            if not signal_list:
                top_signals = []
            else:
                top_signals = sorted(signal_list, key=lambda s: s.ranking, reverse=True)[:20]
                for signal in top_signals:
                    print(f"  ✓ Signal {signal.ticker} on {signal.date.date()} ranking: {signal.ranking} ")

        elif args.mode == "signal":
            if not args.tickers:
                logger.error("Tickers is required for signal mode")
                return 1
            for ticker in args.tickers:
                signals = strategy_runner.get_trading_signals(ticker, start_date, end_date)

                if len(signals) > 0:
                    for signal in signals:
                        print(f"  ✓ Signal {ticker} on {signal.date.date()} ranking: {signal.ranking} ")

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
