"""create_job_runs_table

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-08-15 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create job_runs table recording one row per CLI invocation."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        CREATE TABLE turtle.job_runs (
            id         BIGINT      GENERATED ALWAYS AS IDENTITY,
            name       TEXT        NOT NULL,
            status     TEXT        NOT NULL DEFAULT 'running',
            start_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            end_at     TIMESTAMPTZ,
            duration   INTERVAL    GENERATED ALWAYS AS (end_at - start_at) STORED,
            parameters JSONB       NOT NULL,
            version    TEXT        NOT NULL,
            exit_code  INTEGER,
            error      TEXT,
            hostname   TEXT        NOT NULL,
            CONSTRAINT pk_job_runs PRIMARY KEY (id),
            CONSTRAINT job_runs_status_check CHECK (status IN ('running', 'success', 'failed')),
            CONSTRAINT job_runs_finished_check CHECK ((status = 'running') = (end_at IS NULL))
        )
    """)

    op.execute("COMMENT ON TABLE turtle.job_runs IS 'One row per CLI invocation: timing, parameters, version and outcome'")
    op.execute("COMMENT ON COLUMN turtle.job_runs.id IS 'Surrogate key, returned by the start insert so the finish update can target the row'")
    op.execute("COMMENT ON COLUMN turtle.job_runs.name IS 'Console-script name of the job, e.g. download-eodhd-data'")
    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.status IS
        'running until the job finishes; then success or failed. A row left as running is a job that
         was killed (OOM/SIGKILL) rather than one still in flight, once start_at is old enough'
    """)
    op.execute("COMMENT ON COLUMN turtle.job_runs.start_at IS 'Timestamp the run was recorded as started; doubles as the row creation time'")
    op.execute("COMMENT ON COLUMN turtle.job_runs.end_at IS 'Timestamp the run finished; NULL exactly while status is running'")
    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.duration IS
        'Generated from end_at - start_at, so it can never drift out of sync with them. NULL while the
         run is in flight. Use EXTRACT(EPOCH FROM duration) to chart it'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.parameters IS
        'Nested {"cli": {...}, "strategy": {...}}. cli is the parsed argparse namespace; strategy is the
         resolved trading-strategy parameters and is absent for the standalone utilities and for any run
         killed before it resolved a strategy'
    """)
    op.execute("COMMENT ON COLUMN turtle.job_runs.version IS 'Running code version as <package>+<git-sha>, e.g. 1.0.0+fd66f3b'")
    op.execute("COMMENT ON COLUMN turtle.job_runs.exit_code IS 'Process exit code the CLI returned; NULL for a run that never finished'")
    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.error IS
        'Last ERROR-level log message of a failed run. Most CLIs report failure by logging an error and
         returning 1 rather than raising, so this is captured from the log rather than an exception'
    """)
    op.execute("COMMENT ON COLUMN turtle.job_runs.hostname IS 'Host the run executed on, distinguishing a VPS timer run from an ad-hoc local one'")

    op.execute("CREATE INDEX idx_job_runs_name_start_at ON turtle.job_runs (name, start_at DESC)")
    op.execute("CREATE INDEX idx_job_runs_unfinished ON turtle.job_runs (start_at DESC) WHERE status = 'running'")


def downgrade() -> None:
    """Drop job_runs table."""
    op.execute("DROP TABLE IF EXISTS turtle.job_runs CASCADE")
