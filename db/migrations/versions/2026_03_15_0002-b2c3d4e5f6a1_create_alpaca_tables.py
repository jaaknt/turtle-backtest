"""create_alpaca_tables

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-15 00:02:00.000000+00:00

Creates symbol, bars_history, and company tables in the alpaca schema.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a1"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create alpaca.symbol, alpaca.bars_history, and alpaca.company tables."""
    op.execute("""
        CREATE TABLE alpaca.symbol (
            symbol       TEXT        NOT NULL,
            name         TEXT,
            exchange     TEXT,
            country      TEXT,
            currency     TEXT,
            isin         TEXT,
            symbol_type  TEXT,
            source       TEXT,
            status       TEXT,
            modified_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_alpaca_symbol PRIMARY KEY (symbol)
        )
    """)
    op.execute("COMMENT ON TABLE alpaca.symbol IS 'Symbol list from Alpaca'")

    op.execute("""
        CREATE TABLE alpaca.bars_history (
            symbol      TEXT        NOT NULL,
            hdate       TIMESTAMPTZ NOT NULL,
            open        NUMERIC(10, 4),
            high        NUMERIC(10, 4),
            low         NUMERIC(10, 4),
            close       NUMERIC(10, 4),
            volume      BIGINT,
            trade_count BIGINT,
            source      TEXT,
            modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_alpaca_bars_history PRIMARY KEY (symbol, hdate)
        )
    """)
    op.execute("COMMENT ON TABLE alpaca.bars_history IS 'OHLCV price bars from Alpaca'")
    op.execute("CREATE INDEX idx_alpaca_bars_history_symbol_date ON alpaca.bars_history (symbol, hdate)")

    op.execute("""
        CREATE TABLE alpaca.company (
            symbol               TEXT        NOT NULL,
            short_name           TEXT,
            country              TEXT,
            industry_code        TEXT,
            sector_code          TEXT,
            employees_count      BIGINT,
            dividend_rate        NUMERIC,
            trailing_pe_ratio    NUMERIC,
            forward_pe_ratio     NUMERIC,
            avg_volume           BIGINT,
            avg_price            NUMERIC,
            market_cap           NUMERIC,
            enterprice_value     NUMERIC,
            beta                 NUMERIC,
            shares_float         NUMERIC,
            short_ratio          NUMERIC,
            peg_ratio            NUMERIC,
            recommodation_mean   NUMERIC,
            number_of_analysyst  BIGINT,
            roa_value            NUMERIC,
            roe_value            NUMERIC,
            source               TEXT,
            modified_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_alpaca_company PRIMARY KEY (symbol)
        )
    """)
    op.execute("COMMENT ON TABLE alpaca.company IS 'Company fundamentals from Yahoo Finance (Alpaca pipeline)'")


def downgrade() -> None:
    """Drop alpaca.company, alpaca.bars_history, and alpaca.symbol tables."""
    op.execute("DROP TABLE IF EXISTS alpaca.company CASCADE")
    op.execute("DROP TABLE IF EXISTS alpaca.bars_history CASCADE")
    op.execute("DROP TABLE IF EXISTS alpaca.symbol CASCADE")
