"""Data models for portfolio backtesting."""

from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from collections import defaultdict

from turtle.backtest.models import Benchmark, ClosedTrade


@dataclass
class Position:
    """
    Represents a single portfolio position.

    Attributes:
        ticker: Stock symbol
        entry_date: Date when position was opened
        entry_price: Price at which position was entered
        shares: Number of shares held
        entry_signal_ranking: Original signal ranking when position was opened
        closed_trade: Associated ClosedTrade with pre-calculated exit data
        current_price: Latest known price
        current_value: Current market value of position
        unrealized_pnl: Unrealized profit/loss in dollars
        unrealized_pnl_pct: Unrealized profit/loss as percentage
    """
    ticker: str
    entry_date: datetime
    entry_price: float
    shares: int
    entry_signal_ranking: int
    closed_trade: "ClosedTrade"
    current_price: float = 0.0
    current_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    def update_current_price(self, price: float) -> None:
        """Update position with current market price and recalculate metrics."""
        self.current_price = price
        self.current_value = self.shares * price
        self.unrealized_pnl = self.current_value - (self.shares * self.entry_price)
        self.unrealized_pnl_pct = (self.unrealized_pnl / (self.shares * self.entry_price)) * 100.0


@dataclass
class ClosedPosition:
    """
    Represents a closed position with realized returns.

    Attributes:
        ticker: Stock symbol
        entry_date: Date when position was opened
        exit_date: Date when position was closed
        entry_price: Price at which position was entered
        exit_price: Price at which position was exited
        shares: Number of shares held
        entry_signal_ranking: Original signal ranking
        exit_reason: Reason for position closure
        realized_pnl: Realized profit/loss in dollars
        realized_pnl_pct: Realized profit/loss as percentage
        holding_period_days: Number of days position was held
    """
    ticker: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    shares: int
    entry_signal_ranking: int
    exit_reason: str
    realized_pnl: float
    realized_pnl_pct: float
    holding_period_days: int


@dataclass
class DailyPortfolioSnapshot:
    """
    Daily snapshot of portfolio state.

    Attributes:
        date: Snapshot date
        total_value: Total portfolio value
        cash: Available cash
        positions_value: Total value of all positions
        positions_count: Number of open positions
        daily_return: Daily return percentage
        daily_pnl: Daily profit/loss in dollars
    """
    date: datetime
    total_value: float
    cash: float
    positions_value: float
    positions_count: int
    daily_return: float
    daily_pnl: float


@dataclass
class PortfolioState:
    """
    Current state of the portfolio.

    Attributes:
        cash: Available cash for new positions
        positions: Dictionary of current open positions
        total_value: Total portfolio value (cash + positions)
        daily_snapshots: Historical daily snapshots
        closed_positions: List of all closed positions
        scheduled_exits: Pre-calculated exits mapped by date
        last_update_date: Date of last portfolio update
    """
    cash: float
    positions: dict[str, Position]
    total_value: float
    daily_snapshots: list[DailyPortfolioSnapshot]
    closed_positions: list[ClosedPosition]
    scheduled_exits: dict[datetime, list[ClosedTrade]] = field(default_factory=lambda: defaultdict(list))
    last_update_date: datetime | None = None

    @property
    def positions_value(self) -> float:
        """Total value of all open positions."""
        return sum(position.current_value for position in self.positions.values())

    @property
    def positions_count(self) -> int:
        """Number of open positions."""
        return len(self.positions)

    @property
    def available_cash_for_new_position(self) -> float:
        """Cash available for opening new positions."""
        return self.cash

    def update_total_value(self) -> None:
        """Recalculate total portfolio value."""
        self.total_value = self.cash + self.positions_value


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
    closed_positions: list[ClosedPosition]
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
