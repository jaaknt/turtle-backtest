"""Trailing percentage loss exit strategy."""

import logging
from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.common.pandas_utils import safe_float_conversion
from turtle.model import Trade

import pandas as pd

from .base import ExitStrategy

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

    def initialize(self, ticker: str, start_date: datetime, end_date: datetime, percentage_loss: float = 10.0) -> None:
        super().initialize(ticker, start_date, end_date)
        self.percentage_loss = percentage_loss

    def calculate_indicators(self) -> pd.DataFrame:
        self.df = self.bars_history.get_ticker_history(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate exit using a trailing stop set as a percentage below the running max close."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        df = data.copy()
        multiplier = 1 - self.percentage_loss / 100

        entry_price = safe_float_conversion(df.iloc[0]["open"])
        initial_stop = entry_price * multiplier

        # Trailing stop = running max close * multiplier, but never below initial stop
        df["cummax_close"] = df["close"].cummax()
        df["trailing_stop"] = (df["cummax_close"] * multiplier).clip(lower=initial_stop)

        exit_mask: pd.Series[bool] = df["close"] < df["trailing_stop"]

        if exit_mask.any():
            exit_idx = exit_mask.idxmax()
            exit_position = df.index.get_loc(exit_idx)
            close_price = safe_float_conversion(df.iloc[exit_position]["close"])
            trailing_stop = safe_float_conversion(df.iloc[exit_position]["trailing_stop"])

            logger.debug(f"Trailing stop triggered on {exit_idx}: Close {close_price:.2f} < Stop {trailing_stop:.2f}")

            trade_date = pd.to_datetime(exit_idx).to_pydatetime() if not isinstance(exit_idx, datetime) else exit_idx
            return Trade(ticker=self.ticker, date=trade_date, price=close_price, reason="trailing_percentage_stop")

        last_date = df.index[-1]
        final_close = safe_float_conversion(df.iloc[-1]["close"])

        logger.debug(f"Period end: Final close {final_close:.2f}")

        trade_date = pd.to_datetime(last_date).to_pydatetime() if not isinstance(last_date, datetime) else last_date
        return Trade(ticker=self.ticker, date=trade_date, price=final_close, reason="period_end")
