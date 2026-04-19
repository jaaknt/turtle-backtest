"""ATR-based exit strategy."""

import logging
from datetime import datetime, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.model import Trade

import polars as pl

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

    def calculate_indicators(self) -> pl.DataFrame:
        df = self.bars_history.get_bars_pl(
            self.ticker, self.start_date - timedelta(days=60), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        return (
            df.with_columns(
                pl.max_horizontal(
                    pl.col("high") - pl.col("low"),
                    (pl.col("high") - pl.col("close").shift(1)).abs(),
                    (pl.col("low") - pl.col("close").shift(1)).abs(),
                ).alias("tr")
            )
            .with_columns(pl.col("tr").ewm_mean(alpha=1.0 / self.atr_period, adjust=False).alias("atr"))
            .filter(pl.col("date") >= self.start_date.date())
        )

    def calculate_exit(self, data: pl.DataFrame) -> Trade:
        """Calculate return with ATR trailing stop loss using vectorized operations."""
        if data.is_empty():
            raise ValueError("No valid data available for exit calculation.")

        if "atr" not in data.columns:
            raise ValueError("ATR column not found in data. Ensure calculate_indicators() was called first.")

        first_row = data.row(0, named=True)
        entry_price: float = first_row["open"]
        entry_atr: float | None = first_row["atr"]

        if entry_atr is None or entry_atr == 0:
            raise ValueError("ATR value is NaN or zero for entry date. Cannot calculate stop loss.")

        initial_stop = entry_price - (self.atr_multiplier * entry_atr)
        logger.debug(f"Entry price: {entry_price:.2f}, Entry ATR: {entry_atr:.2f}, Initial stop: {initial_stop:.2f}")

        df = (
            data.with_columns(pl.col("high").cum_max().alias("cummax_high"))
            .with_columns((pl.col("cummax_high") - self.atr_multiplier * pl.col("atr")).alias("potential_stop"))
            .with_columns(pl.col("potential_stop").cum_max().clip(lower_bound=initial_stop).alias("trailing_stop"))
            .with_columns(pl.col("trailing_stop").forward_fill().alias("trailing_stop"))
        )

        exit_rows = df.filter(pl.col("close") < pl.col("trailing_stop"))
        if not exit_rows.is_empty():
            row = exit_rows.row(0, named=True)
            d = row["date"]
            exit_date = datetime(d.year, d.month, d.day)
            logger.debug(f"Stop loss triggered on {exit_date}: Close {row['close']:.2f} < Stop {row['trailing_stop']:.2f}")
            return Trade(ticker=self.ticker, date=exit_date, price=row["close"], reason="atr_trailing_stop")

        row = df.row(-1, named=True)
        d = row["date"]
        final_date = datetime(d.year, d.month, d.day)
        logger.debug(f"Period end: Final close {row['close']:.2f}, Final stop {row['trailing_stop']:.2f}")
        return Trade(ticker=self.ticker, date=final_date, price=row["close"], reason="period_end")
