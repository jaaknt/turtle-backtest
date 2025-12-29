"""create_turtle_schema

Revision ID: cf4ab544aa26
Revises:
Create Date: 2025-12-29 09:17:23.736686+00:00

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'cf4ab544aa26'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create turtle schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS turtle")
    op.execute("COMMENT ON SCHEMA turtle IS 'Trading application schema for stock data and analysis'")


def downgrade() -> None:
    """Drop turtle schema."""
    op.execute("DROP SCHEMA IF EXISTS turtle CASCADE")
