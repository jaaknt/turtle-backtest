import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy

import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)


class TradingStrategy(ABC):
    """
    Abstract base class for trading strategies.

    This interface defines the common methods that all trading strategies
    must implement to provide consistent trading signal functionality.
    """

    def __init__(
        self,
        bars_history: OhlcvAnalyticsRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit,
        warmup_period: int,
        min_bars: int,
        use_polars: bool = False,
    ):
        """
        Initialize the trading strategy with common parameters.

        Args:
            bars_history: Repository for accessing historical bar data
            time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
            warmup_period: Number of days of historical data needed for indicators
            min_bars: Minimum number of bars required for analysis
            use_polars: Use polars DataFrame (self.pl_df) instead of pandas (self.df)
        """

        self.bars_history = bars_history
        self.ranking_strategy = ranking_strategy
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period
        self.min_bars = min_bars
        self.use_polars = use_polars
        self.df = pd.DataFrame()
        self.pl_df = pl.DataFrame()

    def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:  # noqa: ARG002
        raise ValueError(
            f"{self.__class__.__name__} does not support use_polars=True. Implement _get_polars_signals or construct with use_polars=False."
        )

    @abstractmethod
    def _get_pandas_signals(self, ticker: str, start_date: date) -> list[Signal]: ...

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

    def collect_data(self, ticker: str, start_date: date, end_date: date) -> bool:
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
        fetch_start = start_date - timedelta(days=self.warmup_period)
        if self.use_polars:
            self.pl_df = self.bars_history.get_bars_pl(ticker, fetch_start, end_date, self.time_frame_unit)
            return not (self.pl_df.is_empty() or self.pl_df.shape[0] < self.min_bars)
        self.df = self.bars_history.get_ticker_history(ticker, fetch_start, end_date, self.time_frame_unit)
        return not (self.df.empty or self.df.shape[0] < self.min_bars)

    @abstractmethod
    def calculate_indicators(self) -> None:
        """
        Calculate technical indicators based on the collected historical data.

        This method should compute all necessary technical indicators (moving averages,
        oscillators, etc.) and add them as columns to the internal DataFrame.
        The indicators will be used by trading signal methods.
        """
        pass
