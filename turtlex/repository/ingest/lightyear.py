import logging
from dataclasses import asdict

from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert

from turtlex.model import LightyearTransaction
from turtlex.repository.tables import lightyear_transaction_table

logger = logging.getLogger(__name__)


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
