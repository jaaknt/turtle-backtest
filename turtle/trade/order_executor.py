"""Order execution and management for live trading."""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal

from .client import AlpacaTradingClient
from .models import LiveOrder, OrderStatus, OrderType, OrderSide, ExecutionReport
from .trade_logger import TradeLogger

logger = logging.getLogger(__name__)


class OrderExecutor:
    """Handles order execution, monitoring, and lifecycle management."""

    def __init__(
        self,
        trading_client: AlpacaTradingClient,
        trade_logger: TradeLogger,
        max_retry_attempts: int = 3,
        retry_delay_seconds: int = 5
    ):
        """
        Initialize order executor.

        Args:
            trading_client: Alpaca trading client
            trade_logger: Trade logging service
            max_retry_attempts: Maximum retry attempts for failed orders
            retry_delay_seconds: Delay between retry attempts
        """
        self.trading_client = trading_client
        self.trade_logger = trade_logger
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.active_orders: dict[str, LiveOrder] = {}

    def submit_market_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        signal_id: str | None = None
    ) -> LiveOrder | None:
        """
        Submit a market order.

        Args:
            ticker: Stock symbol
            side: Buy or sell
            quantity: Number of shares
            signal_id: Associated signal ID for tracking

        Returns:
            LiveOrder object if successful, None otherwise
        """
        order = LiveOrder(
            ticker=ticker,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            signal_id=signal_id
        )

        return self._submit_order_with_retry(order)

    def submit_limit_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        limit_price: Decimal,
        signal_id: str | None = None
    ) -> LiveOrder | None:
        """
        Submit a limit order.

        Args:
            ticker: Stock symbol
            side: Buy or sell
            quantity: Number of shares
            limit_price: Limit price
            signal_id: Associated signal ID for tracking

        Returns:
            LiveOrder object if successful, None otherwise
        """
        order = LiveOrder(
            ticker=ticker,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=limit_price,
            signal_id=signal_id
        )

        return self._submit_order_with_retry(order)

    def submit_stop_loss_order(
        self,
        ticker: str,
        quantity: int,
        stop_price: Decimal,
        signal_id: str | None = None
    ) -> LiveOrder | None:
        """
        Submit a stop loss order (always sell).

        Args:
            ticker: Stock symbol
            quantity: Number of shares to sell
            stop_price: Stop price
            signal_id: Associated signal ID for tracking

        Returns:
            LiveOrder object if successful, None otherwise
        """
        order = LiveOrder(
            ticker=ticker,
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=quantity,
            stop_price=stop_price,
            signal_id=signal_id
        )

        return self._submit_order_with_retry(order)

    def submit_stop_limit_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        stop_price: Decimal,
        limit_price: Decimal,
        signal_id: str | None = None
    ) -> LiveOrder | None:
        """
        Submit a stop limit order.

        Args:
            ticker: Stock symbol
            side: Buy or sell
            quantity: Number of shares
            stop_price: Stop price
            limit_price: Limit price
            signal_id: Associated signal ID for tracking

        Returns:
            LiveOrder object if successful, None otherwise
        """
        order = LiveOrder(
            ticker=ticker,
            side=side,
            order_type=OrderType.STOP_LIMIT,
            quantity=quantity,
            price=limit_price,
            stop_price=stop_price,
            signal_id=signal_id
        )

        return self._submit_order_with_retry(order)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        try:
            success = self.trading_client.cancel_order(order_id)

            if success:
                # Update local order tracking
                if order_id in self.active_orders:
                    self.active_orders[order_id].status = OrderStatus.CANCELED
                    self.trade_logger.log_order_event(
                        self.active_orders[order_id],
                        "Order cancelled"
                    )

                logger.info(f"Successfully cancelled order {order_id}")
                return True
            else:
                logger.warning(f"Failed to cancel order {order_id}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def update_order_status(self, order_id: str) -> LiveOrder | None:
        """
        Update order status from Alpaca.

        Args:
            order_id: Order ID to update

        Returns:
            Updated LiveOrder object or None if not found
        """
        try:
            updated_order = self.trading_client.get_order(order_id)

            if updated_order:
                # Update local tracking
                self.active_orders[order_id] = updated_order

                # Log status changes
                self.trade_logger.log_order_event(
                    updated_order,
                    f"Status updated to {updated_order.status}"
                )

                return updated_order
            else:
                logger.warning(f"Order {order_id} not found")
                return None

        except Exception as e:
            logger.error(f"Error updating order status {order_id}: {e}")
            return None

    def monitor_orders(self) -> list[LiveOrder]:
        """
        Monitor all active orders and update their status.

        Returns:
            List of orders with updated status
        """
        updated_orders = []

        for order_id in list(self.active_orders.keys()):
            order = self.active_orders[order_id]

            # Skip orders already in terminal state
            if order.is_complete:
                continue

            # Update status
            updated_order = self.update_order_status(order_id)
            if updated_order:
                updated_orders.append(updated_order)

                # Remove from active tracking if complete
                if updated_order.is_complete:
                    self._handle_order_completion(updated_order)

        return updated_orders

    def get_active_orders(self, ticker: str | None = None) -> list[LiveOrder]:
        """
        Get list of active orders.

        Args:
            ticker: Filter by ticker (optional)

        Returns:
            List of active LiveOrder objects
        """
        orders = [order for order in self.active_orders.values() if not order.is_complete]

        if ticker:
            orders = [order for order in orders if order.ticker == ticker]

        return orders

    def get_pending_orders_value(self, side: OrderSide) -> Decimal:
        """
        Calculate total value of pending orders.

        Args:
            side: Order side (buy/sell)

        Returns:
            Total pending order value
        """
        total_value = Decimal(0)

        for order in self.active_orders.values():
            if order.side == side and not order.is_complete:
                if order.order_type == OrderType.MARKET:
                    # Estimate market order value (we don't know exact price)
                    # This is conservative estimation
                    estimated_price = order.filled_price or Decimal(100)  # Default estimate
                    total_value += estimated_price * Decimal(order.quantity)
                elif order.price:
                    total_value += order.price * Decimal(order.quantity)

        return total_value

    def _submit_order_with_retry(self, order: LiveOrder) -> LiveOrder | None:
        """
        Submit order with retry logic.

        Args:
            order: Order to submit

        Returns:
            LiveOrder object if successful, None otherwise
        """
        for attempt in range(self.max_retry_attempts):
            try:
                # Submit order
                submitted_order = self.trading_client.submit_order(order)

                # Track order
                if submitted_order.id:
                    self.active_orders[submitted_order.id] = submitted_order

                # Log submission
                self.trade_logger.log_order_event(
                    submitted_order,
                    f"Order submitted (attempt {attempt + 1})"
                )

                logger.info(f"Successfully submitted order for {order.ticker}")
                return submitted_order

            except Exception as e:
                logger.error(f"Order submission attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retry_attempts - 1:
                    logger.info(f"Retrying in {self.retry_delay_seconds} seconds...")
                    time.sleep(self.retry_delay_seconds)
                else:
                    logger.error(f"All retry attempts failed for {order.ticker} order")

                    # Log failure
                    order.status = OrderStatus.REJECTED
                    self.trade_logger.log_order_event(
                        order,
                        f"Order submission failed after {self.max_retry_attempts} attempts: {e}"
                    )

        return None

    def _handle_order_completion(self, order: LiveOrder) -> None:
        """
        Handle order completion (filled, cancelled, etc.).

        Args:
            order: Completed order
        """
        try:
            if order.is_filled:
                logger.info(f"Order {order.id} filled: {order.filled_quantity} shares at ${order.filled_price}")

                # Create execution report
                if order.filled_price and order.filled_quantity:
                    execution_report = ExecutionReport(
                        order_id=order.id or "",
                        execution_id=f"{order.id}_exec_{int(time.time())}",
                        ticker=order.ticker,
                        side=order.side,
                        quantity=order.filled_quantity,
                        price=order.filled_price,
                        timestamp=order.filled_at or datetime.now(),
                        commission=order.commission or Decimal(0)
                    )

                    # Log execution
                    self.trade_logger.log_execution(execution_report)

            else:
                logger.info(f"Order {order.id} completed with status: {order.status}")

            # Log completion
            self.trade_logger.log_order_event(
                order,
                f"Order completed with status: {order.status}"
            )

        except Exception as e:
            logger.error(f"Error handling order completion: {e}")

    def cleanup_completed_orders(self, hours_old: int = 24) -> int:
        """
        Remove completed orders older than specified hours.

        Args:
            hours_old: Remove orders completed more than this many hours ago

        Returns:
            Number of orders removed
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        removed_count = 0

        for order_id in list(self.active_orders.keys()):
            order = self.active_orders[order_id]

            if (order.is_complete and
                order.filled_at and
                order.filled_at < cutoff_time):

                del self.active_orders[order_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} completed orders")

        return removed_count

    def get_order_statistics(self) -> dict:
        """
        Get order execution statistics.

        Returns:
            Dictionary with order statistics
        """
        total_orders = len(self.active_orders)
        filled_orders = sum(1 for order in self.active_orders.values() if order.is_filled)
        cancelled_orders = sum(1 for order in self.active_orders.values() if order.status == OrderStatus.CANCELED)
        rejected_orders = sum(1 for order in self.active_orders.values() if order.status == OrderStatus.REJECTED)
        pending_orders = sum(1 for order in self.active_orders.values() if not order.is_complete)

        return {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "rejected_orders": rejected_orders,
            "pending_orders": pending_orders,
            "fill_rate": (filled_orders / total_orders * 100) if total_orders > 0 else 0,
            "rejection_rate": (rejected_orders / total_orders * 100) if total_orders > 0 else 0
        }
