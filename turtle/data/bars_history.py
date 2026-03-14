import logging
import pandas as pd
from datetime import datetime
from typing import Any
from dataclasses import asdict
from sqlalchemy import Engine, select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from alpaca.data.enums import DataFeed
from alpaca.data.models.bars import Bar as AlpacaBar
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame
from alpaca.data.timeframe import TimeFrameUnit as AlpacaTimeFrameUnit
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.enums import Adjustment

from turtle.data.models import Bar
from turtle.data.tables import bars_history_table
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


class BarsHistoryRepo:
    def __init__(
        self,
        engine: Engine,
        alpaca_api_key: str,
        alpaca_api_secret: str,
    ):
        self.engine = engine
        self.stock_data_client = StockHistoricalDataClient(alpaca_api_key, alpaca_api_secret)

    def map_alpaca_bars_history(self, symbol: str, bar: AlpacaBar) -> dict[str, datetime | float | str | None]:
        return {
            "symbol": symbol,
            "hdate": bar.timestamp,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "trade_count": bar.trade_count,
            "source": "alpaca",
        }

    def _get_bars_history_db(self, symbol: str, start_date: datetime, end_date: datetime) -> list[Any]:
        table = bars_history_table
        stmt = (
            select(table.c.hdate, table.c.open, table.c.high, table.c.low, table.c.close, table.c.volume, table.c.trade_count)
            .where(table.c.symbol == symbol)
            .where(table.c.hdate >= start_date)
            .where(table.c.hdate <= end_date)
            .order_by(table.c.hdate)
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.fetchall()

    def get_bars_history(self, symbol: str, start_date: datetime, end_date: datetime) -> list[Bar]:
        result = self._get_bars_history_db(symbol, start_date, end_date)
        return [Bar(*row) for row in result]

    def save_bars_history(self, values: dict[str, Any]) -> None:
        self.save_bars_history_bulk([values])

    def save_bars_history_bulk(self, values_list: list[dict[str, Any]]) -> None:
        if not values_list:
            return
        table = bars_history_table
        stmt = pg_insert(table).values(values_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "hdate"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "trade_count": stmt.excluded.trade_count,
                "source": stmt.excluded.source,
                "modified_at": func.current_timestamp(),
            },
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def _map_timeframe_unit(self, time_frame_unit: TimeFrameUnit) -> AlpacaTimeFrameUnit:
        """Map internal TimeFrameUnit to AlpacaTimeFrameUnit"""
        if time_frame_unit == TimeFrameUnit.DAY:
            return AlpacaTimeFrameUnit.Day  # type: ignore
        elif time_frame_unit == TimeFrameUnit.WEEK:
            return AlpacaTimeFrameUnit.Week  # type: ignore
        else:
            return AlpacaTimeFrameUnit.Day

    def update_bars_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime | None = None,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ) -> None:
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
        try:
            bars = data[symbol]
        except KeyError:
            logger.warning(f"No data found for symbol: {symbol}")
            return
        logger.debug(f"Saving: {symbol} ({len(bars)} bars)")
        values_list = [self.map_alpaca_bars_history(symbol, bar) for bar in bars]
        self.save_bars_history_bulk(values_list)

    def convert_df(self, bar_list: list[Bar], time_frame_unit: TimeFrameUnit) -> pd.DataFrame:
        dtypes = {
            "hdate": "string",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "int64",
            "trade_count": "int64",
        }
        bar_dicts = [asdict(bar) for bar in bar_list]
        df = pd.DataFrame(bar_dicts).astype(dtypes)
        df["hdate"] = pd.to_datetime(df["hdate"])
        df = df.set_index(["hdate"])

        if time_frame_unit == TimeFrameUnit.DAY:
            return df
        elif time_frame_unit == TimeFrameUnit.WEEK:
            df_weekly = df.resample("W").agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                    "trade_count": "sum",
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
        time_frame_unit: TimeFrameUnit,
    ) -> pd.DataFrame:
        bar_list = self.get_bars_history(ticker, start_date, end_date)
        return self.convert_df(bar_list, time_frame_unit) if len(bar_list) > 0 else pd.DataFrame()
