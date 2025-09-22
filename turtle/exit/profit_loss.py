"""Profit/Loss target exit strategy."""

from datetime import datetime
import pandas as pd

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
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

    def calculate_indicators(self) -> pd.DataFrame:
        self.df = self.bars_history.get_ticker_history(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with profit/loss targets."""

        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Assume entry at open price of first day
        entry_price = data.iloc[0]["open"]
        self.profit_price = entry_price * (1 + self.profit_target / 100)
        self.stop_price = entry_price * (1 - self.stop_loss / 100)

        # Find first profit target hit
        profit_hits = data[data["high"] >= self.profit_price]
        first_profit_date = profit_hits.index[0] if not profit_hits.empty else None

        # Find first stop loss hit
        loss_hits = data[data["low"] <= self.stop_price]
        first_loss_date = loss_hits.index[0] if not loss_hits.empty else None

        # Determine which target was hit first (if any)
        if first_profit_date is not None and first_loss_date is not None:
            # Both targets hit - use whichever came first
            if first_profit_date <= first_loss_date:
                return Trade(ticker=self.ticker, date=profit_hits.index[0], price=self.profit_price, reason="profit_target")
            else:
                return Trade(ticker=self.ticker, date=loss_hits.index[0], price=self.stop_price, reason="stop_loss")
        elif first_profit_date is not None:
            # Only profit target hit
            return Trade(ticker=self.ticker, date=profit_hits.index[0], price=self.profit_price, reason="profit_target")
        elif first_loss_date is not None:
            # Only stop loss hit
            return Trade(ticker=self.ticker, date=loss_hits.index[0], price=self.stop_price, reason="stop_loss")
        else:
            last_record = data.iloc[-1]
            return Trade(ticker=self.ticker, date=data.index[-1], price=last_record["close"], reason="period_end")
