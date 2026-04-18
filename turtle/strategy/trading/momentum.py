import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy

import pandas as pd
import polars as pl
from pandas_ta.momentum import macd as ta_macd
from pandas_ta.overlap import ema as ta_ema

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
        use_polars: bool = True,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars, use_polars)

    def calculate_indicators(self) -> None:
        """Calculate technical indicators for the strategy.

        Adds the following columns to self.df:
        - max_close_20: 20-period rolling maximum of close prices
        - ema_10/20/50/200: Exponential moving averages of close prices
        - ema_volume_10: 10-period EMA of volume
        - buy_signal: Boolean column initialized to False
        """
        # Rolling window indicators
        self.df["max_close_20"] = self.df["close"].rolling(window=20).max()
        self.df["max_high_20"] = self.df["high"].rolling(window=20).max()
        self.df["max_close_10"] = self.df["close"].shift(1).rolling(window=10).max()
        self.df["min_close_10"] = self.df["close"].shift(1).rolling(window=10).min()

        # MACD indicator
        macd_df = ta_macd(self.df["close"], fast=12, slow=26, signal=9)
        self.df["macd"] = macd_df["MACD_12_26_9"]
        self.df["macd_signal"] = macd_df["MACDs_12_26_9"]

        # Exponential Moving Averages for close prices
        self.df["ema_10"] = ta_ema(self.df["close"], length=10)
        self.df["ema_20"] = ta_ema(self.df["close"], length=20)
        self.df["ema_50"] = ta_ema(self.df["close"], length=50)
        self.df["ema_200"] = ta_ema(self.df["close"], length=200)

        # Volume indicators
        self.df["ema_volume_10"] = ta_ema(self.df["volume"], length=10)

        # 100-day price change: current close vs close 70 bars ago (weekends are skipped, so 70 bars is roughly 100 calendar days)
        self.df["close_100_days_ago"] = self.df["close"].shift(70)

        self.df = self.df.reset_index()
        if "date" in self.df.columns:
            self.df["date"] = pd.to_datetime(self.df["date"]).dt.date

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

    def _get_pandas_signals(self, ticker: str, start_date: date) -> list[Signal]:
        self.calculate_indicators()
        filtered_df = self.df[self.df["date"] >= start_date].copy()
        if filtered_df.empty:
            logger.debug(f"{ticker} - no data after date filtering")
            return []

        buy_signals = (
            (filtered_df["close"] >= filtered_df["max_close_20"])
            & (filtered_df["close"] >= filtered_df["ema_10"])
            & (filtered_df["close"] >= filtered_df["ema_20"])
            & (filtered_df["ema_10"] >= filtered_df["ema_20"])
            & (filtered_df["close"] >= filtered_df["ema_50"])
            & (filtered_df["volume"] >= filtered_df["ema_volume_10"] * 1.10)
            & (filtered_df["macd"] > filtered_df["macd_signal"])
            & ((filtered_df["close"] - filtered_df["open"]) / filtered_df["close"] >= 0.008)
            & ((filtered_df["close"] - filtered_df["close_100_days_ago"]) / filtered_df["close_100_days_ago"] >= 0.30)
            & ((filtered_df["max_close_10"] - filtered_df["min_close_10"]) / filtered_df["close"] <= 0.10)
        )
        if self.time_frame_unit == TimeFrameUnit.DAY:
            buy_signals = buy_signals & (
                (filtered_df["close"] >= filtered_df["ema_200"]) & (filtered_df["ema_50"] >= filtered_df["ema_200"])
            )

        signal_dates = filtered_df[buy_signals]["date"].tolist()
        return [
            Signal(ticker=ticker, date=signal_date, ranking=self.ranking_strategy.ranking(self.df, date=signal_date))
            for signal_date in signal_dates
        ]

    def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
        """
        Get trading signals for a ticker within a date range.

        Args:
            ticker: The stock symbol to analyze
            start_date: The start date of the analysis period
            end_date: The end date of the analysis period

        Returns:
            List[Signal]: List of Signal objects for each trading signal
        """
        if not self.collect_data(ticker, start_date, end_date):
            rows = self.pl_df.shape[0] if self.use_polars else self.df.shape[0]
            logger.warning(f"{ticker} - not enough data, rows: {rows}")
            return []

        if self.use_polars:
            return self._get_polars_signals(ticker, start_date)
        return self._get_pandas_signals(ticker, start_date)
