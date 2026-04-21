import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy

import numpy as np
import pandas as pd
import polars as pl

from .base import TradingStrategy

logger = logging.getLogger(__name__)


# Darvas Box Strategy description
# https://www.tradingview.com/script/ygJLhYt4-Darvas-Box-Theory-Tracking-Uptrends/
class DarvasBoxStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: OhlcvAnalyticsRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
        min_bars: int = 420,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)
        self.df: pd.DataFrame = pd.DataFrame()  # kept for dead code in darvas_box_breakout(); removed in Phase 5

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

    def calculate_indicators_pl(self) -> None:
        """Calculate technical indicators using the polars DataFrame (self.pl_df).

        Adds the following columns:
        - max_close_20: 20-bar rolling maximum of close
        - max_high_20: 20-bar rolling maximum of high
        - ema_10 / ema_20 / ema_50 / ema_200: exponential moving averages of close
        - ema_volume_10: 10-bar EMA of volume
        - macd: difference between 12-bar and 26-bar EMA of close
        - macd_signal: 9-bar EMA of macd
        """
        self.pl_df = self.pl_df.with_columns(
            pl.col("close").rolling_max(20).alias("max_close_20"),
            pl.col("high").rolling_max(20).alias("max_high_20"),
            pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
            pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
            pl.col("close").ewm_mean(span=50, adjust=False).alias("ema_50"),
            pl.col("close").ewm_mean(span=200, adjust=False).alias("ema_200"),
            pl.col("volume").ewm_mean(span=10, adjust=False).alias("ema_volume_10"),
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
        )
        if self.time_frame_unit == TimeFrameUnit.DAY:
            buy_mask = buy_mask & (pl.col("close") >= pl.col("ema_200")) & (pl.col("ema_50") >= pl.col("ema_200"))
        signal_dates = filtered.filter(buy_mask)["date"].to_list()
        return [Signal(ticker=ticker, date=d, ranking=self.ranking_strategy.ranking(self.pl_df, date=d)) for d in signal_dates]

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
                    self.df.at[i, "box_bottom"] = box_bottom  # type: ignore[assignment]
                    self.df.at[i, "box_top"] = box_top  # type: ignore[assignment]
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

    # create similar procedure that will calculate trading signals for all dates in df DataFrame
