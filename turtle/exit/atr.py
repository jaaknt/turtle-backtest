"""ATR-based exit strategy."""

from datetime import datetime, timedelta
import logging
import pandas as pd
import talib
from typing import Any

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from .base import ExitStrategy

logger = logging.getLogger(__name__)


def safe_float_conversion(value: Any) -> float:
    """
    Safely convert pandas Series elements or scalar values to float.

    Handles the type ambiguity that Pylance detects when accessing
    pandas DataFrame elements that could return Series[Any] or scalar values.

    Args:
        value: Value from pandas DataFrame that could be scalar or Series

    Returns:
        float: Converted float value

    Raises:
        ValueError: If value cannot be converted to float
    """
    # Check for pandas Series (has iloc attribute)
    if hasattr(value, "iloc") and hasattr(value, "dtype"):
        # Handle pandas Series case - get first element
        return float(value.iloc[0])
    # Check for pandas scalar (has item attribute but not iloc)
    elif hasattr(value, "item") and not isinstance(value, int | float):
        # Handle pandas scalar case
        return float(value.item())
    else:
        # Handle regular scalar case (int, float, or other numeric types)
        return float(value)


class ATRExitStrategy(ExitStrategy):
    """
    ATR Trailing Stop Exit Strategy.

    Uses Average True Range (ATR) to implement a trailing stop loss that dynamically
    adjusts as the stock price moves favorably:

    - Initial stop: Entry Price - (ATR Multiplier × initial ATR)
    - Trailing logic: Stop adjusts to maintain ATR distance from highest price achieved
    - Stop can only move up (trailing), never down
    - Daily updates: Recalculates stop using current ATR and highest price to date
    - Exit triggers: When close price drops below current trailing stop
    """

    def initialize(self, ticker: str, start_date: datetime, end_date: datetime, atr_period: int = 14, atr_multiplier: float = 2.0) -> None:
        super().initialize(ticker, start_date, end_date)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        # print(f"ATRExitStrategy ATR period {atr_period} and multiplier {atr_multiplier}")

    def calculate_indicators(self) -> pd.DataFrame:
        # Get extra days for ATR calculation
        df = self.bars_history.get_ticker_history(
            self.ticker, self.start_date - timedelta(days=60), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )

        # Calculate ATR using TA-Lib
        high_values = df["high"].values.astype(float)
        low_values = df["low"].values.astype(float)
        close_values = df["close"].values.astype(float)

        df["atr"] = talib.ATR(high_values, low_values, close_values, timeperiod=self.atr_period)

        # Filter to requested date range
        self.df = df[df.index >= self.start_date].copy()
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with ATR trailing stop loss using vectorized operations."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Check if ATR column exists
        if "atr" not in data.columns:
            raise ValueError("ATR column not found in data. Ensure calculate_indicators() was called first.")

        # Create working copy to avoid modifying original data
        df = data.copy()

        # Entry price and ATR validation
        entry_price = safe_float_conversion(df.iloc[0]["open"])
        entry_atr = safe_float_conversion(df.iloc[0]["atr"])

        if pd.isna(entry_atr) or entry_atr == 0:
            raise ValueError("ATR value is NaN or zero for entry date. Cannot calculate stop loss.")

        # Calculate initial stop loss
        initial_stop = entry_price - (self.atr_multiplier * entry_atr)

        logger.debug(f"Entry price: {entry_price:.2f}, Entry ATR: {entry_atr:.2f}, Initial stop: {initial_stop:.2f}")

        # Vectorized calculations for trailing stop
        # Step 1: Calculate cumulative maximum high (running highest price)
        df["cummax_high"] = df["high"].cummax()

        # Step 2: Calculate potential trailing stops based on running max and current ATR
        df["potential_stop"] = df["cummax_high"] - (self.atr_multiplier * df["atr"])

        # Step 3: Ensure stops can only move up (trailing), never down
        # Use cummax to ensure stop levels only increase, and clip to initial stop minimum
        df["trailing_stop"] = df["potential_stop"].cummax().clip(lower=initial_stop)

        # Step 4: Handle NaN ATR values by forward-filling the last valid stop
        df["trailing_stop"] = df["trailing_stop"].ffill()

        # Step 5: Find first exit condition (close < trailing_stop)
        # exit_mask: pd.Series[bool] = df["close"] < df["trailing_stop"]
        exit_mask: pd.Series[bool] = df["low"] < df["trailing_stop"]

        if exit_mask.any():
            # Get first exit index
            exit_idx = exit_mask.idxmax()  # Returns index of first True value

            # Get the row index position for safe iloc access
            exit_position = df.index.get_loc(exit_idx)

            # Extract scalar values using safe conversion to handle type ambiguity
            exit_price = safe_float_conversion(df.iloc[exit_position]["trailing_stop"])
            close_price = safe_float_conversion(df.iloc[exit_position]["close"])

            logger.debug(f"Stop loss triggered on {exit_idx}: Close {close_price:.2f} < Stop {exit_price:.2f}")

            # Convert index to datetime
            trade_date = pd.to_datetime(exit_idx).to_pydatetime() if not isinstance(exit_idx, datetime) else exit_idx

            return Trade(ticker=self.ticker, date=trade_date, price=close_price, reason="atr_trailing_stop")

        # No exit condition met - hold until period end
        last_date = df.index[-1]

        # Extract scalar values using safe conversion to handle type ambiguity
        final_close = safe_float_conversion(df.iloc[-1]["close"])
        final_stop = safe_float_conversion(df.iloc[-1]["trailing_stop"])

        logger.debug(f"Period end: Final close {final_close:.2f}, Final stop {final_stop:.2f}")

        # Convert date to datetime
        trade_date = pd.to_datetime(last_date).to_pydatetime() if not isinstance(last_date, datetime) else last_date

        return Trade(ticker=self.ticker, date=trade_date, price=final_stop, reason="period_end")
