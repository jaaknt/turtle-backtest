"""create_data_source_enum

Revision ID: 5293d810be08
Revises: cf4ab544aa26
Create Date: 2025-12-29 09:17:24.516692+00:00

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5293d810be08'
down_revision: str | Sequence[str] | None = 'cf4ab544aa26'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create data_source_type ENUM."""
    op.execute("SET search_path TO turtle, public")
    op.execute("""
        CREATE TYPE turtle.data_source_type AS ENUM ('eodhd', 'alpaca', 'yahoo')
    """)
    op.execute("""
        COMMENT ON TYPE turtle.data_source_type IS
        'Allowed data source providers for price data'
    """)


def downgrade() -> None:
    """Drop data_source_type ENUM."""
    op.execute("DROP TYPE IF EXISTS turtle.data_source_type CASCADE")
