"""create_company_table

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
    """Create company table and related trigger."""
    op.execute("SET search_path TO turtle, public")
    op.execute("""
        CREATE TABLE turtle.company (
            ticker_code TEXT NOT NULL,
            type TEXT,
            name TEXT,
            sector TEXT,
            industry TEXT,
            average_volume BIGINT,
            average_price NUMERIC(20, 2),
            dividend_yield NUMERIC(12, 2),
            market_cap BIGINT,
            pe NUMERIC(12, 2),
            forward_pe NUMERIC(12, 2),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            -- CONSTRAINT fk_company_symbol FOREIGN KEY (ticker_code) REFERENCES turtle.ticker(code),
            CONSTRAINT pk_company PRIMARY KEY (ticker_code)
        )
    """)

    op.execute("COMMENT ON TABLE turtle.company IS 'Company information from EODHD US quote delayed API'")
    op.execute("COMMENT ON COLUMN turtle.company.ticker_code IS 'Unique ticker identifier (AAPL.US), references ticker.code'")
    op.execute("COMMENT ON COLUMN turtle.company.type IS 'Security type (e.g., Common Stock, ETF)'")
    op.execute("COMMENT ON COLUMN turtle.company.name IS 'Company or security name'")
    op.execute("COMMENT ON COLUMN turtle.company.sector IS 'Business sector'")
    op.execute("COMMENT ON COLUMN turtle.company.industry IS 'Industry classification'")
    op.execute("COMMENT ON COLUMN turtle.company.average_volume IS 'Average trading volume'")
    op.execute("COMMENT ON COLUMN turtle.company.average_price IS 'Fifty day average price'")
    op.execute("COMMENT ON COLUMN turtle.company.dividend_yield IS 'Dividend yield percentage'")
    op.execute("COMMENT ON COLUMN turtle.company.market_cap IS 'Market capitalization'")
    op.execute("COMMENT ON COLUMN turtle.company.pe IS 'Price to earnings ratio'")
    op.execute("COMMENT ON COLUMN turtle.company.forward_pe IS 'Forward price to earnings ratio'")
    op.execute("COMMENT ON COLUMN turtle.company.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.company.modified_at IS 'Timestamp when the record was last updated'")

    op.execute("""
        CREATE TRIGGER company_modified_at
            BEFORE UPDATE ON turtle.company
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_modified_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER company_modified_at ON turtle.company IS
        'Automatically updates modified_at column on row modification'
    """)


def downgrade() -> None:
    """Drop company table and related trigger."""
    op.execute("DROP TRIGGER IF EXISTS company_modified_at ON turtle.company")
    op.execute("DROP TABLE IF EXISTS turtle.company CASCADE")
