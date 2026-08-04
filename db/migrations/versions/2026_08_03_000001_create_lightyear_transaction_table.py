"""create_lightyear_transaction_table

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-08-03 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "c7d8e9f0a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create lightyear_transaction table and modified_at trigger."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        CREATE TABLE turtle.lightyear_transaction (
            reference        TEXT           NOT NULL,
            transacted_at    TIMESTAMP      NOT NULL,
            ticker_code      TEXT           NOT NULL,
            isin             TEXT           NOT NULL,
            transaction_type TEXT           NOT NULL,
            quantity         NUMERIC(20, 9) NOT NULL,
            currency         TEXT           NOT NULL,
            price            NUMERIC(20, 9) NOT NULL,
            gross_amount     NUMERIC(20, 2) NOT NULL,
            fee              NUMERIC(20, 2) NOT NULL,
            tax              NUMERIC(20, 2) NOT NULL,
            net_amount       NUMERIC(20, 2) NOT NULL,
            source_file      TEXT           NOT NULL,
            created_at       TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modified_at      TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_lightyear_transaction PRIMARY KEY (reference),
            CONSTRAINT lightyear_transaction_type_check CHECK (transaction_type IN ('buy', 'sell'))
        )
    """)

    op.execute("COMMENT ON TABLE turtle.lightyear_transaction IS 'Buy/Sell executions imported from Lightyear account statements'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.reference IS 'Lightyear order reference, unique key used for idempotent re-import'")
    op.execute("""
        COMMENT ON COLUMN turtle.lightyear_transaction.transacted_at IS
        'Execution timestamp exactly as printed in the statement. Stored without a time zone because
         the statement does not document one; converting under a guessed zone would be lossy'
    """)
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.ticker_code IS 'Ticker symbol in TICKER.US format'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.isin IS 'ISIN as reported by the statement'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.transaction_type IS 'Lowercased transaction side: buy or sell'")
    op.execute("""
        COMMENT ON COLUMN turtle.lightyear_transaction.quantity IS
        'Number of shares transacted, always positive — the side is carried by transaction_type'
    """)
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.currency IS 'Settlement currency of the transaction'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.price IS 'Price per share'")
    op.execute("""
        COMMENT ON COLUMN turtle.lightyear_transaction.gross_amount IS
        'Gross amount as printed: cost including fee on a buy, proceeds before fee on a sell'
    """)
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.fee IS 'Broker fee, 0 when the statement cell is empty'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.tax IS 'Withholding tax, 0 when the statement cell is empty'")
    op.execute("""
        COMMENT ON COLUMN turtle.lightyear_transaction.net_amount IS
        'Net amount as printed: quantity times price on a buy, proceeds after fee on a sell'
    """)
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.source_file IS 'File name of the statement the row was first imported from'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.created_at IS 'Timestamp when the record was created'")
    op.execute("COMMENT ON COLUMN turtle.lightyear_transaction.modified_at IS 'Timestamp when the record was last updated'")

    op.execute("""
        CREATE TRIGGER lightyear_transaction_modified_at
            BEFORE UPDATE ON turtle.lightyear_transaction
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_modified_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER lightyear_transaction_modified_at ON turtle.lightyear_transaction IS
        'Automatically updates modified_at column on row modification'
    """)


def downgrade() -> None:
    """Drop lightyear_transaction table and trigger."""
    op.execute("DROP TRIGGER IF EXISTS lightyear_transaction_modified_at ON turtle.lightyear_transaction")
    op.execute("DROP TABLE IF EXISTS turtle.lightyear_transaction CASCADE")
