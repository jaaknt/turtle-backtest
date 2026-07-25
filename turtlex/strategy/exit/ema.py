"""EMA-based exit strategy."""

from datetime import date, timedelta

import polars as pl

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Trade

from .base import ExitStrategy, add_adjusted_columns


class EMAExitStrategy(ExitStrategy):
    """
    Exit when price closes below EMA or at period end.

    This strategy calculates EMA indicators and exits when price drops below the EMA.
    Both the EMA and the exit price use the split/dividend-adjusted close, matching the
    adjusted entry price.
    """

    def initialize(self, ticker: str, start_date: date, end_date: date, ema_period: int = 20) -> None:
        super().initialize(ticker, start_date, end_date)
        self.ema_period = ema_period

    def calculate_indicators(self) -> pl.DataFrame:
        df = self.bars_history.get_bars_pl(
            self.ticker, self.start_date - timedelta(days=40), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        df = add_adjusted_columns(df)
        return df.with_columns(pl.col("adj_close").ewm_mean(span=self.ema_period, adjust=False).alias("ema")).filter(
            pl.col("date") >= self.start_date
        )

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return with EMA exit logic."""

        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        below_ema = data.filter(pl.col("adj_close") < pl.col("ema"))
        if not below_ema.is_empty():
            row = below_ema.row(0, named=True)
            return Trade(ticker=self.ticker, date=row["date"], price=row["adj_close"], reason="stop_loss")

        row = data.row(-1, named=True)
        return Trade(ticker=self.ticker, date=row["date"], price=row["adj_close"], reason="period_end")
