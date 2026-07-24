#!/usr/bin/env python3
"""
Signal Runner Script

This script runs trading strategy analysis using the SignalService class.
It can list signals across the strategy's ticker universe, show the top-ranked
signals, or check signals for specific tickers.

Usage:
    uv run signal-runner <command> [options]

Commands:
    list                         List all signals in the strategy's ticker universe
    top                          Show the top-ranked signals (--limit, default 20)
    signal TICKER [TICKER ...]   Check signals for specific tickers

Common options (every command):
    --start-date YYYY-MM-DD      Start date for analysis (required)
    --end-date YYYY-MM-DD        End date for analysis (required)
    --trading-strategy STRATEGY  darvas_box, mars, momentum, qullamaggie (default: darvas_box)
    --ranking-strategy STRATEGY  momentum, volume_momentum, breakout_quality (default: momentum)
    --verbose                    Enable verbose logging

Run `signal-runner <command> --help` for command-specific options.
"""

import argparse
import logging
import sys
import time
from datetime import date

from turtlex.cli.common import build_common_analysis_parser, resolve_trading_strategy, run_cli
from turtlex.config.logging import LogConfig
from turtlex.config.settings import Settings
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.signal_service import SignalService

logger = logging.getLogger(__name__)


def print_signal(ticker: str, signal_date: date, ranking: int) -> None:
    """Print a single signal line in the standard format."""
    print(f"  ✓ Signal {ticker} on {signal_date} ranking: {ranking} ")


def run_list(service: SignalService, args: argparse.Namespace) -> int:
    """List all signals in the strategy's universe, sorted by date and ticker."""
    signals = service.scan(args.start_date, args.end_date, max_tickers=args.max_tickers)
    for signal in sorted(signals, key=lambda s: (s.date, s.ticker)):
        print_signal(signal.ticker, signal.date, signal.ranking)
    return 0


def run_top(service: SignalService, args: argparse.Namespace) -> int:
    """Show the top-ranked signals in the strategy's universe."""
    logger.info(f"Getting top {args.limit} signals...")
    signals = service.scan(args.start_date, args.end_date, max_tickers=args.max_tickers)
    for signal in sorted(signals, key=lambda s: s.ranking, reverse=True)[: args.limit]:
        print_signal(signal.ticker, signal.date, signal.ranking)
    return 0


def run_signal(service: SignalService, args: argparse.Namespace) -> int:
    """Check signals for the specified tickers."""
    for ticker in args.tickers:
        for signal in service.trading_strategy.get_signals(ticker, args.start_date, args.end_date):
            print_signal(ticker, signal.date, signal.ranking)
    return 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser with one subcommand per analysis mode."""
    common = build_common_analysis_parser()

    universe = argparse.ArgumentParser(add_help=False)
    universe.add_argument("--max-tickers", type=int, default=10000, help="Maximum number of universe tickers to scan")

    parser = argparse.ArgumentParser(
        description="Run trading strategy analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    list_parser = subparsers.add_parser("list", parents=[common, universe], help="List all signals in the ticker universe")
    list_parser.set_defaults(handler=run_list)

    top_parser = subparsers.add_parser("top", parents=[common, universe], help="Show the top-ranked signals")
    top_parser.add_argument("--limit", type=int, default=20, help="Number of top signals to show (default: 20)")
    top_parser.set_defaults(handler=run_top)

    signal_parser = subparsers.add_parser("signal", parents=[common], help="Check signals for specific tickers")
    signal_parser.add_argument("tickers", nargs="+", help="Stock ticker symbols")
    signal_parser.set_defaults(handler=run_signal)

    return parser


def main() -> int:
    """Main entry point for strategy runner."""
    parser = create_argument_parser()
    args = parser.parse_args()
    run_start = time.perf_counter()

    # Setup logging before loading settings so the DB connection log is visible
    LogConfig.setup(args.verbose)
    settings = Settings.from_toml()

    logger.info(f"Starting strategy analysis with {args.trading_strategy} strategy and {args.ranking_strategy} ranking")

    def body() -> int:
        try:
            trading_strategy, _bars_history = resolve_trading_strategy(args, settings)
        except ValueError as e:
            logger.error(str(e))
            return 1

        service = SignalService(
            trading_strategy=trading_strategy,
            ticker_repo=TickerQueryRepository(settings.engine),
        )

        result: int = args.handler(service, args)

        logger.info(f"Strategy analysis completed successfully in {time.perf_counter() - run_start:.1f}s")
        return result

    return run_cli(args, body)


if __name__ == "__main__":
    sys.exit(main())
