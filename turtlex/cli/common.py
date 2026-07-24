"""Shared CLI bootstrap helpers for the analysis runner scripts (backtest_runner, signal_runner)."""

import argparse
import logging
from collections.abc import Callable

from turtlex.common.cli import iso_date_type
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.strategy.factory import RANKING_STRATEGIES, TRADING_STRATEGIES, get_ranking_strategy, get_trading_strategy
from turtlex.strategy.trading.base import TradingStrategy

logger = logging.getLogger(__name__)


def build_common_analysis_parser() -> argparse.ArgumentParser:
    """Build a parent parser (add_help=False) for the --start-date/--end-date/--trading-strategy/
    --ranking-strategy/--verbose flags shared by every analysis CLI."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--start-date",
        type=iso_date_type,
        required=True,
        help="Start date for analysis (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--end-date",
        type=iso_date_type,
        required=True,
        help="End date for analysis (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--trading-strategy",
        type=str,
        default="darvas_box",
        choices=list(TRADING_STRATEGIES),
        help="Trading strategy to use (default: darvas_box)",
    )
    parser.add_argument(
        "--ranking-strategy",
        type=str,
        default="momentum",
        choices=list(RANKING_STRATEGIES),
        help="Ranking strategy to use (default: momentum)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser


def resolve_trading_strategy(args: argparse.Namespace, settings: Settings) -> tuple[TradingStrategy, DailyBarsQueryRepository]:
    """Resolve --ranking-strategy/--trading-strategy into a TradingStrategy and its DailyBarsQueryRepository.

    Args:
        args: Parsed CLI arguments, must have `trading_strategy` and `ranking_strategy`
        settings: Loaded application settings, used for the database engine

    Returns:
        Tuple of (trading_strategy, bars_history)

    Raises:
        ValueError: If either strategy name is unknown
    """
    bars_history = DailyBarsQueryRepository(engine=settings.engine)
    ranking_strategy = get_ranking_strategy(args.ranking_strategy)
    trading_strategy = get_trading_strategy(args.trading_strategy, ranking_strategy, bars_history)
    return trading_strategy, bars_history


def run_cli(args: argparse.Namespace, body: Callable[[], int]) -> int:
    """Run `body`, translating KeyboardInterrupt/unexpected exceptions into the logged-error +
    exit-code-1 behavior shared by the analysis CLIs.

    Args:
        args: Parsed CLI arguments, must have `verbose`
        body: Callable performing the CLI's main work, returning its exit code

    Returns:
        The exit code from `body`, or 1 if it raised KeyboardInterrupt/an unexpected exception
    """
    try:
        return body()
    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Analysis failed with error: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        return 1
