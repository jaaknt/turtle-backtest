"""create_update_trigger_function

Revision ID: da84d8a87978
Revises: 5293d810be08
Create Date: 2025-12-29 09:17:25.269583+00:00

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'da84d8a87978'
down_revision: str | Sequence[str] | None = '5293d810be08'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create update_modified_at_column trigger function."""
    op.execute("SET search_path TO turtle, public")
    op.execute("""
        CREATE OR REPLACE FUNCTION turtle.update_modified_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.modified_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        COMMENT ON FUNCTION turtle.update_modified_at_column() IS
        'Trigger function to automatically update modified_at timestamp on row modification'
    """)


def downgrade() -> None:
    """Drop update_modified_at_column trigger function."""
    op.execute("DROP FUNCTION IF EXISTS turtle.update_modified_at_column() CASCADE")
