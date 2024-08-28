import psycopg
from datetime import datetime
import logging
import pandas as pd

from typing import List, Tuple

from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient

from turtle.data.symbol import SymbolRepo
from turtle.data.models import Symbol

logger = logging.getLogger("__name__")


class BarsHistoryRepo:
    def __init__(
        self,
        connection: psycopg.Connection,
        ticker_api_key: str,
        history_api_key: str,
        history_api_secret: str,
    ):
        self.connection: psycopg.Connection = connection
        self.history_api_key: str = history_api_key
        self.history_api_secret: str = history_api_secret
        self.stock_data_client = StockHistoricalDataClient(
            history_api_key, history_api_secret
        )
        self.ticker = SymbolRepo(connection, ticker_api_key)
        self.symbol_list = []

    def map_alpaca_bars_history(self, row) -> dict:
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
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> List[Tuple]:
        # Creating a cursor object using the cursor() method
        with self.connection.cursor() as cursor:
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
        # logger.debug(f"{len(symbol_list)} symbols returned from database")

        return result

    def save_bars_history(self, place_holders: dict) -> None:
        # Creating a cursor object using the cursor() method
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO turtle.bars_history
                (symbol, hdate, open, high, low, close, volume, trade_count, source)
                VALUES(%(symbol)s, %(hdate)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(trade_count)s, %(source)s) 
                ON CONFLICT (symbol, hdate) DO NOTHING                
                        """,
                place_holders,
            )
            self.connection.commit()

    def update_historal_data(self, starting_symbol: str) -> None:
        # stock_data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.symbol_list: List[Symbol] = self.ticker.get_symbol_list("USA")
        for symbol_rec in self.symbol_list:
            if symbol_rec.symbol >= starting_symbol:
                request = StockBarsRequest(
                    symbol_or_symbols=symbol_rec.symbol,
                    start=datetime(year=2024, month=8, day=1),
                    end=datetime(year=2024, month=8, day=10),
                    limit=10000,
                    timeframe=TimeFrame(1, TimeFrameUnit.Day),
                    feed=DataFeed.SIP,
                )
                data = self.stock_data_client.get_stock_bars(request_params=request)
                if data.df.empty:  # type: ignore
                    logger.info(f"Unknown symbol: {symbol_rec.symbol}")
                else:
                    logger.info(f"Saving: {symbol_rec.symbol}")
                    for row in data.df.itertuples(index=True):  # type: ignore
                        place_holders = self.map_alpaca_bars_history(row)
                        self.save_bars_history(place_holders)
                        # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))
            else:
                logger.info(f"Symbol: {symbol_rec.symbol} already exists")

    def update_ticker_history(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        # stock_data_client = StockHistoricalDataClient(self.api_key, self.secret_key)

        request = StockBarsRequest(
            symbol_or_symbols=ticker,
            start=start_date,
            end=end_date,
            limit=10000,
            timeframe=TimeFrame(1, TimeFrameUnit.Day),
            feed=DataFeed.SIP,
        )
        data = self.stock_data_client.get_stock_bars(request_params=request)
        if data.df.empty:  # type: ignore
            logger.info(f"Unknown symbol: {ticker}")
        else:
            logger.info(f"Saving: {ticker}")
            for row in data.df.itertuples(index=True):  # type: ignore
                place_holders = self.map_alpaca_bars_history(row)
                self.save_bars_history(place_holders)
                # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))

    def convert_df(self, query_result: List[Tuple], timeframe: str) -> pd.DataFrame:
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
        else:
            return pd.DataFrame()

    def get_ticker_history(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,  # day, week
    ) -> pd.DataFrame:
        query_result = self.get_bars_history(ticker, start_date, end_date)
        df = self.convert_df(query_result, timeframe)

        # logger.info(df.tail(5))
        return df
