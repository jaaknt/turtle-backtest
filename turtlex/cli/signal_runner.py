#!/usr/bin/env python3
"""
Signal Runner Script

This script runs trading strategy analysis using the SignalService class.
It scans the strategy's ticker universe and lists all signals in the date range.

Usage:
    uv run signal-runner [options]

Options:
    --start-date YYYY-MM-DD      Start date for analysis (required)
    --end-date YYYY-MM-DD        End date for analysis (required)
    --trading-strategy STRATEGY  darvas_box, mars, momentum, qullamaggie (default: darvas_box)
    --ranking-strategy STRATEGY  momentum, volume_momentum, breakout_quality (default: momentum)
    --max-tickers NUM            Maximum number of universe tickers to scan (default: 10000)
    --verbose                    Enable verbose logging

Run `signal-runner --help` for the full option list.
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


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Run trading strategy analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        parents=[build_common_analysis_parser()],
    )
    parser.add_argument("--max-tickers", type=int, default=10000, help="Maximum number of universe tickers to scan")

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

        result: int = run_list(service, args)

        logger.info(f"Strategy analysis completed successfully in {time.perf_counter() - run_start:.1f}s")
        return result

    return run_cli(args, body)


if __name__ == "__main__":
    sys.exit(main())
