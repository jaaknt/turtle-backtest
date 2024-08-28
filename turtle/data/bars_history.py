import psycopg
import logging
import pandas as pd
from datetime import datetime
from typing import List
from dataclasses import asdict

from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient

from turtle.data.models import Bar

logger = logging.getLogger("__name__")


class BarsHistoryRepo:
    def __init__(
        self,
        connection: psycopg.Connection,
        alpaca_api_key: str,
        alpaca_api_secret: str,
    ):
        self.connection: psycopg.Connection = connection
        self.stock_data_client = StockHistoricalDataClient(
            alpaca_api_key, alpaca_api_secret
        )

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
    ) -> List[Bar]:
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
        bar_list = [Bar(*bar) for bar in result]
        # logger.debug(f"{len(symbol_list)} symbols returned from database")
        return bar_list

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

    def update_bars_history(
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
            logger.debug(f"Unknown symbol: {ticker}")
        else:
            logger.debug(f"Saving: {ticker}")
            for row in data.df.itertuples(index=True):  # type: ignore
                place_holders = self.map_alpaca_bars_history(row)
                self.save_bars_history(place_holders)
                # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))

    def convert_df(self, bar_list: List[Bar], timeframe: str) -> pd.DataFrame:
        dtypes = {
            "hdate": "string",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "int64",
            "trade_count": "int64",
        }
        # columns = ["hdate", "open", "high", "low", "close", "volume", "trade_count"]

        # Create a pandas DataFrame from the fetched data
        bar_dicts = [asdict(bar) for bar in bar_list]
        df = pd.DataFrame(bar_dicts).astype(dtypes)
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
        bar_list = self.get_bars_history(ticker, start_date, end_date)
        df = (
            self.convert_df(bar_list, timeframe)
            if len(bar_list) > 0
            else pd.DataFrame()
        )

        return df
