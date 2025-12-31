"""create_ticker_extended_table

Revision ID: 4ab2f4c9d21f
Revises: 8358a5c14bac
Create Date: 2025-12-31 13:12:26.452017+00:00

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4ab2f4c9d21f"
down_revision: str | Sequence[str] | None = "8358a5c14bac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ticker_extended table and related trigger."""
    op.execute("SET search_path TO turtle, public")
    op.execute("""
        CREATE TABLE turtle.ticker_extended (
            symbol TEXT NOT NULL,
            type TEXT,
            name TEXT,
            sector TEXT,
            industry TEXT,
            average_volume BIGINT,
            average_price NUMERIC(20, 10),
            dividend_yield NUMERIC(12, 6),
            market_cap BIGINT,
            pe NUMERIC(12, 6),
            forward_pe NUMERIC(12, 6),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_ticker_extended PRIMARY KEY (symbol),
            CONSTRAINT fk_ticker_extended_symbol FOREIGN KEY (symbol) REFERENCES turtle.ticker(unique_name) ON DELETE CASCADE
        )
    """)

    op.execute("COMMENT ON TABLE turtle.ticker_extended IS 'Extended ticker information from EODHD US quote delayed API'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.symbol IS 'Unique ticker identifier (AAPL.US), references ticker.unique_name'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.type IS 'Security type (e.g., Common Stock, ETF)'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.name IS 'Company or security name'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.sector IS 'Business sector'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.industry IS 'Industry classification'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.average_volume IS 'Average trading volume'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.average_price IS 'Fifty day average price'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.dividend_yield IS 'Dividend yield percentage'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.market_cap IS 'Market capitalization'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.pe IS 'Price to earnings ratio'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.forward_pe IS 'Forward price to earnings ratio'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.ticker_extended.updated_at IS 'Timestamp when the record was last updated'")

    op.execute("""
        CREATE TRIGGER ticker_extended_updated_at
            BEFORE UPDATE ON turtle.ticker_extended
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_updated_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER ticker_extended_updated_at ON turtle.ticker_extended IS
        'Automatically updates updated_at column on row modification'
    """)


def downgrade() -> None:
    """Drop ticker_extended table and related trigger."""
    op.execute("DROP TRIGGER IF EXISTS ticker_extended_updated_at ON turtle.ticker_extended")
    op.execute("DROP TABLE IF EXISTS ticker_extended CASCADE")
