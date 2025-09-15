import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import talib

from turtle.common.enums import TimeFrameUnit
from turtle.data.bars_history import BarsHistoryRepo
from .models import Signal
from .base import TradingStrategy
from turtle.ranking.ranking_strategy import RankingStrategy

logger = logging.getLogger(__name__)


# Darvas Box Strategy description
# https://www.tradingview.com/script/ygJLhYt4-Darvas-Box-Theory-Tracking-Uptrends/
class DarvasBoxStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
        min_bars: int = 420,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

    @staticmethod
    def check_local_max(
        row_index: int,
        series: pd.Series,
        preceding_count: int = 10,
        following_count: int = 4,
    ) -> bool:
        # return False if there are not enough preceding values
        if row_index < preceding_count:
            return False

        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 10 previous values (handling start of DataFrame edge cases)
        preceding_values = series.iloc[max(0, row_index - preceding_count) : row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[row_index + 1 : min(row_index + following_count + 1, len(series))]

        # Check if all previous 10 and next 3 values are less than current
        if (preceding_values < current_value).all() and (following_values < current_value).all():
            return True
        else:
            return False

    @staticmethod
    def check_local_min(row_index: int, series: pd.Series, following_count: int = 3) -> bool:
        # return False if there are not enough following values
        if row_index + following_count >= len(series):
            return False

        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[row_index + 1 : min(row_index + following_count + 1, len(series))]

        # Check if all next 3 values are less than current
        if (following_values >= current_value).all():
            return True
        else:
            return False

    @staticmethod
    def is_local_max_valid(df: pd.DataFrame, local_max: float, following_count: int = 3) -> bool:
        # iterate over the following rows
        # return True if 0:following_count high values after is_local_min are less than local_max
        following: int = -1
        for _, row in df.iterrows():
            if following >= 0:
                following += 1
            if row["high"] > local_max:
                return False
            if row["is_local_min"]:
                following = 0
            if following == following_count:
                return True
        return True

    def collect_data(self, ticker: str, start_date: datetime, end_date: datetime) -> bool:
        self.df = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=self.warmup_period),
            end_date,
            self.time_frame_unit,
        )
        return not (self.df.empty or self.df.shape[0] < self.min_bars)

    def calculate_indicators(self) -> None:
        """Calculate technical indicators for the strategy.

        Adds the following columns to self.df:
        - max_close_20: 20-period rolling maximum of close prices
        - ema_10/20/50/200: Exponential moving averages of close prices
        - ema_volume_10: 10-period EMA of volume
        - buy_signal: Boolean column initialized to False
        """
        # Pre-convert arrays once for performance optimization
        close_values = self.df["close"].values.astype(float)
        volume_values = self.df["volume"].values.astype(float)

        # Rolling window indicators
        self.df["max_close_20"] = self.df["close"].rolling(window=20).max()
        self.df["max_high_20"] = self.df["high"].rolling(window=20).max()

        # MACD indicator
        self.df["macd"], self.df["macd_signal"], _ = talib.MACD(close_values, fastperiod=12, slowperiod=26, signalperiod=9)

        # Exponential Moving Averages for close prices
        self.df["ema_10"] = talib.EMA(close_values, timeperiod=10)
        self.df["ema_20"] = talib.EMA(close_values, timeperiod=20)
        self.df["ema_50"] = talib.EMA(close_values, timeperiod=50)
        self.df["ema_200"] = talib.EMA(close_values, timeperiod=200)

        # Volume indicators
        self.df["ema_volume_10"] = talib.EMA(volume_values, timeperiod=10)

        # Initialize buy signal column
        self.df["buy_signal"] = False

        self.df = self.df.reset_index()

        # self.darvas_box_breakout()

    def darvas_box_breakout(self, lookback_period: int = 10, validation_period: int = 3) -> bool:
        # status values: unknown, box_top_set, box_bottom_set, box_formed, breakout_up, breakout_down
        self.df["status"] = "unknown"
        self.df["box_top"] = np.nan
        self.df["box_bottom"] = np.nan
        self.df["is_local_max"] = self.df.index.to_series().apply(
            lambda i: self.check_local_max(i, self.df["high"], lookback_period, validation_period)
        )
        self.df["is_local_min"] = self.df.index.to_series().apply(lambda i: self.check_local_min(i, self.df["low"], validation_period))

        # Initialize variables for box formation
        status: str = "unknown"
        # box_top_index: int = 0
        # box_bottom_index: int = 0
        box_top = pd.Float64Dtype()
        box_bottom = pd.Float64Dtype()

        # iterate over the self.df_weekly rows
        for idx, (i, row) in enumerate(self.df.iterrows()):
            # if status is unknown, check if the current row is a local max
            if status == "unknown":
                if row["is_local_max"]:
                    if self.is_local_max_valid(self.df.iloc[idx:], row["high"], validation_period):
                        status = "box_top_set"
                        box_top = row["high"]
                        # self.df_weekly.at[i, "status"] = status
                        self.df.at[i, "box_top"] = box_top
                    else:
                        # fixing local max value
                        self.df["is_local_max"] = False
                        # status = "unknown"
                        continue
                else:
                    continue
            # if status is box_top_set, check if the current row is a local min
            # there can be local max and min in the same bar
            if status == "box_top_set":
                if row["is_local_min"]:
                    status = "box_bottom_set"
                    box_bottom = row["low"]
                    # self.df_weekly.at[i, "status"] = status
                    self.df.at[i, "box_bottom"] = box_bottom
            # if status is box_bottom_set, check if the current row is a local max
            elif status == "box_bottom_set":
                if row["is_local_min"]:
                    status = "box_formed"
            # if status is box_formed, check if the current row is a breakout
            elif status == "box_formed":
                if row["close"] > box_top:
                    status = "breakout_up"
                    # for further filtering afterwards
                    self.df.at[i, "box_bottom"] = box_bottom
                    self.df.at[i, "box_top"] = box_top
                elif row["close"] < box_bottom:
                    status = "breakout_down"
            elif status == "breakout_up" or status == "breakout_down":
                status = "unknown"

            # update the status
            self.df.at[i, "status"] = status

        # check if the last or previous row was a breakout up
        return bool(
            self.df.iloc[-1]["status"] == "breakout_up"
            # or self.df.iloc[-2]["status"] == "breakout_up"
        )

    def is_buy_signal(self, ticker: str, row: pd.Series) -> bool:
        # last_record: pd.Series = self.df.iloc[-1]

        # is darvas_box breakout up
        # if not row["status"] == "breakout_up":
        #    logger.debug(f"{ticker} darvas_box_breakout failed")
        #    return False

        # last close > max(close, 20)
        if row["close"] < row["max_close_20"]:
            logger.debug(f"{ticker} close < max_close_20, close: {row['close']} max_close_20: {row['max_close_20']}")
            return False

        # last close > EMA(close, 10)
        if row["close"] < row["ema_10"]:
            logger.debug(f"{ticker} close < EMA_10, close: {row['close']} EMA10: {row['ema_10']}")
            return False

        # last close > EMA(close, 20)
        if row["close"] < row["ema_20"]:
            logger.debug(f"{ticker} close < EMA_20, close: {row['close']} EMA20: {row['ema_20']}")
            return False

        # EMA(close, 10) > EMA(close, 20)
        if row["ema_10"] < row["ema_20"]:
            logger.debug(f"{ticker} EMA_10 < EMA_20, EMA10: {row['ema_10']} EMA20: {row['ema_20']}")
            return False

        # last close > EMA(close, 50)
        if row["close"] < row["ema_50"]:
            logger.debug(f"{ticker} close < EMA_50, close: {row['close']} EMA50: {row['ema_50']}")
            return False

        if self.time_frame_unit == TimeFrameUnit.DAY:
            # last close > EMA(close, 200)
            if row["close"] < row["ema_200"]:
                logger.debug(f"{ticker} close < EMA_200, close: {row['close']} EMA200: {row['ema_200']}")
                return False

            # EMA(close, 50) > EMA(close, 200)
            if row["ema_50"] < row["ema_200"]:
                logger.debug(f"{ticker} EMA_50 < EMA_200, EMA50: {row['ema_50']} EMA200: {row['ema_200']}")
                return False

        # if last volume < EMA(volume, 10)*1.10
        if row["volume"] < row["ema_volume_10"] * 1.10:
            logger.debug(
                f"{ticker} volume < EMA_volume_10 * 1.10, volume: {row['volume']} EMA_volume_10 * 1.10: {row['ema_volume_10'] * 1.10}"
            )
            return False

        # At least 1% raise between close and open
        if (row["close"] - row["open"]) / row["close"] < 0.01:
            logger.debug(f"{ticker} (close - open) / close < 0.01, close: {row['close']} open: {row['open']}")
            return False

        return True

    def has_signal(self, ticker: str, date_to_check: datetime) -> bool:
        if not self.collect_data(ticker, date_to_check, date_to_check):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return False

        self.calculate_indicators()

        # compare last row [hdate] with the date_to_check
        if self.df.iloc[-1]["hdate"] != date_to_check:
            logger.warning(f"{ticker} - last row date {self.df.iloc[-1]['hdate']} does not match {date_to_check}")

        return self.is_buy_signal(ticker, self.df.iloc[-1])

    def get_signals(self, ticker: str, start_date: datetime, end_date: datetime) -> list[Signal]:
        """
        Get trading signals for a ticker within a date range.

        Args:
            ticker: The stock symbol to analyze
            start_date: The start date of the analysis period
            end_date: The end date of the analysis period

        Returns:
            List[Signal]: List of Signal objects for each trading signal
        """
        # collect data for the ticker and end_date
        if not self.collect_data(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return []

        self.calculate_indicators()

        # Filter data to target date range
        filtered_df = self.df[self.df["hdate"] >= start_date].copy()
        if filtered_df.empty:
            logger.debug(f"{ticker} - no data after date filtering")
            return []

        # Vectorized buy signal calculation - much faster than iterrows()
        buy_signals = (
            (filtered_df["close"] >= filtered_df["max_close_20"])
            & (filtered_df["close"] >= filtered_df["ema_10"])
            & (filtered_df["close"] >= filtered_df["ema_20"])
            & (filtered_df["ema_10"] >= filtered_df["ema_20"])
            & (filtered_df["close"] >= filtered_df["ema_50"])
            & (filtered_df["volume"] >= filtered_df["ema_volume_10"] * 1.10)
            & (filtered_df["macd"] > filtered_df["macd_signal"])
            & ((filtered_df["close"] - filtered_df["open"]) / filtered_df["close"] >= 0.008)
        )

        # Add EMA200 conditions only for daily timeframe
        if self.time_frame_unit == TimeFrameUnit.DAY:
            buy_signals = buy_signals & (
                (filtered_df["close"] >= filtered_df["ema_200"]) & (filtered_df["ema_50"] >= filtered_df["ema_200"])
            )

        # print all values from start_date to end_date where buy_signals is False
        for _, row in filtered_df[~buy_signals].iterrows():
            logger.debug(f"{ticker} - no buy signal on {row['hdate'].date()}")
            logger.debug(f"  close: {row['close']} max_close_20: {row['max_close_20']} ema_10: {row['ema_10']} ema_20: {row['ema_20']}")
            logger.debug(
                f"  ema_50: {row['ema_50']} ema_200: {row['ema_200']} "
                f"volume: {row['volume']} ema_volume_10 * 1.10: {row['ema_volume_10'] * 1.10}"
            )
            logger.debug(f"  macd: {row['macd']} macd_signal: {row['macd_signal']}")
            logger.debug(f"  (close - open) / close: {(row['close'] - row['open']) / row['close']}")

        # Get the dates where buy signals occur
        signal_dates = filtered_df[buy_signals]["hdate"].tolist()

        # Return list of Signal objects
        return [
            Signal(ticker=ticker, date=signal_date, ranking=self.ranking_strategy.ranking(self.df, date=signal_date))
            for signal_date in signal_dates
        ]

    # create similar procedure as has_signal that will calculate trading signals for all dates in df DataFrame
