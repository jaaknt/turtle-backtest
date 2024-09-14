from datetime import datetime, timedelta
import logging
import pandas as pd
import pandas_ta as ta

from turtle.data.bars_history import BarsHistoryRepo

logger = logging.getLogger(__name__)


class DarvasBoxStrategy:
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        period_length: int = 720,
        min_bars: int = 80,
    ):
        # self.connection = connection
        # self.ticker = SymbolRepo(connection, ticker_api_key)
        self.bars_history = bars_history
        # self.market_data = MarketData(self.bars_history)

        self.df_weekly = pd.DataFrame()
        # self.df_daily = pd.DataFrame()
        # self.df_daily_filtered = pd.DataFrame()
        self.PERIOD_LENGTH = period_length
        self.MIN_BARS = min_bars

    @staticmethod
    def check_local_max(
        row_index: int, series: pd.Series, preceding_count=10, following_count=3
    ):
        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 10 previous values (handling start of DataFrame edge cases)
        preceding_values = series.iloc[max(0, row_index - preceding_count) : row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[
            row_index + 1 : min(row_index + following_count, len(series))
        ]

        # Check if all previous 10 and next 3 values are less than current
        if (preceding_values < current_value).all() and (
            following_values < current_value
        ).all():
            return True
        else:
            return False

    @staticmethod
    def check_local_min(row_index: int, series: pd.Series, following_count=3):
        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[
            row_index + 1 : min(row_index + following_count, len(series))
        ]

        # Check if all next 3 values are less than current
        if (following_values >= current_value).all():
            return True
        else:
            return False

    def collect(self, ticker: str, end_date: datetime) -> bool:
        self.df_weekly = self.bars_history.get_ticker_history(
            ticker,
            end_date - timedelta(days=self.PERIOD_LENGTH),
            end_date,
            "week",
        )
        if self.df_weekly.empty or self.df_weekly.shape[0] < self.MIN_BARS:
            return False

        # add indicators
        self.df_weekly["max_close_20"] = (
            self.df_weekly["close"].rolling(window=20).max()
        )
        self.df_weekly["ema_10"] = ta.ema(self.df_weekly["close"], length=10)
        self.df_weekly["ema_20"] = ta.ema(self.df_weekly["close"], length=20)
        self.df_weekly["ema_50"] = ta.ema(self.df_weekly["close"], length=50)

        self.df_weekly = self.df_weekly.reset_index()
        return True

    def darvas_box_breakout(self, lookback_period=10, validation_period=3) -> bool:
        self.df_weekly["box_top"] = pd.NA
        self.df_weekly["box_bottom"] = pd.NA
        self.df_weekly["box_breakout"] = False
        self.df_weekly["is_local_max"] = self.df_weekly.index.to_series().apply(
            lambda i: self.check_local_max(
                i, self.df_weekly["close"], lookback_period, validation_period
            )
        )
        self.df_weekly["is_local_min"] = self.df_weekly.index.to_series().apply(
            lambda i: self.check_local_min(
                i, self.df_weekly["close"], validation_period
            )
        )

        # Initialize variables for box formation
        box_top = pd.NA
        box_bottom = pd.NA
        box_top_index: int = 0
        box_bottom_index: int = 0
        box_breakout_index: int = 0

        # for i in range(lookback_period, len(self.df_weekly)):
        #    row = self.df_weekly[i]

        # Check if the box top has been set

        return True

    def weekly_momentum(self, ticker: str, end_date: datetime) -> bool:
        if not self.collect(ticker, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.df_weekly.shape[0]}")
            return False

        last_record = self.df_weekly.iloc[-1]
        # last close > max(close, 20)
        if last_record["close"] < last_record["max_close_20"]:
            logger.debug(
                f"{ticker} close < max_close_20, close: {last_record["close"]} max_close_20: {last_record["max_close_20"]}"
            )
            return False

        # last close > EMA(close, 10)
        if last_record["close"] < last_record["ema_10"]:
            logger.debug(
                f"{ticker} close < EMA_10, close: {last_record["close"]} EMA10: {last_record["ema_10"]}"
            )
            return False

        # last close > EMA(close, 20)
        if last_record["close"] < last_record["ema_20"]:
            logger.debug(
                f"{ticker} close < EMA_20, close: {last_record["close"]} EMA20: {last_record["ema_20"]}"
            )
            return False

        # EMA(close, 10) > EMA(close, 20)
        if last_record["ema_10"] < last_record["ema_20"]:
            logger.debug(
                f"{ticker} EMA_10 < EMA_20, EMA10: {last_record["ema_10"]} EMA20: {last_record["ema_20"]}"
            )
            return False

        # last close > EMA(close, 50)
        if last_record["close"] < last_record["ema_50"]:
            logger.debug(
                f"{ticker} close < EMA_50, close: {last_record["close"]} EMA50: {last_record["ema_50"]}"
            )
            return False

        # call darvas_box_breakout
        if not self.darvas_box_breakout():
            return False

        return True
