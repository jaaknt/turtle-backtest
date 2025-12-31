"""create_price_history_table

Revision ID: 42179cc9d2e1
Revises: da84d8a87978
Create Date: 2025-12-29 09:17:25.982600+00:00

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "42179cc9d2e1"
down_revision: str | Sequence[str] | None = "da84d8a87978"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create price_history table with all columns and trigger."""
    op.execute("SET search_path TO turtle, public")

    # Create table (EXACT copy from Liquibase)
    op.execute("""
        CREATE TABLE turtle.price_history (
            symbol         TEXT                    NOT NULL,
            time           TIMESTAMPTZ             NOT NULL,
            open           NUMERIC(10, 2)          NOT NULL,
            high           NUMERIC(10, 2)          NOT NULL,
            low            NUMERIC(10, 2)          NOT NULL,
            close          NUMERIC(10, 2)          NOT NULL,
            adjusted_close NUMERIC(10, 2)          NOT NULL,
            volume         BIGINT                  NOT NULL,
            source         turtle.data_source_type NOT NULL,
            created_at     TIMESTAMPTZ             NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at     TIMESTAMPTZ             NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT pk_price_history PRIMARY KEY (symbol, time),
            CONSTRAINT price_history_symbol_check CHECK (length(symbol) > 0)
        )
    """)

    # Add all column comments
    op.execute("COMMENT ON TABLE turtle.price_history IS 'Historical stock price data (OHLCV format) indexed by symbol and time'")
    op.execute("COMMENT ON COLUMN turtle.price_history.symbol IS 'Unique ticker identifier with exchange suffix (e.g., AAPL.US, GOOGL.US)'")
    op.execute("COMMENT ON COLUMN turtle.price_history.time IS 'Timestamp of the price data point'")
    op.execute("COMMENT ON COLUMN turtle.price_history.open IS 'Opening price for the time period'")
    op.execute("COMMENT ON COLUMN turtle.price_history.high IS 'Highest price during the time period'")
    op.execute("COMMENT ON COLUMN turtle.price_history.low IS 'Lowest price during the time period'")
    op.execute("COMMENT ON COLUMN turtle.price_history.close IS 'Closing price for the time period'")
    op.execute(
        "COMMENT ON COLUMN turtle.price_history.adjusted_close IS 'Adjusted closing price for the time period (splits/dividends adjusted)'"
    )
    op.execute("COMMENT ON COLUMN turtle.price_history.volume IS 'Trading volume (number of shares traded)'")
    op.execute("COMMENT ON COLUMN turtle.price_history.source IS 'Data source (e.g., alpaca, yahoo, eodhd)'")
    op.execute("COMMENT ON COLUMN turtle.price_history.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.price_history.updated_at IS 'Timestamp when the record was last updated'")

    # Create trigger for automatic updated_at management
    op.execute("""
        CREATE TRIGGER price_history_updated_at
            BEFORE UPDATE ON turtle.price_history
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_updated_at_column()
    """)

    op.execute("""
        COMMENT ON TRIGGER price_history_updated_at ON turtle.price_history IS
        'Automatically updates updated_at column on row modification'
    """)


def downgrade() -> None:
    """Drop price_history table and trigger."""
    op.execute("DROP TRIGGER IF EXISTS price_history_updated_at ON turtle.price_history")
    op.execute("DROP TABLE IF EXISTS turtle.price_history CASCADE")
