"""fix_job_runs_column_comments

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-08-16 00:00:01.000000+00:00

Corrects two COMMENT ON strings that shipped with the job_runs table. They are the documentation
an analyst reads straight from the database, months later, with no code in front of them:

- parameters omitted the "exit_strategy" section that backtest-runner and portfolio-runner write,
  so a reader would query parameters->'strategy' and silently miss the exit configuration.
- status claimed a 'running' row means the job was killed. A failed closing update leaves the same
  row, so the two are not distinguishable from the row alone.

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a4b5c6d7e8"
down_revision: str | Sequence[str] | None = "e2f3a4b5c6d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Correct the parameters and status column comments."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.parameters IS
        'Nested {"cli": {...}, "strategy": {...}, "exit_strategy": {...}}. cli is the parsed argparse
         namespace and is always present. strategy is the resolved trading-strategy parameters, present
         only for the three analysis runners; exit_strategy is the effective exit parameters, present
         only for backtest-runner and portfolio-runner. Both are absent for the standalone utilities
         and for any run that ended before it resolved them'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.status IS
        'running until the job finishes; then success or failed. A row still running well after
         start_at means either the process died (OOM/SIGKILL/power loss) or its closing update could
         not reach the database — the two are not distinguishable from this row alone'
    """)


def downgrade() -> None:
    """Restore the original parameters and status column comments."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.parameters IS
        'Nested {"cli": {...}, "strategy": {...}}. cli is the parsed argparse namespace; strategy is the
         resolved trading-strategy parameters and is absent for the standalone utilities and for any run
         killed before it resolved a strategy'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.job_runs.status IS
        'running until the job finishes; then success or failed. A row left as running is a job that
         was killed (OOM/SIGKILL) rather than one still in flight, once start_at is old enough'
    """)
