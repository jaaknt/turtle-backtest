import logging
from turtle.data.models import SymbolGroup
from turtle.data.tables import symbol_group_table
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


class SymbolGroupRepo:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def map_symbol_group(self, symbol_group: str, symbol: str, rate: float | None) -> dict[str, float | None | str]:
        return {
            "symbol": symbol,
            "symbol_group": symbol_group,
            "rate": rate,
        }

    def _get_symbol_group_list_db(self, symbol_group: str) -> list[Any]:
        table = symbol_group_table
        stmt = (
            select(table.c.symbol_group, table.c.symbol, table.c.rate).where(table.c.symbol_group == symbol_group).order_by(table.c.symbol)
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return list(result.fetchall())

    def get_symbol_group_list(self, symbol_group: str) -> list[SymbolGroup]:
        result = self._get_symbol_group_list_db(symbol_group)
        self.symbol_list = [SymbolGroup(*row) for row in result]
        logger.debug(f"{len(self.symbol_list)} symbols returned from database")
        return self.symbol_list

    def save_symbol_group(self, values: dict[str, Any]) -> None:
        table = symbol_group_table
        stmt = pg_insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_group", "symbol"],
            set_={
                "rate": stmt.excluded.rate,
                "modified_at": func.current_timestamp(),
            },
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def update_symbol_group(self, symbol_group: str, symbol: str, rate: float | None = None) -> None:
        values = self.map_symbol_group(symbol_group, symbol, rate)
        self.save_symbol_group(values)
