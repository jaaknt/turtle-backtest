"""rebuild_ticker_table_to_match_application_schema

Revision ID: 1377bceba44a
Revises: 4ab2f4c9d21f
Create Date: 2026-03-14 21:57:29.527162+00:00

The original ticker table used a different schema (unique_name, code, type,
created_at, updated_at) that diverged from the application's table definition
in tables.py which expects (symbol, symbol_type, source, status, modified_at).
This migration drops and recreates ticker with the correct schema.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1377bceba44a"
down_revision: str | Sequence[str] | None = "4ab2f4c9d21f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop and recreate ticker table with the schema matching tables.py."""
    op.execute("SET search_path TO turtle, public")

    op.execute("DROP TRIGGER IF EXISTS ticker_updated_at ON turtle.ticker")
    op.execute("DROP TABLE IF EXISTS turtle.ticker CASCADE")

    op.execute("""
        CREATE TABLE turtle.ticker (
            symbol      TEXT        NOT NULL,
            name        TEXT,
            exchange    TEXT,
            country     TEXT,
            currency    TEXT,
            isin        TEXT,
            symbol_type TEXT,
            source      TEXT,
            status      TEXT,
            modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_ticker PRIMARY KEY (symbol)
        )
    """)

    op.execute("COMMENT ON TABLE turtle.ticker IS 'Stock tickers from EODHD'")
    op.execute("COMMENT ON COLUMN turtle.ticker.symbol IS 'Ticker symbol (e.g. AAPL)'")
    op.execute("COMMENT ON COLUMN turtle.ticker.symbol_type IS 'Asset type (e.g. stock)'")
    op.execute("COMMENT ON COLUMN turtle.ticker.source IS 'Data source (e.g. eodhd)'")
    op.execute("COMMENT ON COLUMN turtle.ticker.status IS 'Ticker status (e.g. ACTIVE)'")
    op.execute("COMMENT ON COLUMN turtle.ticker.modified_at IS 'Timestamp of last modification'")


def downgrade() -> None:
    """Restore the original ticker table schema."""
    op.execute("DROP TABLE IF EXISTS turtle.ticker CASCADE")

    op.execute("""
        CREATE TABLE turtle.ticker (
            unique_name TEXT        NOT NULL,
            code        TEXT        NOT NULL,
            name        TEXT        NOT NULL,
            country     TEXT,
            exchange    TEXT        NOT NULL,
            currency    TEXT,
            type        TEXT,
            isin        TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_ticker PRIMARY KEY (unique_name),
            CONSTRAINT uq_ticker_code_exchange UNIQUE (code, exchange)
        )
    """)

    op.execute("""
        CREATE TRIGGER ticker_updated_at
            BEFORE UPDATE ON turtle.ticker
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_updated_at_column()
    """)
