from datetime import datetime, timedelta

import logging
import pandas as pd
import pandas_ta as ta

from turtle.data.bars_history import BarsHistoryRepo

logger = logging.getLogger(__name__)


class MarketData:
    def __init__(self, bars_history: BarsHistoryRepo):
        self.bars_history = bars_history
        self.df_weekly = pd.DataFrame()
        # self.df_daily = pd.DataFrame()

    def spy_momentum(self, end_date: datetime) -> bool:
        PERIOD_LENGTH: int = 360
        self.df_weekly = self.bars_history.get_ticker_history(
            "SPY",
            end_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            "week",
        )

        self.df_weekly["EMA_20"] = ta.ema(self.df_weekly["close"], length=20)
        self.df_weekly["EMA_10"] = ta.ema(self.df_weekly["close"], length=10)
        last_record = self.df_weekly.iloc[-1]

        logger.info(
            f"SPY EMA10 - {last_record["EMA_10"]} EMA20: {last_record["EMA_20"]}"
        )
        return last_record["EMA_10"] > last_record["EMA_20"]
