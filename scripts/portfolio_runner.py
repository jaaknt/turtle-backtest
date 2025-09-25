#!/usr/bin/env python3
"""
Portfolio Runner Script

This script runs portfolio backtests using the PortfolioService class with configurable
trading strategies, exit strategies, and portfolio parameters.

Usage:
    python scripts/portfolio_runner.py [options]

Options:
    --start-date YYYY-MM-DD          Start date for backtest (required)
    --end-date YYYY-MM-DD            End date for backtest (required)
    --trading-strategy STRATEGY      Trading strategy: darvas_box, mars, momentum (default: darvas_box)
    --exit-strategy STRATEGY         Exit strategy: buy_and_hold, profit_loss, ema, macd, atr (default: buy_and_hold)
    --ranking-strategy STRATEGY      Ranking strategy: momentum, volume_weighted_technical (default: momentum)
    --initial-capital NUM            Starting capital amount (default: 30000.0)
    --position-min-amount NUM        Minimum position size (default: 1500.0)
    --position-max-amount NUM        Maximum position size (default: 3000.0)
    --min-signal-ranking NUM         Minimum signal ranking threshold (default: 70)
    --max-tickers NUM                Maximum number of tickers to test (default: 10000)
    --tickers TICKER [TICKER ...]    Specific tickers to test (optional)
    --benchmark-tickers TICKER [TICKER ...] Custom benchmark tickers (default: SPY QQQ)
    --output-file FILE               Optional CSV output file for results
    --verbose                        Enable verbose logging
    --help                           Show this help message

Examples:
    # Basic portfolio backtest
    python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31

    # Advanced backtest with custom parameters
    python scripts/portfolio_runner.py \
        --start-date 2024-01-01 --end-date 2024-12-31 \
        --trading-strategy mars --exit-strategy profit_loss \
        --initial-capital 50000 --min-signal-ranking 80 \
        --output-file results.csv --verbose

    # Test specific tickers
    python scripts/portfolio_runner.py \
        --start-date 2024-01-01 --end-date 2024-12-31 \
        --tickers AAPL MSFT GOOGL --verbose
"""

import argparse
import csv
import logging
import pathlib
import sys
from datetime import datetime

# Add project root to path to import turtle modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from turtle.config.logging import LogConfig
from turtle.config.settings import Settings
from turtle.common.enums import TimeFrameUnit
from turtle.data.bars_history import BarsHistoryRepo
from turtle.service.portfolio_service import PortfolioService
from turtle.signal.base import TradingStrategy
from turtle.signal.darvas_box import DarvasBoxStrategy
from turtle.signal.mars import MarsStrategy
from turtle.signal.momentum import MomentumStrategy
from turtle.exit.base import ExitStrategy
from turtle.exit.buy_and_hold import BuyAndHoldExitStrategy
from turtle.exit.profit_loss import ProfitLossExitStrategy
from turtle.exit.ema import EMAExitStrategy
from turtle.exit.macd import MACDExitStrategy
from turtle.exit.atr import ATRExitStrategy
from turtle.ranking.base import RankingStrategy
from turtle.ranking.momentum import MomentumRanking
from turtle.ranking.volume_weighted_technical import VolumeWeightedTechnicalRanking
from turtle.portfolio.models import PortfolioResults

logger = logging.getLogger(__name__)


def _get_trading_strategy(strategy_name: str, ranking_strategy: RankingStrategy, bars_history: BarsHistoryRepo) -> TradingStrategy:
    """Create trading strategy instance by name."""
    strategy_classes = {
        "darvas_box": DarvasBoxStrategy,
        "mars": MarsStrategy,
        "momentum": MomentumStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available_strategies = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown trading strategy '{strategy_name}'. Available strategies: {available_strategies}")

    return strategy_class(
        bars_history=bars_history,
        ranking_strategy=ranking_strategy,
        time_frame_unit=TimeFrameUnit.DAY,
        warmup_period=730,
    )


def _get_exit_strategy(strategy_name: str, bars_history: BarsHistoryRepo) -> ExitStrategy:
    """Create exit strategy instance by name."""
    strategy_classes = {
        "buy_and_hold": BuyAndHoldExitStrategy,
        "profit_loss": ProfitLossExitStrategy,
        "ema": EMAExitStrategy,
        "macd": MACDExitStrategy,
        "atr": ATRExitStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available_strategies = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown exit strategy '{strategy_name}'. Available strategies: {available_strategies}")

    return strategy_class(bars_history=bars_history)


def _get_ranking_strategy(strategy_name: str) -> RankingStrategy:
    """Create ranking strategy instance by name."""
    strategy_classes = {
        "momentum": MomentumRanking,
        "volume_weighted_technical": VolumeWeightedTechnicalRanking,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available_strategies = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown ranking strategy '{strategy_name}'. Available strategies: {available_strategies}")

    return strategy_class()


def iso_date_type(date_string: str) -> datetime:
    """Custom argparse type for ISO date validation."""
    try:
        return datetime.fromisoformat(date_string)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Expected ISO format (YYYY-MM-DD)") from err


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Run portfolio backtest analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

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
        choices=["momentum", "volume_weighted_technical"],
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
        help="Optional CSV output file for results",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    return parser


def export_results_to_csv(results: PortfolioResults, filename: str) -> None:
    """Export portfolio results to CSV file."""
    try:
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(["Metric", "Value"])

            # Write key metrics
            writer.writerow(["Total Trades", results.total_trades])
            writer.writerow(["Total Return %", f"{results.total_return_pct:.2f}"])
            writer.writerow(["Win Rate %", f"{results.win_rate:.1f}"])
            writer.writerow(["Average Win %", f"{results.avg_win_pct:.2f}"])
            writer.writerow(["Average Loss %", f"{results.avg_loss_pct:.2f}"])
            writer.writerow(["Max Drawdown %", f"{results.max_drawdown_pct:.2f}"])
            writer.writerow(["Sharpe Ratio", f"{results.sharpe_ratio:.2f}"])
            writer.writerow(["Total Return $", f"{results.total_return_dollars:.2f}"])

        logger.info(f"Results exported to {filename}")

    except Exception as e:
        logger.error(f"Failed to export results to CSV: {e}")


def display_results(results: PortfolioResults) -> None:
    """Display portfolio backtest results in a formatted way."""
    print("\n" + "=" * 60)
    print("PORTFOLIO BACKTEST RESULTS")
    print("=" * 60)

    print(f"📊 Total Trades: {results.total_trades}")
    print(f"💰 Total Return: {results.total_return_pct:.2f}% (${results.total_return_dollars:,.2f})")
    print(f"🎯 Win Rate: {results.win_rate:.1f}%")
    print(f"📈 Average Win: {results.avg_win_pct:.2f}%")
    print(f"📉 Average Loss: {results.avg_loss_pct:.2f}%")
    print(f"⬇️  Max Drawdown: {results.max_drawdown_pct:.2f}%")
    print(f"📏 Sharpe Ratio: {results.sharpe_ratio:.2f}")

    print("=" * 60)


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
        bars_history = BarsHistoryRepo(
            pool=settings.pool,
            alpaca_api_key=settings.app.alpaca["api_key"],
            alpaca_api_secret=settings.app.alpaca["secret_key"],
        )

        # Create strategy instances
        ranking_strategy = _get_ranking_strategy(args.ranking_strategy)
        trading_strategy = _get_trading_strategy(args.trading_strategy, ranking_strategy, bars_history)
        exit_strategy = _get_exit_strategy(args.exit_strategy, bars_history)

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
        )

        # Determine universe of stocks to test
        if args.tickers:
            universe = args.tickers
            logger.info(f"Using specific tickers: {', '.join(universe)}")
        else:
            from turtle.service.signal_service import SignalService

            signal_service = SignalService(
                pool=settings.pool,
                app_config=settings.app,
                trading_strategy=trading_strategy,
                time_frame_unit=TimeFrameUnit.DAY,
            )
            universe = signal_service.get_symbol_list(max_symbols=args.max_tickers)
            logger.info(f"Using {len(universe)} tickers from symbol database")

        # Run the backtest
        logger.info(f"Running portfolio backtest from {args.start_date.date()} to {args.end_date.date()}")
        results = portfolio_service.run_backtest(
            start_date=args.start_date,
            end_date=args.end_date,
            universe=universe,
            benchmark_tickers=args.benchmark_tickers,
        )

        # Display results
        display_results(results)

        # Export to CSV if requested
        if args.output_file:
            export_results_to_csv(results, args.output_file)

        logger.info("Portfolio backtest completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("Backtest interrupted by user")
        return 1
    # except Exception as e:
    #    logger.error(f"Backtest failed with error: {e}")
    #    if args.verbose:
    #        logger.exception("Full error details:")
    #    return 1


if __name__ == "__main__":
    sys.exit(main())
