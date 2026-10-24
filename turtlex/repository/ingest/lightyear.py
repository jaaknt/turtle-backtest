import logging
from dataclasses import asdict

from sqlalchemy import Engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from turtlex.model import LightyearTransaction
from turtlex.repository.tables import lightyear_transaction_table

logger = logging.getLogger(__name__)

# How far before a buy its triggering signal may sit, in calendar days
SIGNAL_LOOKBACK_DAYS = 30

# Join form rather than a correlated subquery in SET: only matched rows are updated, so the
# modified_at trigger never fires on a buy that still has no signal.
_LINK_SIGNALS_SQL = text("""
    UPDATE turtle.lightyear_transaction lt
    SET    signal_id = m.signal_id
    FROM  (SELECT DISTINCT ON (t.reference) t.reference, s.id AS signal_id
           FROM   turtle.lightyear_transaction t
           JOIN   turtle.signal s
                  ON  s.symbol = t.ticker_code
                  AND s.signal_date <  t.transacted_at::date
                  AND s.signal_date >= t.transacted_at::date - :lookback_days
           WHERE  t.transaction_type = 'buy' AND t.signal_id IS NULL
           ORDER  BY t.reference, s.signal_date DESC, s.ranking DESC, s.id) m
    WHERE  lt.reference = m.reference
    RETURNING lt.reference
""")


class LightyearRepository:
    """Sync Engine-based repository for Lightyear transaction writes."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def insert_transactions(self, transactions: list[LightyearTransaction]) -> int:
        """Insert transactions, skipping any whose reference is already stored.

        Conflicts do nothing, so a reference already stored from an earlier file keeps
        its original source_file — first seen wins. This is intended: overlapping
        statements repeat the same transaction by design.

        Args:
            transactions: Buy/Sell rows to store

        Returns:
            int: Number of rows actually inserted
        """
        if not transactions:
            return 0

        # LightyearTransaction's field names are the insert columns one for one, and it
        # carries no DB-owned created_at/modified_at, so asdict is the whole payload.
        values = [asdict(t) for t in transactions]
        stmt = pg_insert(lightyear_transaction_table).values(values)
        # RETURNING, not rowcount: rowcount is unreliable here (psycopg reports -1), while
        # ON CONFLICT DO NOTHING returns a row only for the inserts it actually accepted.
        on_conflict_stmt = stmt.on_conflict_do_nothing(index_elements=[lightyear_transaction_table.c.reference]).returning(
            lightyear_transaction_table.c.reference
        )
        with self._engine.begin() as conn:
            inserted = len(conn.execute(on_conflict_stmt).fetchall())
        logger.debug("Inserted %d of %d Lightyear transactions", inserted, len(transactions))
        return inserted

    def link_signals(self) -> int:
        """Point every unlinked buy at the signal it was most plausibly bought off.

        Covers all stored buys with a NULL signal_id, not just this run's inserts, so a buy
        imported before its signal was persisted is linked by a later import. A candidate signal
        has the buy's symbol and a signal_date within SIGNAL_LOOKBACK_DAYS calendar days strictly
        before the buy — a signal fires on a closed bar, so a same-day one cannot be the trigger.
        The newest wins, then the highest ranking. No ranking threshold applies. Sells are never
        linked.

        Returns:
            int: Number of buys linked by this call
        """
        with self._engine.begin() as conn:
            linked = len(conn.execute(_LINK_SIGNALS_SQL, {"lookback_days": SIGNAL_LOOKBACK_DAYS}).fetchall())
        logger.debug("Linked %d Lightyear buys to a signal", linked)
        return linked
