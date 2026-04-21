import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy

import polars as pl

from .base import TradingStrategy

logger = logging.getLogger(__name__)


class MomentumStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: OhlcvAnalyticsRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 720,  # 2 years for daily EMA200 + weekly data
        min_bars: int = 100,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

    def calculate_indicators_pl(self) -> None:
        """Calculate technical indicators using the polars DataFrame (self.pl_df).

        Adds the following columns:
        - max_close_20: 20-bar rolling maximum of close (breakout level)
        - max_high_20: 20-bar rolling maximum of high
        - max_close_10 / min_close_10: 10-bar rolling max/min of close.shift(1)
          (excludes current bar; used for consolidation-range check)
        - ema_10 / ema_20 / ema_50 / ema_200: exponential moving averages of close
        - ema_volume_10: 10-bar EMA of volume (average volume baseline)
        - close_100_days_ago: close price 70 bars back (~100 calendar days)
        - macd: difference between 12-bar and 26-bar EMA of close
        - macd_signal: 9-bar EMA of macd (signal line)
        """
        self.pl_df = self.pl_df.with_columns(
            pl.col("close").rolling_max(20).alias("max_close_20"),
            pl.col("high").rolling_max(20).alias("max_high_20"),
            pl.col("close").shift(1).rolling_max(10).alias("max_close_10"),
            pl.col("close").shift(1).rolling_min(10).alias("min_close_10"),
            pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
            pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
            pl.col("close").ewm_mean(span=50, adjust=False).alias("ema_50"),
            pl.col("close").ewm_mean(span=200, adjust=False).alias("ema_200"),
            pl.col("volume").ewm_mean(span=10, adjust=False).alias("ema_volume_10"),
            pl.col("close").shift(70).alias("close_100_days_ago"),
            (pl.col("close").ewm_mean(span=12, adjust=False) - pl.col("close").ewm_mean(span=26, adjust=False)).alias("macd"),
        ).with_columns(
            pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal"),
        )

    def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
        self.calculate_indicators_pl()
        filtered = self.pl_df.filter(pl.col("date") >= start_date)
        if filtered.is_empty():
            logger.debug(f"{ticker} - no data after date filtering")
            return []

        buy_mask = (
            (pl.col("close") >= pl.col("max_close_20"))
            & (pl.col("close") >= pl.col("ema_10"))
            & (pl.col("close") >= pl.col("ema_20"))
            & (pl.col("ema_10") >= pl.col("ema_20"))
            & (pl.col("close") >= pl.col("ema_50"))
            & (pl.col("volume") >= pl.col("ema_volume_10") * 1.10)
            & (pl.col("macd") > pl.col("macd_signal"))
            & ((pl.col("close") - pl.col("open")) / pl.col("close") >= 0.008)
            & ((pl.col("close") - pl.col("close_100_days_ago")) / pl.col("close_100_days_ago") >= 0.30)
            & ((pl.col("max_close_10") - pl.col("min_close_10")) / pl.col("close") <= 0.10)
        )
        if self.time_frame_unit == TimeFrameUnit.DAY:
            buy_mask = buy_mask & (pl.col("close") >= pl.col("ema_200")) & (pl.col("ema_50") >= pl.col("ema_200"))

        signal_dates = filtered.filter(buy_mask)["date"].to_list()
        return [Signal(ticker=ticker, date=d, ranking=self.ranking_strategy.ranking(self.pl_df, date=d)) for d in signal_dates]
