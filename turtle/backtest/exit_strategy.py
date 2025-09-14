from abc import ABC, abstractmethod
import pandas as pd
import talib

from turtle.backtest.models import Trade


class ExitStrategy(ABC):
    """
    Abstract base class for period return calculation strategies.
    """

    @abstractmethod
    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """
        Calculate period return based on strategy-specific logic.

        Args:
            data: DataFrame with OHLCV data (index should be datetime)

        Returns:
            Trade object representing the exit trade or None if calculation failed
        """
        pass


class BuyAndHoldExitStrategy(ExitStrategy):
    """
    Simple buy and hold strategy - exit at period end.
    """

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return by holding until target date."""

        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # find last record in DataFrame
        last_record = data.iloc[-1]
        return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")


class ProfitLossExitStrategy(ExitStrategy):
    """
    Exit when 10% profit target or 5% stop loss is hit, whichever comes first.
    """

    def __init__(self, profit_target: float = 20.0, stop_loss: float = 7.0):
        """
        Initialize with profit and loss targets.

        Args:
            profit_target: Profit target percentage (default 20%)
            stop_loss: Stop loss percentage (default 7%)
        """
        self.profit_target = profit_target
        self.stop_loss = stop_loss

    def set_trade_data(self, entry_price: float) -> None:
        self.entry_price = entry_price
        self.profit_price = entry_price * (1 + self.profit_target / 100)
        self.stop_price = entry_price * (1 - self.stop_loss / 100)

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with profit/loss targets."""

        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Find first profit target hit
        profit_hits = data[data["high"] >= self.profit_price]
        first_profit_date = profit_hits.index[0] if not profit_hits.empty else None

        # Find first stop loss hit
        loss_hits = data[data["low"] <= self.stop_price]
        first_loss_date = loss_hits.index[0] if not loss_hits.empty else None

        # Determine which target was hit first (if any)
        if first_profit_date is not None and first_loss_date is not None:
            # Both targets hit - use whichever came first
            if first_profit_date <= first_loss_date:
                return Trade(date=profit_hits.index[0], price=self.profit_price, reason="profit_target")
            else:
                return Trade(date=loss_hits.index[0], price=self.stop_price, reason="stop_loss")
        elif first_profit_date is not None:
            # Only profit target hit
            return Trade(date=profit_hits.index[0], price=self.profit_price, reason="profit_target")
        elif first_loss_date is not None:
            # Only stop loss hit
            return Trade(date=loss_hits.index[0], price=self.stop_price, reason="stop_loss")
        else:
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")


class EMAExitStrategy(ExitStrategy):
    """
    Exit when price closes below EMA or at period end.

    Note: This strategy assumes that the EMA column already exists in the data
    (e.g., 'ema_10', 'ema_20', etc.). If the column doesn't exist, an error will be raised.
    """

    def __init__(self, ema_period: int = 20):
        """
        Initialize with EMA period.

        Args:
            ema_period: Period for EMA to look for in data (default 20 days)
                       Will look for column named 'ema_{ema_period}' in the DataFrame
        """
        self.ema_period = ema_period
        self.ema_column = f"ema_{ema_period}"

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with EMA exit logic."""
        # Check if required EMA column exists
        if self.ema_column not in data.columns:
            raise ValueError(
                f"Required EMA column '{self.ema_column}' not found in data. "
                f"Available columns: {list(data.columns)}. "
                f"Please ensure the data contains pre-calculated EMA values."
            )
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Find first day where close is below EMA
        below_ema = data[data["close"] < data[self.ema_column]]

        if not below_ema.empty:
            # Exit on first close below EMA
            return Trade(date=below_ema.index[0], price=below_ema.iloc[0]["close"], reason="stop_loss")
        else:
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")


class MACDExitStrategy(ExitStrategy):
    """
    Exit when MACD signal turns bearish or at period end.

    Uses MACD (Moving Average Convergence Divergence) to determine exit points:
    - MACD line crosses below signal line (bearish crossover)
    - Or MACD histogram turns negative after being positive

    The strategy calculates MACD indicators if not present in the data.
    """

    def __init__(self, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9, use_histogram: bool = False):
        """
        Initialize with MACD parameters.

        Args:
            fastperiod: Fast EMA period for MACD calculation (default 12)
            slowperiod: Slow EMA period for MACD calculation (default 26)
            signalperiod: Signal line EMA period (default 9)
            use_histogram: Whether to use histogram crossover in addition to signal crossover (default False)
        """
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod
        self.use_histogram = use_histogram

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with MACD exit logic."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Make a copy to avoid modifying original data
        df = data.copy()

        # Calculate MACD indicators if not present
        close_values = df["close"].values.astype(float)
        macd_line, macd_signal, macd_histogram = talib.MACD(
            close_values, fastperiod=self.fastperiod, slowperiod=self.slowperiod, signalperiod=self.signalperiod
        )

        df["macd_line"] = macd_line
        df["macd_signal"] = macd_signal
        df["macd_histogram"] = macd_histogram

        # Skip initial NaN values from MACD calculation
        # Need enough data for MACD calculation (typically slowperiod + signalperiod)
        min_periods_needed = self.slowperiod + self.signalperiod
        if len(df) < min_periods_needed:
            # Not enough data for MACD calculation, exit at period end
            last_record = df.iloc[-1]
            return Trade(date=df.index[-1], price=last_record["close"], reason="period_end")

        # Remove rows with NaN MACD values
        valid_data = df.dropna(subset=["macd_line", "macd_signal"])
        if valid_data.empty:
            last_record = df.iloc[-1]
            return Trade(date=df.index[-1], price=last_record["close"], reason="period_end")

        # Look for bearish signals
        exit_signals = []

        # Signal 1: MACD line crosses below signal line (bearish crossover)
        for i in range(1, len(valid_data)):
            current_row = valid_data.iloc[i]
            prev_row = valid_data.iloc[i - 1]

            # Bearish crossover: MACD was above signal, now below
            if prev_row["macd_line"] >= prev_row["macd_signal"] and current_row["macd_line"] < current_row["macd_signal"]:
                exit_signals.append((valid_data.index[i], current_row["close"], "macd_bearish_cross"))

        # Signal 2: MACD histogram turns negative (optional)
        if self.use_histogram:
            for i in range(1, len(valid_data)):
                current_row = valid_data.iloc[i]
                prev_row = valid_data.iloc[i - 1]

                # Histogram turns negative: was positive, now negative
                if prev_row["macd_histogram"] > 0 and current_row["macd_histogram"] <= 0:
                    exit_signals.append((valid_data.index[i], current_row["close"], "macd_histogram_negative"))

        # Use the first (earliest) exit signal if any found
        if exit_signals:
            # Sort by date and take the earliest
            exit_signals.sort(key=lambda x: x[0])
            exit_date, exit_price, exit_reason = exit_signals[0]
            return Trade(date=exit_date, price=exit_price, reason=exit_reason)

        # No exit signals found, hold until period end
        last_record = df.iloc[-1]
        return Trade(date=df.index[-1], price=last_record["close"], reason="period_end")
