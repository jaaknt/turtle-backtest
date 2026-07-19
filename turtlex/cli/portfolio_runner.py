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

from turtlex.common.cli import iso_date_type
from turtlex.common.enums import TimeFrameUnit
from turtlex.config.logging import LogConfig
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.portfolio_service import PortfolioService
from turtlex.strategy.factory import (
    EXIT_STRATEGIES,
    RANKING_STRATEGIES,
    TRADING_STRATEGIES,
    get_exit_strategy,
    get_ranking_strategy,
    get_trading_strategy,
)

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="Run portfolio backtest analysis")

    # Required arguments
    parser.add_argument(
        "--start-date",
        type=iso_date_type,
        required=True,
        help="Start date for backtest (YYYY-MM-DD format)",
    )

    parser.add_argument(
        "--end-date",
        type=iso_date_type,
        required=True,
        help="End date for backtest (YYYY-MM-DD format)",
    )

    # Strategy arguments
    parser.add_argument(
        "--trading-strategy",
        type=str,
        default="darvas_box",
        choices=list(TRADING_STRATEGIES),
        help="Trading strategy to use (default: darvas_box)",
    )

    parser.add_argument(
        "--exit-strategy",
        type=str,
        default="buy_and_hold",
        choices=list(EXIT_STRATEGIES),
        help="Exit strategy to use (default: buy_and_hold)",
    )

    parser.add_argument(
        "--ranking-strategy",
        type=str,
        default="momentum",
        choices=list(RANKING_STRATEGIES),
        help="Ranking strategy to use (default: momentum)",
    )

    # Portfolio configuration arguments
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=30000.0,
        help="Starting capital amount (default: 30000.0)",
    )

    parser.add_argument(
        "--position-min-amount",
        type=float,
        default=1500.0,
        help="Minimum position size (default: 1500.0)",
    )

    parser.add_argument(
        "--position-max-amount",
        type=float,
        default=3000.0,
        help="Maximum position size (default: 3000.0)",
    )

    parser.add_argument(
        "--min-signal-ranking",
        type=int,
        default=70,
        help="Minimum signal ranking threshold (default: 70)",
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
        "--benchmark-tickers",
        nargs="*",
        default=["SPY", "QQQ"],
        help="Benchmark ticker symbols (default: SPY QQQ)",
    )

    # Output and logging
    parser.add_argument(
        "--output-file",
        type=str,
        help="Optional HTML tearsheet filename (saved in reports/ folder)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    return parser


# Note: Results display and export now handled by PortfolioAnalytics.generate_results()
# which prints performance summary and generates HTML tearsheet reports


def main() -> int:
    """Main entry point for portfolio runner."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    LogConfig.setup(args.verbose)

    logger.info(f"Starting portfolio backtest with {args.trading_strategy} trading strategy and {args.exit_strategy} exit strategy")

    try:
        # Load settings
        settings = Settings.from_toml()

        # Create bars history repository
        bars_history = DailyBarsQueryRepository(engine=settings.engine)

        # Create strategy instances
        ranking_strategy = get_ranking_strategy(args.ranking_strategy)
        trading_strategy = get_trading_strategy(args.trading_strategy, ranking_strategy, bars_history)
        exit_strategy = get_exit_strategy(args.exit_strategy, bars_history)

        # Initialize portfolio service
        logger.info("Initializing portfolio service...")
        portfolio_service = PortfolioService(
            trading_strategy=trading_strategy,
            exit_strategy=exit_strategy,
            bars_history=bars_history,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.initial_capital,
            position_min_amount=args.position_min_amount,
            position_max_amount=args.position_max_amount,
            min_signal_ranking=args.min_signal_ranking,
            time_frame_unit=TimeFrameUnit.DAY,
            max_holding_period=args.max_holding_days,
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

    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("Backtest interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Backtest failed with error: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
