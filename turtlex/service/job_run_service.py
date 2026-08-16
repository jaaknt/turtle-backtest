"""Record one CLI invocation into turtle.job_runs.

Telemetry must never fail the job it is measuring, so every entry point here is isolated: a
Postgres hiccup, an unresolvable hostname or an unserializable argument degrades job-run logging
to nothing rather than turning a successful download into a non-zero exit.

The catches are deliberately `Exception` rather than a narrow database class. That is a departure
from the CLAUDE.md "no swallowed exceptions" rule, and it is the right one here: this module has
no recovery that depends on the exception type, and the cost of guessing the type wrong is
exactly the outcome the rule above forbids. Every catch names the job in its log line — WARNING
where the run simply goes unrecorded, ERROR from finish(), where the row is left looking like a
kill and the log is the only thing saying otherwise.
"""

import logging
import socket
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path

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
        """Buffer the CLI arguments for a run that is about to start.

        Args:
            repository: Destination for the two writes, or None to make this recorder inert.
                The caller decides from settings.job_runs.enabled; None means no work at all
            name: Console-script name recorded as the job name, e.g. "signal-runner"
            parameters: Parsed argparse namespace, stored as the "cli" section
        """
        self._repository = repository
        self._name = name
        self._run_id: int | None = None
        self._error_capture = LastErrorCapture()
        self._parameters: dict[str, object] = {}
        # Serializing before the disabled check would let an unserializable argument take down a
        # job whose telemetry is switched off, which is the one thing the switch must guarantee.
        if repository is None:
            return
        self._parameters = {"cli": self._serialize(parameters, "cli")}

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
        except Exception as e:
            # Deliberately swallowed: see the module docstring. Not just SQLAlchemyError --
            # socket.gethostname() raises OSError on a resolver hiccup, and killing a nightly
            # download over a hostname lookup is exactly the failure this module must not cause.
            # Without the id there is nothing to update later, so the run goes unrecorded.
            logger.warning("Could not record start of job run '%s' -- the run will have no row: %s", self._name, e)

    def add_parameters(self, section: str, values: Mapping[str, object]) -> None:
        """Buffer a named parameter section, written by the closing update if the run was recorded.

        Resolved strategy parameters only exist after the run has already started, so they are
        held in memory and folded into the update finish() was making anyway.

        Args:
            section: Key the values are stored under, e.g. "strategy"
            values: Parameter name to effective value
        """
        if self._repository is None:
            return
        self._parameters[section] = self._serialize(values, section)

    def _serialize(self, values: Mapping[str, object], section: str) -> object:
        # Called from inside the job body, so an unserializable parameter must not surface to the
        # user as the analysis failing. Records the failure in place of the section instead.
        try:
            return _jsonable(values)
        except Exception as e:
            logger.warning("Could not serialize '%s' parameters for job run '%s': %s", section, self._name, e)
            return {"_serialization_failed": str(e)}

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
        except Exception as e:
            # Deliberately swallowed: the job's own outcome stands regardless of whether we could
            # record it. Logged at ERROR, not WARNING: the row is now stuck at 'running' and is
            # indistinguishable from an OOM kill in the orphan query, so this line is the only
            # thing that tells an operator the job actually succeeded.
            logger.error(
                "Could not record completion of job run '%s' (status=%s, exit_code=%d) -- its row stays 'running' "
                "and is NOT evidence of a kill: %s",
                self._name,
                "success" if exit_code == 0 else "failed",
                exit_code,
                e,
            )
        finally:
            # In a finally so a failed update can never leave the handler attached to the root
            # logger, where it would accumulate across runs in a long-lived process or test session.
            self._error_capture.detach()
