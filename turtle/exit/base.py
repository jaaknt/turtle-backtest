"""Base exit strategy class."""

from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

from turtle.backtest.models import Trade
from turtle.data.bars_history import BarsHistoryRepo


class ExitStrategy(ABC):
    """Abstract base class for exit strategies."""

    def __init__(self, bars_history: BarsHistoryRepo):
        self.bars_history = bars_history

    def initialize(self, ticker: str, start_date: datetime, end_date: datetime) -> None:
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date

    @abstractmethod
    def calculate_indicators(self) -> pd.DataFrame:
        """
        Calculate technical indicators for the given ticker and date range.

        Returns:
            DataFrame with calculated indicators.
        """
        pass

    @abstractmethod
    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """
        Calculate exit trade based on strategy-specific logic.

        Args:
            data: DataFrame with OHLCV data (index should be datetime)

        Returns:
            Trade object representing the exit trade with ticker populated
        """
        pass
