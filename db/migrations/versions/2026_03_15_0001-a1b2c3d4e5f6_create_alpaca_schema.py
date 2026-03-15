"""create_alpaca_schema

Revision ID: a1b2c3d4e5f6
Revises: d5a4fcae22c8
Create Date: 2026-03-15 00:01:00.000000+00:00

Creates the alpaca schema to isolate Alpaca data from EODHD data.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "d5a4fcae22c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create alpaca schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS alpaca")


def downgrade() -> None:
    """Drop alpaca schema."""
    op.execute("DROP SCHEMA IF EXISTS alpaca CASCADE")
