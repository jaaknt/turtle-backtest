"""Profit/Loss target exit strategy."""

from datetime import date, datetime
from turtle.common.enums import TimeFrameUnit
from turtle.model import Trade

import polars as pl

from .base import ExitStrategy


class ProfitLossExitStrategy(ExitStrategy):
    """
    Exit when profit target or stop loss is hit, whichever comes first.
    """

    def initialize(
        self, ticker: str, start_date: datetime, end_date: datetime, profit_target: float = 10.0, stop_loss: float = 5.0
    ) -> None:
        super().initialize(ticker, start_date, end_date)
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        print(f"Initialized ProfitLossExitStrategy with profit target {profit_target}% and stop loss {stop_loss}%")

    def calculate_indicators(self) -> pl.DataFrame:
        return self.bars_history.get_bars_pl(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return with profit/loss targets."""

        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        entry_price = data["open"][0]
        self.profit_price = entry_price * (1 + self.profit_target / 100)
        self.stop_price = entry_price * (1 - self.stop_loss / 100)

        profit_rows = data.filter(pl.col("high") >= self.profit_price)
        loss_rows = data.filter(pl.col("low") <= self.stop_price)

        first_profit_date = profit_rows["date"][0] if not profit_rows.is_empty() else None
        first_loss_date = loss_rows["date"][0] if not loss_rows.is_empty() else None

        def to_dt(d: date) -> datetime:
            return datetime(d.year, d.month, d.day)

        if first_profit_date is not None and first_loss_date is not None:
            if first_profit_date <= first_loss_date:
                return Trade(ticker=self.ticker, date=to_dt(first_profit_date), price=self.profit_price, reason="profit_target")
            else:
                return Trade(ticker=self.ticker, date=to_dt(first_loss_date), price=self.stop_price, reason="stop_loss")
        elif first_profit_date is not None:
            return Trade(ticker=self.ticker, date=to_dt(first_profit_date), price=self.profit_price, reason="profit_target")
        elif first_loss_date is not None:
            return Trade(ticker=self.ticker, date=to_dt(first_loss_date), price=self.stop_price, reason="stop_loss")

        row = data.row(-1, named=True)
        return Trade(ticker=self.ticker, date=to_dt(row["date"]), price=row["close"], reason="period_end")
