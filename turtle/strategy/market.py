from datetime import datetime, timedelta

import logging
import pandas as pd
import talib

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


class MarketData:
    def __init__(self, bars_history: BarsHistoryRepo):
        self.bars_history = bars_history
        self.df = pd.DataFrame()
        # self.df_daily = pd.DataFrame()

    def spy_momentum(self, end_date: datetime) -> bool:
        PERIOD_LENGTH: int = 360
        self.df = self.bars_history.get_ticker_history(
            "SPY",
            end_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            TimeFrameUnit.WEEK,
        )

        self.df["ema_20"] = talib.EMA(self.df["close"], timeperiod=20)
        self.df["ema_10"] = talib.EMA(self.df["close"], timeperiod=10)
        last_record = self.df.iloc[-1]

        logger.info(
            f"SPY EMA10 - {last_record["ema_10"]} EMA20: {last_record["ema_20"]}"
        )
        return last_record["ema_10"] > last_record["ema_20"]
