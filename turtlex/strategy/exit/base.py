"""Base exit strategy class."""

from abc import ABC, abstractmethod
from datetime import date

import polars as pl

from turtlex.model import Trade
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository


class ExitStrategy(ABC):
    """Abstract base class for exit strategies."""

    def __init__(self, bars_history: DailyBarsQueryRepository):
        self.bars_history = bars_history

    def initialize(self, ticker: str, start_date: date, end_date: date) -> None:
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date

    @abstractmethod
    def calculate_indicators(self) -> pl.DataFrame:
        """
        Calculate technical indicators for the given ticker and date range.

        Returns:
            DataFrame with calculated indicators.
        """
        pass

    @abstractmethod
    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """
        Calculate exit trade based on strategy-specific logic.

        Args:
            data: Polars DataFrame with OHLCV data and a `date` column.

        Returns:
            Trade object representing the exit trade with ticker populated

        Raises:
            ValueError: If `data` is empty or otherwise insufficient to calculate an exit.
        """
        pass
