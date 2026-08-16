"""Shared CLI bootstrap helpers for the analysis runner scripts (backtest_runner, signal_runner)."""

import argparse
import functools
import logging
from collections.abc import Callable, Mapping

from turtlex.common.cli import iso_date_type, key_value_type
from turtlex.config.settings import Settings
from turtlex.repository.ingest.job_run import JobRunRepository
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.service.job_run_service import JobRunRecorder
from turtlex.strategy.factory import RANKING_STRATEGIES, TRADING_STRATEGIES, get_ranking_strategy, get_trading_strategy
from turtlex.strategy.trading.base import TradingStrategy

logger = logging.getLogger(__name__)


def add_logging_args(parser: argparse.ArgumentParser) -> None:
    """Add the shared --verbose/-v logging flag to `parser`.

    Args:
        parser: Parser to extend
    """
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")


def build_common_analysis_parser() -> argparse.ArgumentParser:
    """Build a parent parser (add_help=False) for the --start-date/--end-date/--trading-strategy/
    --ranking-strategy/--trading-param/--verbose flags shared by every analysis CLI."""
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
    parser.add_argument(
        "--trading-param",
        action="append",
        default=[],
        type=key_value_type,
        metavar="KEY=VALUE",
        help="Override a trading-strategy constructor parameter, e.g. --trading-param sma_thresh=0.20 "
        "(qullamaggie's SMA distance, a fraction and not a percent) (repeatable)",
    )
    add_logging_args(parser)
    return parser


def log_parameters(label: str, params: Mapping[str, object]) -> None:
    """Log one `label: name=value, ...` line at INFO, so a run records the configuration it used.

    Args:
        label: Names the group, e.g. "qullamaggie parameters" or "CLI arguments"
        params: Parameter name → effective value, logged in iteration order
    """
    logger.info(f"{label}: {', '.join(f'{name}={value}' for name, value in params.items())}")


def resolve_trading_strategy(
    args: argparse.Namespace, settings: Settings, recorder: JobRunRecorder
) -> tuple[TradingStrategy, DailyBarsQueryRepository]:
    """Resolve --ranking-strategy/--trading-strategy into a TradingStrategy and its DailyBarsQueryRepository.

    Reports the resolved strategy's effective parameters to both sinks — INFO for whoever reads
    the journal, and the job-run row for whoever queries it later — so every analysis CLI records
    the configuration its run used without repeating the call itself.

    Args:
        args: Parsed CLI arguments, must have `trading_strategy`, `ranking_strategy` and `trading_param`
        settings: Loaded application settings, used for the database engine
        recorder: Job-run recorder receiving the resolved parameters as the "strategy" section

    Returns:
        Tuple of (trading_strategy, bars_history)

    Raises:
        ValueError: If either strategy name is unknown, or a --trading-param key/value is not
            accepted by the selected trading strategy
    """
    bars_history = DailyBarsQueryRepository(engine=settings.engine)
    ranking_strategy = get_ranking_strategy(args.ranking_strategy)
    trading_strategy = get_trading_strategy(args.trading_strategy, ranking_strategy, bars_history, args.trading_param)
    parameters = trading_strategy.describe_parameters()
    log_parameters(f"{args.trading_strategy} parameters", parameters)
    recorder.add_parameters("strategy", parameters)
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


def run_job(name: str, args: argparse.Namespace, settings: Settings, body: Callable[[JobRunRecorder], int]) -> int:
    """Run `body` under run_cli, recording the invocation in turtle.job_runs.

    Wraps run_cli rather than replacing it: run_cli already maps KeyboardInterrupt and unexpected
    exceptions to a logged error plus exit code 1, and the recorder reads the outcome off the
    return value and the error it logged.

    Args:
        name: Console-script name recorded as the job name, e.g. "signal-runner"
        args: Parsed CLI arguments, recorded as the "cli" parameter section
        settings: Loaded application settings, supplying the engine and the on/off switch
        body: Callable performing the CLI's main work, returning its exit code. Receives the
            recorder so it can report parameters resolved mid-run

    Returns:
        The exit code from `body`, or 1 if it raised KeyboardInterrupt/an unexpected exception
    """
    recorder = JobRunRecorder(JobRunRepository(settings.engine) if settings.job_runs.enabled else None, name, vars(args))
    # try/finally rather than relying on run_cli: it catches Exception, but a BaseException such as
    # SystemExit passes straight through and must still close the row out. start() is inside the
    # try so that nothing it raises can kill the job before the body has run.
    exit_code = 1
    try:
        recorder.start()
        exit_code = run_cli(args, functools.partial(body, recorder))
    finally:
        # The recorder guards itself, but this is the boundary where a telemetry failure would
        # replace the job's real outcome, so it gets a second belt.
        try:
            recorder.finish(exit_code)
        except Exception:
            logger.exception("Job-run recording failed; the job's own outcome stands")
    return exit_code
