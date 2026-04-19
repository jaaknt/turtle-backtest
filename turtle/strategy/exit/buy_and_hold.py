"""Buy and hold exit strategy."""

from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.model import Trade

import polars as pl

from .base import ExitStrategy


class BuyAndHoldExitStrategy(ExitStrategy):
    """
    Simple buy and hold strategy - exit at period end.
    """

    def calculate_indicators(self) -> pl.DataFrame:
        return self.bars_history.get_bars_pl(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return by holding until target date."""

        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        row = data.row(-1, named=True)
        d = row["date"]
        return Trade(ticker=self.ticker, date=datetime(d.year, d.month, d.day), price=row["close"], reason="period_end")
