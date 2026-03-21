import logging
from turtle.data.models import SymbolGroup
from turtle.repositories.tables import symbol_group_table

from sqlalchemy import Engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


class SymbolGroupRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_symbol_group_list(self, symbol_group: str) -> list[SymbolGroup]:
        table = symbol_group_table
        stmt = (
            select(table.c.symbol_group, table.c.symbol, table.c.rate).where(table.c.symbol_group == symbol_group).order_by(table.c.symbol)
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        symbol_list = [SymbolGroup(*row) for row in rows]
        logger.debug(f"{len(symbol_list)} symbols returned from database")
        return symbol_list

    def update_symbol_group(self, symbol_group: str, symbol: str, rate: float | None = None) -> None:
        values = {"symbol": symbol, "symbol_group": symbol_group, "rate": rate}
        table = symbol_group_table
        stmt = pg_insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_group", "symbol"],
            set_={
                "rate": stmt.excluded.rate,
                "modified_at": func.current_timestamp(),
            },
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
