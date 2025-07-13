from datetime import datetime, timedelta
import logging
import pandas as pd
import talib

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.strategy.trading_strategy import TradingStrategy

logger = logging.getLogger(__name__)


class MomentumStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.WEEK,
        warmup_period: int = 720,  # 2 years for daily EMA200 + weekly data
        min_bars: int = 240,
    ):
        super().__init__(bars_history, time_frame_unit, warmup_period, min_bars)
        
        self.df_weekly = pd.DataFrame()
        self.df_daily = pd.DataFrame()
        self.df_daily_filtered = pd.DataFrame()

    def weekly_momentum(self, ticker: str, end_date: datetime) -> bool:
        PERIOD_LENGTH: int = 360
        self.df_weekly = self.bars_history.get_ticker_history(
            ticker,
            end_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            TimeFrameUnit.WEEK,
        )

        if self.df_weekly.empty:
            return False

        self.df_weekly["sma_20"] = talib.SMA(
            self.df_weekly["close"].values.astype("float64"), timeperiod=20
        )
        self.df_weekly["max_last_10"] = self.df_weekly["close"].rolling(window=10).max()

        self.df_daily = self.bars_history.get_ticker_history(
            ticker,
            end_date - timedelta(days=2 * PERIOD_LENGTH),
            end_date,
            TimeFrameUnit.DAY,
        )
        if self.df_daily.empty:
            return False

        self.df_daily["ema_200"] = talib.EMA(
            self.df_daily["close"].values.astype("float64"), timeperiod=200
        )

        start_date: datetime = end_date - timedelta(days=PERIOD_LENGTH)
        self.df_daily_filtered = self.df_daily.loc[start_date:end_date]  # type: ignore[misc]
        if self.df_daily_filtered.shape[0] < 240:
            logger.debug(
                f"{ticker} - not enough data, rows: {self.df_daily_filtered.shape[0]}"
            )
            return False

        # logger.debug(df_daily_filtered)
        days_below_200_ema = (
            self.df_daily_filtered["close"] < self.df_daily_filtered["ema_200"]
        ).sum()

        if days_below_200_ema > 40:
            logger.debug(
                f"{ticker} - too many days below 200 EMA: {days_below_200_ema}"
            )
            return False

        # there must be at least 30 records in DataFrame
        if self.df_weekly.shape[0] < 30:
            logger.debug(f"{ticker} - not enough data, rows: {self.df_weekly.shape[0]}")
            return False

        # last close > EMA(close, 20)
        last_record = self.df_weekly.iloc[-1]
        if last_record["close"] < last_record["sma_20"]:
            logger.debug(
                f"{ticker} close < SMA_20, close: {last_record['close']} SMA20: {last_record['sma_20']}"
            )
            return False

        # there has been >10% raise 1, 3 or 6 months ago
        prev_record = self.df_weekly.iloc[-2]
        month_1_record = self.df_weekly.iloc[-6]
        month_3_record = self.df_weekly.iloc[-15]
        month_6_record = self.df_weekly.iloc[-28]
        if not (
            prev_record["close"]
            > min(
                month_1_record["close"],
                month_3_record["close"],
                month_6_record["close"],
            )
            * 1.1
        ):
            logger.debug(
                f"{ticker} missing 10% raise , close: {prev_record['close']} month_1: {month_1_record['close']} month_3: {month_3_record['close']} month_6: {month_6_record['close']}"
            )
            return False

        # close must be > max(last 10 close)
        if not (last_record["close"] > prev_record["max_last_10"]):
            logger.debug(
                f"{ticker} close < max(close 10), prev_close: {last_record['close']}, max_last_10: {prev_record['max_last_10']}"
            )
            return False

        # close must be > (high + low) / 2
        if not (
            last_record["close"] > (last_record["high"] + last_record["low"]) / 2.0
        ):
            logger.debug(
                f"{ticker} close < (high + low)/2, close: {last_record['close']}, high: {last_record['high']}, low: {last_record['low']}"
            )
            return False

        # close must be 2-20% higher than in previous week
        if not (
            (last_record["close"] > prev_record["close"] * 1.02)
            and (last_record["close"] < (prev_record["close"] * 1.15))
        ):
            logger.debug(
                f"{ticker} close must be 2-15% higher then previous close: {last_record['close']}, 1.02 prev_close: {prev_record['close'] * 1.02}, 1.15 prev_close: {prev_record['close'] * 1.15}"
            )
            return False

        # volume must be >10% higher than in previous week
        if not (last_record["volume"] > prev_record["volume"] * 1.10):
            logger.debug(
                f"{ticker} volume must be >10% higher than in previous week: {last_record['volume']}, 1.10 * prev_volume: {prev_record['volume'] * 1.10}"
            )
            return False

        return True

    def collect_historical_data(self, ticker: str, start_date: datetime, end_date: datetime) -> bool:
        """
        Collect historical market data for momentum analysis.
        
        Args:
            ticker: The stock symbol to collect data for
            start_date: The start date for data collection
            end_date: The end date for data collection
            
        Returns:
            bool: True if sufficient data was collected, False otherwise
        """
        PERIOD_LENGTH = 360
        
        # Collect weekly data
        self.df_weekly = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            TimeFrameUnit.WEEK,
        )
        
        # Collect daily data for EMA200
        self.df_daily = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=2 * PERIOD_LENGTH),
            end_date,
            TimeFrameUnit.DAY,
        )
        
        return not (self.df_weekly.empty or self.df_daily.empty or self.df_weekly.shape[0] < 30)

    def calculate_indicators(self) -> None:
        """
        Calculate technical indicators for momentum analysis.
        """
        if not self.df_weekly.empty:
            self.df_weekly["sma_20"] = talib.SMA(
                self.df_weekly["close"].values.astype("float64"), timeperiod=20
            )
            self.df_weekly["max_last_10"] = self.df_weekly["close"].rolling(window=10).max()
        
        if not self.df_daily.empty:
            self.df_daily["ema_200"] = talib.EMA(
                self.df_daily["close"].values.astype("float64"), timeperiod=200
            )

    def is_trading_signal(self, ticker: str, date_to_check: datetime) -> bool:
        """
        Check if there is a momentum trading signal for a specific ticker on a given date.
        
        Args:
            ticker: The stock symbol to check
            date_to_check: The specific date to evaluate for trading signals
            
        Returns:
            bool: True if there is a trading signal, False otherwise
        """
        # Use the existing weekly_momentum method
        return self.weekly_momentum(ticker, date_to_check)

    def trading_signals_count(self, ticker: str, start_date: datetime, end_date: datetime) -> int:
        """
        Count the number of momentum trading signals for a ticker within a date range.
        
        For momentum strategy, we check weekly signals, so we'll check each week
        in the date range.
        
        Args:
            ticker: The stock symbol to analyze
            start_date: The start date of the analysis period
            end_date: The end date of the analysis period
            
        Returns:
            int: The total number of trading signals found in the date range
        """
        signal_count = 0
        current_date = start_date
        
        # Check weekly (every 7 days) for signals
        while current_date <= end_date:
            if self.weekly_momentum(ticker, current_date):
                signal_count += 1
            current_date += timedelta(days=7)
                
        return signal_count
