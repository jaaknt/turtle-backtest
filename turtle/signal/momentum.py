from datetime import datetime, timedelta
import logging
import talib

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.ranking.ranking_strategy import RankingStrategy
from .base import TradingStrategy
from .models import Signal


logger = logging.getLogger(__name__)


class MomentumStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.WEEK,
        warmup_period: int = 720,  # 2 years for daily EMA200 + weekly data
        min_bars: int = 240,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

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
