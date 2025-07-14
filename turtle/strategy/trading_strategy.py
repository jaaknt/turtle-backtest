import pandas as pd
from abc import ABC, abstractmethod

from datetime import datetime
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit


class TradingStrategy(ABC):
    """
    Abstract base class for trading strategies.

    This interface defines the common methods that all trading strategies
    must implement to provide consistent trading signal functionality.
    """

    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 365,
        min_bars: int = 201,
    ):
        """
        Initialize the trading strategy with common parameters.

        Args:
            bars_history: Repository for accessing historical bar data
            time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
            warmup_period: Number of days of historical data needed for indicators
            min_bars: Minimum number of bars required for analysis
        """

        self.bars_history = bars_history
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period
        self.min_bars = min_bars
        self.df = pd.DataFrame()

    @abstractmethod
    def is_trading_signal(self, ticker: str, date_to_check: datetime) -> bool:
        """
        Check if there is a trading signal for a specific ticker on a given date.

        Args:
            ticker: The stock symbol to check
            date_to_check: The specific date to evaluate for trading signals

        Returns:
            bool: True if there is a trading signal, False otherwise
        """
        pass

    @abstractmethod
    def trading_signals_count(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> int:
        """
        Count the number of trading signals for a ticker within a date range.

        Args:
            ticker: The stock symbol to analyze
            start_date: The start date of the analysis period
            end_date: The end date of the analysis period

        Returns:
            int: The total number of trading signals found in the date range
        """
        pass

    @abstractmethod
    def collect_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> bool:
        """
        Collect historical market data for analysis.

        This method should retrieve OHLCV data for the specified ticker and date range,
        typically including a warmup period for indicator calculations.

        Args:
            ticker: The stock symbol to collect data for
            start_date: The start date for data collection
            end_date: The end date for data collection

        Returns:
            bool: True if sufficient data was collected, False otherwise
        """
        pass

    @abstractmethod
    def calculate_indicators(self) -> None:
        """
        Calculate technical indicators based on the collected historical data.

        This method should compute all necessary technical indicators (moving averages,
        oscillators, etc.) and add them as columns to the internal DataFrame.
        The indicators will be used by trading signal methods.
        """
        pass

    @abstractmethod
    def ranking(self, ticker: str, date_to_check: datetime) -> int:
        """
        Calculate a ranking score for a ticker based on its closing price on a given date.

        The ranking is integer between 0-100, where 100 is the highest rank.

        Args:
            ticker: The stock symbol to rank
            date_to_check: The specific date to evaluate the stock price

        Returns:
            int: Ranking score between 0-100, with higher scores for lower-priced stocks
        """
        pass
