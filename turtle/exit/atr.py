"""ATR-based exit strategy."""

from datetime import datetime, timedelta
import logging
import pandas as pd
import talib

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from .base import ExitStrategy

logger = logging.getLogger(__name__)


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
        """Calculate return with ATR trailing stop loss."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Check if ATR column exists
        if "atr" not in data.columns:
            raise ValueError("ATR column not found in data. Ensure calculate_indicators() was called first.")

        # Entry price is the open of the first day
        entry_price = data.iloc[0]["open"]
        entry_atr = data.iloc[0]["atr"]

        if pd.isna(entry_atr):
            raise ValueError("ATR value is NaN for entry date. Cannot calculate stop loss.")

        # Initialize tracking variables
        highest_price = entry_price  # Track highest price achieved
        current_stop = entry_price - (self.atr_multiplier * entry_atr)  # Initial stop

        logger.debug(f"Entry price: {entry_price:.2f}, Entry ATR: {entry_atr:.2f}, Initial stop: {current_stop:.2f}")

        # Iterate through each day to implement trailing stop
        for date, row in data.iterrows():
            daily_close = row["close"]
            daily_high = row["high"]
            daily_atr = row["atr"]

            # Skip if ATR is not available
            if pd.isna(daily_atr):
                logger.warning(f"ATR is NaN for date {date}, skipping trailing stop update")
                continue

            # Update highest price achieved
            if daily_high > highest_price:
                highest_price = daily_high

                # Calculate new trailing stop based on highest price and current ATR
                new_stop = highest_price - (self.atr_multiplier * daily_atr)

                # Stop can only move up (trailing), never down
                if new_stop > current_stop:
                    current_stop = new_stop
                    logger.debug(f"Date {date}: New high {highest_price:.2f}, trailing stop updated to {current_stop:.2f}")

            # Check if stop loss is triggered
            if daily_close < current_stop:
                logger.debug(f"Date {date}: Stop loss triggered - Close {daily_close:.2f} < Stop {current_stop:.2f}")
                # Convert date to datetime - handle various types from pandas index
                if isinstance(date, datetime):
                    trade_date = date
                else:
                    trade_date = pd.to_datetime(str(date)).to_pydatetime()
                return Trade(ticker=self.ticker, date=trade_date, price=current_stop, reason="atr_trailing_stop")

            logger.debug(f"Date {date}: Close {daily_close:.2f}, High {daily_high:.2f}, "
                        f"Highest {highest_price:.2f}, Current stop {current_stop:.2f}")

        # If we get here, no stop was triggered - hold until period end
        last_record = data.iloc[-1]
        last_date = data.index[-1]
        logger.debug(f"Period end: Final close {last_record['close']:.2f}, Final stop {current_stop:.2f}")
        # Convert date to datetime - handle various types from pandas index
        if isinstance(last_date, datetime):
            trade_date = last_date
        else:
            trade_date = pd.to_datetime(str(last_date)).to_pydatetime()
        return Trade(ticker=self.ticker, date=trade_date, price=last_record["close"], reason="period_end")
