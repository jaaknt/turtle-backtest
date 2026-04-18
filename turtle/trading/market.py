import logging
from datetime import datetime, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository

import pandas as pd
from pandas_ta.overlap import ema as ta_ema

logger = logging.getLogger(__name__)


class MarketData:
    def __init__(self, bars_history: OhlcvAnalyticsRepository):
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

        self.df["ema_20"] = ta_ema(self.df["close"], length=20)
        self.df["ema_10"] = ta_ema(self.df["close"], length=10)
        last_record = self.df.iloc[-1]

        logger.info(f"SPY EMA10 - {last_record['ema_10']} EMA20: {last_record['ema_20']}")
        return bool(last_record["ema_10"] > last_record["ema_20"])
