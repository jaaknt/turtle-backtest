import logging
from typing import Any
from psycopg_pool import ConnectionPool
from psycopg.rows import TupleRow

from turtle.data.models import SymbolGroup

logger = logging.getLogger(__name__)


class SymbolGroupRepo:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def map_symbol_group(self, symbol_group: str, symbol: str, rate: float | None) -> dict[str, float | None | str]:
        place_holders: dict[str, float | None | str] = {}
        place_holders["symbol"] = symbol
        place_holders["symbol_group"] = symbol_group
        place_holders["rate"] = rate

        return place_holders

    def _get_symbol_group_list_db(self, symbol_group: str) -> list[TupleRow]:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT symbol_group, symbol, rate
                        FROM turtle.symbol_group
                        WHERE symbol_group = %s
                        ORDER BY symbol
                    """,
                    (symbol_group,),
                )
                result = cursor.fetchall()
        return result

    def get_symbol_group_list(self, symbol_group: str) -> list[SymbolGroup]:
        result = self._get_symbol_group_list_db(symbol_group)
        self.symbol_list = [SymbolGroup(*symbol_group) for symbol_group in result]
        logger.debug(f"{len(self.symbol_list)} symbols returned from database")

        return self.symbol_list

    def save_symbol_group(self, place_holders: dict[str, Any]) -> None:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                # logger.debug(
                #    f"Inserting symbol {place_holders['symbol']} into database"
                # )
                cursor.execute(
                    """
                    INSERT INTO turtle.symbol_group(symbol_group, symbol, rate)
                    VALUES(%(symbol_group)s, %(symbol)s, %(rate)s)
                        ON CONFLICT (symbol_group, symbol) DO UPDATE SET
                        (rate, modified_at) = (EXCLUDED.rate, CURRENT_TIMESTAMP)
                    """,
                    place_holders,
                )
                connection.commit()

    def update_symbol_group(self, symbol_group: str, symbol: str, rate: float | None = None) -> None:
        place_holders = self.map_symbol_group(symbol_group, symbol, rate)
        self.save_symbol_group(place_holders)
