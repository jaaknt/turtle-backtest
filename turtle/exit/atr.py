"""ATR-based exit strategy."""

from datetime import datetime, timedelta
import pandas as pd
import talib

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from .base import ExitStrategy


class ATRExitStrategy(ExitStrategy):
    """
    Exit when price drops below entry - (ATR multiplier * ATR) or at period end.

    Uses Average True Range (ATR) to set volatility-adjusted stop losses:
    - Stop loss = Entry Price - (ATR Multiplier × ATR)
    - No profit target - holds until stop loss or period end
    - ATR provides dynamic stop based on recent volatility
    """

    def initialize(
        self, ticker: str, start_date: datetime, end_date: datetime, atr_period: int = 14, atr_multiplier: float = 2.0
    ) -> None:
        super().initialize(ticker, start_date, end_date)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

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
        """Calculate return with ATR-based stop loss."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Check if ATR column exists
        if "atr" not in data.columns:
            raise ValueError("ATR column not found in data. Ensure calculate_indicators() was called first.")

        # Entry price is the open of the first day
        entry_price = data.iloc[0]["open"]

        # Calculate stop loss for each day based on current ATR
        # Stop = Entry Price - (ATR Multiplier × Current ATR)
        data_copy = data.copy()
        data_copy["stop_price"] = entry_price - (self.atr_multiplier * data_copy["atr"])

        # Find first day where low touches or goes below stop price
        stop_hits = data_copy[data_copy["low"] <= data_copy["stop_price"]]

        if not stop_hits.empty:
            # Exit at stop price on first stop hit
            first_stop_date = stop_hits.index[0]
            stop_price = stop_hits.iloc[0]["stop_price"]
            return Trade(date=first_stop_date, price=stop_price, reason="atr_stop_loss")
        else:
            # Hold until period end
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")