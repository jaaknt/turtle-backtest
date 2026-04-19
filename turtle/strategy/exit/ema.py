"""EMA-based exit strategy."""

from datetime import datetime, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.model import Trade

import polars as pl

from .base import ExitStrategy


class EMAExitStrategy(ExitStrategy):
    """
    Exit when price closes below EMA or at period end.

    This strategy calculates EMA indicators and exits when price drops below the EMA.
    """

    def initialize(self, ticker: str, start_date: datetime, end_date: datetime, ema_period: int = 20) -> None:
        super().initialize(ticker, start_date, end_date)
        self.ema_period = ema_period

    def calculate_indicators(self) -> pl.DataFrame:
        df = self.bars_history.get_bars_pl(
            self.ticker, self.start_date - timedelta(days=40), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        return df.with_columns(pl.col("close").ewm_mean(span=self.ema_period, adjust=False).alias("ema")).filter(
            pl.col("date") >= self.start_date.date()
        )

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return with EMA exit logic."""

        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        below_ema = data.filter(pl.col("close") < pl.col("ema"))
        if not below_ema.is_empty():
            row = below_ema.row(0, named=True)
            d = row["date"]
            return Trade(ticker=self.ticker, date=datetime(d.year, d.month, d.day), price=row["close"], reason="stop_loss")

        row = data.row(-1, named=True)
        d = row["date"]
        return Trade(ticker=self.ticker, date=datetime(d.year, d.month, d.day), price=row["close"], reason="period_end")
