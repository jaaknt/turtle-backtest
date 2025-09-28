#!/usr/bin/env python3
"""
Signal Runner Script

This script runs trading strategy analysis using the SignalService class.
It can get ticker lists, ticker counts, check individual ticker signals, or count signals
for specific tickers using different trading strategies.

Usage:
    python scripts/signal_runner.py [options]

Options:
    --start-date YYYY-MM-DD      Start date for analysis (required for count mode)
    --end-date YYYY-MM-DD        End date for analysis (required for count mode)
    --tickers TICKER             Space separated list of specific tickers to test
    --trading-strategy STRATEGY  Trading strategy: darvas_box, mars, momentum (default: darvas_box)
    --ranking-strategy STRATEGY  Ranking strategy: momentum, volume_momentum (default: momentum)
    --max-tickers NUM            Maximum number of tickers to test (default: 10000)
    --mode MODE                  Analysis mode: signal, list, top (default: signal)
    --verbose                    Enable verbose logging
    --help                       Show this help message
"""

import argparse
import pathlib
import sys
import logging
from datetime import datetime
from psycopg_pool import ConnectionPool

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.config.model import AppConfig
from turtle.config.logging import LogConfig
from turtle.config.settings import Settings
from turtle.common.enums import TimeFrameUnit
from turtle.data.bars_history import BarsHistoryRepo
from turtle.ranking.momentum import MomentumRanking
from turtle.ranking.volume_momentum import VolumeMomentumRanking
from turtle.ranking.base import RankingStrategy
from turtle.service.signal_service import SignalService
from turtle.signal.base import TradingStrategy

logger = logging.getLogger(__name__)


def get_ranking_strategy_instance(ranking_name: str) -> RankingStrategy:
    """Create and return a ranking strategy instance by name."""
    ranking_classes: dict[str, type[RankingStrategy]] = {
        "momentum": MomentumRanking,
        "volume_momentum": VolumeMomentumRanking,
    }

    ranking_class = ranking_classes.get(ranking_name.lower())
    if ranking_class is None:
        available_rankings = ", ".join(ranking_classes.keys())
        raise ValueError(f"Unknown ranking strategy '{ranking_name}'. Available strategies: {available_rankings}")

    return ranking_class()


def get_trading_strategy_instance(
    strategy_name: str, ranking_strategy: RankingStrategy, pool: ConnectionPool, app: AppConfig
) -> TradingStrategy:
    """Create and return a trading strategy instance by name."""
    from turtle.signal.darvas_box import DarvasBoxStrategy
    from turtle.signal.mars import MarsStrategy
    from turtle.signal.momentum import MomentumStrategy

    strategy_classes: dict[str, type[TradingStrategy]] = {
        "darvas_box": DarvasBoxStrategy,
        "mars": MarsStrategy,
        "momentum": MomentumStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available_strategies = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available strategies: {available_strategies}")

    # Create BarsHistoryRepo instance for strategy
    bars_history = BarsHistoryRepo(
        pool,
        alpaca_api_key=app.alpaca["api_key"],
        alpaca_api_secret=app.alpaca["secret_key"],
    )

    # Create strategy instance with common parameters
    return strategy_class(
        bars_history=bars_history, ranking_strategy=ranking_strategy, time_frame_unit=TimeFrameUnit.DAY, warmup_period=365
    )


def iso_date_type(date_string: str) -> datetime:
    """Custom argparse type for ISO date validation"""
    try:
        return datetime.fromisoformat(date_string)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Expected ISO format (YYYY-MM-DD)") from err


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
        "--trading-strategy",
        type=str,
        default="darvas_box",
        choices=["darvas_box", "mars", "momentum"],
        help="Trading strategy to use (default: darvas_box)",
    )

    parser.add_argument(
        "--ranking-strategy",
        type=str,
        default="momentum",
        choices=["momentum", "volume_momentum"],
        help="Ranking strategy to use (default: momentum)",
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
    settings = Settings.from_toml()

    # Setup logging
    LogConfig.setup(args.verbose)

    logger.info(f"Starting strategy analysis with {args.trading_strategy} strategy and {args.ranking_strategy} ranking")

    try:
        # Parse and validate dates
        start_date, end_date = (args.start_date, args.end_date)

        # Get the ranking strategy first
        try:
            ranking_strategy = get_ranking_strategy_instance(args.ranking_strategy)
        except ValueError as e:
            logger.error(str(e))
            return 1

        # Get the trading strategy (we need it for service initialization)
        try:
            trading_strategy = get_trading_strategy_instance(args.trading_strategy, ranking_strategy, pool=settings.pool, app=settings.app)
        except ValueError as e:
            logger.error(str(e))
            return 1

        # Initialize strategy runner with the trading strategy
        logger.info("Initializing strategy runner...")
        strategy_runner = SignalService(
            pool=settings.pool, app_config=settings.app, trading_strategy=trading_strategy, time_frame_unit=TimeFrameUnit.DAY
        )

        # Run analysis based on mode
        if args.mode == "list":
            if args.tickers:
                logger.warning("Tickers parameter is ignored in list mode")
            for ticker in strategy_runner.get_symbol_list(max_symbols=args.max_tickers):
                signals = strategy_runner.get_signals(ticker, start_date, end_date)

                if len(signals) > 0:
                    for signal in signals:
                        print(f"  ✓ Signal {ticker} on {signal.date.date()} ranking: {signal.ranking} ")

        elif args.mode == "top":
            logger.info("Getting top 20 signals...")
            signal_list = []
            for ticker in strategy_runner.get_symbol_list(max_symbols=args.max_tickers):
                signal_list.extend(strategy_runner.get_signals(ticker, start_date, end_date))

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
                signals = strategy_runner.get_signals(ticker, start_date, end_date)

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
