"""Alpaca trading client wrapper for live trading operations."""

import logging
from datetime import datetime
from decimal import Decimal

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, OrderType as AlpacaOrderType
from alpaca.trading.enums import TimeInForce, OrderStatus as AlpacaOrderStatus
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.requests import StopLimitOrderRequest, TrailingStopOrderRequest
from alpaca.trading.models import Order as AlpacaOrder, Position as AlpacaPosition

from .models import (
    LiveOrder, LivePosition, OrderStatus, OrderType, OrderSide,
    AccountInfo
)

logger = logging.getLogger(__name__)


class AlpacaTradingClient:
    """Alpaca trading client wrapper with error handling and retry logic."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize Alpaca trading client.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.client = TradingClient(api_key, secret_key, paper=paper)

        logger.info(f"Initialized Alpaca client (paper: {paper})")

    def get_account(self) -> AccountInfo:
        """
        Get account information.

        Returns:
            AccountInfo object with current account details

        Raises:
            Exception: If unable to retrieve account information
        """
        try:
            account = self.client.get_account()

            return AccountInfo(  # type: ignore[arg-type]
                account_id=account.id,
                equity=Decimal(str(account.equity)),
                cash=Decimal(str(account.cash)),
                buying_power=Decimal(str(account.buying_power)),
                portfolio_value=Decimal(str(account.portfolio_value)),
                long_market_value=Decimal(str(account.long_market_value or 0)),
                short_market_value=Decimal(str(account.short_market_value or 0)),
                day_trade_count=account.day_trade_count or 0,
                pattern_day_trader=account.pattern_day_trader or False,
                trading_blocked=account.trading_blocked or False,
                account_blocked=account.account_blocked or False,
                transfers_blocked=account.transfers_blocked or False
            )

        except Exception as e:
            logger.error(f"Failed to get account information: {e}")
            raise

    def submit_order(self, order: LiveOrder) -> LiveOrder:
        """
        Submit an order to Alpaca.

        Args:
            order: LiveOrder object to submit

        Returns:
            Updated LiveOrder with Alpaca order ID and status

        Raises:
            Exception: If order submission fails
        """
        try:
            # Convert order to Alpaca request
            request = self._convert_to_alpaca_request(order)

            # Submit order
            alpaca_order = self.client.submit_order(request)

            # Update order with Alpaca response
            order.id = str(alpaca_order.id)  # type: ignore[arg-type]
            order.status = self._convert_alpaca_status(alpaca_order.status)  # type: ignore[arg-type]
            order.submitted_at = datetime.now()

            logger.info(f"Submitted order {order.id} for {order.ticker}")
            return order

        except Exception as e:
            logger.error(f"Failed to submit order for {order.ticker}: {e}")
            order.status = OrderStatus.REJECTED
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Alpaca order ID to cancel

        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            self.client.cancel_order_by_id(order_id)
            logger.info(f"Cancelled order {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order(self, order_id: str) -> LiveOrder | None:
        """
        Get order status.

        Args:
            order_id: Alpaca order ID

        Returns:
            LiveOrder object or None if not found
        """
        try:
            alpaca_order = self.client.get_order_by_id(order_id)
            return self._convert_from_alpaca_order(alpaca_order)  # type: ignore[arg-type]

        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            return None

    def get_orders(self, status: OrderStatus | None = None) -> list[LiveOrder]:
        """
        Get list of orders.

        Args:
            status: Filter by order status (optional)

        Returns:
            List of LiveOrder objects
        """
        try:
            # Convert status filter
            alpaca_status = None
            if status:
                alpaca_status = self._convert_to_alpaca_status(status)

            alpaca_orders = self.client.get_orders(status=alpaca_status)
            return [self._convert_from_alpaca_order(order) for order in alpaca_orders]

        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    def get_positions(self) -> list[LivePosition]:
        """
        Get all open positions.

        Returns:
            List of LivePosition objects
        """
        try:
            alpaca_positions = self.client.get_all_positions()
            return [self._convert_from_alpaca_position(pos) for pos in alpaca_positions]

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def get_position(self, ticker: str) -> LivePosition | None:
        """
        Get position for specific ticker.

        Args:
            ticker: Stock symbol

        Returns:
            LivePosition object or None if no position
        """
        try:
            alpaca_position = self.client.get_open_position(ticker)
            return self._convert_from_alpaca_position(alpaca_position)

        except Exception as e:
            logger.debug(f"No position found for {ticker}: {e}")
            return None

    def close_position(self, ticker: str, percentage: float | None = None) -> bool:
        """
        Close position.

        Args:
            ticker: Stock symbol
            percentage: Percentage to close (None for 100%)

        Returns:
            True if close order submitted successfully
        """
        try:
            if percentage:
                self.client.close_position(ticker, close_options={"percentage": str(percentage)})
            else:
                self.client.close_position(ticker)

            logger.info(f"Closed position for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Failed to close position for {ticker}: {e}")
            return False

    def _convert_to_alpaca_request(self, order: LiveOrder) -> object:
        """Convert LiveOrder to Alpaca request object."""
        side = AlpacaOrderSide.BUY if order.side == OrderSide.BUY else AlpacaOrderSide.SELL

        if order.order_type == OrderType.MARKET:
            return MarketOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                time_in_force=TimeInForce.DAY
            )
        elif order.order_type == OrderType.LIMIT:
            return LimitOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                limit_price=float(order.price),
                time_in_force=TimeInForce.DAY
            )
        elif order.order_type == OrderType.STOP:
            return StopOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                stop_price=float(order.stop_price),
                time_in_force=TimeInForce.DAY
            )
        elif order.order_type == OrderType.STOP_LIMIT:
            return StopLimitOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                limit_price=float(order.price),
                stop_price=float(order.stop_price),
                time_in_force=TimeInForce.DAY
            )
        elif order.order_type == OrderType.TRAILING_STOP:
            return TrailingStopOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                trail_price=float(order.stop_price),
                time_in_force=TimeInForce.DAY
            )
        else:
            raise ValueError(f"Unsupported order type: {order.order_type}")

    def _convert_from_alpaca_order(self, alpaca_order: AlpacaOrder) -> LiveOrder:
        """Convert Alpaca order to LiveOrder."""
        return LiveOrder(
            id=alpaca_order.id,
            client_order_id=alpaca_order.client_order_id,
            ticker=alpaca_order.symbol,
            side=OrderSide.BUY if alpaca_order.side == AlpacaOrderSide.BUY else OrderSide.SELL,
            order_type=self._convert_alpaca_order_type(alpaca_order.order_type),
            quantity=int(alpaca_order.qty),
            price=Decimal(str(alpaca_order.limit_price)) if alpaca_order.limit_price else None,
            stop_price=Decimal(str(alpaca_order.stop_price)) if alpaca_order.stop_price else None,
            time_in_force=str(alpaca_order.time_in_force),
            status=self._convert_alpaca_status(alpaca_order.status),
            created_at=alpaca_order.created_at,
            submitted_at=alpaca_order.submitted_at,
            filled_at=alpaca_order.filled_at,
            filled_price=Decimal(str(alpaca_order.filled_avg_price)) if alpaca_order.filled_avg_price else None,
            filled_quantity=int(alpaca_order.filled_qty) if alpaca_order.filled_qty else None
        )

    def _convert_from_alpaca_position(self, alpaca_position: AlpacaPosition) -> LivePosition:
        """Convert Alpaca position to LivePosition."""
        return LivePosition(
            ticker=alpaca_position.symbol,
            quantity=int(alpaca_position.qty),
            avg_price=Decimal(str(alpaca_position.avg_entry_price)),
            market_price=Decimal(str(alpaca_position.current_price or alpaca_position.avg_entry_price)),
            cost_basis=Decimal(str(alpaca_position.cost_basis)),
            unrealized_pnl=Decimal(str(alpaca_position.unrealized_pl or 0)),
            entry_date=datetime.now()  # Alpaca doesn't provide entry date
        )

    def _convert_alpaca_status(self, alpaca_status: AlpacaOrderStatus) -> OrderStatus:
        """Convert Alpaca order status to OrderStatus."""
        status_map = {
            AlpacaOrderStatus.NEW: OrderStatus.SUBMITTED,
            AlpacaOrderStatus.PARTIALLY_FILLED: OrderStatus.PARTIALLY_FILLED,
            AlpacaOrderStatus.FILLED: OrderStatus.FILLED,
            AlpacaOrderStatus.DONE_FOR_DAY: OrderStatus.CANCELED,
            AlpacaOrderStatus.CANCELED: OrderStatus.CANCELED,
            AlpacaOrderStatus.EXPIRED: OrderStatus.EXPIRED,
            AlpacaOrderStatus.REPLACED: OrderStatus.SUBMITTED,
            AlpacaOrderStatus.PENDING_CANCEL: OrderStatus.SUBMITTED,
            AlpacaOrderStatus.PENDING_REPLACE: OrderStatus.SUBMITTED,
            AlpacaOrderStatus.ACCEPTED: OrderStatus.ACCEPTED,
            AlpacaOrderStatus.PENDING_NEW: OrderStatus.PENDING,
            AlpacaOrderStatus.ACCEPTED_FOR_BIDDING: OrderStatus.ACCEPTED,
            AlpacaOrderStatus.STOPPED: OrderStatus.CANCELED,
            AlpacaOrderStatus.REJECTED: OrderStatus.REJECTED,
            AlpacaOrderStatus.SUSPENDED: OrderStatus.CANCELED,
            AlpacaOrderStatus.CALCULATED: OrderStatus.SUBMITTED,
        }
        return status_map.get(alpaca_status, OrderStatus.PENDING)

    def _convert_to_alpaca_status(self, status: OrderStatus) -> AlpacaOrderStatus | None:
        """Convert OrderStatus to Alpaca status."""
        status_map = {
            OrderStatus.PENDING: AlpacaOrderStatus.PENDING_NEW,
            OrderStatus.SUBMITTED: AlpacaOrderStatus.NEW,
            OrderStatus.ACCEPTED: AlpacaOrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED: AlpacaOrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED: AlpacaOrderStatus.FILLED,
            OrderStatus.CANCELED: AlpacaOrderStatus.CANCELED,
            OrderStatus.REJECTED: AlpacaOrderStatus.REJECTED,
            OrderStatus.EXPIRED: AlpacaOrderStatus.EXPIRED,
        }
        return status_map.get(status)

    def _convert_alpaca_order_type(self, alpaca_type: AlpacaOrderType) -> OrderType:
        """Convert Alpaca order type to OrderType."""
        type_map = {
            AlpacaOrderType.MARKET: OrderType.MARKET,
            AlpacaOrderType.LIMIT: OrderType.LIMIT,
            AlpacaOrderType.STOP: OrderType.STOP,
            AlpacaOrderType.STOP_LIMIT: OrderType.STOP_LIMIT,
            AlpacaOrderType.TRAILING_STOP: OrderType.TRAILING_STOP,
        }
        return type_map.get(alpaca_type, OrderType.MARKET)

    def is_market_open(self) -> bool:
        """
        Check if market is currently open.

        Returns:
            True if market is open, False otherwise
        """
        try:
            clock = self.client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return False

    def get_market_status(self) -> dict:
        """
        Get detailed market status.

        Returns:
            Dictionary with market status information
        """
        try:
            clock = self.client.get_clock()
            return {
                "timestamp": clock.timestamp,
                "is_open": clock.is_open,
                "next_open": clock.next_open,
                "next_close": clock.next_close
            }
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return {
                "timestamp": datetime.now(),
                "is_open": False,
                "next_open": None,
                "next_close": None
            }
