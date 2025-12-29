"""create_ticker_table

Revision ID: 8358a5c14bac
Revises: 7e3c9131289f
Create Date: 2025-12-29 22:46:27.751336+00:00

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8358a5c14bac"
down_revision: str | Sequence[str] | None = "7e3c9131289f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ticker table and related trigger."""
    op.execute("SET search_path TO turtle, public")
    op.execute("""
        CREATE TABLE turtle.ticker (
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            country TEXT,
            exchange TEXT NOT NULL,
            currency TEXT,
            type TEXT,
            isin TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_ticker PRIMARY KEY (code, exchange)
        )
    """)

    op.execute("COMMENT ON TABLE turtle.ticker IS 'Stock tickers from EODHD'")
    op.execute("COMMENT ON COLUMN turtle.ticker.code IS 'Ticker symbol'")
    op.execute("COMMENT ON COLUMN turtle.ticker.name IS 'Company or instrument name'")
    op.execute("COMMENT ON COLUMN turtle.ticker.country IS 'Country of listing'")
    op.execute("COMMENT ON COLUMN turtle.ticker.exchange IS 'Exchange code where the ticker is listed'")
    op.execute("COMMENT ON COLUMN turtle.ticker.currency IS 'Trading currency'")
    op.execute("COMMENT ON COLUMN turtle.ticker.type IS 'Type of asset (e.g., Common Stock, ETF)'")
    op.execute("COMMENT ON COLUMN turtle.ticker.isin IS 'International Securities Identification Number'")
    op.execute("COMMENT ON COLUMN turtle.ticker.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.ticker.updated_at IS 'Timestamp when the record was last updated'")

    op.execute("""
        CREATE TRIGGER ticker_updated_at
            BEFORE UPDATE ON turtle.ticker
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_updated_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER ticker_updated_at ON turtle.ticker IS
        'Automatically updates updated_at column on row modification'
    """)


def downgrade() -> None:
    """Drop ticker table and related trigger."""
    op.execute("DROP TRIGGER IF EXISTS ticker_updated_at ON turtle.ticker")
    op.execute("DROP TABLE IF EXISTS turtle.ticker CASCADE")
