import logging
from turtle.data.models import Symbol
from turtle.data.tables import ticker_table
from typing import Any

import httpx
from httpx import URL
from sqlalchemy import Engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


class SymbolRepo:
    def __init__(self, engine: Engine, api_key: str):
        self.engine = engine
        self.api_key = api_key

    def map_eodhd_symbol_list(self, ticker: dict[str, Any]) -> dict[str, Any]:
        return {
            "unique_symbol": ticker["Code"] + ".US",
            "exchange_symbol": ticker["Code"],
            "name": ticker["Name"],
            "exchange": ticker["Exchange"],
            "country": ticker["Country"],
            "currency": ticker["Currency"],
            "isin": ticker["Isin"],
            "type": "stock",
        }

    def _get_symbol_list_db(self, country: str) -> list[Any]:
        table = ticker_table
        stmt = (
            select(table.c.unique_symbol, table.c.name, table.c.exchange, table.c.country)
            .where(table.c.country == country)
            .order_by(table.c.unique_symbol)
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return list(result.fetchall())

    def get_symbol_list(self, country: str, symbol: str = "") -> list[Symbol]:
        result = self._get_symbol_list_db(country)
        symbol_list = [Symbol(*row) for row in result]
        if symbol:
            symbol_list = [s for s in symbol_list if s.symbol >= symbol]
        logger.debug(f"{len(symbol_list)} symbols returned from database")
        return symbol_list

    def save_symbol_list(self, values: dict[str, Any]) -> None:
        self.save_symbol_list_bulk([values])

    def save_symbol_list_bulk(self, values_list: list[dict[str, Any]]) -> None:
        if not values_list:
            return
        table = ticker_table
        stmt = pg_insert(table).values(values_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=["unique_symbol"],
            set_={
                "exchange_symbol": stmt.excluded.exchange_symbol,
                "name": stmt.excluded.name,
                "exchange": stmt.excluded.exchange,
                "country": stmt.excluded.country,
                "currency": stmt.excluded.currency,
                "isin": stmt.excluded.isin,
                "type": stmt.excluded.type,
                "updated_at": func.current_timestamp(),
            },
        )
        with self.engine.begin() as conn:
            logger.debug(f"Bulk inserting {len(values_list)} symbols into database")
            conn.execute(stmt)

    def get_eodhd_exchange_symbol_list(self, exchange_code: str) -> list[dict[str, Any]]:
        params = {"api_token": self.api_key, "fmt": "json", "type": "stock"}
        url = URL(f"https://eodhd.com/api/exchange-symbol-list/{exchange_code}", params=params)
        safe_params = {k: ("***" if k == "api_token" else v) for k, v in params.items()}
        base = f"https://eodhd.com/api/exchange-symbol-list/{exchange_code}"
        logger.debug(f"Fetching symbol list from EODHD: {URL(base, params=safe_params)}")
        response = httpx.get(url)
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
        return data

    def update_symbol_list(self) -> None:
        for exchange in ["NYSE", "NASDAQ"]:
            data = self.get_eodhd_exchange_symbol_list(exchange)
            values_list = [self.map_eodhd_symbol_list(ticker) for ticker in data if "-" not in ticker["Code"]]
            self.save_symbol_list_bulk(values_list)
