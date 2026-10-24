"""add_lightyear_transaction_signal_id

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-10-24 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5c6d7e8f9a0"
down_revision: str | Sequence[str] | None = "a4b5c6d7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add signal_id linking a buy to the signal it was bought off."""
    op.execute("SET search_path TO turtle, public")

    op.execute("ALTER TABLE turtle.lightyear_transaction ADD COLUMN signal_id BIGINT")
    op.execute("""
        ALTER TABLE turtle.lightyear_transaction
            ADD CONSTRAINT fk_lightyear_transaction_signal
            FOREIGN KEY (signal_id) REFERENCES turtle.signal (id) ON DELETE SET NULL
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.lightyear_transaction.signal_id IS
        'The turtle.signal row this buy was most plausibly bought off, filled by lightyear-import: same
         symbol, signal_date within the 30 calendar days strictly before transacted_at, newest first, then
         highest ranking. Ungated - no ranking threshold is applied. Every import re-links buys still NULL,
         so a signal persisted after the buy was imported is picked up later. Always NULL on sells'
    """)


def downgrade() -> None:
    """Drop signal_id; its foreign key goes with it."""
    op.execute("ALTER TABLE turtle.lightyear_transaction DROP COLUMN IF EXISTS signal_id")
