from datetime import datetime, timedelta
import logging
import pandas as pd
import talib

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.ranking.ranking_strategy import RankingStrategy
from .base import TradingStrategy
from .models import Signal

logger = logging.getLogger(__name__)


# Mars Strategy (@marsrides)
# https://docs.google.com/document/d/1BZgaYWFOnsOFMFWRt0jJgNVeLicEMB-ccf9kUwtIxYI/edit?tab=t.0
class MarsStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.WEEK,
        warmup_period: int = 720,  # 2 years for daily EMA200 + weekly data
        min_bars: int = 240,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

        self.df_orig = pd.DataFrame()

    def collect_data(self, ticker: str, start_date: datetime, end_date: datetime) -> bool:
        self.df = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=self.warmup_period),
            end_date,
            self.time_frame_unit,
        )
        return not (self.df.empty or self.df.shape[0] < self.min_bars)

    def calculate_indicators(self) -> None:
        # calculate min and max over last 4 period open and close (excluding current period)
        self.df["max_box_4"] = self.df[["open", "close"]].shift(1).rolling(window=4).max().max(axis=1)
        self.df["min_box_4"] = self.df[["open", "close"]].shift(1).rolling(window=4).min().min(axis=1)

        # consolidation_change (max_box_4 - min_box_4) / close
        self.df["consolidation_change"] = (self.df["max_box_4"] - self.df["min_box_4"]) / self.df["close"]
        self.df["hard_stoploss"] = (self.df["max_box_4"] + self.df["min_box_4"]) / 2 - 0.02

        self.df["ema_10"] = talib.EMA(self.df["close"].values.astype(float), timeperiod=10)
        self.df["ema_20"] = talib.EMA(self.df["close"].values.astype(float), timeperiod=20)

        macd_line, macd_signal, macd_histogram = talib.MACD(
            self.df["close"].values.astype(float),
            fastperiod=12,
            slowperiod=26,
            signalperiod=9,
        )
        self.df["macd"] = macd_line
        self.df["macd_histogram"] = macd_histogram
        self.df["macd_signal"] = macd_signal

        self.df["max_close_10"] = self.df["close"].rolling(window=10).max()

        # volume indicators
        self.df["ema_volume_4"] = talib.SMA(self.df["volume"].shift(1).values.astype(float), timeperiod=4)
        self.df["volume_change"] = self.df["volume"] / self.df["ema_volume_4"]

        self.df["buy_signal"] = False

        self.df = self.df.reset_index()
        self.df["hdate"] = pd.to_datetime(self.df["hdate"]) - pd.Timedelta(days=6)

    def is_buy_signal(self, ticker: str, row: pd.Series) -> bool:
        # last close > max(close, 10)
        if row["close"] < row["max_close_10"]:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} close < max_close_10, "
                f"close: {row['close']} max_close_10: {row['max_close_10']}"
            )
            return False

        # EMA(close, 10) > EMA(close, 20)
        if row["ema_10"] < row["ema_20"]:
            logger.debug(f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} EMA_10 < EMA_20, EMA10: {row['ema_10']} EMA20: {row['ema_20']}")
            return False

        # MACD_signal is not NaN or MACD is not NaN
        if pd.isna(row["macd"]) or pd.isna(row["macd_signal"]):
            logger.debug(f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} MACD_signal is NaN")
            return False

        # consolidation_change < 0.12
        if row["consolidation_change"] > 0.12:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} consolidation_change > 0.12, "
                f"consolidation_change: {row['consolidation_change']}"
            )
            return False

        # (close - hard_stoploss / close < 0.16
        if (row["close"] - row["hard_stoploss"]) / row["close"] > 0.25:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} (close - (max_box_4 - min_box_4) / 2) / close < 0.16, "
                f"close: {row['close']} hard_stoploss: {row['hard_stoploss']}"
            )
            return False

        """
        # if last volume < EMA(volume, 4)*1.10
        if row["volume"] < row["ema_volume_4"] * 0.9:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} volume < EMA_volume_4 * 1.10, "
                f"volume: {row['volume']} EMA_volume_4 * 1.10: {row['ema_volume_4']*1.10}"
            )
            return False
        """

        logger.debug(f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} buy signal")
        return True

    def calculate_entries(self, ticker: str, start_date: datetime, end_date: datetime) -> None:
        # collect data for the ticker and end_date
        if not self.collect_data(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return

        self.calculate_indicators()

        self.df_orig = self.df.copy()
        self.df = self.df.query("hdate >= @start_date and hdate <= @end_date")

        # skip rows before start_date and after end_date
        for i, row in self.df.iterrows():
            self.df.at[i, "buy_signal"] = self.is_buy_signal(ticker, row)


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
        # Collect data for the date range
        if not self.collect_data(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data for range {start_date.date()} to {end_date.date()}")
            return []

        self.calculate_indicators()

        # Filter to the date range
        filtered_df = self.df[(self.df["hdate"].dt.date >= start_date.date()) & (self.df["hdate"].dt.date <= end_date.date())]

        signals = []
        for _, row in filtered_df.iterrows():
            if self.is_buy_signal(ticker, row):
                signals.append(Signal(ticker=ticker, date=row["hdate"], ranking=0))

        return signals


    def _price_to_ranking(self, price: float) -> int:
        """
        Convert stock price to ranking score based on predefined price ranges.

        Args:
            price: The stock price to convert

        Returns:
            int: Ranking score (0-20)
        """
        if price <= 0:
            return 0
        elif price <= 10:
            return 20
        elif price <= 20:
            return 16
        elif price <= 60:
            return 12
        elif price <= 240:
            return 8
        elif price <= 1000:
            return 4
        else:
            return 0

    def ranking(self, ticker: str, date_to_check: datetime) -> int:
        """
        Calculate a ranking score for a ticker based on its closing price on a given date.

        Args:
            ticker: The stock symbol to rank
            date_to_check: The specific date to evaluate the stock price

        Returns:
            int: Ranking score between 0-20, with higher scores for lower-priced stocks
        """
        # Collect data for the specific date
        if not self.collect_data(ticker, date_to_check, date_to_check):
            logger.debug(f"{ticker} - not enough data for ranking on date {date_to_check.date()}")
            return 0

        # Filter to the specific date
        target_df = self.df[self.df["hdate"].dt.date == date_to_check.date()]

        if target_df.empty:
            logger.debug(f"{ticker} - no data for ranking on date {date_to_check.date()}")
            return 0

        # Get the closing price from the target date
        closing_price = target_df.iloc[-1]["close"]

        return self._price_to_ranking(closing_price)
