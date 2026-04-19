"""MACD-based exit strategy."""

from datetime import datetime, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.model import Trade

import polars as pl

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

    def calculate_indicators(self) -> pl.DataFrame:
        df = self.bars_history.get_bars_pl(
            self.ticker, self.start_date - timedelta(days=40), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        return (
            df.with_columns(
                (
                    pl.col("close").ewm_mean(span=self.fastperiod, adjust=False)
                    - pl.col("close").ewm_mean(span=self.slowperiod, adjust=False)
                ).alias("macd_line")
            )
            .with_columns(pl.col("macd_line").ewm_mean(span=self.signalperiod, adjust=False).alias("macd_signal"))
            .filter(pl.col("date") >= self.start_date.date())
        )

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return with MACD exit logic."""
        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        below_signal = data.filter(pl.col("macd_line") < pl.col("macd_signal"))
        if not below_signal.is_empty():
            row = below_signal.row(0, named=True)
            d = row["date"]
            return Trade(ticker=self.ticker, date=datetime(d.year, d.month, d.day), price=row["close"], reason="below_signal")

        row = data.row(-1, named=True)
        d = row["date"]
        return Trade(ticker=self.ticker, date=datetime(d.year, d.month, d.day), price=row["close"], reason="period_end")
