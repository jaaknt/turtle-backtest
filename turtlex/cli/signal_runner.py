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
    --min-signal-ranking NUM     Drop signals scoring below this ranking (default: 0, keep all)
    --persist                    Write every emitted signal to turtle.signal (default: off)
    --persist-label LABEL        Value written to turtle.signal.trading_strategy
                                 (default: the --trading-strategy name)
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
from turtlex.repository.ingest import SignalRepository
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

    Identity, then the signal-date indicators, then ranking and the two prices. The indicator
    columns share their layout with the signal table of scripts/qullamaggie-signals-v4.py; that
    script gates at ranking >= 44, so its rows are a subset of these.

    Signal $ is the signal date's raw close -- the bar every filter was evaluated on, which is
    already closed when the signal appears. Next Open $ is the following bar's raw open, the
    first price the signal could be acted on, and is blank until that bar exists.

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
    hdr += f" │ {'Ranking':>7} │ {'Signal $':>9} │ {'Next Open $':>11}"
    lines = [hdr, "─" * len(hdr)]
    for s in signals:
        cells = " │ ".join(
            _cell(s.indicators.get(key), width, scale, spec, suffix) for _, key, width, scale, spec, suffix in _INDICATOR_COLUMNS
        )
        lines.append(
            f"{str(s.date):<11}│ {s.ticker:<7}│ {sectors.get(s.ticker) or '--':<23}│ {cells} │ {s.ranking:>7} │ "
            f"{_cell(s.signal_close, 9, 1.0, '>9.2f', '')} │ {_cell(s.next_open, 11, 1.0, '>11.2f', '')}"
        )
    return "\n".join(lines)


def run_list(service: SignalService, args: argparse.Namespace, signal_repo: SignalRepository | None = None) -> int:
    """List all signals in the strategy's universe, sorted by date and ticker.

    Args:
        service: Signal service used to scan the universe; its ticker repository also
            supplies turtle.company.sector for the Sector column
        args: Parsed CLI arguments -- start/end date, max_tickers, min_signal_ranking,
            persist_label and ranking_strategy
        signal_repo: Repository to persist to, or None when --persist was not given

    Returns:
        int: Process exit code, always 0 -- a failed scan or a failed persist raises rather
            than returning
    """
    # `signals` stays the ungated truth for the whole function; the gate produces `listed`. Rebinding
    # `signals` to the gated list would leave the ungated one unreachable below that point, which is
    # what forces any persist call placed after the gate to write gated rows.
    signals = service.scan(args.start_date, args.end_date, max_tickers=args.max_tickers)
    if signal_repo is not None:
        if not signals:
            # An explicit --persist that wrote nothing is worth a warning: a quiet window looks
            # identical to a broken universe query, a future-dated range, or --max-tickers 0.
            logger.warning(
                f"--persist requested but the scan produced no signals for {args.start_date}..{args.end_date}; "
                "nothing written to turtle.signal"
            )
        # Ahead of the ranking gate on purpose: --min-signal-ranking narrows what is printed, never
        # what is written. A gated write destroys rows no reader can recover without a full rescan.
        written = signal_repo.upsert_signals(signals, trading_strategy=args.persist_label, ranking_strategy=args.ranking_strategy)
        logger.info(f"Persisted {written} signals as '{args.persist_label}' ranked by {args.ranking_strategy}")

    listed = signals
    if args.min_signal_ranking > 0:
        listed = [s for s in signals if s.ranking >= args.min_signal_ranking]
        logger.info(f"Ranking gate >= {args.min_signal_ranking}: kept {len(listed)} of {len(signals)} signals")
    print(format_signal_table(sorted(listed, key=lambda s: (s.date, s.ticker)), service.ticker_repo.get_sectors()))
    return 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Run trading strategy analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        parents=[build_common_analysis_parser()],
    )
    parser.add_argument(
        "--min-signal-ranking",
        type=int,
        default=0,
        help="Drop signals scoring below this ranking; 0 keeps every signal (default: 0). "
        "The reference algorithm gates at 44, matching portfolio-runner's own default",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write every emitted signal to turtle.signal, before the --min-signal-ranking gate is applied. "
        "Requires a strategy that reports the signal-date close, which today means qullamaggie",
    )
    parser.add_argument(
        "--persist-label",
        type=str,
        default=None,
        metavar="LABEL",
        help="Value written to turtle.signal.trading_strategy, e.g. bk50d_s12_v2.0 "
        "(default: the --trading-strategy name). Ignored without --persist",
    )
    parser.add_argument("--max-tickers", type=int, default=10000, help="Maximum number of universe tickers to scan")

    return parser


def main() -> int:
    """Main entry point for strategy runner."""
    parser = create_argument_parser()
    args = parser.parse_args()
    # Normalised before log_parameters and run_job so the effective label is what both record --
    # resolving it lazily at the call site would store persist_label=null in turtle.job_runs.
    if not args.persist_label:
        args.persist_label = args.trading_strategy
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

        result: int = run_list(service, args, SignalRepository(settings.engine) if args.persist else None)

        logger.info(f"Strategy analysis completed successfully in {time.perf_counter() - run_start:.1f}s")
        return result

    return run_job("signal-runner", args, settings, body)


if __name__ == "__main__":
    sys.exit(main())
