"""Data models for portfolio backtesting."""

from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from turtle.backtest.models import Benchmark, ClosedTrade, Trade


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
        daily_return: Daily return percentage
        daily_pnl: Daily profit/loss in dollars
    """

    date: datetime
    cash: float
    positions: list[Position]
    daily_return: float
    daily_pnl: float

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
            daily_return=0.0,
            daily_pnl=0.0,
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
        closed_trades: List of all closed trades
    """

    daily_snapshots: list[DailyPortfolioSnapshot] = field(default_factory=list)
    closed_trades: list[ClosedTrade] = field(default_factory=list)


@dataclass
class PortfolioResults:
    """
    Complete portfolio backtesting results with performance metrics.

    Attributes:
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital amount
        final_value: Final portfolio value
        final_cash: Final cash amount
        total_return_pct: Total return percentage
        total_return_dollars: Total return in dollars
        daily_returns: Series of daily returns
        daily_values: Series of daily portfolio values
        closed_positions: All closed positions during backtest
        max_positions_held: Maximum number of positions held simultaneously
        total_trades: Total number of completed trades
        winning_trades: Number of profitable trades
        losing_trades: Number of losing trades
        win_rate: Percentage of winning trades
        avg_win_pct: Average winning trade percentage
        avg_loss_pct: Average losing trade percentage
        avg_holding_period: Average holding period in days
        max_drawdown_pct: Maximum drawdown percentage
        sharpe_ratio: Sharpe ratio
        volatility: Portfolio volatility
        benchmark_returns: List of benchmark comparison data
    """

    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    final_cash: float
    total_return_pct: float
    total_return_dollars: float
    daily_returns: pd.Series
    daily_values: pd.Series
    closed_positions: list[ClosedTrade]
    max_positions_held: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    avg_holding_period: float
    max_drawdown_pct: float
    sharpe_ratio: float
    volatility: float
    benchmark_returns: list[Benchmark] | None = None
