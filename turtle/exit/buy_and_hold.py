"""Buy and hold exit strategy."""

import pandas as pd

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from .base import ExitStrategy


class BuyAndHoldExitStrategy(ExitStrategy):
    """
    Simple buy and hold strategy - exit at period end.
    """

    def calculate_indicators(self) -> pd.DataFrame:
        self.df = self.bars_history.get_ticker_history(self.ticker, self.start_date, self.end_date, time_frame_unit=TimeFrameUnit.DAY)
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return by holding until target date."""

        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # find last record in DataFrame
        last_record = data.iloc[-1]
        return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")
