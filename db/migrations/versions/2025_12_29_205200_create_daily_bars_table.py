"""create_daily_bars_table

Revision ID: 42179cc9d2e1
Revises: da84d8a87978
Create Date: 2025-12-29 09:17:25.982600+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "42179cc9d2e1"
down_revision: str | Sequence[str] | None = "4ab2f4c9d21f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create daily_bars table with all columns and trigger."""
    op.execute("SET search_path TO turtle, public")

    # Create table (EXACT copy from Liquibase)
    op.execute("""
        CREATE TABLE turtle.daily_bars (
            symbol         TEXT                    NOT NULL,
            date           date                    NOT NULL,
            open           FLOAT8                  NOT NULL,
            high           FLOAT8                  NOT NULL,
            low            FLOAT8                  NOT NULL,
            close          FLOAT8                  NOT NULL,
            adjusted_close FLOAT8                  NOT NULL,
            volume         BIGINT                  NOT NULL,
            source         turtle.data_source_type NOT NULL,
            created_at     TIMESTAMPTZ             NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at     TIMESTAMPTZ             NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT pk_daily_bars PRIMARY KEY (symbol, date),
            CONSTRAINT daily_bars_symbol_check CHECK (length(symbol) > 0)
        )
    """)
    # Add all column comments
    op.execute("COMMENT ON TABLE turtle.daily_bars IS 'Historical stock price data (OHLCV format) indexed by symbol and date'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.symbol IS 'Unique ticker identifier with exchange suffix (e.g., AAPL.US, GOOGL.US)'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.date IS 'Date of the price data point'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.open IS 'Opening price for the time period'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.high IS 'Highest price during the time period'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.low IS 'Lowest price during the time period'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.close IS 'Closing price for the time period'")
    op.execute(
        "COMMENT ON COLUMN turtle.daily_bars.adjusted_close IS 'Adjusted closing price for the time period (splits/dividends adjusted)'"
    )
    op.execute("COMMENT ON COLUMN turtle.daily_bars.volume IS 'Trading volume (number of shares traded)'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.source IS 'Data source (e.g., alpaca, yahoo, eodhd)'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.daily_bars.updated_at IS 'Timestamp when the record was last updated'")

    # Create trigger for automatic updated_at management
    op.execute("""
        CREATE TRIGGER daily_bars_updated_at
            BEFORE UPDATE ON turtle.daily_bars
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_updated_at_column()
    """)

    op.execute("""
        COMMENT ON TRIGGER daily_bars_updated_at ON turtle.daily_bars IS
        'Automatically updates updated_at column on row modification'
    """)


def downgrade() -> None:
    """Drop price_history table and trigger."""
    op.execute("DROP TRIGGER IF EXISTS price_history_updated_at ON turtle.price_history")
    op.execute("DROP TABLE IF EXISTS turtle.price_history CASCADE")
