"""MACD-based exit strategy."""

from datetime import datetime, timedelta
import pandas as pd
import talib

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from .base import ExitStrategy


class MACDExitStrategy(ExitStrategy):
    """
    Exit when MACD signal turns bearish or at period end.

    Uses MACD (Moving Average Convergence Divergence) to determine exit points:
    - Exits when close price drops below MACD signal line
    """

    def initialize(
        self, ticker: str, start_date: datetime, end_date: datetime, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9
    ) -> None:
        super().initialize(ticker, start_date, end_date)
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

    def calculate_indicators(self) -> pd.DataFrame:
        df = self.bars_history.get_ticker_history(
            self.ticker, self.start_date - timedelta(days=40), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        close_values = df["close"].values.astype(float)
        df["macd_line"], df["macd_signal"], _ = talib.MACD(
            close_values, fastperiod=self.fastperiod, slowperiod=self.slowperiod, signalperiod=self.signalperiod
        )
        # filter index >= start_date
        self.df = df[df.index >= self.start_date].copy()
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with MACD exit logic."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Find first day where close is below signal line
        below_signal = data[data["close"] < data["macd_signal"]]

        if not below_signal.empty:
            # Exit on first close below signal line
            return Trade(date=below_signal.index[0], price=below_signal.iloc[0]["close"], reason="below_signal")
        else:
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")