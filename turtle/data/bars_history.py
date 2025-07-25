import logging
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from psycopg.rows import TupleRow
from dataclasses import asdict
from psycopg_pool import ConnectionPool

from alpaca.data.enums import DataFeed
from alpaca.data.models.bars import Bar as AlpacaBar
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame
from alpaca.data.timeframe import TimeFrameUnit as AlpacaTimeFrameUnit
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.enums import Adjustment

from turtle.data.models import Bar
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


class BarsHistoryRepo:
    def __init__(
        self,
        pool: ConnectionPool,
        alpaca_api_key: str,
        alpaca_api_secret: str,
    ):
        self.pool = pool
        self.stock_data_client = StockHistoricalDataClient(
            alpaca_api_key, alpaca_api_secret
        )

    def map_alpaca_bars_history(self, symbol: str, bar: AlpacaBar) -> Dict[str, Any]:
        place_holders = {}
        place_holders["symbol"] = symbol
        place_holders["hdate"] = bar.timestamp
        place_holders["open"] = bar.open
        place_holders["high"] = bar.high
        place_holders["low"] = bar.low
        place_holders["close"] = bar.close
        place_holders["volume"] = bar.volume
        place_holders["trade_count"] = bar.trade_count
        place_holders["source"] = "alpaca"

        return place_holders

    def _get_bars_history_db(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[TupleRow]:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT hdate, open, high, low, close, volume, trade_count
                        FROM turtle.bars_history
                        WHERE symbol = %s
                        AND hdate >= %s
                        AND hdate <= %s     
                        ORDER BY hdate       
                    """,
                    (symbol, start_date, end_date),
                )
                result = cursor.fetchall()
        return result

    def get_bars_history(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[Bar]:
        result = self._get_bars_history_db(symbol, start_date, end_date)
        bar_list = [Bar(*bar) for bar in result]
        # logger.debug(f"{len(symbol_list)} symbols returned from database")
        return bar_list

    def save_bars_history(self, place_holders: Dict[str, Any]) -> None:
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO turtle.bars_history
                    (symbol, hdate, open, high, low, close, volume, trade_count, source)
                    VALUES(%(symbol)s, %(hdate)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(trade_count)s, %(source)s) 
                    ON CONFLICT (symbol, hdate) DO UPDATE SET
                    (open, high, low, close, volume, trade_count, source, modified_at) =
                    (EXCLUDED.open, EXCLUDED.high, EXCLUDED.low, EXCLUDED.close, EXCLUDED.volume, EXCLUDED.trade_count, EXCLUDED.source, CURRENT_TIMESTAMP)                
                   """,
                    place_holders,
                )
            connection.commit()

    def _map_timeframe_unit(self, time_frame_unit: TimeFrameUnit) -> AlpacaTimeFrameUnit:
        """Map internal TimeFrameUnit to AlpacaTimeFrameUnit"""
        mapping = {
            TimeFrameUnit.DAY: AlpacaTimeFrameUnit.Day,
            TimeFrameUnit.WEEK: AlpacaTimeFrameUnit.Week,
        }
        return mapping.get(time_frame_unit, AlpacaTimeFrameUnit.Day)

    def update_bars_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ) -> None:
        # stock_data_client = StockHistoricalDataClient(self.api_key, self.secret_key)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            start=start_date,
            end=end_date,
            limit=10000,
            timeframe=AlpacaTimeFrame(1, self._map_timeframe_unit(time_frame_unit)),
            adjustment=Adjustment.ALL,
            feed=DataFeed.SIP,
        )
        data = self.stock_data_client.get_stock_bars(request_params=request)
        # logger.info(f"Stocks update: {symbol} {data}")
        try:
            bars = data[symbol]
        except KeyError:
            logger.warning(f"No data found for symbol: {symbol}")
            return
        logger.debug(f"Saving: {symbol}")
        for bar in bars:
            place_holders = self.map_alpaca_bars_history(symbol, bar)
            self.save_bars_history(place_holders)
            # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))

    def convert_df(
        self, bar_list: List[Bar], time_frame_unit: TimeFrameUnit
    ) -> pd.DataFrame:
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

        if time_frame_unit == TimeFrameUnit.DAY:
            return df
        elif time_frame_unit == TimeFrameUnit.WEEK:
            df_weekly = df.resample("W").agg(
                {
                    "open": "first",  # First day's open price
                    "high": "max",  # Highest price of the week
                    "low": "min",  # Lowest price of the week
                    "close": "last",  # Last day's close price
                    "volume": "sum",  # Sum of weekly volume
                    "trade_count": "sum",  # Sum of weekly trade count
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
        time_frame_unit: TimeFrameUnit,  # day, week
    ) -> pd.DataFrame:
        bar_list = self.get_bars_history(ticker, start_date, end_date)
        df = (
            self.convert_df(bar_list, time_frame_unit)
            if len(bar_list) > 0
            else pd.DataFrame()
        )

        return df
