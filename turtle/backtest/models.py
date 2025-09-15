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
    reason: str = ""  # Default reason for exit


@dataclass
class SignalResult:
    """
    Represents a single trading signal and its outcomes.

    Attributes:
        signal: Signal that is input for calculation
        entry: Trade object containing entry date, price, and reason
        exit: Trade object containing exit date, price, and reason
        return_pct: Percentage return between entry.price and exit.price
        return_pct_qqq: QQQ benchmark percentage return for the same period
        return_pct_spy: SPY benchmark percentage return for the same period
    """

    signal: Signal
    entry: Trade
    exit: Trade
    return_pct: float
    return_pct_qqq: float
    return_pct_spy: float
