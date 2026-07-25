"""Trailing percentage loss exit strategy."""

import logging
from datetime import date

import polars as pl

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Trade

from .base import ExitStrategy, add_adjusted_columns

logger = logging.getLogger(__name__)


class TrailingPercentageLossExitStrategy(ExitStrategy):
    """
    Trailing Percentage Stop Loss Exit Strategy.

    Sets a stop loss as a fixed percentage below the highest close price seen
    since entry. The stop only moves up as price rises, never down.

    - Initial stop: entry_price * (1 - percentage_loss / 100)
    - Trailing stop: max(close) * (1 - percentage_loss / 100)
    - Exit triggers: when close price drops below current trailing stop
    """

    def initialize(self, ticker: str, start_date: date, end_date: date, percentage_loss: float = 10.0) -> None:
        super().initialize(ticker, start_date, end_date)
        self.percentage_loss = percentage_loss

    def calculate_indicators(self) -> pl.DataFrame:
        df = self.bars_history.get_bars_pl(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)
        return add_adjusted_columns(df)

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate exit using a trailing stop set as a percentage below the running max close."""
        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        multiplier = 1 - self.percentage_loss / 100
        entry_price: float = data["adj_open"][0]
        initial_stop = entry_price * multiplier

        df = data.with_columns(pl.col("adj_close").cum_max().alias("cummax_close")).with_columns(
            (pl.col("cummax_close") * multiplier).clip(lower_bound=initial_stop).alias("trailing_stop")
        )

        exit_rows = df.filter(pl.col("adj_close") < pl.col("trailing_stop"))
        if not exit_rows.is_empty():
            row = exit_rows.row(0, named=True)
            exit_date = row["date"]
            logger.debug(f"Trailing stop triggered on {exit_date}: Close {row['adj_close']:.2f} < Stop {row['trailing_stop']:.2f}")
            return Trade(ticker=self.ticker, date=exit_date, price=row["adj_close"], reason="trailing_percentage_stop")

        row = df.row(-1, named=True)
        final_date = row["date"]
        logger.debug(f"Period end: Final close {row['adj_close']:.2f}")
        return Trade(ticker=self.ticker, date=final_date, price=row["adj_close"], reason="period_end")
