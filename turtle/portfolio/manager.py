"""Portfolio position and cash management."""

import logging
from datetime import datetime
from turtle.backtest.models import Trade
from .models import PortfolioState, DailyPortfolioSnapshot, Position

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Manages portfolio positions, cash allocation, and transactions.

    Handles opening and closing positions, cash management, and portfolio state updates.
    """

    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 30000.0,
        position_min_amount: float = 1500.0,
        position_max_amount: float = 3000.0,
    ):
        """
        Initialize portfolio manager.

        Args:
            initial_capital: Starting capital amount
            position_size_strategy: Strategy for position sizing ("equal_weight", "percentage")
            position_size_amount: Fixed amount per position for equal_weight strategy
            min_cash_reserve: Minimum cash to maintain for operational flexibility
        """
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.position_min_amount = position_min_amount
        self.position_max_amount = position_max_amount

        # Initialize portfolio state
        self.state = PortfolioState(
            daily_snapshots=[],
            closed_trades=[],
        )

    @property
    def current_snapshot(self) -> DailyPortfolioSnapshot:
        """Get the current daily snapshot."""
        return self.state.daily_snapshots[-1]

    def calculate_position_size(self, entry: Trade) -> int:
        """
        Calculate position size for a new entry.

        Args:
            signal: Trading signal
            current_price: Current stock price

        Returns:
            position_size: Number of shares to buy
        """
        target_value = min(self.position_max_amount, self.current_snapshot.cash)
        position_size = int(target_value / entry.price)
        logger.debug(
            f"Position size calculation for {entry.ticker}: target=${target_value}, "
            f"price=${entry.price}, shares={position_size}, cash=${self.current_snapshot.cash}"
        )
        return position_size

    def open_position(
        self,
        entry: Trade,
        exit: Trade,
        position_size: int,
    ) -> Position:
        """
        Open a new position.

        Args:
            entry: Trade entry data
            position_size: Number of shares to buy

        Returns:
            Position object
        """

        cost = entry.price * position_size

        position = Position(
            entry=entry,
            exit=exit,
            position_size=position_size,
            current_price=entry.price,
        )

        self.current_snapshot.add_position(position)

        logger.info(
            f"Opened position: {entry.date.date()} {entry.ticker} x{position_size} "
            f"@ ${entry.price:.2f} cost=${cost:.2f} cash=${self.current_snapshot.cash:.2f}"
        )

        return position

    def close_position(
        self,
        exit: Trade,
        position_size: int,
    ) -> None:
        """
        Close an existing position.

        Args:
            exit: Exit trade data

        Returns:
            None
        """

        ticker = exit.ticker
        cost = exit.price * position_size

        # Update portfolio state
        self.current_snapshot.remove_position(ticker, price=exit.price)

        logger.info(
            f"Closed position: {exit.date.date()} {exit.ticker} ${exit.price:.2f} cost=${cost:.2f} cash=${self.current_snapshot.cash:.2f}"
        )

        return None

    def record_daily_snapshot(self, current_date: datetime) -> DailyPortfolioSnapshot:
        """
        Record daily portfolio snapshot for performance tracking.

        Args:
            current_date: Date of snapshot

        Returns:
            DailyPortfolioSnapshot object
        """

        if not self.state.daily_snapshots:
            snapshot = DailyPortfolioSnapshot(
                date=self.start_date,
                cash=self.initial_capital,
                positions=[],
            )
        else:
            snapshot = self.current_snapshot.copy()

        snapshot.date = current_date
        self.state.daily_snapshots.append(snapshot)

        return snapshot
