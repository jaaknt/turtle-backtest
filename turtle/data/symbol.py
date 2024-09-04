import requests
import logging
from typing import List, Dict, Any
from psycopg_pool import ConnectionPool
from psycopg.rows import TupleRow

from turtle.data.models import Symbol

logger = logging.getLogger(__name__)


class SymbolRepo:
    def __init__(self, pool: ConnectionPool, api_key: str):
        self.pool = pool
        self.api_key = api_key
        self.symbol_list: List[Symbol] = []

    def map_eodhd_symbol_list(self, ticker: Dict[str, Any]) -> Dict[str, Any]:
        place_holders = {}
        place_holders["symbol"] = ticker["Code"]
        place_holders["name"] = ticker["Name"]
        place_holders["exchange"] = ticker["Exchange"]
        place_holders["country"] = ticker["Country"]
        place_holders["currency"] = ticker["Currency"]
        place_holders["isin"] = ticker["Isin"]
        place_holders["symbol_type"] = "stock"
        place_holders["source"] = "eodhd"
        place_holders["status"] = "ACTIVE"

        return place_holders

    def _get_symbol_list_db(self, country: str) -> List[TupleRow]:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT symbol, name, exchange, country
                        FROM turtle.ticker
                        WHERE country = %s
                        AND status = 'ACTIVE'     
                        ORDER BY symbol       
                    """,
                    (country,),
                )
                result = cursor.fetchall()
        return result

    def get_symbol_list(self, country: str) -> List[Symbol]:
        result = self._get_symbol_list_db(country)
        self.symbol_list = [Symbol(*symbol) for symbol in result]
        logger.debug(f"{len(self.symbol_list)} symbols returned from database")

        return self.symbol_list

    def save_symbol_list(self, place_holders: Dict[str, Any]) -> None:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                logger.debug(
                    f"Inserting symbol {place_holders['symbol']} into database"
                )
                cursor.execute(
                    """
                    INSERT INTO turtle.ticker
                    (symbol, "name", exchange, country, currency, isin, symbol_type, source, status)
                    VALUES(%(symbol)s, %(name)s, %(exchange)s, %(country)s, %(currency)s, %(isin)s, %(symbol_type)s, %(source)s, %(status)s) 
                        ON CONFLICT (symbol) DO UPDATE SET              
                    ("name", exchange, country, currency, isin, symbol_type, source, modified_at) = 
                    (EXCLUDED."name", EXCLUDED.exchange, EXCLUDED.country, EXCLUDED.currency, EXCLUDED.isin, EXCLUDED.symbol_type, EXCLUDED."source", CURRENT_TIMESTAMP)         
                    """,
                    place_holders,
                )
                connection.commit()

    def get_eodhd_exchange_symbol_list(
        self, exchange_code: str
    ) -> List[Dict[str, Any]]:
        url = f"https://eodhd.com/api/exchange-symbol-list/{exchange_code}?api_token={self.api_key}&fmt=json&type=stock"
        data = requests.get(url).json()
        # print(data)
        # print(type(data))
        # print(type(data[0]))
        return data

    def update_symbol_list(self) -> None:
        for exchange in ["NYSE", "NASDAQ"]:
            data = self.get_eodhd_exchange_symbol_list(exchange)
            for ticker in data:
                if "-" not in ticker["Code"]:
                    place_holders = self.map_eodhd_symbol_list(ticker)
                    self.save_symbol_list(place_holders)
