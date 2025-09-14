#!/usr/bin/env python3
"""
Backtest Script

This script runs trading strategy analysis using the SignalService class.
It can get ticker lists, ticker counts, check individual ticker signals, or count signals
for specific tickers using different trading strategies.

Usage:
    python scripts/signal_runner.py [options]

Options:
    --start-date YYYY-MM-DD  Start date for analysis (required for count mode)
    --end-date YYYY-MM-DD    End date for analysis (required for count mode)
    --tickers TICKER         Comma-separated list of specific tickers to test
    --trading-strategy STRATEGY      Trading strategy: darvas_box, mars, momentum (default: darvas_box)
    --exit-strategy STRATEGY         Exit strategy: buy_and_hold, profit_loss, ema, macd, atr (default: buy_and_hold)
    --ranking-strategy STRATEGY      Ranking strategy: momentum (default: momentum)
    --max-tickers NUM        Maximum number of tickers to test (default: 10000)
    --mode MODE              Analysis mode: list (default: list)
    --verbose                Enable verbose logging
    --help                   Show this help message
"""

import argparse
import logging
import pathlib
import sys
from datetime import datetime

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.config.logging import LogConfig
from turtle.config.settings import Settings

from turtle.backtest.processor import SignalProcessor
from turtle.ranking.ranking_strategy import RankingStrategy
from turtle.service.backtest_service import BacktestService
from turtle.strategy.darvas_box import DarvasBoxStrategy
from turtle.strategy.momentum import MomentumStrategy
from turtle.strategy.mars import MarsStrategy

from turtle.service.signal_service import SignalService
from turtle.common.enums import TimeFrameUnit
from turtle.data.bars_history import BarsHistoryRepo
from turtle.strategy.trading_strategy import TradingStrategy
from turtle.ranking.momentum import MomentumRanking
from turtle.backtest.exit_strategy import (
    ExitStrategy,
    BuyAndHoldExitStrategy,
    EMAExitStrategy,
    ProfitLossExitStrategy,
    MACDExitStrategy,
    ATRExitStrategy,
)

logger = logging.getLogger(__name__)


def _get_trading_strategy(strategy_name: str, ranking_strategy: RankingStrategy, bars_history: BarsHistoryRepo) -> TradingStrategy:
    """Get the trading strategy instance by name."""

    if strategy_name == "darvas_box":
        return DarvasBoxStrategy(
            bars_history=bars_history,
            ranking_strategy=ranking_strategy,
            time_frame_unit=TimeFrameUnit.DAY,
            warmup_period=730,
        )
    elif strategy_name == "mars":
        return MarsStrategy(
            bars_history=bars_history,
            ranking_strategy=ranking_strategy,
            time_frame_unit=TimeFrameUnit.DAY,
            warmup_period=730,
        )
    elif strategy_name == "momentum":
        return MomentumStrategy(
            bars_history=bars_history,
            ranking_strategy=ranking_strategy,
            time_frame_unit=TimeFrameUnit.DAY,
            warmup_period=730,
        )
    else:
        raise ValueError(f"Unknown trading strategy '{strategy_name}'")


def _get_ranking_strategy(strategy_name: str) -> RankingStrategy:
    """Get the ranking strategy instance by name."""
    if strategy_name == "momentum":
        return MomentumRanking()
    else:
        raise ValueError(f"Unknown ranking strategy '{strategy_name}'")


def _get_exit_strategy(strategy_name: str, bars_history: BarsHistoryRepo) -> ExitStrategy:
    """Get the exit strategy instance by name."""
    if strategy_name == "buy_and_hold":
        return BuyAndHoldExitStrategy(bars_history=bars_history)
    elif strategy_name == "profit_loss":
        return ProfitLossExitStrategy(bars_history=bars_history)
    elif strategy_name == "ema":
        return EMAExitStrategy(bars_history=bars_history)
    elif strategy_name == "macd":
        return MACDExitStrategy(bars_history=bars_history)
    elif strategy_name == "atr":
        return ATRExitStrategy(bars_history=bars_history)
    else:
        raise ValueError(f"Unknown exit strategy '{strategy_name}'")


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
        help="Stock ticker symbols",
    )

    parser.add_argument(
        "--trading-strategy",
        type=str,
        default="darvas_box",
        choices=["darvas_box", "mars", "momentum"],
        help="Trading strategy to use (default: darvas_box)",
    )

    parser.add_argument(
        "--exit-strategy",
        type=str,
        default="buy_and_hold",
        choices=["buy_and_hold", "profit_loss", "ema", "macd", "atr"],
        help="Exit strategy to use (default: buy_and_hold)",
    )

    parser.add_argument(
        "--ranking-strategy",
        type=str,
        default="momentum",
        choices=["momentum"],
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

    logger.info(f"Starting strategy analysis with {args.trading_strategy} strategy")

    try:
        # Parse and validate dates
        start_date, end_date = (args.start_date, args.end_date)

        # Get the trading strategy first (we need it for service initialization)
        try:
            # Create database connection and bars_history for strategy

            bars_history = BarsHistoryRepo(
                pool=settings.pool,
                alpaca_api_key=settings.app.alpaca["api_key"],
                alpaca_api_secret=settings.app.alpaca["secret_key"],
            )

            ranking_strategy: RankingStrategy = _get_ranking_strategy(args.ranking_strategy)
            exit_strategy: ExitStrategy = _get_exit_strategy(args.exit_strategy, bars_history)
            trading_strategy: TradingStrategy = _get_trading_strategy(args.trading_strategy, ranking_strategy, bars_history)
        except ValueError as e:
            logger.error(str(e))
            return 1

        # Initialize strategy runner with the trading strategy
        logger.info("Initializing strategy runner...")
        signal_service = SignalService(
            pool=settings.pool, app_config=settings.app, trading_strategy=trading_strategy, time_frame_unit=TimeFrameUnit.DAY
        )
        signal_processor = SignalProcessor(max_holding_period=60, bars_history=signal_service.bars_history, exit_strategy=exit_strategy)
        backtest_service = BacktestService(signal_service=signal_service, signal_processor=signal_processor)

        # Run analysis based on mode
        if args.mode == "list":
            if args.tickers:
                backtest_service.run(start_date, end_date, args.tickers)
            else:
                backtest_service.run(start_date, end_date, None)

        logger.info("Backtest analysis completed successfully")
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
