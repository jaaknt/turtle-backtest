"""Base exit strategy class."""

from abc import ABC, abstractmethod
from datetime import date

import polars as pl

from turtlex.model import Trade
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository


def add_adjusted_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Add split/dividend-adjusted OHLC columns, scaling by the bar's own adjustment factor.

    Exit prices and any indicator derived from them must be on the adjusted basis, because
    entries are (`SignalProcessor.calculate_entry_data`). Mixing the two bases misstates
    returns by the cumulative adjustment between the exit bar and the latest stored bar —
    a bias that grows with trade age, since `adjusted_close` is normalised to the newest bar.

    Args:
        df: Bar frame with open, high, low, close and adjusted_close columns

    Returns:
        The frame with adj_open, adj_high, adj_low and adj_close added. Rows whose close is
        non-positive get null adjusted columns rather than a division error.
    """
    if df.is_empty():
        return df
    factor = pl.when(pl.col("close") > 0).then(pl.col("adjusted_close") / pl.col("close")).otherwise(None)
    return df.with_columns(
        (pl.col("open") * factor).alias("adj_open"),
        (pl.col("high") * factor).alias("adj_high"),
        (pl.col("low") * factor).alias("adj_low"),
        pl.col("adjusted_close").alias("adj_close"),
    )


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
