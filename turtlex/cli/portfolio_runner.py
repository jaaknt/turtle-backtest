#!/usr/bin/env python3
"""
Portfolio Runner

Runs portfolio backtests using the PortfolioService class with configurable
trading strategies, exit strategies, and portfolio parameters. Run with
``--help`` for the full option list.

Usage:
    uv run portfolio-runner [options]

Examples:
    # Basic portfolio backtest
    uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31

    # Advanced backtest with custom parameters
    uv run portfolio-runner \
        --start-date 2024-01-01 --end-date 2024-12-31 \
        --trading-strategy mars --exit-strategy profit_loss \
        --initial-capital 50000 --min-signal-ranking 80 \
        --output-file results.html --verbose

    # Test specific tickers
    uv run portfolio-runner \
        --start-date 2024-01-01 --end-date 2024-12-31 \
        --tickers AAPL MSFT GOOGL --verbose
"""

import argparse
import logging
import sys

from turtlex.cli.common import build_common_analysis_parser, log_parameters, resolve_trading_strategy, run_cli
from turtlex.common.cli import key_value_type
from turtlex.common.enums import TimeFrameUnit
from turtlex.config.logging import setup_logging
from turtlex.config.settings import Settings
from turtlex.portfolio.analytics import DEFAULT_BENCHMARK_TICKER
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.portfolio_service import PortfolioService
from turtlex.strategy.factory import EXIT_STRATEGIES, describe_exit_parameters, get_exit_strategy, resolve_exit_strategy_kwargs

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="Run portfolio backtest analysis", parents=[build_common_analysis_parser()])

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
        help="Override an exit-strategy parameter, e.g. --exit-param holding_days=365 (repeatable)",
    )

    # Portfolio configuration arguments
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=30000.0,
        help="Starting capital amount (default: 30000.0)",
    )

    parser.add_argument(
        "--position-size-pct",
        type=float,
        default=0.04,
        help="Fraction of portfolio value committed per position, so size compounds with the portfolio (default: 0.04 = 4%%)",
    )

    parser.add_argument(
        "--min-signal-ranking",
        type=int,
        default=40,
        help="Minimum signal ranking threshold (default: 40)",
    )

    parser.add_argument(
        "--max-tickers",
        type=int,
        default=10000,
        help="Maximum number of tickers to test (default: 10000)",
    )

    parser.add_argument(
        "--max-holding-days",
        type=int,
        default=365,
        help="Maximum calendar days a position may stay open (default: 365)",
    )

    # Optional ticker list
    parser.add_argument(
        "--tickers",
        nargs="*",
        help="Specific ticker symbols to test",
    )

    parser.add_argument(
        "--benchmark-ticker",
        type=str,
        default=DEFAULT_BENCHMARK_TICKER,
        help=f"Symbol the tearsheet compares the portfolio against; quantstats takes exactly one (default: {DEFAULT_BENCHMARK_TICKER})",
    )

    # Output
    parser.add_argument(
        "--output-file",
        type=str,
        help="Optional HTML tearsheet filename (saved in reports/ folder)",
    )

    return parser


# Note: Results display and export now handled by PortfolioAnalytics.generate_results()
# which prints performance summary and generates HTML tearsheet reports


def main() -> int:
    """Main entry point for portfolio runner."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging before loading settings so the DB connection log is visible
    setup_logging(args.verbose)
    settings = Settings.from_toml()

    logger.info(f"Starting portfolio backtest with {args.trading_strategy} trading strategy and {args.exit_strategy} exit strategy")
    log_parameters("CLI arguments", vars(args))

    def body() -> int:
        try:
            trading_strategy, bars_history = resolve_trading_strategy(args, settings)
            exit_strategy = get_exit_strategy(args.exit_strategy, bars_history)
            exit_strategy_kwargs = resolve_exit_strategy_kwargs(exit_strategy, args.exit_param)
        except ValueError as e:
            logger.error(f"Invalid configuration: {e}")
            return 1

        log_parameters(f"{args.exit_strategy} exit parameters", describe_exit_parameters(exit_strategy, exit_strategy_kwargs))

        # Initialize portfolio service
        logger.info("Initializing portfolio service...")
        portfolio_service = PortfolioService(
            trading_strategy=trading_strategy,
            exit_strategy=exit_strategy,
            bars_history=bars_history,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.initial_capital,
            position_size_pct=args.position_size_pct,
            min_signal_ranking=args.min_signal_ranking,
            time_frame_unit=TimeFrameUnit.DAY,
            max_holding_period=args.max_holding_days,
            benchmark_ticker=args.benchmark_ticker,
            exit_strategy_kwargs=exit_strategy_kwargs,
        )

        # Determine universe of stocks to test
        if args.tickers:
            universe = args.tickers
            logger.info(f"Using specific tickers: {', '.join(universe)}")
        else:
            # each strategy defines its own universe (symbol group or custom query)
            universe = trading_strategy.get_universe(TickerQueryRepository(settings.engine), limit=args.max_tickers)
            logger.info(f"Using {len(universe)} tickers from strategy universe")

        # Run the backtest (now prints results and generates tearsheet automatically)
        logger.info(f"Running portfolio backtest from {args.start_date} to {args.end_date}")
        portfolio_service.run_backtest(
            start_date=args.start_date,
            end_date=args.end_date,
            universe=universe,
            output_file=args.output_file,  # HTML tearsheet output file
        )

        logger.info("Portfolio backtest completed successfully")
        return 0

    return run_cli(args, body)


if __name__ == "__main__":
    sys.exit(main())
