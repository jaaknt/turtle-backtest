"""create_eodhd_exchange_table

Revision ID: 7e3c9131289f
Revises: 9f929020ed09
Create Date: 2025-12-29 20:50:35.218148+00:00

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7e3c9131289f'
down_revision: str | Sequence[str] | None = '9f929020ed09'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("SET search_path TO turtle, public")
    op.execute("""
        CREATE TABLE turtle.exchange (
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            currency TEXT NOT NULL,
            country_iso3 TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_exchange PRIMARY KEY (code)
        )
    """)
    op.execute("COMMENT ON TABLE turtle.exchange IS 'List of stock exchanges from EODHD'")
    op.execute("COMMENT ON COLUMN turtle.exchange.code IS 'Unique code for the exchange (e.g., US, LSE, TASE)'")
    op.execute("COMMENT ON COLUMN turtle.exchange.name IS 'Full name of the exchange'")
    op.execute("COMMENT ON COLUMN turtle.exchange.country IS 'Country where the exchange is located'")
    op.execute("COMMENT ON COLUMN turtle.exchange.currency IS 'Default currency for the exchange'")
    op.execute("COMMENT ON COLUMN turtle.exchange.country_iso3 IS 'ISO 3166-1 alpha-3 country code'")
    op.execute("COMMENT ON COLUMN turtle.exchange.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.exchange.updated_at IS 'Timestamp when the record was last updated'")

    op.execute("""
        CREATE TRIGGER exchange_updated_at
            BEFORE UPDATE ON turtle.exchange
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_updated_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER exchange_updated_at ON turtle.exchange IS
        'Automatically updates updated_at column on row modification'
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("SET search_path TO turtle, public")
    op.execute("DROP TRIGGER IF EXISTS exchange_updated_at ON turtle.exchange")
    op.execute("DROP TABLE IF EXISTS turtle.exchange CASCADE")
