"""Portfolio position and cash management."""

import logging
from datetime import date

from turtlex.model import DailyPortfolioSnapshot, PortfolioState, Position, Trade

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Manages portfolio positions, cash allocation, and transactions.

    Handles opening and closing positions, cash management, and portfolio state updates.
    """

    def __init__(
        self,
        start_date: date,
        end_date: date,
        initial_capital: float = 30000.0,
        position_size_pct: float = 0.04,
    ):
        """
        Initialize portfolio manager.

        Args:
            start_date: Backtest start date, used for the opening snapshot
            end_date: Backtest end date
            initial_capital: Starting capital amount
            position_size_pct: Fraction of current portfolio value committed per position
                (0.04 = 4%), so position size compounds with the portfolio
        """
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct

        # Initialize portfolio state
        self.state = PortfolioState(
            daily_snapshots=[],
            future_trades=[],
        )

    @property
    def current_snapshot(self) -> DailyPortfolioSnapshot:
        """Get the current daily snapshot."""
        return self.state.daily_snapshots[-1]

    def calculate_position_size(self, entry: Trade) -> int:
        """
        Calculate position size for a new entry as a fraction of current portfolio value.

        The target commits `position_size_pct` of total value (cash plus open positions
        marked to market), so it compounds as the portfolio grows. Two situations skip the
        entry outright rather than part-filling it, both returning 0 shares: available cash
        cannot fund the target, or one share already costs more than the whole target.

        Args:
            entry: Entry trade carrying the ticker and fill price

        Returns:
            position_size: Number of whole shares to buy, or 0 if the entry is skipped
        """
        cash = self.current_snapshot.cash
        target_value = self.position_size_pct * self.current_snapshot.total_value
        if cash + 1e-9 < target_value:
            logger.debug(f"Skipping {entry.ticker}: target ${target_value:.2f} exceeds cash ${cash:.2f}")
            return 0
        position_size = int(target_value / entry.price)
        if position_size <= 0:
            logger.debug(f"Skipping {entry.ticker}: price ${entry.price:.2f} exceeds target ${target_value:.2f}")
            return 0
        logger.debug(
            f"Position size calculation for {entry.ticker}: target=${target_value:.2f}, "
            f"price=${entry.price}, shares={position_size}, cash=${cash:.2f}"
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
            f"Opened position: {entry.date} {entry.ticker} x{position_size} "
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

        logger.info(f"Closed position: {exit.date} {exit.ticker} ${exit.price:.2f} cost=${cost:.2f} cash=${self.current_snapshot.cash:.2f}")

        return None

    def record_daily_snapshot(self, current_date: date) -> DailyPortfolioSnapshot:
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
