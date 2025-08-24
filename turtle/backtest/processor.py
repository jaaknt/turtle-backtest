import logging
import pandas as pd
from datetime import datetime, timedelta

from turtle.strategy.models import Signal
from turtle.backtest.models import SignalResult, Trade
from turtle.backtest.exit_strategy import ExitStrategy, ProfitLossExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Processes Signal objects to create complete SignalResult objects with entry/exit data,
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
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ):
        """
        Initialize SignalProcessor with required dependencies.

        Args:
            start_date: Minimum date for historical data retrieval
            end_date: Maximum date for historical data retrieval
            bars_history: Repository for accessing historical bar data
            exit_strategy: Strategy for determining exit conditions
            time_frame_unit: Time frame for data (default: DAY)
        """
        self.max_holding_period = max_holding_period
        self.bars_history = bars_history
        self.exit_strategy = exit_strategy
        self.time_frame_unit = time_frame_unit

        # Will be populated by init_benchmarks()
        self.df_spy: pd.DataFrame | None = None
        self.df_qqq: pd.DataFrame | None = None

    def init_benchmarks(self, start_date: datetime, end_date: datetime) -> None:
        """
        Initialize processor by pre-loading benchmark data for SPY and QQQ.
        This should be called once before processing signals to improve performance.
        """
        logger.info("Initializing SignalProcessor with benchmark data...")

        self.df_spy = self.bars_history.get_ticker_history(
            "SPY",
            start_date,
            end_date,
            self.time_frame_unit,
        )
        logger.debug(f"Loaded SPY data: {len(self.df_spy)} records")

        self.df_qqq = self.bars_history.get_ticker_history(
            "QQQ",
            start_date,
            end_date,
            self.time_frame_unit,
        )
        logger.debug(f"Loaded QQQ data: {len(self.df_qqq)} records")
        logger.info("Benchmarks initialization complete")

    def run(self, signal: Signal) -> SignalResult:
        """
        Process a Signal object to create a complete SignalResult.

        Args:
            signal: Signal object containing ticker, date, and ranking

        Returns:
            SignalResult with all calculated fields

        Raises:
            ValueError: If entry data cannot be calculated or required data is missing
            RuntimeError: If processor was not initialized
        """

        logger.debug(f"Processing signal for {signal.ticker} on {signal.date}")

        # Step 1: Calculate entry data
        entry: Trade = self._calculate_entry_data(signal)
        logger.debug(f"Entry calculated: {entry.date} at ${entry.price}")

        # Step 2: Calculate exit data using strategy
        exit: Trade = self._calculate_exit_data(signal, entry.date, entry.price)
        logger.debug(f"Exit calculated: {exit.date} at ${exit.price} ({exit.reason})")

        # Step 3: Initialize benchmarks
        self.init_benchmarks(entry.date, exit.date)
        if self.df_spy is None or self.df_qqq is None:
            raise RuntimeError("Benchmarks must be initialized before processing signals")

        # Step 4: Calculate return percentage
        return_pct = self._calculate_return_pct(entry.price, exit.price)
        logger.debug(f"Return calculated: {return_pct:.2f}%")

        # Step 4: Calculate benchmark returns
        return_pct_qqq, return_pct_spy = self._calculate_benchmark_returns(entry.date, exit.date)
        logger.debug(f"Benchmark returns - QQQ: {return_pct_qqq:.2f}%, SPY: {return_pct_spy:.2f}%")

        # Create and return SignalResult
        self.result = SignalResult(
            signal=signal,
            entry=entry,
            exit=exit,
            return_pct=return_pct,
            return_pct_qqq=return_pct_qqq,
            return_pct_spy=return_pct_spy,
        )

        logger.debug(f"Signal processing complete for {signal.ticker}")
        return self.result

    def _calculate_entry_data(self, signal: Signal) -> Trade:
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
            raise ValueError(f"No trading data available for {signal.ticker} after {signal.date}")

        # Get first available trading day
        first_row = df.iloc[0]
        entry_date = pd.to_datetime(df.index[0])
        entry_price = float(first_row["open"])

        if pd.isna(entry_price) or entry_price <= 0:
            raise ValueError(f"Invalid entry price for {signal.ticker}: {entry_price}")

        return Trade(date=entry_date, price=entry_price, reason="next_day_open")

    def _calculate_exit_data(self, signal: Signal, entry_date: datetime, entry_price: float) -> Trade:
        """
        Calculate exit date, price, and reason using the configured exit strategy.

        Args:
            signal: Original signal object
            entry_date: Date when position was entered
            entry_price: Price at entry

        Returns:
            Tuple of (exit_date, exit_price, exit_reason)

        Raises:
            ValueError: If exit calculation fails
        """

        # Get historical data for the ticker from entry date onwards
        df = self.bars_history.get_ticker_history(
            signal.ticker,
            entry_date,
            entry_date + timedelta(days=self.max_holding_period),  # Limit to max_holding_period days max for exit search
            self.time_frame_unit,
        )

        if df.empty:
            raise ValueError(f"No historical data available for {signal.ticker} from {entry_date}")

        # Use exit strategy to calculate return
        if isinstance(self.exit_strategy, ProfitLossExitStrategy):
            self.exit_strategy.set_trade_data(entry_price)
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

    def _calculate_benchmark_returns(self, entry_date: datetime, exit_date: datetime) -> tuple[float, float]:
        """
        Calculate benchmark returns for QQQ and SPY over the same period.
        Uses opening price at entry date and closing price at exit date.

        Args:
            entry_date: Position entry date
            exit_date: Position exit date

        Returns:
            Tuple of (qqq_return_pct, spy_return_pct)
        """
        qqq_return = 0.0 if self.df_qqq is None else self._calculate_single_benchmark_return(self.df_qqq, "QQQ", entry_date, exit_date)
        spy_return = 0.0 if self.df_spy is None else self._calculate_single_benchmark_return(self.df_spy, "SPY", entry_date, exit_date)

        return qqq_return, spy_return

    def _calculate_single_benchmark_return(self, df: pd.DataFrame, symbol: str, entry_date: datetime, exit_date: datetime) -> float:
        """
        Calculate return for a single benchmark symbol.

        Args:
            df: DataFrame with benchmark data
            symbol: Symbol name for logging
            entry_date: Position entry date
            exit_date: Position exit date

        Returns:
            Percentage return, or 0.0 if calculation fails
        """
        try:
            if df.empty:
                logger.warning(f"No {symbol} data available for benchmark calculation")
                return 0.0

            # Find entry price (open price on or after entry_date)
            entry_data = df[df.index == pd.Timestamp(entry_date)]

            if entry_data.empty:
                logger.warning(f"No {symbol} entry data available for {entry_date}")
                return 0.0

            entry_price = float(entry_data.iloc[0]["open"])

            # Find exit price (close price on or closest to exit_date)
            exit_data = df[df.index == pd.Timestamp(exit_date)]

            if exit_data.empty:
                logger.warning(f"No {symbol} exit data available for {exit_date}")
                return 0.0

            # Get last available date up to exit_date
            exit_price = float(exit_data.iloc[-1]["close"])

            if entry_price <= 0:
                logger.warning(f"Invalid {symbol} entry price: {entry_price}")
                return 0.0

            return ((exit_price - entry_price) / entry_price) * 100.0

        except Exception as e:
            logger.error(f"Error calculating {symbol} benchmark return: {e}")
            return 0.0
