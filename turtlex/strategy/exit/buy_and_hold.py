"""Buy and hold exit strategy."""

from datetime import date, timedelta

import polars as pl

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Trade

from .base import ExitStrategy


class BuyAndHoldExitStrategy(ExitStrategy):
    """
    Simple buy and hold strategy - exit after a fixed holding period.

    Sells at the first bar on or after ``start_date + holding_days`` calendar
    days, or at the last available bar if the data ends before the cutoff.

    Exits on the split/dividend-adjusted close so the exit shares a price basis
    with the adjusted entry price, keeping returns correct across a split.
    """

    def initialize(self, ticker: str, start_date: date, end_date: date, holding_days: int = 30) -> None:
        """Initialize the strategy for one exit calculation.

        Args:
            ticker: Ticker symbol to calculate the exit for
            start_date: Position entry date (start of the holding period)
            end_date: Upper limit for the exit calculation
            holding_days: Calendar days the position is kept before selling (default 30)
        """
        super().initialize(ticker, start_date, end_date)
        self.holding_days = holding_days

    def calculate_indicators(self) -> pl.DataFrame:
        return self.bars_history.get_bars_pl(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return by holding for the configured number of calendar days."""

        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        cutoff = self.start_date + timedelta(days=self.holding_days)
        eligible = data.filter(pl.col("date") >= cutoff)
        if not eligible.is_empty():
            row = eligible.row(0, named=True)
            reason = "holding_period"
        else:
            row = data.row(-1, named=True)
            reason = "period_end"
        return Trade(ticker=self.ticker, date=row["date"], price=row["adjusted_close"], reason=reason)
