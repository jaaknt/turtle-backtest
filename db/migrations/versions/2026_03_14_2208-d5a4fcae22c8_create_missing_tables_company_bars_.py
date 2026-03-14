"""create_missing_tables_company_bars_history_symbol_group

Revision ID: d5a4fcae22c8
Revises: 1377bceba44a
Create Date: 2026-03-14 22:08:03.483199+00:00

Creates the three tables that were missing from migrations but present in
tables.py: company, bars_history, and symbol_group.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5a4fcae22c8"
down_revision: str | Sequence[str] | None = "1377bceba44a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create company, bars_history, and symbol_group tables."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        CREATE TABLE turtle.company (
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
            CONSTRAINT pk_company PRIMARY KEY (symbol)
        )
    """)
    op.execute("COMMENT ON TABLE turtle.company IS 'Company fundamentals from Yahoo Finance'")

    op.execute("""
        CREATE TABLE turtle.bars_history (
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
            CONSTRAINT pk_bars_history PRIMARY KEY (symbol, hdate)
        )
    """)
    op.execute("COMMENT ON TABLE turtle.bars_history IS 'OHLCV price bars from Alpaca'")
    op.execute("CREATE INDEX idx_bars_history_ticker_date ON turtle.bars_history (symbol, hdate)")

    op.execute("""
        CREATE TABLE turtle.symbol_group (
            symbol_group TEXT    NOT NULL,
            symbol       TEXT    NOT NULL,
            rate         NUMERIC,
            modified_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_symbol_group PRIMARY KEY (symbol_group, symbol)
        )
    """)
    op.execute("COMMENT ON TABLE turtle.symbol_group IS 'Custom symbol watchlists/groups'")


def downgrade() -> None:
    """Drop company, bars_history, and symbol_group tables."""
    op.execute("DROP TABLE IF EXISTS turtle.symbol_group CASCADE")
    op.execute("DROP TABLE IF EXISTS turtle.bars_history CASCADE")
    op.execute("DROP TABLE IF EXISTS turtle.company CASCADE")
