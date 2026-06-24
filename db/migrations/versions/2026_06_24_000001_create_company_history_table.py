"""create_company_history_table

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create company_history table for monthly snapshots."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        CREATE TABLE turtle.company_history (
            ticker_code    TEXT           NOT NULL,
            snapshot_date  DATE           NOT NULL,
            type           TEXT,
            name           TEXT,
            sector         TEXT,
            industry       TEXT,
            average_volume BIGINT,
            average_price  NUMERIC(20, 2),
            dividend_yield NUMERIC(12, 2),
            market_cap     BIGINT,
            pe             NUMERIC(12, 2),
            forward_pe     NUMERIC(12, 2),
            created_at     TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_company_history PRIMARY KEY (ticker_code, snapshot_date)
        )
    """)

    op.execute("COMMENT ON TABLE turtle.company_history IS 'Monthly point-in-time snapshots of turtle.company; snapshot_date is the last day of the previous month'")
    op.execute("COMMENT ON COLUMN turtle.company_history.ticker_code IS 'Unique ticker identifier (AAPL.US), matches company.ticker_code'")
    op.execute("COMMENT ON COLUMN turtle.company_history.snapshot_date IS 'Last day of the month being captured (e.g. 2026-05-31 for a June 1st run)'")
    op.execute("COMMENT ON COLUMN turtle.company_history.created_at IS 'Timestamp when this snapshot row was inserted'")

    op.execute("GRANT INSERT ON turtle.company_history TO app_user")


def downgrade() -> None:
    """Drop company_history table."""
    op.execute("DROP TABLE IF EXISTS turtle.company_history CASCADE")
