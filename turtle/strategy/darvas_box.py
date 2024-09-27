from datetime import datetime, timedelta
import logging
import pandas as pd
import pandas_ta as ta
import numpy as np

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


# Darvas Box Strategy description
# https://www.tradingview.com/script/ygJLhYt4-Darvas-Box-Theory-Tracking-Uptrends/
class DarvasBoxStrategy:
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.WEEK,
        warmup_period: int = 300,
        min_bars: int = 80,
    ):
        # self.connection = connection
        # self.ticker = SymbolRepo(connection, ticker_api_key)
        self.bars_history = bars_history
        # self.market_data = MarketData(self.bars_history)

        self.df = pd.DataFrame()
        self.time_frame_unit: TimeFrameUnit = time_frame_unit
        self.warmup_period = warmup_period
        self.min_bars = min_bars

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
        following_values = series.iloc[
            row_index + 1 : min(row_index + following_count + 1, len(series))
        ]

        # Check if all previous 10 and next 3 values are less than current
        if (preceding_values < current_value).all() and (
            following_values < current_value
        ).all():
            return True
        else:
            return False

    @staticmethod
    def check_local_min(
        row_index: int, series: pd.Series, following_count: int = 3
    ) -> bool:
        # return False if there are not enough following values
        if row_index + following_count >= len(series):
            return False

        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[
            row_index + 1 : min(row_index + following_count + 1, len(series))
        ]

        # Check if all next 3 values are less than current
        if (following_values >= current_value).all():
            return True
        else:
            return False

    @staticmethod
    def is_local_max_valid(
        df: pd.DataFrame, local_max: float, following_count: int = 3
    ):
        # iterate over the following rows
        # return True if 0:following_count high values after is_local_min are less than local_max
        following: int = -1
        for i, row in df.iterrows():
            if following >= 0:
                following += 1
            if row["high"] > local_max:
                return False
            if row["is_local_min"]:
                following = 0
            if following == following_count:
                return True
        return True

    def collect(self, ticker: str, start_date: datetime, end_date: datetime) -> bool:
        self.df = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=self.warmup_period),
            end_date,
            self.time_frame_unit,
        )
        return not (self.df.empty or self.df.shape[0] < self.min_bars)

    def calculate_indicators(self) -> None:
        # add indicators
        self.df["max_close_20"] = self.df["close"].rolling(window=20).max()
        self.df["ema_10"] = ta.ema(self.df["close"], length=10)
        self.df["ema_20"] = ta.ema(self.df["close"], length=20)
        self.df["ema_50"] = ta.ema(self.df["close"], length=50)
        self.df["ema_200"] = ta.ema(self.df["close"], length=200)
        self.df["ema_volume_10"] = ta.ema(self.df["volume"], length=10)
        self.df["buy_signal"] = False

        self.df = self.df.reset_index()

        self.darvas_box_breakout()

    def darvas_box_breakout(self, lookback_period=10, validation_period=3) -> None:
        # status values: unknown, box_top_set, box_bottom_set, box_formed, breakout_up, breakout_down
        self.df["status"] = "unknown"
        self.df["box_top"] = np.nan
        self.df["box_bottom"] = np.nan
        self.df["is_local_max"] = self.df.index.to_series().apply(
            lambda i: self.check_local_max(
                i, self.df["high"], lookback_period, validation_period
            )
        )
        self.df["is_local_min"] = self.df.index.to_series().apply(
            lambda i: self.check_local_min(i, self.df["low"], validation_period)
        )

        # Initialize variables for box formation
        status: str = "unknown"
        # box_top_index: int = 0
        # box_bottom_index: int = 0
        box_top = pd.Float64Dtype()
        box_bottom = pd.Float64Dtype()

        # iterate over the self.df_weekly rows
        for i, row in self.df.iterrows():
            # if status is unknown, check if the current row is a local max
            if status == "unknown":
                if row["is_local_max"]:
                    if self.is_local_max_valid(
                        self.df[i:], row["high"], validation_period
                    ):
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
        return (
            self.df.iloc[-1]["status"] == "breakout_up"
            # or self.df.iloc[-2]["status"] == "breakout_up"
        )

    def is_buy_signal(self, ticker: str, row: pd.Series) -> bool:
        # last_record: pd.Series = self.df.iloc[-1]

        # is darvas_box breakout up
        if not row["status"] == "breakout_up":
            logger.debug(f"{ticker} darvas_box_breakout failed")
            return False

        # last close > max(close, 20)
        if row["close"] < row["max_close_20"]:
            logger.debug(
                f"{ticker} close < max_close_20, close: {row["close"]} max_close_20: {row["max_close_20"]}"
            )
            return False

        # last close > EMA(close, 10)
        if row["close"] < row["ema_10"]:
            logger.debug(
                f"{ticker} close < EMA_10, close: {row["close"]} EMA10: {row["ema_10"]}"
            )
            return False

        # last close > EMA(close, 20)
        if row["close"] < row["ema_20"]:
            logger.debug(
                f"{ticker} close < EMA_20, close: {row["close"]} EMA20: {row["ema_20"]}"
            )
            return False

        # EMA(close, 10) > EMA(close, 20)
        if row["ema_10"] < row["ema_20"]:
            logger.debug(
                f"{ticker} EMA_10 < EMA_20, EMA10: {row["ema_10"]} EMA20: {row["ema_20"]}"
            )
            return False

        # last close > EMA(close, 50)
        if row["close"] < row["ema_50"]:
            logger.debug(
                f"{ticker} close < EMA_50, close: {row["close"]} EMA50: {row["ema_50"]}"
            )
            return False

        if self.time_frame_unit == TimeFrameUnit.DAY:
            # last close > EMA(close, 200)
            if row["close"] < row["ema_200"]:
                logger.debug(
                    f"{ticker} close < EMA_200, close: {row["close"]} EMA200: {row["ema_200"]}"
                )
                return False

            # EMA(close, 50) > EMA(close, 200)
            if row["ema_50"] < row["ema_200"]:
                logger.debug(
                    f"{ticker} EMA_50 < EMA_200, EMA50: {row["ema_50"]} EMA200: {row["ema_200"]}"
                )
                return False

        # if last volume < EMA(volume, 10)*1.10
        if row["volume"] < row["ema_volume_10"] * 1.10:
            logger.debug(
                f"{ticker} volume < EMA_volume_10 * 1.10, volume: {row["volume"]} EMA_volume_10 * 1.10: {row["ema_volume_10"]*1.10}"
            )
            return False

        # if last (close - open) / close < 0.01
        if (row["close"] - row["open"]) / row["close"] < 0.01:
            logger.debug(
                f"{ticker} (close - open) / close < 0.01, close: {row["close"]} open: {row["open"]}"
            )
            return False

        return True

    def validate_momentum(self, ticker: str, date_to_check: datetime) -> bool:
        if not self.collect(ticker, date_to_check, date_to_check):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return False

        self.calculate_indicators()

        return self.is_buy_signal(ticker, self.df.iloc[-1])

    # create similar procedure as validate_momentum that will calculate validate_momentum for all dates in df DataFrame
    # parameters - self, ticker, start_date, end_date
    # adds a new column to the DataFrame - df["buy_signal"] with boolean values
    # returns count of buy signals
    def validate_momentum_all_dates(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> int:
        # collect data for the ticker and end_date
        if not self.collect(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return 0

        self.calculate_indicators()

        # iterate over the dates in the df DataFrame
        # skip first 200 rows as EMA200 is not calculated for them
        for i, row in self.df.iterrows():
            if row["hdate"] < start_date:
                logger.debug(f"Skipping date: {row["hdate"]}")
                continue

            self.df.at[i, "buy_signal"] = self.is_buy_signal(ticker, row)

        return self.df["buy_signal"].sum()
