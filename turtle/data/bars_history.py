from psycopg import connection
from datetime import datetime
import logging
import pandas as pd

from typing import List, Tuple

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


def get_bars_history(
    conn: connection, ticker: str, start_date: datetime, end_date: datetime
) -> List[Tuple]:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute(
        """
           SELECT hdate, open, high, low, close, volume, trade_count
             FROM turtle.bars_history
            WHERE symbol = %s
              AND hdate >= %s
              AND hdate <= %s     
            ORDER BY hdate       
                   """,
        (ticker, start_date, end_date),
    )
    result = cursor.fetchall()
    # print(type(result))
    # print(type(result[0]))
    return result
    # symbol_list = list(map(" ".join, result))

    # logger.info(f"{len(symbol_list)} symbols returned from database")


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
                logger.info(f"Unknown symbol: {_symbol}")
            else:
                logger.info(f"Saving: {_symbol}")
                for row in data.df.itertuples(index=True):
                    place_holders = map_alpaca_bars_history(row)
                    save_bars_history(conn, place_holders)
                    # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))
        else:
            logger.info(f"Symbol: {_symbol} already exists")


def update_ticker_history(
    conn: connection,
    api_key: str,
    secret_key: str,
    ticker: str,
    start_date: datetime,
    end_date: datetime,
) -> None:
    stock_data_client = StockHistoricalDataClient(api_key, secret_key)

    request = StockBarsRequest(
        symbol_or_symbols=ticker,
        start=start_date,
        end=end_date,
        limit=10000,
        timeframe=TimeFrame.Day,
        feed=DataFeed.SIP,
    )
    data = stock_data_client.get_stock_bars(request_params=request)
    if data.df.empty:
        logger.info(f"Unknown symbol: {ticker}")
    else:
        logger.info(f"Saving: {ticker}")
        for row in data.df.itertuples(index=True):
            place_holders = map_alpaca_bars_history(row)
            save_bars_history(conn, place_holders)
            # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))


def convert_df(query_result: List[Tuple], timeframe: str) -> pd.DataFrame:
    dtypes = {
        "hdate": "string",
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "int64",
        "trade_count": "int64",
    }
    columns = ["hdate", "open", "high", "low", "close", "volume", "trade_count"]

    # Create a pandas DataFrame from the fetched data
    df = pd.DataFrame(query_result, columns=columns).astype(dtypes)
    df["hdate"] = pd.to_datetime(df["hdate"])
    df = df.set_index(["hdate"])

    if timeframe == "day":
        return df
    elif timeframe == "week":
        df_weekly = df.resample("W").agg(
            {
                "open": "first",  # First day's open price
                "high": "max",  # Highest price of the week
                "low": "min",  # Lowest price of the week
                "close": "last",  # Last day's close price
                "volume": "sum",  # Last day's close price
                "trade_count": "sum",  # Last day's close price
            }
        )
        return df_weekly


def get_ticker_history(
    conn: connection,
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,  # day, week
) -> pd.DataFrame:
    query_result = get_bars_history(conn, ticker, start_date, end_date)
    df = convert_df(query_result, timeframe)

    # logger.info(df.tail(5))
    return df
