from __future__ import annotations

import logging
from datetime import date, timedelta

import polars as pl

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Benchmark, FutureTrade, Signal, Trade
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.strategy.exit import ExitStrategy

from .benchmark_utils import calculate_benchmark

logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Processes Signal objects to create complete FutureTrade objects with entry/exit data,
    returns, and benchmark comparisons.

    The SignalProcessor is responsible for:
    - Calculating entry date and price based on Signal
    - Calculating exit date, price, and reason using ExitStrategy
    - Computing return percentages
    - Computing benchmark returns for QQQ and SPY
    """

    def __init__(
        self,
        max_holding_period: int,
        bars_history: DailyBarsQueryRepository,
        exit_strategy: ExitStrategy,
        benchmark_tickers: list[str],
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        exit_strategy_kwargs: dict[str, int | float | str] | None = None,
    ):
        """
        Initialize SignalProcessor with required dependencies.

        Args:
            max_holding_period: Maximum days to hold a position
            bars_history: Repository for accessing historical bar data
            exit_strategy: Strategy for determining exit conditions
            benchmark_tickers: List of benchmark ticker symbols (e.g., ['SPY', 'QQQ'])
            time_frame_unit: Time frame for data (default: DAY)
            exit_strategy_kwargs: Extra keyword arguments forwarded to
                `exit_strategy.initialize()` (e.g. `{"profit_target": 15.0}`).
                Parameters left unspecified fall back to that strategy's own
                defaults. See `strategy.factory.resolve_exit_strategy_kwargs`
                for building this from CLI arguments.
        """
        self.max_holding_period = max_holding_period
        self.bars_history = bars_history
        self.exit_strategy = exit_strategy
        self.benchmark_tickers = benchmark_tickers
        self.time_frame_unit = time_frame_unit
        self.exit_strategy_kwargs = exit_strategy_kwargs or {}
        self._benchmark_cache: dict[str, tuple[pl.DataFrame, date, date]] = {}

    def run(self, signal: Signal, end_date: date | None = None) -> FutureTrade | None:
        """
        Process a Signal object to create a complete ClosedTrade.

        Args:
            signal: Signal object containing ticker, date, and ranking
            end_date: Optional maximum date for exit calculation. If provided, used as upper limit
                     combined with max_holding_period constraint.

        Returns:
            FutureTrade with all calculated fields, or None if entry/exit data could not be
            calculated for this signal (e.g. missing historical data).
        """

        logger.debug(f"Processing signal for {signal.ticker} on {signal.date}")

        try:
            # Step 1: Calculate entry data
            entry: Trade | None = self.calculate_entry_data(signal)
            if entry is None:  # No trading data available for entry
                logger.warning(f"Skipping signal for {signal.ticker} on {signal.date}: No entry data")
                return None

            logger.debug(f"Entry calculated: {entry.date} at ${entry.price}")

            # Step 2: Calculate exit data using strategy
            exit: Trade = self.calculate_exit_data(signal, entry.date, entry.price, end_date)
        except ValueError as e:
            logger.warning(f"Skipping signal for {signal.ticker} on {signal.date}: {e}")
            return None

        logger.debug(f"Exit calculated: {exit.date} at ${exit.price} ({exit.reason})")

        # Step 4: Calculate benchmark returns
        benchmarks = self._calculate_benchmark_returns(entry.date, exit.date)
        logger.debug(f"Benchmark returns calculated: {[(b.ticker, b.return_pct) for b in benchmarks]}")

        # Create and return FutureTrade
        self.result = FutureTrade(
            signal=signal,
            entry=entry,
            exit=exit,
            benchmark_list=benchmarks,
            slippage_pct=0.3,
        )

        # Log return percentage using the new property
        logger.debug(f"Return calculated: {self.result.realized_pct:.2f}%")

        logger.debug(f"Signal processing complete for {signal.ticker}")
        return self.result

    def calculate_entry_data(self, signal: Signal) -> Trade | None:
        """
        Calculate entry date and price based on signal.
        Entry date is the next trading date after signal date.
        Entry price is the opening price on the entry date.

        Args:
            signal: Signal object

        Returns:
            Entry Trade object

        Raises:
            ValueError: If no trading data is available for entry calculation
        """
        # Get data starting from day after signal date
        search_start = signal.date + timedelta(days=1)
        search_end = signal.date + timedelta(days=7)  # Search up to 7 days for next trading day

        df = self.bars_history.get_bars_pl(signal.ticker, search_start, search_end, self.time_frame_unit)

        if df.is_empty():
            logger.warning(f"No trading data available for {signal.ticker} after {signal.date}")
            return None

        # Get first available trading day
        row = df.row(0, named=True)
        entry_date = row["date"]

        if row["open"] is None or float(row["open"]) <= 0:
            raise ValueError(f"Invalid entry price for {signal.ticker}: {row['open']}")
        entry_price = float(row["open"])

        return Trade(ticker=signal.ticker, date=entry_date, price=entry_price, reason="next_day_open")

    def calculate_exit_data(self, signal: Signal, entry_date: date, entry_price: float, end_date: date | None = None) -> Trade:
        """
        Calculate exit date, price, and reason using the configured exit strategy.

        Args:
            signal: Original signal object
            entry_date: Date when position was entered
            entry_price: Price at entry
            end_date: Optional maximum date for exit calculation. If provided, used as upper limit
                     combined with max_holding_period constraint.

        Returns:
            Tuple of (exit_date, exit_price, exit_reason)

        Raises:
            ValueError: If exit calculation fails
        """

        # Calculate effective end date considering both end_date parameter and max_holding_period
        max_holding_end_date = entry_date + timedelta(days=self.max_holding_period)
        effective_end_date = min(end_date, max_holding_end_date) if end_date is not None else max_holding_end_date

        # Exit strategies own their default parameters (see each ExitStrategy
        # subclass's `initialize()`); exit_strategy_kwargs only carries overrides.
        self.exit_strategy.initialize(signal.ticker, entry_date, effective_end_date, **self.exit_strategy_kwargs)

        indicators = self.exit_strategy.calculate_indicators()
        trade: Trade = self.exit_strategy.calculate_exit(data=indicators)

        if trade is None:
            raise ValueError(f"Exit strategy failed to calculate return for {signal.ticker}")

        return trade

    def _calculate_benchmark_returns(self, entry_date: date, exit_date: date) -> list[Benchmark]:
        """
        Calculate benchmark returns for configured tickers over the same period.
        Uses opening price at entry date and closing price at exit date.

        Args:
            entry_date: Position entry date
            exit_date: Position exit date

        Returns:
            List of Benchmark objects with returns for each benchmark
        """
        benchmarks = []
        for ticker in self.benchmark_tickers:
            try:
                df = self._get_cached_benchmark_bars(ticker, entry_date, exit_date)
                benchmark = calculate_benchmark(df, ticker, entry_date, exit_date)
                if benchmark is not None:
                    benchmarks.append(benchmark)
            except Exception as e:
                logger.error(f"Error calculating benchmark return for {ticker}: {e}")
                continue
        return benchmarks

    def _get_cached_benchmark_bars(self, ticker: str, entry_date: date, exit_date: date) -> pl.DataFrame:
        """
        Fetch a benchmark ticker's bars, reusing the cached DataFrame when it already covers the
        requested range and widening it (once, on cache miss) otherwise. Benchmark tickers repeat
        identically across every signal in a run, so caching them here avoids refetching the same
        data per signal.

        Args:
            ticker: Benchmark ticker symbol
            entry_date: Position entry date
            exit_date: Position exit date

        Returns:
            DataFrame of bars covering at least [entry_date, exit_date]
        """
        cached = self._benchmark_cache.get(ticker)
        if cached is not None:
            df, cached_start, cached_end = cached
            if cached_start <= entry_date and exit_date <= cached_end:
                return df
            fetch_start = min(cached_start, entry_date)
        else:
            fetch_start = entry_date

        # Pad the end so later signals with slightly later exit dates can reuse this fetch too.
        fetch_end = exit_date + timedelta(days=self.max_holding_period)

        df = self.bars_history.get_bars_pl(ticker, fetch_start, fetch_end, self.time_frame_unit)
        self._benchmark_cache[ticker] = (df, fetch_start, fetch_end)
        return df
