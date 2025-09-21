"""Portfolio position and cash management."""

import logging
from datetime import datetime
from turtle.signal.models import Signal
from turtle.backtest.models import ClosedTrade
from .models import Position, ClosedPosition, PortfolioState, DailyPortfolioSnapshot

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Manages portfolio positions, cash allocation, and transactions.

    Handles opening and closing positions, cash management, and portfolio state updates.
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_size_strategy: str = "equal_weight",
        position_size_amount: float = 1000.0,
        min_cash_reserve: float = 500.0,
    ):
        """
        Initialize portfolio manager.

        Args:
            initial_capital: Starting capital amount
            position_size_strategy: Strategy for position sizing ("equal_weight", "percentage")
            position_size_amount: Fixed amount per position for equal_weight strategy
            min_cash_reserve: Minimum cash to maintain for operational flexibility
        """
        self.initial_capital = initial_capital
        self.position_size_strategy = position_size_strategy
        self.position_size_amount = position_size_amount
        self.min_cash_reserve = min_cash_reserve

        # Initialize portfolio state
        self.state = PortfolioState(
            cash=initial_capital,
            positions={},
            total_value=initial_capital,
            daily_snapshots=[],
            closed_positions=[],
        )

    def can_open_new_position(self, required_capital: float | None = None) -> bool:
        """
        Check if portfolio can open a new position.

        Args:
            required_capital: Required capital for position (uses default sizing if None)

        Returns:
            True if sufficient cash is available
        """
        required = required_capital or self.position_size_amount
        available_cash = self.state.cash - self.min_cash_reserve
        return available_cash >= required

    def calculate_position_size(self, signal: Signal, current_price: float) -> tuple[int, float]:
        """
        Calculate position size for a new entry.

        Args:
            signal: Trading signal
            current_price: Current stock price

        Returns:
            Tuple of (shares, total_cost)
        """
        if self.position_size_strategy == "equal_weight":
            target_value = self.position_size_amount
        else:
            # Default to equal weight if strategy not recognized
            target_value = self.position_size_amount

        shares = int(target_value / current_price)
        total_cost = shares * current_price

        logger.debug(
            f"Position size calculation for {signal.ticker}: "
            f"target=${target_value}, price=${current_price}, shares={shares}, cost=${total_cost}"
        )

        return shares, total_cost

    def open_position(
        self,
        signal: Signal,
        entry_date: datetime,
        entry_price: float,
        closed_trade: ClosedTrade,
    ) -> Position | None:
        """
        Open a new position with associated ClosedTrade for pre-calculated exit data.

        Args:
            signal: Trading signal triggering the position
            entry_date: Date of position entry
            entry_price: Price at entry
            closed_trade: Complete trade data including pre-calculated exit

        Returns:
            New Position object if successful, None if insufficient cash
        """
        shares, total_cost = self.calculate_position_size(signal, entry_price)

        if not self.can_open_new_position(total_cost):
            logger.warning(
                f"Insufficient cash to open position in {signal.ticker}: "
                f"required=${total_cost}, available=${self.state.cash - self.min_cash_reserve}"
            )
            return None

        if shares <= 0:
            logger.warning(f"Invalid share count for {signal.ticker}: {shares}")
            return None

        # Create new position with ClosedTrade reference
        position = Position(
            ticker=signal.ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
            entry_signal_ranking=signal.ranking,
            closed_trade=closed_trade,
            current_price=entry_price,
            current_value=total_cost,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
        )

        # Update portfolio state
        self.state.positions[signal.ticker] = position
        self.state.cash -= total_cost
        self.state.update_total_value()

        logger.info(
            f"Opened position with scheduled exit: {signal.ticker} x{shares} @ ${entry_price:.2f} "
            f"(total: ${total_cost:.2f}, exit scheduled: {closed_trade.exit.date.date()}, remaining cash: ${self.state.cash:.2f})"
        )

        return position

    def close_position(
        self,
        ticker: str,
        exit_date: datetime,
        exit_price: float,
        exit_reason: str,
    ) -> ClosedPosition | None:
        """
        Close an existing position.

        Args:
            ticker: Stock ticker to close
            exit_date: Date of position closure
            exit_price: Price at exit
            exit_reason: Reason for closure

        Returns:
            ClosedPosition object if successful, None if position doesn't exist
        """
        if ticker not in self.state.positions:
            logger.warning(f"Cannot close position - {ticker} not found in portfolio")
            return None

        position = self.state.positions[ticker]
        exit_value = position.shares * exit_price

        # Calculate realized P&L
        realized_pnl = exit_value - (position.shares * position.entry_price)
        realized_pnl_pct = (realized_pnl / (position.shares * position.entry_price)) * 100.0

        # Calculate holding period
        holding_period_days = (exit_date - position.entry_date).days

        # Create closed position record
        closed_position = ClosedPosition(
            ticker=ticker,
            entry_date=position.entry_date,
            exit_date=exit_date,
            entry_price=position.entry_price,
            exit_price=exit_price,
            shares=position.shares,
            entry_signal_ranking=position.entry_signal_ranking,
            exit_reason=exit_reason,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            holding_period_days=holding_period_days,
        )

        # Update portfolio state
        self.state.cash += exit_value
        del self.state.positions[ticker]
        self.state.closed_positions.append(closed_position)
        self.state.update_total_value()

        logger.info(
            f"Closed position: {ticker} x{position.shares} @ ${exit_price:.2f} "
            f"(P&L: ${realized_pnl:.2f} / {realized_pnl_pct:.2f}%, "
            f"held {holding_period_days} days, reason: {exit_reason})"
        )

        return closed_position

    def close_position_with_trade_data(
        self,
        ticker: str,
        exit_date: datetime,
        exit_price: float,
        exit_reason: str,
    ) -> ClosedPosition | None:
        """
        Close an existing position using pre-calculated trade data (optimization path).

        Args:
            ticker: Stock ticker to close
            exit_date: Date of position closure
            exit_price: Price at exit
            exit_reason: Reason for closure

        Returns:
            ClosedPosition object if successful, None if position doesn't exist
        """
        if ticker not in self.state.positions:
            logger.warning(f"Cannot close position - {ticker} not found in portfolio")
            return None

        position = self.state.positions[ticker]
        exit_value = position.shares * exit_price

        # Calculate realized P&L
        realized_pnl = exit_value - (position.shares * position.entry_price)
        realized_pnl_pct = (realized_pnl / (position.shares * position.entry_price)) * 100.0

        # Calculate holding period
        holding_period_days = (exit_date - position.entry_date).days

        # Create closed position record
        closed_position = ClosedPosition(
            ticker=ticker,
            entry_date=position.entry_date,
            exit_date=exit_date,
            entry_price=position.entry_price,
            exit_price=exit_price,
            shares=position.shares,
            entry_signal_ranking=position.entry_signal_ranking,
            exit_reason=exit_reason,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            holding_period_days=holding_period_days,
        )

        # Update portfolio state
        self.state.cash += exit_value
        del self.state.positions[ticker]
        self.state.closed_positions.append(closed_position)
        self.state.update_total_value()

        logger.info(
            f"Closed scheduled position: {ticker} x{position.shares} @ ${exit_price:.2f} "
            f"(P&L: ${realized_pnl:.2f} / {realized_pnl_pct:.2f}%, "
            f"held {holding_period_days} days, reason: {exit_reason})"
        )

        return closed_position

    def update_position_prices(self, price_data: dict[str, float], current_date: datetime) -> None:
        """
        Update current prices for all open positions.

        Args:
            price_data: Dictionary mapping ticker to current price
            current_date: Current date for price update
        """
        updated_count = 0

        for ticker, position in self.state.positions.items():
            if ticker in price_data:
                position.update_current_price(price_data[ticker])
                updated_count += 1

        if updated_count > 0:
            self.state.update_total_value()
            logger.debug(f"Updated prices for {updated_count} positions on {current_date}")

    def record_daily_snapshot(self, current_date: datetime) -> DailyPortfolioSnapshot:
        """
        Record daily portfolio snapshot for performance tracking.

        Args:
            current_date: Date of snapshot

        Returns:
            DailyPortfolioSnapshot object
        """
        # Calculate daily return
        daily_return = 0.0
        daily_pnl = 0.0

        if self.state.daily_snapshots:
            previous_value = self.state.daily_snapshots[-1].total_value
            daily_pnl = self.state.total_value - previous_value
            daily_return = (daily_pnl / previous_value) * 100.0

        snapshot = DailyPortfolioSnapshot(
            date=current_date,
            total_value=self.state.total_value,
            cash=self.state.cash,
            positions_value=self.state.positions_value,
            positions_count=self.state.positions_count,
            daily_return=daily_return,
            daily_pnl=daily_pnl,
        )

        self.state.daily_snapshots.append(snapshot)
        self.state.last_update_date = current_date

        return snapshot

    def get_available_position_slots(self, max_positions: int) -> int:
        """
        Get number of available slots for new positions.

        Args:
            max_positions: Maximum allowed positions

        Returns:
            Number of available position slots
        """
        return max(0, max_positions - self.state.positions_count)

    def get_position_summary(self) -> dict[str, float]:
        """
        Get summary statistics of current portfolio state.

        Returns:
            Dictionary with portfolio summary metrics
        """
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.state.positions.values())
        total_cost_basis = sum(pos.shares * pos.entry_price for pos in self.state.positions.values())

        avg_unrealized_pnl_pct = 0.0
        if self.state.positions_count > 0:
            avg_unrealized_pnl_pct = sum(pos.unrealized_pnl_pct for pos in self.state.positions.values()) / self.state.positions_count

        return {
            "total_value": self.state.total_value,
            "cash": self.state.cash,
            "positions_value": self.state.positions_value,
            "positions_count": self.state.positions_count,
            "total_unrealized_pnl": total_unrealized_pnl,
            "avg_unrealized_pnl_pct": avg_unrealized_pnl_pct,
            "total_cost_basis": total_cost_basis,
            "cash_utilization_pct": ((self.initial_capital - self.state.cash) / self.initial_capital) * 100.0,
        }
