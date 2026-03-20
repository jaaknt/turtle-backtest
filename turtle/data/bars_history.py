import logging
from dataclasses import asdict
from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.data.models import Bar
from turtle.data.tables import daily_bars_table
from typing import Any

import pandas as pd
from sqlalchemy import Engine, select

logger = logging.getLogger(__name__)


class BarsHistoryRepo:
    def __init__(self, engine: Engine):
        self.engine = engine

    def _get_bars_history_db(self, symbol: str, start_date: datetime, end_date: datetime) -> list[Any]:
        table = daily_bars_table
        stmt = (
            select(table.c.hdate, table.c.open, table.c.high, table.c.low, table.c.close, table.c.volume, table.c.trade_count)
            .where(table.c.symbol == symbol)
            .where(table.c.hdate >= start_date)
            .where(table.c.hdate <= end_date)
            .order_by(table.c.hdate)
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return list(result.fetchall())

    def get_bars_history(self, symbol: str, start_date: datetime, end_date: datetime) -> list[Bar]:
        result = self._get_bars_history_db(symbol, start_date, end_date)
        return [Bar(*row) for row in result]

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
