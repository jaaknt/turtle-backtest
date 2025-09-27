"""Data models for portfolio backtesting."""

from dataclasses import dataclass, field
from datetime import datetime

from turtle.backtest.models import FutureTrade, Trade


@dataclass
class Position:
    """
    Represents a single portfolio position.

    Attributes:
        entry: Trade object representing entry trade
        exit: Trade object representing exit trade in future
        position_size: Number of shares held
    """

    entry: Trade
    exit: Trade
    current_price: float
    position_size: int

    @property
    def ticker(self) -> str:
        """Get the ticker symbol from the entry trade."""
        return self.entry.ticker

    @property
    def current_value(self) -> float:
        """Get the current market value of the position."""
        return self.current_price * self.position_size

    @property
    def unrealized_pnl(self) -> float:
        """Get unrealized P&L"""
        return (self.current_price - self.entry.price) * self.position_size

    @property
    def holding_period_days(self) -> int:
        """Get the holding period in days"""
        return (self.exit.date - self.entry.date).days


@dataclass
class DailyPortfolioSnapshot:
    """
    Daily snapshot of portfolio state.

    Attributes:
        date: Snapshot date
        total_value: Total portfolio value
        cash: Available cash
        positions: List of positions at snapshot time
    """

    date: datetime
    cash: float
    positions: list[Position]

    @property
    def positions_value(self) -> float:
        """Total value of all positions at snapshot time."""
        return sum(position.current_value for position in self.positions)

    @property
    def positions_count(self) -> int:
        """Number of positions at snapshot time."""
        return len(self.positions)

    @property
    def total_value(self) -> float:
        """Total value of all positions at snapshot time."""
        return self.cash + self.positions_value

    def get_position(self, ticker: str) -> Position:
        """Get a position by ticker symbol."""
        for position in self.positions:
            if position.ticker == ticker:
                return position
        raise ValueError(f"Position not found for ticker: {ticker}")

    def add_position(self, position: Position) -> None:
        """Add a new position."""
        self.positions.append(position)
        self.cash -= position.current_value

    def remove_position(self, ticker: str, price: float) -> None:
        """Remove a position by ticker symbol."""
        position = self.get_position(ticker)
        self.cash += position.position_size * price
        self.positions = [p for p in self.positions if p.ticker != ticker]

    def update_position_price(self, ticker: str, new_price: float) -> None:
        """Update the price of an existing position by creating a new exit trade."""
        position = self.get_position(ticker)
        position.current_price = new_price
        return None

    def copy(self) -> "DailyPortfolioSnapshot":
        """Create a deep copy of the snapshot."""
        return DailyPortfolioSnapshot(
            date=self.date,
            cash=self.cash,
            positions=[
                Position(
                    entry=Trade(p.entry.ticker, p.entry.date, p.entry.price, p.entry.reason),
                    exit=Trade(p.exit.ticker, p.exit.date, p.exit.price, p.exit.reason),
                    position_size=p.position_size,
                    current_price=p.current_price,
                )
                for p in self.positions
            ],
        )

    def get_tickers(self) -> list[str]:
        """Get a list of all ticker symbols in the portfolio."""
        return [position.ticker for position in self.positions]


@dataclass
class PortfolioState:
    """
    Current state of the portfolio.

    Attributes:
        daily_snapshots: Historical daily snapshots
        future_trades: List of all future trades
    """

    daily_snapshots: list[DailyPortfolioSnapshot] = field(default_factory=list)
    future_trades: list[FutureTrade] = field(default_factory=list)
