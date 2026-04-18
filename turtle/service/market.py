import logging
from datetime import date, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository

import polars as pl

logger = logging.getLogger(__name__)


class MarketData:
    def __init__(self, bars_history: OhlcvAnalyticsRepository, ticker: str):
        self.bars_history = bars_history
        self.ticker = ticker
        self.pl = pl.DataFrame()

    def market_momentum(self, end_date: date) -> bool:
        PERIOD_LENGTH: int = 360
        self.pl = self.bars_history.get_bars_pl(
            self.ticker,
            end_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            TimeFrameUnit.WEEK,
        )

        self.pl = self.pl.with_columns(
            pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
            pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
        )
        last_record = self.pl.row(-1, named=True)

        logger.info(f"{self.ticker} EMA10 - {last_record['ema_10']} EMA20: {last_record['ema_20']}")
        return bool(last_record["ema_10"] > last_record["ema_20"])
