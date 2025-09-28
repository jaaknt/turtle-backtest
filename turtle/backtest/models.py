from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from turtle.signal.models import Signal


@dataclass
class Trade:
    """
    Represents a single trade.

    Attributes:
        ticker: Stock symbol for the trade
        date: Trade date and time
        price: Price at which the trade was executed
        reason: Reason for entry or exit
    """

    ticker: str
    date: datetime
    price: float
    reason: str


@dataclass
class Benchmark:
    """
    Represents a benchmark return comparison.

    Attributes:
        ticker: Benchmark ticker symbol (e.g., 'SPY', 'QQQ')
        return_pct: Percentage return for the benchmark over the same period
        entry_date: Date when the benchmark calculation period starts
        exit_date: Date when the benchmark calculation period ends
    """

    ticker: str
    return_pct: float
    entry_date: datetime
    exit_date: datetime


@dataclass
class FutureTrade:
    """
    Represents a completed trading signal and its outcomes.

    Attributes:
        signal: Signal that is input for calculation
        entry: Trade object containing entry date, price, and reason
        exit: Trade object containing exit date, price, and reason
        benchmark_list: List of benchmark comparisons for the same period
        position_size: Position size in shares or dollar amount (defaults to 1.0)
        entry_signal_ranking: Original signal ranking when position was opened (optional)
    """

    signal: Signal
    entry: Trade
    exit: Trade
    benchmark_list: list[Benchmark]
    position_size: float = 1.0

    @property
    def holding_days(self) -> int:
        """
        Calculate the number of days the position was held.

        Returns:
            Number of days between entry and exit dates
        """
        return (self.exit.date - self.entry.date).days

    @property
    def realized_pnl(self) -> float:
        """
        Calculate the realized profit/loss in dollars.

        Returns:
            Realized profit/loss = (exit_price - entry_price) * position_size
        """
        return (self.exit.price - self.entry.price) * self.position_size

    @property
    def realized_pct(self) -> float:
        """
        Calculate the realized percentage return.

        Returns:
            Percentage return = ((exit_price - entry_price) / entry_price) * 100
        """
        if self.entry.price <= 0:
            raise ValueError(f"Invalid entry price: {self.entry.price}")
        return ((self.exit.price - self.entry.price) / self.entry.price) * 100.0

    @property
    def exit_reason(self) -> str:
        """
        Get the exit reason from the exit trade.

        Returns:
            Exit reason string
        """
        return self.exit.reason

    @property
    def ticker(self) -> str:
        """
        Get the ticker symbol from the signal or entry trade.

        Returns:
            Ticker symbol string
        """
        return self.signal.ticker

    @property
    def slippage(self) -> float:
        """
        Calculate the slippage in dollars.
        Returns:
            slippage = (entry_price + exit_price) / 2 * 0.005 * position_size
        """
        entry_price = self.entry.price
        exit_price = self.exit.price
        return (entry_price + exit_price) / 2 * 0.005 * self.position_size
