import logging
from turtle.repository.models import SymbolGroup
from turtle.repository.tables import ticker_group_table

from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


class SymbolGroupRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_symbol_group_list(self, ticker_group: str) -> list[SymbolGroup]:
        table = ticker_group_table
        stmt = select(table.c.code, table.c.ticker_code, table.c.rate).where(table.c.code == ticker_group).order_by(table.c.ticker_code)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        symbol_list = [SymbolGroup(*row) for row in rows]
        logger.debug(f"{len(symbol_list)} symbols returned from database")
        return symbol_list

    def update_symbol_group(self, ticker_group: str, ticker_code: str, rate: float | None = None) -> None:
        values = {"code": ticker_group, "ticker_code": ticker_code, "rate": rate}
        table = ticker_group_table
        stmt = pg_insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code", "ticker_code"],
            set_={"rate": stmt.excluded.rate},
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
