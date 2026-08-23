"""create_signal_table

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-08-23 00:00:01.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4b5c6d7e8f9"
down_revision: str | Sequence[str] | None = "f3a4b5c6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create signal table and modified_at trigger."""
    op.execute("SET search_path TO turtle, public")

    op.execute("""
        CREATE TABLE turtle.signal (
            id               BIGINT      GENERATED ALWAYS AS IDENTITY,
            trading_strategy TEXT        NOT NULL,
            ranking_strategy TEXT        NOT NULL,
            symbol           TEXT        NOT NULL,
            signal_date      DATE        NOT NULL,
            ranking          SMALLINT    NOT NULL,
            signal_close     FLOAT8      NOT NULL,
            parameters       JSONB       NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modified_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_signal PRIMARY KEY (id),
            CONSTRAINT uq_signal_trading_strategy_symbol_signal_date UNIQUE (trading_strategy, symbol, signal_date),
            CONSTRAINT signal_ranking_check CHECK (ranking BETWEEN 0 AND 100),
            CONSTRAINT signal_close_positive_check CHECK (signal_close > 0 AND signal_close < 'Infinity'),
            CONSTRAINT signal_parameters_object_check CHECK (jsonb_typeof(parameters) = 'object')
        )
    """)

    op.execute("COMMENT ON TABLE turtle.signal IS 'One row per signal a strategy emitted, keyed by the strategy variant label'")
    op.execute("COMMENT ON COLUMN turtle.signal.id IS 'Surrogate key, generated always as identity and never supplied by the writer'")
    op.execute("""
        COMMENT ON COLUMN turtle.signal.trading_strategy IS
        'Full variant label supplied by signal-runner --persist-label, e.g. bk50d_s12_v2.0, defaulting to
         the --trading-strategy registry key. Part of the natural key so the s12/s16/s20 variants of one
         strategy do not overwrite each other. Nothing validates that the label matches the parameters
         actually used - turtle.job_runs.parameters is the authoritative record of those, on hosts where
         job-run logging is enabled'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.signal.ranking_strategy IS
        'Ranking scheme that produced ranking, e.g. qullamaggie. Deliberately NOT part of the natural key:
         a later run of the same trading strategy under a different scheme replaces the row, and this
         column names whichever scheme won'
    """)
    op.execute("COMMENT ON COLUMN turtle.signal.symbol IS 'Ticker symbol in TICKER.US format, matching turtle.daily_bars.symbol'")
    op.execute("""
        COMMENT ON COLUMN turtle.signal.signal_date IS
        'Trading day the signal fired: the bar every entry filter was evaluated on, already closed by the
         time the signal appears'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.signal.ranking IS
        'Score from ranking_strategy, 0-100; the two columns always travel together. Stored ungated -
         signal-runner --min-signal-ranking narrows what it prints, never what it writes, so readers apply
         their own ranking >= threshold. Thresholds are scheme-relative, so read this with
         ranking_strategy and never alone'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.signal.signal_close IS
        'Raw (unadjusted) close on signal_date, the bar every entry filter was evaluated on. Not the entry
         fill: the backtest enters at the next trading day adjusted open'
    """)
    op.execute("""
        COMMENT ON COLUMN turtle.signal.parameters IS
        'Per-signal values as of signal_date, flat: the strategy reported indicators - see
         QullamaggieStrategy.REPORTED_INDICATORS, which is authoritative and has changed before - plus
         next_open, the raw open of the following bar. A key is absent, never null, when not reported or
         not computed; next_open is missing until a bar after signal_date has been loaded. Only the
         object-ness of this column is enforced, so a reader must not assume any particular key is
         present. The upsert merges next_open rather than replacing the object, so that one key may
         predate the row other columns - every other key is rewritten by the latest run. Per-signal payload only: the run configuration that produced it is in
         turtle.job_runs.parameters, on hosts where job-run logging is enabled'
    """)
    op.execute("COMMENT ON COLUMN turtle.signal.created_at IS 'Timestamp when the record was created'")
    op.execute("""
        COMMENT ON COLUMN turtle.signal.modified_at IS
        'Timestamp when the record was last written. The upsert rewrites every row it carries, so this
         moves on every persist run whether or not anything changed - use created_at for first-seen'
    """)

    op.execute("CREATE INDEX idx_signal_signal_date ON turtle.signal (signal_date DESC)")

    op.execute("""
        CREATE TRIGGER signal_modified_at
            BEFORE UPDATE ON turtle.signal
            FOR EACH ROW
            EXECUTE FUNCTION turtle.update_modified_at_column()
    """)
    op.execute("""
        COMMENT ON TRIGGER signal_modified_at ON turtle.signal IS
        'Automatically updates modified_at column on row modification'
    """)


def downgrade() -> None:
    """Drop signal table and trigger."""
    op.execute("DROP TRIGGER IF EXISTS signal_modified_at ON turtle.signal")
    op.execute("DROP TABLE IF EXISTS turtle.signal CASCADE")
