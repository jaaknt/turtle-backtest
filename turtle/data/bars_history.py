from psycopg import connection
from datetime import datetime
import logging

from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient

from turtle.data import symbol

logger = logging.getLogger("__name__")


def map_alpaca_bars_history(row) -> dict:
    place_holders = {}
    place_holders["symbol"] = row[0][0]
    place_holders["hdate"] = row[0][1].to_pydatetime().date()
    place_holders["open"] = row[1]
    place_holders["high"] = row[2]
    place_holders["low"] = row[3]
    place_holders["close"] = row[4]
    place_holders["volume"] = row[5]
    place_holders["trade_count"] = row[6]
    place_holders["source"] = "alpaca"

    return place_holders


def save_bars_history(conn: connection, place_holders: dict) -> None:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute(
        """
           INSERT INTO turtle.bars_history
           (symbol, hdate, open, high, low, close, volume, trade_count, source)
           VALUES(%(symbol)s, %(hdate)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(trade_count)s, %(source)s) 
           ON CONFLICT (symbol, hdate) DO NOTHING                
                   """,
        place_holders,
    )
    conn.commit()


def update_historal_data(
    conn: connection, api_key: str, secret_key: str, starting_symbol: str
) -> None:
    stock_data_client = StockHistoricalDataClient(api_key, secret_key)
    symbol_list = symbol.get_symbol_list(conn, "USA")
    for _symbol in symbol_list:
        if _symbol >= starting_symbol:
            request = StockBarsRequest(
                symbol_or_symbols=_symbol,
                start=datetime(year=2024, month=8, day=1).date(),
                end=datetime(year=2024, month=8, day=10).date(),
                limit=10000,
                timeframe=TimeFrame.Day,
                feed=DataFeed.SIP,
            )
            data = stock_data_client.get_stock_bars(request_params=request)
            if data.df.empty:
                logger.info(f"{datetime.now():%c} Unknown symbol: {_symbol}")
            else:
                logger.info(f"{datetime.now():%c} Saving: {_symbol}")
                for row in data.df.itertuples(index=True):
                    place_holders = map_alpaca_bars_history(row)
                    save_bars_history(conn, place_holders)
                    # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))
        else:
            logger.info(f"{datetime.now():%c} Symbol: {_symbol} already exists")
