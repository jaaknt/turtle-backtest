from dataclasses import dataclass
from datetime import datetime

from turtle.signal.models import Signal


@dataclass
class Trade:
    """
    Represents a single trade.

    Attributes:
        date: Trade date and time
        price: Price at which the trade was executed
    """

    date: datetime
    price: float
    reason: str = ""  # Default reason for entry or exit


@dataclass
class Benchmark:
    """
    Represents a benchmark return comparison.

    Attributes:
        ticker: Benchmark ticker symbol (e.g., 'SPY', 'QQQ')
        return_pct: Percentage return for the benchmark over the same period
    """

    ticker: str
    return_pct: float


@dataclass
class ClosedTrade:
    """
    Represents a completed trading signal and its outcomes.

    Attributes:
        signal: Signal that is input for calculation
        entry: Trade object containing entry date, price, and reason
        exit: Trade object containing exit date, price, and reason
        return_pct: Percentage return between entry.price and exit.price
        benchmark_list: List of benchmark comparisons for the same period
    """

    signal: Signal
    entry: Trade
    exit: Trade
    return_pct: float
    benchmark_list: list[Benchmark]

    @property
    def holding_days(self) -> int:
        """
        Calculate the number of days the position was held.

        Returns:
            Number of days between entry and exit dates
        """
        return (self.exit.date - self.entry.date).days
