import requests
import logging
from typing import List
from psycopg import connection

logger = logging.getLogger("__name__")


def map_eodhd_symbol_list(ticker: dict) -> dict:
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


def get_symbol_list(conn: connection, country: str) -> List[str]:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute(
        """
           SELECT symbol
             FROM turtle.ticker
            WHERE country = %s
              AND status = 'ACTIVE'     
            ORDER BY symbol       
                   """,
        (country,),
    )
    result = cursor.fetchall()
    symbol_list = list(map(" ".join, result))

    logger.info(f"{len(symbol_list)} symbols returned from database")

    return symbol_list


def save_symbol_list(conn: connection, place_holders: dict) -> None:
    cursor = conn.cursor()
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
    conn.commit()


def get_eodhd_exchange_symbol_list(exchange_code: str, api_key: str) -> list[dict]:
    url = f"https://eodhd.com/api/exchange-symbol-list/{exchange_code}?api_token={api_key}&fmt=json&type=stock"
    print(url)
    data = requests.get(url).json()
    # print(data)
    # print(type(data))
    # print(type(data[0]))
    return data


def update_exchange_symbol_list(conn: connection, api_key: str) -> None:
    for exchange in ["NYSE", "NASDAQ"]:
        data = get_eodhd_exchange_symbol_list(exchange, api_key)
        for ticker in data:
            if "-" not in ticker["Code"]:
                place_holders = map_eodhd_symbol_list(ticker)
                save_symbol_list(conn, place_holders)
    """
    data = get_eodhd_exchange_symbol_list("NYSE", api_key)
    for ticker in data:
        if "-" not in ticker["Code"]:
            place_holders = map_eodhd_symbol_list(ticker)
            save_symbol_list(conn, place_holders)
    data = get_eodhd_exchange_symbol_list("NASDAQ", api_key)
    for ticker in data:
        if "-" not in ticker["Code"]:
            place_holders = map_eodhd_symbol_list(ticker)
            save_symbol_list(conn, place_holders)
    """
