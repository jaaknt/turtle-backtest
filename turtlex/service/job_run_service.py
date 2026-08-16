"""Record one CLI invocation into turtle.job_runs.

Telemetry must never fail the job it is measuring, so every database call here is isolated: a
Postgres hiccup degrades job-run logging to nothing rather than turning a successful download
into a non-zero exit.
"""

import logging
import socket
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from turtlex.common.version import resolve_version
from turtlex.config.logging import LastErrorCapture
from turtlex.repository.ingest.job_run import JobRunRepository

logger = logging.getLogger(__name__)


def _jsonable(value: object) -> object:
    """Convert `value` into something json (and therefore jsonb) accepts.

    argparse namespaces carry types json rejects outright: dates from iso_date_type, Paths from
    --folder, and (key, value) tuples from key_value_type.

    Args:
        value: Any parameter value taken from a parsed argparse namespace

    Returns:
        object: A json-serializable equivalent; unknown types degrade to their str()
    """
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_jsonable(item) for item in value]
    return str(value)


class JobRunRecorder:
    """Records one CLI invocation into turtle.job_runs; a no-op when repository is None."""

    def __init__(self, repository: JobRunRepository | None, name: str, parameters: Mapping[str, object]) -> None:
        self._repository = repository
        self._name = name
        self._parameters: dict[str, object] = {"cli": _jsonable(parameters)}
        self._run_id: int | None = None
        self._error_capture = LastErrorCapture()

    def start(self) -> None:
        """Insert the 'running' row and begin capturing ERROR-level log messages.

        A failure to insert leaves the recorder inert rather than raising, so the job proceeds.
        """
        if self._repository is None:
            return

        self._error_capture.attach()

        try:
            self._run_id = self._repository.start_run(
                name=self._name,
                parameters=self._parameters,
                version=resolve_version(),
                hostname=socket.gethostname(),
            )
        except SQLAlchemyError as e:
            # Deliberately swallowed: see the module docstring. Without the id there is nothing to
            # update later, so the run simply goes unrecorded.
            logger.warning("Could not record start of job run '%s': %s", self._name, e)

    def add_parameters(self, section: str, values: Mapping[str, object]) -> None:
        """Buffer a named parameter section, written when the run finishes.

        Resolved strategy parameters only exist after the run has already started, so they are
        held in memory and folded into the update finish() was making anyway.

        Args:
            section: Key the values are stored under, e.g. "strategy"
            values: Parameter name to effective value
        """
        self._parameters[section] = _jsonable(values)

    def finish(self, exit_code: int) -> None:
        """Close out the run, recording its status, exit code and error.

        Args:
            exit_code: Exit code the CLI is about to return; 0 means success
        """
        if self._repository is None:
            return

        try:
            # Inside the try, so a start() that failed to insert still reaches the finally and
            # detaches the handler.
            if self._run_id is not None:
                self._repository.finish_run(
                    run_id=self._run_id,
                    status="success" if exit_code == 0 else "failed",
                    exit_code=exit_code,
                    error=self._error_capture.last_message if exit_code != 0 else None,
                    parameters=self._parameters,
                )
        except SQLAlchemyError as e:
            # Deliberately swallowed: see the module docstring. The row stays 'running' and shows
            # up alongside genuinely killed runs, which is the honest outcome.
            logger.warning("Could not record completion of job run '%s': %s", self._name, e)
        finally:
            # In a finally so a failed update can never leave the handler attached to the root
            # logger, where it would accumulate across runs in a long-lived process or test session.
            self._error_capture.detach()
