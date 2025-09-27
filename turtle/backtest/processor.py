from __future__ import annotations

import logging
import pandas as pd
from datetime import datetime, timedelta

from turtle.exit.atr import ATRExitStrategy
from turtle.signal.models import Signal
from turtle.backtest.models import Benchmark, FutureTrade, Trade

from turtle.portfolio.models import Position
from turtle.exit import EMAExitStrategy, ExitStrategy, MACDExitStrategy, ProfitLossExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from .benchmark_utils import calculate_benchmark_list

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
        bars_history: BarsHistoryRepo,
        exit_strategy: ExitStrategy,
        benchmark_tickers: list[str],
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ):
        """
        Initialize SignalProcessor with required dependencies.

        Args:
            max_holding_period: Maximum days to hold a position
            bars_history: Repository for accessing historical bar data
            exit_strategy: Strategy for determining exit conditions
            benchmark_tickers: List of benchmark ticker symbols (e.g., ['SPY', 'QQQ'])
            time_frame_unit: Time frame for data (default: DAY)
        """
        self.max_holding_period = max_holding_period
        self.bars_history = bars_history
        self.exit_strategy = exit_strategy
        self.benchmark_tickers = benchmark_tickers
        self.time_frame_unit = time_frame_unit

    def run(self, signal: Signal, end_date: datetime | None = None) -> FutureTrade | None:
        """
        Process a Signal object to create a complete ClosedTrade.

        Args:
            signal: Signal object containing ticker, date, and ranking
            end_date: Optional maximum date for exit calculation. If provided, used as upper limit
                     combined with max_holding_period constraint.

        Returns:
            FutureTrade with all calculated fields

        Raises:
            ValueError: If entry data cannot be calculated or required data is missing
            RuntimeError: If processor was not initialized
        """

        logger.debug(f"Processing signal for {signal.ticker} on {signal.date}")

        # Step 1: Calculate entry data
        entry: Trade | None = self.calculate_entry_data(signal)
        if entry is None:  # No trading data available for entry
            logger.warning(f"Skipping signal for {signal.ticker} on {signal.date}: No entry data")
            return None

        logger.debug(f"Entry calculated: {entry.date} at ${entry.price}")

        # Step 2: Calculate exit data using strategy
        exit: Trade | None = self.calculate_exit_data(signal, entry.date, entry.price, end_date)
        if exit is None:  # No trading data available for exit
            logger.warning(f"Skipping signal for {signal.ticker} on {signal.date}: No exit data")
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

        df = self.bars_history.get_ticker_history(signal.ticker, search_start, search_end, self.time_frame_unit)

        if df.empty:
            logger.warning(f"No trading data available for {signal.ticker} after {signal.date}")
            return None

        # Get first available trading day
        first_row = df.iloc[0]
        entry_date = pd.to_datetime(df.index[0])
        entry_price = float(first_row["open"])

        if pd.isna(entry_price) or entry_price <= 0:
            raise ValueError(f"Invalid entry price for {signal.ticker}: {entry_price}")

        return Trade(ticker=signal.ticker, date=entry_date, price=entry_price, reason="next_day_open")

    def calculate_exit_data(self, signal: Signal, entry_date: datetime, entry_price: float, end_date: datetime | None = None) -> Trade:
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

        # Get historical data for the ticker from entry date onwards
        df = self.bars_history.get_ticker_history(
            signal.ticker,
            entry_date,
            effective_end_date,  # Use calculated effective end date
            self.time_frame_unit,
        )

        if df.empty:
            raise ValueError(f"No historical data available for {signal.ticker} from {entry_date}")

        # Use exit strategy to calculate return
        if isinstance(self.exit_strategy, ProfitLossExitStrategy):
            self.exit_strategy.initialize(signal.ticker, entry_date, effective_end_date, profit_target=10.0, stop_loss=5.0)
        elif isinstance(self.exit_strategy, EMAExitStrategy):
            self.exit_strategy.initialize(signal.ticker, entry_date, effective_end_date, ema_period=20)
        elif isinstance(self.exit_strategy, ATRExitStrategy):
            self.exit_strategy.initialize(signal.ticker, entry_date, effective_end_date, atr_period=14, atr_multiplier=2.0)
        elif isinstance(self.exit_strategy, MACDExitStrategy):
            self.exit_strategy.initialize(
                signal.ticker,
                entry_date,
                effective_end_date,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9,
            )
        else:
            self.exit_strategy.initialize(signal.ticker, entry_date, effective_end_date)

        df = self.exit_strategy.calculate_indicators()
        trade: Trade = self.exit_strategy.calculate_exit(data=df)

        if trade is None:
            raise ValueError(f"Exit strategy failed to calculate return for {signal.ticker}")

        return trade

    def _calculate_return_pct(self, entry_price: float, exit_price: float) -> float:
        """
        Calculate percentage return between entry and exit prices.

        Args:
            entry_price: Price at entry
            exit_price: Price at exit

        Returns:
            Percentage return

        Raises:
            ValueError: If entry price is invalid
        """
        if entry_price <= 0:
            raise ValueError(f"Invalid entry price: {entry_price}")

        return ((exit_price - entry_price) / entry_price) * 100.0

    def _calculate_benchmark_returns(self, entry_date: datetime, exit_date: datetime) -> list[Benchmark]:
        """
        Calculate benchmark returns for configured tickers over the same period.
        Uses opening price at entry date and closing price at exit date.

        Args:
            entry_date: Position entry date
            exit_date: Position exit date

        Returns:
            List of Benchmark objects with returns for each benchmark
        """
        return calculate_benchmark_list(
            entry_date,
            exit_date,
            self.benchmark_tickers,
            self.bars_history,
            self.time_frame_unit,
        )

    def calculate_batch_entry_data(self, signals: list[Signal]) -> dict[str, Trade | None]:
        """
        Calculate entry data for multiple signals in batch.

        Args:
            signals: List of signals to process

        Returns:
            Dictionary mapping signal ticker to entry Trade or None
        """
        entry_data = {}

        for signal in signals:
            try:
                entry_data[signal.ticker] = self.calculate_entry_data(signal)
            except Exception as e:
                logger.error(f"Error calculating entry for {signal.ticker}: {e}")
                entry_data[signal.ticker] = None

        return entry_data

    def evaluate_exit_conditions(self, positions: dict[str, Position], current_date: datetime) -> list[dict[str, object]]:
        """
        Evaluate exit conditions for multiple positions.

        Args:
            positions: Dictionary of current positions (ticker -> position object)
            current_date: Current date for evaluation

        Returns:
            List of exit signals with ticker, price, and reason
        """
        exit_signals = []

        for ticker, position in positions.items():
            try:
                # Get current price data for exit evaluation
                search_end = current_date + timedelta(days=1)
                df = self.bars_history.get_ticker_history(ticker, position.entry.date, search_end, self.time_frame_unit)

                if df.empty:
                    logger.warning(f"No price data for exit evaluation: {ticker} on {current_date}")
                    continue

                # Initialize exit strategy for this position
                self.exit_strategy.initialize(ticker, position.entry.date, current_date)

                # Calculate indicators and check exit conditions
                df_with_indicators = self.exit_strategy.calculate_indicators()

                if df_with_indicators.empty:
                    continue

                # Check if we should exit on current date
                current_row = df_with_indicators[df_with_indicators.index == pd.Timestamp(current_date)]

                if not current_row.empty:
                    # Use exit strategy to determine if we should exit
                    exit_trade = self.exit_strategy.calculate_exit(df_with_indicators)

                    if exit_trade and exit_trade.date.date() == current_date.date():
                        exit_signals.append(
                            {
                                "ticker": ticker,
                                "exit_price": float(exit_trade.price),
                                "exit_reason": str(exit_trade.reason),
                            }
                        )

            except Exception as e:
                logger.error(f"Error evaluating exit for {ticker}: {e}")
                continue

        return exit_signals
