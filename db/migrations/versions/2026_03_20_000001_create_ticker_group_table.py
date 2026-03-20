"""create_ticker_group_table

Revision ID: a1b2c3d4e5f6
Revises: 42179cc9d2e1
Create Date: 2026-03-20 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "42179cc9d2e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ticker_group table and modified_at trigger."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        CREATE TABLE turtle.ticker_group (
            code        TEXT        NOT NULL,
            ticker_code TEXT        NOT NULL,
            rate        NUMERIC,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modified_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_ticker_group PRIMARY KEY (code, ticker_code)
        )
    """)

    op.execute("COMMENT ON TABLE turtle.ticker_group IS 'Custom ticker watchlists/groups'")
    op.execute("COMMENT ON COLUMN turtle.ticker_group.code IS 'Group identifier code'")
    op.execute("COMMENT ON COLUMN turtle.ticker_group.ticker_code IS 'Ticker symbol belonging to the group'")
    op.execute("COMMENT ON COLUMN turtle.ticker_group.rate IS 'Optional weighting rate for the ticker within the group'")
    op.execute("COMMENT ON COLUMN turtle.ticker_group.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.ticker_group.modified_at IS 'Timestamp when the record was last updated'")

    op.execute("""
        CREATE TRIGGER ticker_group_modified_at
            BEFORE UPDATE ON turtle.ticker_group
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_modified_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER ticker_group_modified_at ON turtle.ticker_group IS
        'Automatically updates modified_at column on row modification'
    """)


def downgrade() -> None:
    """Drop ticker_group table and trigger."""
    op.execute("DROP TRIGGER IF EXISTS ticker_group_modified_at ON turtle.ticker_group")
    op.execute("DROP TABLE IF EXISTS turtle.ticker_group CASCADE")
