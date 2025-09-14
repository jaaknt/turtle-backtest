from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pandas as pd
import talib

from turtle.backtest.models import Trade
from turtle.common.enums import TimeFrameUnit
from turtle.data.bars_history import BarsHistoryRepo


class ExitStrategy(ABC):
    """Abstract base class for exit strategies."""

    def __init__(self, bars_history: BarsHistoryRepo):
        self.bars_history = bars_history

    def initialize(self, ticker: str, start_date: datetime, end_date: datetime) -> None:
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        # self.kwargs = kwargs

    @abstractmethod
    def calculate_indicators(self) -> pd.DataFrame:
        """
        Calculate technical indicators for the given ticker and date range.

        Returns:
            DataFrame with calculated indicators.
        """
        pass

    @abstractmethod
    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """
        Calculate period return based on strategy-specific logic.

        Args:
            data: DataFrame with OHLCV data (index should be datetime)

        Returns:
            Trade object representing the exit trade or None if calculation failed
        """
        pass


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


class ProfitLossExitStrategy(ExitStrategy):
    """
    Exit when 10% profit target or 5% stop loss is hit, whichever comes first.
    """

    #    def __init__(self, profit_target: float = 20.0, stop_loss: float = 7.0):
    #        self.profit_target = profit_target
    #        self.stop_loss = stop_loss

    def initialize(
        self, ticker: str, start_date: datetime, end_date: datetime, profit_target: float = 10.0, stop_loss: float = 5.0
    ) -> None:
        super().initialize(ticker, start_date, end_date)
        self.profit_target = profit_target
        self.stop_loss = stop_loss

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
                return Trade(date=profit_hits.index[0], price=self.profit_price, reason="profit_target")
            else:
                return Trade(date=loss_hits.index[0], price=self.stop_price, reason="stop_loss")
        elif first_profit_date is not None:
            # Only profit target hit
            return Trade(date=profit_hits.index[0], price=self.profit_price, reason="profit_target")
        elif first_loss_date is not None:
            # Only stop loss hit
            return Trade(date=loss_hits.index[0], price=self.stop_price, reason="stop_loss")
        else:
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")


class EMAExitStrategy(ExitStrategy):
    """
    Exit when price closes below EMA or at period end.

    Note: This strategy assumes that the EMA column already exists in the data
    (e.g., 'ema_10', 'ema_20', etc.). If the column doesn't exist, an error will be raised.
    """

    #    def __init__(self, ema_period: int = 20):
    #        self.ema_period = ema_period
    #        self.ema_column = f"ema_{ema_period}"
    def initialize(self, ticker: str, start_date: datetime, end_date: datetime, ema_period: int = 20) -> None:
        super().initialize(ticker, start_date, end_date)
        self.ema_period = ema_period

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
            return Trade(date=below_ema.index[0], price=below_ema.iloc[0]["close"], reason="stop_loss")
        else:
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")


class MACDExitStrategy(ExitStrategy):
    """
    Exit when MACD signal turns bearish or at period end.

    Uses MACD (Moving Average Convergence Divergence) to determine exit points:
    - MACD line crosses below signal line (bearish crossover)
    - Or MACD histogram turns negative after being positive

    The strategy calculates MACD indicators if not present in the data.
    """

    #    def __init__(self, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9):
    #        self.fastperiod = fastperiod
    #        self.slowperiod = slowperiod
    #        self.signalperiod = signalperiod

    def initialize(
        self, ticker: str, start_date: datetime, end_date: datetime, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9
    ) -> None:
        super().initialize(ticker, start_date, end_date)
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

    def calculate_indicators(self) -> pd.DataFrame:
        df = self.bars_history.get_ticker_history(
            self.ticker, self.start_date - timedelta(days=40), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )
        close_values = df["close"].values.astype(float)
        df["macd_line"], df["macd_signal"], _ = talib.MACD(
            close_values, fastperiod=self.fastperiod, slowperiod=self.slowperiod, signalperiod=self.signalperiod
        )
        # filter index >= start_date
        self.df = df[df.index >= self.start_date].copy()
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with MACD exit logic."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Find first day where close is below signal line
        below_signal = data[data["close"] < data["macd_signal"]]

        if not below_signal.empty:
            # Exit on first close below signal line
            return Trade(date=below_signal.index[0], price=below_signal.iloc[0]["close"], reason="below_signal")
        else:
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")


class ATRExitStrategy(ExitStrategy):
    """
    Exit when price drops below entry - (ATR multiplier * ATR) or at period end.

    Uses Average True Range (ATR) to set volatility-adjusted stop losses:
    - Stop loss = Entry Price - (ATR Multiplier × ATR)
    - No profit target - holds until stop loss or period end
    - ATR provides dynamic stop based on recent volatility
    """

    def initialize(
        self, ticker: str, start_date: datetime, end_date: datetime, atr_period: int = 14, atr_multiplier: float = 2.0
    ) -> None:
        super().initialize(ticker, start_date, end_date)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

    def calculate_indicators(self) -> pd.DataFrame:
        # Get extra days for ATR calculation
        df = self.bars_history.get_ticker_history(
            self.ticker, self.start_date - timedelta(days=60), self.end_date, time_frame_unit=TimeFrameUnit.DAY
        )

        # Calculate ATR using TA-Lib
        high_values = df["high"].values.astype(float)
        low_values = df["low"].values.astype(float)
        close_values = df["close"].values.astype(float)

        df["atr"] = talib.ATR(high_values, low_values, close_values, timeperiod=self.atr_period)

        # Filter to requested date range
        self.df = df[df.index >= self.start_date].copy()
        return self.df

    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        """Calculate return with ATR-based stop loss."""
        if data.empty:
            raise ValueError("No valid data available for exit calculation.")

        # Check if ATR column exists
        if "atr" not in data.columns:
            raise ValueError("ATR column not found in data. Ensure calculate_indicators() was called first.")

        # Entry price is the open of the first day
        entry_price = data.iloc[0]["open"]

        # Calculate stop loss for each day based on current ATR
        # Stop = Entry Price - (ATR Multiplier × Current ATR)
        data_copy = data.copy()
        data_copy["stop_price"] = entry_price - (self.atr_multiplier * data_copy["atr"])

        # Find first day where low touches or goes below stop price
        stop_hits = data_copy[data_copy["low"] <= data_copy["stop_price"]]

        if not stop_hits.empty:
            # Exit at stop price on first stop hit
            first_stop_date = stop_hits.index[0]
            stop_price = stop_hits.iloc[0]["stop_price"]
            return Trade(date=first_stop_date, price=stop_price, reason="atr_stop_loss")
        else:
            # Hold until period end
            last_record = data.iloc[-1]
            return Trade(date=data.index[-1], price=last_record["close"], reason="period_end")
