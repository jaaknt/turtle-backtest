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
    --trading-strategy STRATEGY  darvas_box, mars, momentum, qullamaggie (default: qullamaggie)
    --ranking-strategy STRATEGY  momentum, volume_momentum, breakout_quality, qullamaggie (default: qullamaggie)
    --trading-param KEY=VALUE    Override a trading-strategy parameter, e.g. --trading-param
                                 sma_thresh=0.20 (repeatable)
    --max-tickers NUM            Maximum number of universe tickers to scan (default: 10000)
    --verbose                    Enable verbose logging

Run `signal-runner --help` for the full option list.
"""

import argparse
import logging
import sys
import time
from collections.abc import Mapping

from turtlex.cli.common import build_common_analysis_parser, log_parameters, resolve_trading_strategy, run_job
from turtlex.config.logging import setup_logging
from turtlex.config.settings import Settings
from turtlex.model import Signal
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.job_run_service import JobRunRecorder
from turtlex.service.signal_service import SignalService

logger = logging.getLogger(__name__)


# (header, Signal.indicators key, width, scale, format spec, suffix). The keys must stay in
# step with QullamaggieStrategy.REPORTED_INDICATORS -- test_indicator_columns_match_strategy
# pins that, because a drifted key renders "--" forever rather than failing. A strategy that
# does not produce an indicator leaves it out of Signal.indicators and the cell renders "--".
_INDICATOR_COLUMNS: tuple[tuple[str, str, int, float, str, str], ...] = (
    ("%abv SMA50", "pct_vs_sma50", 10, 100.0, ">+9.1f", "%"),
    ("ADR%", "adr_pct", 6, 100.0, ">5.1f", "%"),
    ("ADR_CHG", "adr_pct_change", 7, 1.0, ">7.2f", ""),
    ("VOL_DRY", "vol_dry_up_ratio", 7, 1.0, ">7.2f", ""),
    ("RSI14", "rsi14", 6, 1.0, ">6.1f", ""),
    ("TR%", "tight_range_ratio", 6, 100.0, ">5.1f", "%"),
    ("ROC252%", "roc_252d", 8, 100.0, ">+7.1f", "%"),
)


def _cell(value: float | None, width: int, scale: float, spec: str, suffix: str) -> str:
    """Render one numeric cell, or a right-aligned "--" when the value is missing."""
    if value is None:
        return f"{'--':>{width}}"
    return f"{value * scale:{spec}}{suffix}"


def format_signal_table(signals: list[Signal], sectors: Mapping[str, str]) -> str:
    """Render signals as a fixed-width table, one row per signal.

    The column layout matches the signal table of scripts/qullamaggie-signals-v4.py, so the
    two read the same way: identity and the signal-date indicators first, then ranking and the
    prices at the right edge. The *rows* are not the same set -- that script additionally gates
    at ranking >= 44 and drops signals whose raw close moved more than 50% in a day, so its
    table is a subset of this one.

    Args:
        signals: Signals to render, already in the order they should appear
        sectors: Ticker code -> sector name; a missing ticker renders as "--"

    Returns:
        str: The rendered table, or a single line when there are no signals
    """
    if not signals:
        return "No signals in the requested period."
    hdr = f"{'Date':<11}│ {'Symbol':<7}│ {'Sector':<23}│ " + " │ ".join(
        f"{name:>{width}}" for name, _, width, _, _, _ in _INDICATOR_COLUMNS
    )
    hdr += f" │ {'Last date':>11} │ {'Ranking':>7} │ {'Entry $':>8} │ {'Curr Price':>10} │ {'Change %':>9}"
    lines = [hdr, "─" * len(hdr)]
    for s in signals:
        cells = " │ ".join(
            _cell(s.indicators.get(key), width, scale, spec, suffix) for _, key, width, scale, spec, suffix in _INDICATOR_COLUMNS
        )
        # `is not None` throughout, matching _cell: a 0.0 entry price is a data fault, not a
        # missing value, and should raise here rather than render as an indistinguishable "--".
        change = (s.last_price / s.entry_price - 1.0) * 100.0 if s.entry_price is not None and s.last_price is not None else None
        lines.append(
            f"{str(s.date):<11}│ {s.ticker:<7}│ {sectors.get(s.ticker) or '--':<23}│ {cells} │ "
            f"{str(s.last_date) if s.last_date else '--':>11} │ {s.ranking:>7} │ "
            f"{_cell(s.entry_price, 8, 1.0, '>8.2f', '')} │ {_cell(s.last_price, 10, 1.0, '>10.2f', '')} │ "
            f"{_cell(change, 9, 1.0, '>+8.1f', '%')}"
        )
    return "\n".join(lines)


def run_list(service: SignalService, args: argparse.Namespace) -> int:
    """List all signals in the strategy's universe, sorted by date and ticker.

    Args:
        service: Signal service used to scan the universe; its ticker repository also
            supplies turtle.company.sector for the Sector column
        args: Parsed CLI arguments (start/end date, max_tickers)

    Returns:
        int: Process exit code, always 0 -- a failed scan raises rather than returning
    """
    signals = service.scan(args.start_date, args.end_date, max_tickers=args.max_tickers)
    print(format_signal_table(sorted(signals, key=lambda s: (s.date, s.ticker)), service.ticker_repo.get_sectors()))
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
    setup_logging(args.verbose)
    settings = Settings.from_toml()

    logger.info(f"Starting strategy analysis with {args.trading_strategy} strategy and {args.ranking_strategy} ranking")
    log_parameters("CLI arguments", vars(args))

    def body(recorder: JobRunRecorder) -> int:
        try:
            trading_strategy, _bars_history = resolve_trading_strategy(args, settings, recorder)
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

    return run_job("signal-runner", args, settings, body)


if __name__ == "__main__":
    sys.exit(main())
