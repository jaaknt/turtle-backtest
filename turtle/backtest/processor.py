import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from turtle.strategy.models import Signal
from turtle.backtest.models import SignalResult
from turtle.backtest.period_return import TradeExitStrategy
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
        start_date: datetime,  # minimum date for OHLCV history
        end_date: datetime,    # maximum date for OHLCV history
        bars_history: BarsHistoryRepo,
        exit_strategy: TradeExitStrategy,
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
        self.start_date = start_date
        self.end_date = end_date
        self.bars_history = bars_history
        self.exit_strategy = exit_strategy
        self.time_frame_unit = time_frame_unit

        # Will be populated by initialize()
        self.df_spy: pd.DataFrame | None = None
        self.df_qqq: pd.DataFrame | None = None

    def initialize(self) -> None:
        """
        Initialize processor by pre-loading benchmark data for SPY and QQQ.
        This should be called once before processing signals to improve performance.
        """
        logger.info("Initializing SignalProcessor with benchmark data...")

        try:
            self.df_spy = self.bars_history.get_ticker_history(
                "SPY",
                self.start_date,
                self.end_date,
                self.time_frame_unit,
            )
            logger.debug(f"Loaded SPY data: {len(self.df_spy)} records")
        except Exception as e:
            logger.error(f"Failed to load SPY benchmark data: {e}")
            self.df_spy = pd.DataFrame()

        try:
            self.df_qqq = self.bars_history.get_ticker_history(
                "QQQ",
                self.start_date,
                self.end_date,
                self.time_frame_unit,
            )
            logger.debug(f"Loaded QQQ data: {len(self.df_qqq)} records")
        except Exception as e:
            logger.error(f"Failed to load QQQ benchmark data: {e}")
            self.df_qqq = pd.DataFrame()

        logger.info("SignalProcessor initialization complete")

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
        if self.df_spy is None or self.df_qqq is None:
            raise RuntimeError("SignalProcessor must be initialized before processing signals")

        logger.debug(f"Processing signal for {signal.ticker} on {signal.date}")

        # Step 1: Calculate entry data
        entry_date, entry_price = self._calculate_entry_data(signal)
        logger.debug(f"Entry calculated: {entry_date} at ${entry_price}")

        # Step 2: Calculate exit data using strategy
        exit_date, exit_price, exit_reason = self._calculate_exit_data(
            signal, entry_date, entry_price
        )
        logger.debug(f"Exit calculated: {exit_date} at ${exit_price} ({exit_reason})")

        # Step 3: Calculate return percentage
        return_pct = self._calculate_return_pct(entry_price, exit_price)
        logger.debug(f"Return calculated: {return_pct:.2f}%")

        # Step 4: Calculate benchmark returns
        return_pct_qqq, return_pct_spy = self._calculate_benchmark_returns(
            entry_date, exit_date
        )
        logger.debug(f"Benchmark returns - QQQ: {return_pct_qqq:.2f}%, SPY: {return_pct_spy:.2f}%")

        # Create and return SignalResult
        result = SignalResult(
            signal=signal,
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=exit_date,
            exit_price=exit_price,
            exit_reason=exit_reason,
            return_pct=return_pct,
            return_pct_qqq=return_pct_qqq,
            return_pct_spy=return_pct_spy,
        )

        logger.debug(f"Signal processing complete for {signal.ticker}")
        return result

    def _calculate_entry_data(self, signal: Signal) -> tuple[datetime, float]:
        """
        Calculate entry date and price based on signal.
        Entry date is the next trading date after signal date.
        Entry price is the opening price on the entry date.

        Args:
            signal: Signal object

        Returns:
            Tuple of (entry_date, entry_price)

        Raises:
            ValueError: If no trading data is available for entry calculation
        """
        # Get data starting from day after signal date
        search_start = signal.date + timedelta(days=1)
        search_end = signal.date + timedelta(days=7)  # Search up to 7 days for next trading day

        try:
            df = self.bars_history.get_ticker_history(
                signal.ticker, search_start, search_end, self.time_frame_unit
            )

            if df.empty:
                raise ValueError(f"No trading data available for {signal.ticker} after {signal.date}")

            # Get first available trading day
            first_row = df.iloc[0]
            entry_date = pd.to_datetime(df.index[0])
            entry_price = float(first_row["open"])

            if pd.isna(entry_price) or entry_price <= 0:
                raise ValueError(f"Invalid entry price for {signal.ticker}: {entry_price}")

            return entry_date, entry_price

        except Exception as e:
            logger.error(f"Error calculating entry data for {signal.ticker}: {e}")
            raise ValueError(f"Could not calculate entry data for {signal.ticker}: {e}") from e

    def _calculate_exit_data(
        self, signal: Signal, entry_date: datetime, entry_price: float
    ) -> tuple[datetime, float, str]:
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
        # Estimate target date for data retrieval (add buffer for strategy calculations)
        # Different strategies may need different time horizons
        buffer_days = 60  # Allow for up to 2 months of data
        data_end_date = min(entry_date + timedelta(days=buffer_days), self.end_date)

        try:
            # Get historical data for the ticker from entry date onwards
            df = self.bars_history.get_ticker_history(
                signal.ticker,
                entry_date - timedelta(days=30),  # Include some history for indicators
                data_end_date,
                self.time_frame_unit
            )

            if df.empty:
                raise ValueError(f"No historical data available for {signal.ticker} from {entry_date}")

            # Use exit strategy to calculate return
            result = self.exit_strategy.calculate_return(
                data=df,
                entry_price=entry_price,
                entry_date=entry_date,
                target_date=data_end_date,
            )

            if result is None:
                raise ValueError(f"Exit strategy failed to calculate return for {signal.ticker}")

            return result.exit_date, result.exit_price, result.exit_reason

        except Exception as e:
            logger.error(f"Error calculating exit data for {signal.ticker}: {e}")
            raise ValueError(f"Could not calculate exit data for {signal.ticker}: {e}") from e

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

    def _calculate_benchmark_returns(
        self, entry_date: datetime, exit_date: datetime
    ) -> tuple[float, float]:
        """
        Calculate benchmark returns for QQQ and SPY over the same period.
        Uses opening price at entry date and closing price at exit date.

        Args:
            entry_date: Position entry date
            exit_date: Position exit date

        Returns:
            Tuple of (qqq_return_pct, spy_return_pct)
        """
        qqq_return = 0.0 if self.df_qqq is None else self._calculate_single_benchmark_return(
            self.df_qqq, "QQQ", entry_date, exit_date
        )
        spy_return = 0.0 if self.df_spy is None else self._calculate_single_benchmark_return(
            self.df_spy, "SPY", entry_date, exit_date
        )

        return qqq_return, spy_return

    def _calculate_single_benchmark_return(
        self, df: pd.DataFrame, symbol: str, entry_date: datetime, exit_date: datetime
    ) -> float:
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
            entry_mask = df.index >= pd.Timestamp(entry_date)
            entry_data = df[entry_mask]

            if entry_data.empty:
                logger.warning(f"No {symbol} entry data available for {entry_date}")
                return 0.0

            entry_price = float(entry_data.iloc[0]["open"])

            # Find exit price (close price on or closest to exit_date)
            exit_mask = df.index <= pd.Timestamp(exit_date)
            exit_data = df[exit_mask]

            if exit_data.empty:
                logger.warning(f"No {symbol} exit data available for {exit_date}")
                return 0.0

            # Get closest date to exit_date
            target_timestamp = pd.Timestamp(exit_date)
            # Use numpy for absolute difference calculation
            date_diffs = np.abs((exit_data.index - target_timestamp).astype('timedelta64[ns]'))
            min_diff_idx = int(np.argmin(date_diffs))
            closest_idx = exit_data.index[min_diff_idx]
            close_value = exit_data.loc[closest_idx, "close"]
            exit_price = float(close_value)

            if entry_price <= 0:
                logger.warning(f"Invalid {symbol} entry price: {entry_price}")
                return 0.0

            return ((exit_price - entry_price) / entry_price) * 100.0

        except Exception as e:
            logger.error(f"Error calculating {symbol} benchmark return: {e}")
            return 0.0
