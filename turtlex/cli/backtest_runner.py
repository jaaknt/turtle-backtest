#!/usr/bin/env python3
"""
Backtest Script

This script runs a complete signal-to-exit backtest using the BacktestService class,
combining signal generation with exit strategy processing across one or more tickers.

Usage:
    uv run backtest-runner [options]

Options:
    --start-date YYYY-MM-DD  Start date for analysis (required for count mode)
    --end-date YYYY-MM-DD    End date for analysis (required for count mode)
    --tickers TICKER         Comma-separated list of specific tickers to test
    --trading-strategy STRATEGY      Trading strategy: darvas_box, mars, momentum, qullamaggie (default: darvas_box)
    --exit-strategy STRATEGY         Exit strategy: buy_and_hold, profit_loss, ema, macd, atr,
                                     trailing_percentage_loss (default: buy_and_hold)
    --exit-param KEY=VALUE    Override an exit-strategy parameter, e.g. --exit-param
                              profit_target=15 (repeatable)
    --max-holding-days NUM    Maximum calendar days a position may stay open (default: 60)
    --ranking-strategy STRATEGY      Ranking strategy: momentum, volume_momentum, breakout_quality, qullamaggie (default: momentum)
    --trading-param KEY=VALUE Override a trading-strategy constructor parameter, e.g.
                              --trading-param sma_thresh=0.20 (repeatable)
    --max-tickers NUM        Maximum number of tickers to test (default: 10000)
    --mode MODE              Analysis mode: list (default: list)
    --verbose                Enable verbose logging
    --help                   Show this help message
"""

import argparse
import logging
import sys

from turtlex.backtest.processor import SignalProcessor
from turtlex.cli.common import build_common_analysis_parser, resolve_trading_strategy, run_cli
from turtlex.common.cli import key_value_type
from turtlex.config.logging import setup_logging
from turtlex.config.settings import Settings
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.backtest_service import BacktestService
from turtlex.strategy.factory import EXIT_STRATEGIES, get_exit_strategy, resolve_exit_strategy_kwargs

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Run trading strategy analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        parents=[build_common_analysis_parser()],
    )

    parser.add_argument(
        "--tickers",
        nargs="*",  # Zero or more arguments
        help="Stock ticker symbols",
    )

    parser.add_argument(
        "--exit-strategy",
        type=str,
        default="buy_and_hold",
        choices=list(EXIT_STRATEGIES),
        help="Exit strategy to use (default: buy_and_hold)",
    )

    parser.add_argument(
        "--exit-param",
        action="append",
        default=[],
        type=key_value_type,
        metavar="KEY=VALUE",
        help="Override an exit-strategy parameter, e.g. --exit-param profit_target=15 (repeatable)",
    )

    parser.add_argument(
        "--max-holding-days",
        type=int,
        default=60,
        help="Maximum calendar days a position may stay open (default: 60)",
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

    return parser


def main() -> int:
    """Main entry point for strategy runner."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging before loading settings so the DB connection log is visible
    setup_logging(args.verbose)
    settings = Settings.from_toml()

    logger.info(f"Starting strategy analysis with {args.trading_strategy} strategy")

    def body() -> int:
        # Parse and validate dates
        start_date, end_date = (args.start_date, args.end_date)

        # Get the trading strategy first (we need it for service initialization)
        try:
            trading_strategy, bars_history = resolve_trading_strategy(args, settings)
            exit_strategy = get_exit_strategy(args.exit_strategy, bars_history)
            exit_strategy_kwargs = resolve_exit_strategy_kwargs(exit_strategy, args.exit_param)
        except ValueError as e:
            logger.error(str(e))
            return 1

        # Initialize strategy runner with the trading strategy
        logger.info("Initializing strategy runner...")
        symbol_repo = TickerQueryRepository(settings.engine)
        signal_processor = SignalProcessor(
            max_holding_period=args.max_holding_days,
            bars_history=bars_history,
            exit_strategy=exit_strategy,
            benchmark_tickers=["SPY.US", "QQQ.US"],
            exit_strategy_kwargs=exit_strategy_kwargs,
        )
        backtest_service = BacktestService(trading_strategy=trading_strategy, signal_processor=signal_processor, symbol_repo=symbol_repo)

        # Run analysis based on mode
        if args.mode == "list":
            backtest_service.run(start_date, end_date, args.tickers, max_tickers=args.max_tickers)

        logger.info("Backtest analysis completed successfully")
        return 0

    return run_cli(args, body)


if __name__ == "__main__":
    sys.exit(main())
