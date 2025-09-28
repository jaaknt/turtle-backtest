"""Position tracking and P&L monitoring for live trading."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .client import AlpacaTradingClient
from .models import LivePosition, OrderSide, ExecutionReport, TradingSession
from .trade_logger import TradeLogger

logger = logging.getLogger(__name__)


class PositionTracker:
    """Tracks positions and calculates real-time P&L."""

    def __init__(
        self,
        trading_client: AlpacaTradingClient,
        trade_logger: TradeLogger,
        session: TradingSession
    ):
        """
        Initialize position tracker.

        Args:
            trading_client: Alpaca trading client
            trade_logger: Trade logging service
            session: Current trading session
        """
        self.trading_client = trading_client
        self.trade_logger = trade_logger
        self.session = session
        self.positions: dict[str, LivePosition] = {}
        self.last_update = datetime.now()

    def update_positions(self) -> list[LivePosition]:
        """
        Update all positions from Alpaca.

        Returns:
            List of updated positions
        """
        try:
            # Get current positions from Alpaca
            alpaca_positions = self.trading_client.get_positions()

            # Update local tracking
            updated_positions = []
            for position in alpaca_positions:
                if position.quantity != 0:  # Only track non-zero positions
                    self.positions[position.ticker] = position
                    updated_positions.append(position)

                    # Log position update
                    self.trade_logger.log_position_event(
                        position,
                        f"Position updated: {position.quantity} shares @ ${position.market_price}"
                    )
                elif position.ticker in self.positions:
                    # Position was closed
                    del self.positions[position.ticker]
                    self.trade_logger.log_position_event(
                        position,
                        "Position closed"
                    )

            self.last_update = datetime.now()
            logger.info(f"Updated {len(updated_positions)} positions")
            return updated_positions

        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            return []

    def get_position(self, ticker: str) -> LivePosition | None:
        """
        Get position for specific ticker.

        Args:
            ticker: Stock symbol

        Returns:
            LivePosition object or None if no position
        """
        return self.positions.get(ticker)

    def get_all_positions(self) -> list[LivePosition]:
        """
        Get all current positions.

        Returns:
            List of all LivePosition objects
        """
        return list(self.positions.values())

    def calculate_total_pnl(self) -> Decimal:
        """
        Calculate total unrealized P&L across all positions.

        Returns:
            Total unrealized P&L
        """
        total_pnl = Decimal(0)

        for position in self.positions.values():
            total_pnl += position.unrealized_pnl

        return total_pnl

    def calculate_total_market_value(self) -> Decimal:
        """
        Calculate total market value of all positions.

        Returns:
            Total market value
        """
        total_value = Decimal(0)

        for position in self.positions.values():
            total_value += position.market_value

        return total_value

    def process_execution(self, execution: ExecutionReport) -> None:
        """
        Process trade execution and update positions.

        Args:
            execution: Execution report to process
        """
        try:
            ticker = execution.ticker

            # Get current position or create new one
            current_position = self.positions.get(ticker)

            if current_position is None:
                # New position
                if execution.side == OrderSide.BUY:
                    new_position = LivePosition(
                        ticker=ticker,
                        quantity=execution.quantity,
                        avg_price=execution.price,
                        market_price=execution.price,
                        cost_basis=execution.execution_value,
                        entry_date=execution.timestamp
                    )
                    self.positions[ticker] = new_position

                    logger.info(f"New long position: {ticker} {execution.quantity} shares @ ${execution.price}")

                else:  # Short position
                    new_position = LivePosition(
                        ticker=ticker,
                        quantity=-execution.quantity,
                        avg_price=execution.price,
                        market_price=execution.price,
                        cost_basis=-execution.execution_value,
                        entry_date=execution.timestamp
                    )
                    self.positions[ticker] = new_position

                    logger.info(f"New short position: {ticker} {execution.quantity} shares @ ${execution.price}")

                # Log new position
                self.trade_logger.log_position_event(
                    new_position,
                    f"Position opened: {execution.side.value} {execution.quantity} shares @ ${execution.price}"
                )

            else:
                # Update existing position
                self._update_existing_position(current_position, execution)

        except Exception as e:
            logger.error(f"Error processing execution: {e}")

    def _update_existing_position(self, position: LivePosition, execution: ExecutionReport) -> None:
        """
        Update existing position with new execution.

        Args:
            position: Current position
            execution: New execution to process
        """
        old_quantity = position.quantity
        old_cost_basis = position.cost_basis

        if execution.side == OrderSide.BUY:
            if position.quantity >= 0:
                # Adding to long position
                new_quantity = position.quantity + execution.quantity
                new_cost_basis = position.cost_basis + execution.execution_value
                position.avg_price = new_cost_basis / Decimal(new_quantity)

            else:
                # Covering short position
                new_quantity = position.quantity + execution.quantity
                if new_quantity == 0:
                    # Position closed
                    self._close_position(position, execution)
                    return
                elif new_quantity > 0:
                    # Short became long
                    position.avg_price = execution.price
                    new_cost_basis = execution.execution_value
                else:
                    # Still short, reduce size
                    new_cost_basis = position.cost_basis * (new_quantity / position.quantity)

        else:  # SELL
            if position.quantity > 0:
                # Reducing long position
                new_quantity = position.quantity - execution.quantity
                if new_quantity == 0:
                    # Position closed
                    self._close_position(position, execution)
                    return
                elif new_quantity < 0:
                    # Long became short
                    position.avg_price = execution.price
                    new_cost_basis = -execution.execution_value
                else:
                    # Still long, reduce size
                    new_cost_basis = position.cost_basis * (new_quantity / position.quantity)

            else:
                # Adding to short position
                new_quantity = position.quantity - execution.quantity
                new_cost_basis = position.cost_basis - execution.execution_value
                position.avg_price = abs(new_cost_basis) / Decimal(abs(new_quantity))

        # Update position
        position.quantity = new_quantity
        position.cost_basis = new_cost_basis

        # Log position update
        self.trade_logger.log_position_event(
            position,
            f"Position updated: {old_quantity} → {new_quantity} shares, cost basis: ${old_cost_basis} → ${new_cost_basis}"
        )

        logger.info(f"Updated position {position.ticker}: {old_quantity} → {new_quantity} shares")

    def _close_position(self, position: LivePosition, execution: ExecutionReport) -> None:
        """
        Close a position and calculate realized P&L.

        Args:
            position: Position being closed
            execution: Closing execution
        """
        # Calculate realized P&L
        if position.quantity > 0:
            # Closing long position
            realized_pnl = execution.execution_value - position.cost_basis
        else:
            # Closing short position
            realized_pnl = position.cost_basis - execution.execution_value

        # Update session statistics
        self.session.total_trades += 1
        self.session.total_pnl += realized_pnl

        if realized_pnl > 0:
            self.session.winning_trades += 1
        else:
            self.session.losing_trades += 1

        # Log position closure
        self.trade_logger.log_position_event(
            position,
            f"Position closed: realized P&L ${realized_pnl}, total trades: {self.session.total_trades}"
        )

        # Remove from tracking
        del self.positions[position.ticker]

        logger.info(f"Closed position {position.ticker}: realized P&L ${realized_pnl}")

    def update_market_prices(self) -> None:
        """Update market prices for all positions."""
        try:
            for ticker in self.positions.keys():
                # Get current market price from Alpaca
                alpaca_position = self.trading_client.get_position(ticker)

                if alpaca_position:
                    old_position = self.positions[ticker]
                    old_position.market_price = alpaca_position.market_price
                    old_position.unrealized_pnl = alpaca_position.unrealized_pnl

                    # Log price update
                    self.trade_logger.log_position_event(
                        old_position,
                        f"Market price updated: ${old_position.market_price}, unrealized P&L: ${old_position.unrealized_pnl}"
                    )

            logger.debug(f"Updated market prices for {len(self.positions)} positions")

        except Exception as e:
            logger.error(f"Error updating market prices: {e}")

    def get_position_summary(self) -> dict:
        """
        Get summary of all positions.

        Returns:
            Dictionary with position summary statistics
        """
        if not self.positions:
            return {
                "total_positions": 0,
                "total_market_value": Decimal(0),
                "total_cost_basis": Decimal(0),
                "total_unrealized_pnl": Decimal(0),
                "total_unrealized_pnl_percentage": 0.0,
                "long_positions": 0,
                "short_positions": 0
            }

        total_market_value = Decimal(0)
        total_cost_basis = Decimal(0)
        total_unrealized_pnl = Decimal(0)
        long_positions = 0
        short_positions = 0

        for position in self.positions.values():
            total_market_value += position.market_value
            total_cost_basis += abs(position.cost_basis)
            total_unrealized_pnl += position.unrealized_pnl

            if position.is_long:
                long_positions += 1
            else:
                short_positions += 1

        unrealized_pnl_percentage = 0.0
        if total_cost_basis > 0:
            unrealized_pnl_percentage = float(total_unrealized_pnl / total_cost_basis * 100)

        return {
            "total_positions": len(self.positions),
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_unrealized_pnl_percentage": unrealized_pnl_percentage,
            "long_positions": long_positions,
            "short_positions": short_positions
        }

    def get_positions_at_risk(self, risk_threshold: float = 0.05) -> list[LivePosition]:
        """
        Get positions that exceed risk threshold.

        Args:
            risk_threshold: Risk threshold as percentage (0.05 = 5%)

        Returns:
            List of positions at risk
        """
        at_risk_positions = []

        for position in self.positions.values():
            pnl_percentage = abs(position.pnl_percentage) / 100.0

            if pnl_percentage >= risk_threshold:
                at_risk_positions.append(position)

        return at_risk_positions

    def cleanup_stale_positions(self, hours_old: int = 24) -> int:
        """
        Remove positions that haven't been updated recently.

        Args:
            hours_old: Remove positions not updated in this many hours

        Returns:
            Number of positions removed
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        removed_count = 0

        # Only remove if we haven't updated recently
        if self.last_update < cutoff_time:
            # Force update to get current state
            self.update_positions()
            removed_count = 1  # Indicate we refreshed

        return removed_count
