"""enable_timescaledb_features

Revision ID: 9f929020ed09
Revises: 42179cc9d2e1
Create Date: 2025-12-29 09:17:26.676872+00:00

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9f929020ed09'
down_revision: str | Sequence[str] | None = '42179cc9d2e1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable TimescaleDB hypertable and compression features."""
    op.execute("SET search_path TO turtle, public")

    # Enable TimescaleDB extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # Convert to hypertable with 1-month chunks
    op.execute("""
        SELECT create_hypertable(
            'turtle.price_history',
            'time',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        )
    """)

    # Enable compression with segmentation by symbol
    op.execute("""
        ALTER TABLE turtle.price_history SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'time DESC'
        )
    """)

    # Add compression policy for data older than 2 years
    op.execute("""
        SELECT add_compression_policy(
            'turtle.price_history',
            INTERVAL '2 years',
            if_not_exists => TRUE
        )
    """)

    # Update table comment to reflect TimescaleDB features
    op.execute("""
        COMMENT ON TABLE turtle.price_history IS
        'Historical stock price data (OHLCV format) - TimescaleDB hypertable
        with 1-month chunks and 2-year compression policy'
    """)


def downgrade() -> None:
    """Disable TimescaleDB features (WARNING: Destructive)."""
    # Remove compression policy
    op.execute("""
        SELECT remove_compression_policy('turtle.price_history', if_exists => TRUE)
    """)

    # Disable compression
    op.execute("""
        ALTER TABLE turtle.price_history SET (timescaledb.compress = FALSE)
    """)

    # Drop hypertable (converts back to regular table)
    # WARNING: This may cause data loss if chunks exist
    op.execute("""
        SELECT drop_hypertable('turtle.price_history', if_exists => TRUE)
    """)
