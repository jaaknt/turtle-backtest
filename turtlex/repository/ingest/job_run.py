import logging

from sqlalchemy import Engine, func, insert, update

from turtlex.repository.tables import job_runs_table

logger = logging.getLogger(__name__)


class JobRunRepository:
    """Sync Engine-based repository for job-run writes."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def start_run(self, name: str, parameters: dict[str, object], version: str, hostname: str) -> int:
        """Insert a 'running' row for a job that has just started and return its id.

        `start_at` and `status` come from their column defaults, so the row is consistent with
        job_runs_finished_check from the moment it exists.

        Args:
            name: Console-script name of the job, e.g. "download-eodhd-data"
            parameters: Serialized parameter sections, at this point only {"cli": {...}}
            version: Running code version, as produced by resolve_version()
            hostname: Host executing the run

        Returns:
            int: Generated id of the new row, needed to close the run out later
        """
        stmt = (
            insert(job_runs_table)
            .values(name=name, parameters=parameters, version=version, hostname=hostname)
            .returning(job_runs_table.c.id)
        )
        with self._engine.begin() as conn:
            run_id: int = conn.execute(stmt).scalar_one()
        logger.debug("Started job run %d for %s", run_id, name)
        return run_id

    def finish_run(self, run_id: int, status: str, exit_code: int, error: str | None, parameters: dict[str, object]) -> None:
        """Close out a run, setting end_at (which populates the generated duration column).

        `parameters` is rewritten rather than left alone: sections resolved during the run — the
        strategy one — do not exist yet at insert time, so this is where they land.

        Args:
            run_id: Id returned by start_run
            status: Terminal status, either "success" or "failed"
            exit_code: Exit code the CLI returned
            error: Last error message of a failed run, or None
            parameters: Full serialized parameter sections, replacing what start_run wrote
        """
        stmt = (
            update(job_runs_table)
            .where(job_runs_table.c.id == run_id)
            .values(
                status=status,
                end_at=func.current_timestamp(),
                exit_code=exit_code,
                error=error,
                parameters=parameters,
            )
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
        logger.debug("Finished job run %d with status %s", run_id, status)
