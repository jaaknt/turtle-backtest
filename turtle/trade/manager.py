"""Live trading manager that orchestrates signal-to-execution pipeline."""

import logging
import uuid
from datetime import datetime
from decimal import Decimal

from turtle.signal.models import Signal

from .client import AlpacaTradingClient
from .models import (
    LiveOrder, OrderSide, OrderType, TradingSession, RiskParameters,
    AccountInfo, OrderStatus
)
from .order_executor import OrderExecutor
from .position_tracker import PositionTracker
from .risk_manager import RiskManager
from .trade_logger import TradeLogger

logger = logging.getLogger(__name__)


class LiveTradingManager:
    """Main orchestrator for live trading operations."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        strategy_name: str,
        risk_parameters: RiskParameters,
        db_dsn: str,
        paper_trading: bool = True,
        universe: list[str] | None = None
    ):
        """
        Initialize live trading manager.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            strategy_name: Name of trading strategy
            risk_parameters: Risk management parameters
            db_dsn: Database connection string
            paper_trading: Whether to use paper trading
            universe: List of symbols to trade
        """
        self.strategy_name = strategy_name
        self.paper_trading = paper_trading
        self.universe = universe or []

        # Initialize core components
        self.trading_client = AlpacaTradingClient(api_key, secret_key, paper_trading)
        self.trade_logger = TradeLogger(db_dsn)

        # Create trading session
        self.session = self._create_session()

        # Initialize managers
        self.position_tracker = PositionTracker(
            self.trading_client,
            self.trade_logger,
            self.session
        )

        self.order_executor = OrderExecutor(
            self.trading_client,
            self.trade_logger
        )

        self.risk_manager = RiskManager(
            risk_parameters,
            self.position_tracker,
            self.order_executor,
            self.trade_logger,
            self.session
        )

        # Track session state
        self.is_running = False
        self.last_update = datetime.now()

        logger.info(f"Live trading manager initialized: {strategy_name} (paper: {paper_trading})")

    def start_session(self) -> bool:
        """
        Start live trading session.

        Returns:
            True if session started successfully
        """
        try:
            # Check if market is open
            if not self.trading_client.is_market_open():
                logger.warning("Cannot start session: market is closed")
                return False

            # Get initial account information
            account = self.trading_client.get_account()
            self.session.initial_balance = account.portfolio_value
            self.session.current_balance = account.portfolio_value

            # Log account snapshot
            self.trade_logger.log_account_snapshot(
                account.account_id,
                float(account.equity),
                float(account.cash),
                float(account.buying_power),
                float(account.portfolio_value),
                float(account.long_market_value),
                float(account.short_market_value),
                account.day_trade_count,
                account.pattern_day_trader,
                self.session.id
            )

            # Log session start
            self.trade_logger.log_session_event(
                self.session,
                f"Session started with ${account.portfolio_value} portfolio value"
            )

            self.is_running = True
            logger.info(f"Trading session started: {self.session.id}")
            return True

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return False

    def stop_session(self) -> bool:
        """
        Stop live trading session.

        Returns:
            True if session stopped successfully
        """
        try:
            # Cancel all pending orders
            self._cancel_all_pending_orders()

            # Update session end time
            self.session.end_time = datetime.now()
            self.session.is_active = False

            # Get final account information
            account = self.trading_client.get_account()
            self.session.current_balance = account.portfolio_value

            # Log final account snapshot
            self.trade_logger.log_account_snapshot(
                account.account_id,
                float(account.equity),
                float(account.cash),
                float(account.buying_power),
                float(account.portfolio_value),
                float(account.long_market_value),
                float(account.short_market_value),
                account.day_trade_count,
                account.pattern_day_trader,
                self.session.id
            )

            # Log session end
            self.trade_logger.log_session_event(
                self.session,
                f"Session ended with ${account.portfolio_value} portfolio value, {self.session.total_trades} trades"
            )

            self.is_running = False
            logger.info(f"Trading session stopped: {self.session.id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping session: {e}")
            return False

    def process_signal(self, signal: Signal) -> LiveOrder | None:
        """
        Process trading signal and execute order.

        Args:
            signal: Trading signal to process

        Returns:
            LiveOrder if order was submitted, None otherwise
        """
        try:
            if not self.is_running:
                logger.warning("Cannot process signal: session not running")
                return None

            # Check if signal is for a symbol in our universe
            if self.universe and signal.ticker not in self.universe:
                logger.debug(f"Signal for {signal.ticker} ignored: not in trading universe")
                return None

            # Get current account information
            account = self.trading_client.get_account()

            # Determine order parameters from signal
            order_side = OrderSide.BUY if signal.signal_type == "BUY" else OrderSide.SELL

            # Calculate position size
            position_size = self._calculate_position_size(signal, account)

            if position_size <= 0:
                logger.warning(f"Position size calculation failed for {signal.ticker}")
                return None

            # Create order
            order = LiveOrder(
                ticker=signal.ticker,
                side=order_side,
                order_type=OrderType.MARKET,  # Default to market orders
                quantity=position_size,
                signal_id=signal.id
            )

            # Risk check
            risk_approved, risk_reason = self.risk_manager.check_order_risk(order, account)

            if not risk_approved:
                logger.warning(f"Order rejected by risk manager: {risk_reason}")
                return None

            # Execute order
            submitted_order = self.order_executor.submit_market_order(
                ticker=signal.ticker,
                side=order_side,
                quantity=position_size,
                signal_id=signal.id
            )

            if submitted_order:
                logger.info(f"Signal processed: {signal.ticker} {signal.signal_type} → order {submitted_order.id}")
                return submitted_order
            else:
                logger.error(f"Failed to submit order for signal: {signal.ticker}")
                return None

        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return None

    def update_positions_and_orders(self) -> None:
        """Update positions and monitor orders."""
        try:
            # Update positions
            self.position_tracker.update_positions()

            # Monitor orders
            self.order_executor.monitor_orders()

            # Update market prices
            self.position_tracker.update_market_prices()

            # Monitor for risk events
            self.risk_manager.monitor_positions()

            # Check emergency conditions
            account = self.trading_client.get_account()
            self.risk_manager.check_emergency_conditions(account)

            self.last_update = datetime.now()

        except Exception as e:
            logger.error(f"Error updating positions and orders: {e}")

    def get_portfolio_summary(self) -> dict:
        """
        Get comprehensive portfolio summary.

        Returns:
            Dictionary with portfolio metrics
        """
        try:
            # Get account information
            account = self.trading_client.get_account()

            # Get position summary
            position_summary = self.position_tracker.get_position_summary()

            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()

            # Get order statistics
            order_stats = self.order_executor.get_order_statistics()

            return {
                "session": {
                    "id": self.session.id,
                    "strategy": self.session.strategy_name,
                    "start_time": self.session.start_time,
                    "duration_hours": self.session.duration_hours,
                    "is_running": self.is_running,
                    "paper_trading": self.paper_trading
                },
                "account": {
                    "equity": float(account.equity),
                    "cash": float(account.cash),
                    "buying_power": float(account.buying_power),
                    "portfolio_value": float(account.portfolio_value),
                    "day_trade_count": account.day_trade_count,
                    "pattern_day_trader": account.pattern_day_trader
                },
                "positions": position_summary,
                "orders": order_stats,
                "risk": risk_summary,
                "performance": {
                    "total_trades": self.session.total_trades,
                    "winning_trades": self.session.winning_trades,
                    "losing_trades": self.session.losing_trades,
                    "win_rate": self.session.win_rate,
                    "total_pnl": float(self.session.total_pnl),
                    "max_drawdown": float(self.session.max_drawdown)
                }
            }

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}

    def close_position(self, ticker: str, percentage: float | None = None) -> bool:
        """
        Close position manually.

        Args:
            ticker: Stock symbol
            percentage: Percentage to close (None for 100%)

        Returns:
            True if close order submitted successfully
        """
        try:
            position = self.position_tracker.get_position(ticker)
            if not position:
                logger.warning(f"No position found for {ticker}")
                return False

            # Determine order side
            side = OrderSide.SELL if position.is_long else OrderSide.BUY

            # Calculate quantity
            if percentage:
                quantity = int(abs(position.quantity) * percentage / 100)
            else:
                quantity = abs(position.quantity)

            # Get account for risk check
            account = self.trading_client.get_account()

            # Create closing order
            order = LiveOrder(
                ticker=ticker,
                side=side,
                order_type=OrderType.MARKET,
                quantity=quantity
            )

            # Risk check (should pass for closing orders)
            risk_approved, risk_reason = self.risk_manager.check_order_risk(order, account)

            if not risk_approved:
                logger.warning(f"Close order rejected by risk manager: {risk_reason}")
                return False

            # Submit order
            submitted_order = self.order_executor.submit_market_order(
                ticker=ticker,
                side=side,
                quantity=quantity
            )

            if submitted_order:
                logger.info(f"Position close order submitted: {ticker} {quantity} shares")
                return True
            else:
                logger.error(f"Failed to submit close order for {ticker}")
                return False

        except Exception as e:
            logger.error(f"Error closing position {ticker}: {e}")
            return False

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order manually.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        return self.order_executor.cancel_order(order_id)

    def get_active_orders(self, ticker: str | None = None) -> list:
        """
        Get active orders.

        Args:
            ticker: Filter by ticker (optional)

        Returns:
            List of active orders
        """
        return self.order_executor.get_active_orders(ticker)

    def get_positions(self) -> list:
        """
        Get all positions.

        Returns:
            List of positions
        """
        return self.position_tracker.get_all_positions()

    def _create_session(self) -> TradingSession:
        """Create new trading session."""
        session_id = f"{self.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Get initial account balance
        try:
            account = self.trading_client.get_account()
            initial_balance = account.portfolio_value
        except Exception:
            initial_balance = Decimal(0)

        session = TradingSession(
            id=session_id,
            strategy_name=self.strategy_name,
            initial_balance=initial_balance,
            paper_trading=self.paper_trading,
            universe=self.universe
        )

        return session

    def _calculate_position_size(self, signal: Signal, account: AccountInfo) -> int:
        """
        Calculate position size for signal.

        Args:
            signal: Trading signal
            account: Account information

        Returns:
            Number of shares to trade
        """
        try:
            # Get signal price (use current market price if not available)
            signal_price = signal.price or Decimal(100)  # Default estimate

            # Calculate position value based on risk parameters
            risk_per_trade = self.risk_manager.risk_parameters.risk_per_trade
            max_position_size = self.risk_manager.risk_parameters.max_position_size

            # Risk-based sizing
            portfolio_value = account.portfolio_value
            risk_amount = portfolio_value * Decimal(risk_per_trade)

            # Position size based on risk
            position_value = min(risk_amount / Decimal(0.02), max_position_size)  # Assume 2% stop loss

            # Calculate shares
            shares = int(position_value / signal_price)

            # Ensure we have buying power
            if shares * signal_price > account.buying_power:
                shares = int(account.buying_power / signal_price)

            # Minimum position size
            shares = max(shares, 1)

            logger.debug(f"Position size calculated for {signal.ticker}: {shares} shares @ ${signal_price}")
            return shares

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    def _cancel_all_pending_orders(self) -> None:
        """Cancel all pending orders."""
        try:
            active_orders = self.order_executor.get_active_orders()
            for order in active_orders:
                if order.id and order.status not in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED]:
                    self.order_executor.cancel_order(order.id)
                    logger.info(f"Cancelled pending order: {order.id}")

        except Exception as e:
            logger.error(f"Error cancelling pending orders: {e}")

    def emergency_stop(self, reason: str) -> bool:
        """
        Execute emergency stop.

        Args:
            reason: Reason for emergency stop

        Returns:
            True if emergency stop executed successfully
        """
        try:
            logger.critical(f"EMERGENCY STOP REQUESTED: {reason}")

            # Stop the session
            self.stop_session()

            # Activate risk manager emergency stop
            self.risk_manager._activate_emergency_stop(reason)

            return True

        except Exception as e:
            logger.error(f"Error executing emergency stop: {e}")
            return False

    def get_session_performance(self) -> dict:
        """
        Get detailed session performance.

        Returns:
            Dictionary with performance metrics
        """
        return self.trade_logger.get_session_performance(self.session.id)

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old trading data.

        Args:
            days_to_keep: Number of days of data to keep

        Returns:
            Number of records cleaned up
        """
        return self.trade_logger.cleanup_old_data(days_to_keep)
