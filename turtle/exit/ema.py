"""EMA-based exit strategy."""

from datetime import datetime, timedelta
import pandas as pd
import talib

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from .base import ExitStrategy


class EMAExitStrategy(ExitStrategy):
    """
    Exit when price closes below EMA or at period end.

    This strategy calculates EMA indicators and exits when price drops below the EMA.
    """

    def initialize(self, ticker: str, start_date: datetime, end_date: datetime, ema_period: int = 20) -> None:
        super().initialize(ticker, start_date, end_date)
        self.ema_period = ema_period
        # print(f"EMAExitStrategy EMA period {ema_period}")

    def calculate_indicators(self) -> pd.DataFrame:
        df = self.bars_history.get_ticker_history(
            self.ticker, self.start_date - timedelta(days=40), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        close_values = df["close"].values.astype(float)
        df["ema"] = talib.EMA(close_values, timeperiod=self.ema_period)

        self.df = df[df.index >= self.start_date].copy()
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with EMA exit logic."""

        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Find first day where close is below EMA
        below_ema = data[data["close"] < data["ema"]]

        if not below_ema.empty:
            # Exit on first close below EMA
            return Trade(ticker=self.ticker, date=below_ema.index[0], price=below_ema.iloc[0]["close"], reason="stop_loss")
        else:
            last_record = data.iloc[-1]
            return Trade(ticker=self.ticker, date=data.index[-1], price=last_record["close"], reason="period_end")
