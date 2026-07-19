import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta

import polars as pl

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Signal
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.strategy.ranking.base import RankingStrategy

logger = logging.getLogger(__name__)


class TradingStrategy(ABC):
    """
    Abstract base class for trading strategies.

    This interface defines the common methods that all trading strategies
    must implement to provide consistent trading signal functionality.

    Each strategy also owns its ticker universe: the default get_universe
    implementation returns the members of the symbol_group class attribute,
    so a strategy can either point symbol_group at a different group in the
    ticker_group table or override get_universe entirely with a custom
    repository query.
    """

    symbol_group: str = "active"

    def __init__(
        self,
        bars_history: DailyBarsQueryRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit,
        warmup_period: int,
        min_bars: int,
    ):
        """
        Initialize the trading strategy with common parameters.

        Args:
            bars_history: Repository for accessing historical bar data
            ranking_strategy: Strategy for ranking signals
            time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
            warmup_period: Number of days of historical data needed for indicators
            min_bars: Minimum number of bars required for analysis
        """
        self.bars_history = bars_history
        self.ranking_strategy = ranking_strategy
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period
        self.min_bars = min_bars
        self.pl_df = pl.DataFrame()

    @abstractmethod
    def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]: ...

    def get_universe(self, ticker_repo: TickerQueryRepository, limit: int | None = None) -> list[str]:
        """
        Return the ticker universe this strategy generates signals for.

        The default implementation returns the US members of the symbol group
        named by the symbol_group class attribute. Strategies with a custom
        universe (e.g. a fundamentals-based query) should override this method.

        Args:
            ticker_repo: Repository used to query the ticker universe
            limit: Optional maximum number of symbols to return

        Returns:
            list[str]: Ticker symbols in "TICKER.US" format
        """
        return ticker_repo.get_symbol_list("USA", limit=limit, ticker_group=self.symbol_group)

    def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
        """
        Get trading signals for a ticker within a date range.

        Args:
            ticker: The stock symbol to analyze
            start_date: The start date of the analysis period
            end_date: The end date of the analysis period

        Returns:
            list[Signal]: List of Signal objects for each trading signal
        """
        if not self.collect_data(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.pl_df.shape[0]}")
            return []
        return self._get_polars_signals(ticker, start_date)

    def collect_data(self, ticker: str, start_date: date, end_date: date) -> bool:
        """
        Collect historical market data for analysis.

        This method retrieves OHLCV data for the specified ticker and date range,
        including a warmup period for indicator calculations.

        Args:
            ticker: The stock symbol to collect data for
            start_date: The start date for data collection
            end_date: The end date for data collection

        Returns:
            bool: True if sufficient data was collected, False otherwise
        """
        fetch_start = start_date - timedelta(days=self.warmup_period)
        self.pl_df = self.bars_history.get_bars_pl(ticker, fetch_start, end_date, self.time_frame_unit)
        return not (self.pl_df.is_empty() or self.pl_df.shape[0] < self.min_bars)
