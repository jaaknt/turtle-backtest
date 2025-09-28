"""Risk management and safety controls for live trading."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    RiskParameters, LiveOrder, LivePosition, OrderSide, OrderType,
    AccountInfo, TradingSession
)
from .position_tracker import PositionTracker
from .order_executor import OrderExecutor
from .trade_logger import TradeLogger

logger = logging.getLogger(__name__)


class RiskEvent:
    """Risk event for logging and tracking."""

    def __init__(
        self,
        event_type: str,
        severity: str,
        message: str,
        ticker: str | None = None,
        order_id: str | None = None,
        action_taken: str | None = None
    ):
        self.event_type = event_type
        self.severity = severity  # low, medium, high, critical
        self.message = message
        self.ticker = ticker
        self.order_id = order_id
        self.action_taken = action_taken
        self.timestamp = datetime.now()
        self.resolved = False


class RiskManager:
    """Comprehensive risk management with safety controls."""

    def __init__(
        self,
        risk_parameters: RiskParameters,
        position_tracker: PositionTracker,
        order_executor: OrderExecutor,
        trade_logger: TradeLogger,
        session: TradingSession
    ):
        """
        Initialize risk manager.

        Args:
            risk_parameters: Risk management parameters
            position_tracker: Position tracking service
            order_executor: Order execution service
            trade_logger: Trade logging service
            session: Current trading session
        """
        self.risk_parameters = risk_parameters
        self.position_tracker = position_tracker
        self.order_executor = order_executor
        self.trade_logger = trade_logger
        self.session = session

        self.risk_events: list[RiskEvent] = []
        self.daily_loss = Decimal(0)
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()

        # Emergency stop flag
        self.emergency_stop = False

        # Validate risk parameters
        self.risk_parameters.validate()

        logger.info("Risk manager initialized with safety controls")

    def check_order_risk(self, order: LiveOrder, account: AccountInfo) -> tuple[bool, str]:
        """
        Check if order passes risk management rules.

        Args:
            order: Order to validate
            account: Current account information

        Returns:
            Tuple of (approved, reason)
        """
        try:
            # Emergency stop check
            if self.emergency_stop:
                return False, "Emergency stop activated"

            # Reset daily counters if new day
            self._reset_daily_counters_if_needed()

            # Check account balance
            if account.cash < self.risk_parameters.min_account_balance:
                self._log_risk_event(
                    "INSUFFICIENT_BALANCE",
                    "critical",
                    f"Account balance ${account.cash} below minimum ${self.risk_parameters.min_account_balance}",
                    order.ticker,
                    order.id
                )
                return False, f"Account balance ${account.cash} below minimum ${self.risk_parameters.min_account_balance}"

            # Check daily loss limit
            if self.daily_loss >= self.risk_parameters.max_daily_loss:
                self._log_risk_event(
                    "DAILY_LOSS_LIMIT",
                    "critical",
                    f"Daily loss ${self.daily_loss} exceeds limit ${self.risk_parameters.max_daily_loss}",
                    order.ticker,
                    order.id,
                    "Order rejected"
                )
                return False, f"Daily loss limit ${self.risk_parameters.max_daily_loss} exceeded"

            # Check position size limit
            order_value = self._calculate_order_value(order, account)
            if order_value > self.risk_parameters.max_position_size:
                self._log_risk_event(
                    "POSITION_SIZE_LIMIT",
                    "high",
                    f"Order value ${order_value} exceeds position limit ${self.risk_parameters.max_position_size}",
                    order.ticker,
                    order.id,
                    "Order rejected"
                )
                return False, f"Position size ${order_value} exceeds limit ${self.risk_parameters.max_position_size}"

            # Check max open positions
            current_positions = len(self.position_tracker.get_all_positions())
            if current_positions >= self.risk_parameters.max_open_positions:
                # Only allow closing orders
                if not self._is_closing_order(order):
                    self._log_risk_event(
                        "MAX_POSITIONS_LIMIT",
                        "medium",
                        f"Maximum positions ({self.risk_parameters.max_open_positions}) reached",
                        order.ticker,
                        order.id,
                        "Order rejected - only closing orders allowed"
                    )
                    return False, f"Maximum positions ({self.risk_parameters.max_open_positions}) reached"

            # Check portfolio exposure
            total_exposure = self._calculate_portfolio_exposure(order, account)
            if total_exposure > self.risk_parameters.max_portfolio_exposure:
                self._log_risk_event(
                    "PORTFOLIO_EXPOSURE_LIMIT",
                    "high",
                    f"Portfolio exposure {total_exposure:.1%} exceeds limit {self.risk_parameters.max_portfolio_exposure:.1%}",
                    order.ticker,
                    order.id,
                    "Order rejected"
                )
                return False, f"Portfolio exposure {total_exposure:.1%} exceeds limit {self.risk_parameters.max_portfolio_exposure:.1%}"

            # Check buying power
            if order.side == OrderSide.BUY and order_value > account.buying_power:
                self._log_risk_event(
                    "INSUFFICIENT_BUYING_POWER",
                    "medium",
                    f"Order value ${order_value} exceeds buying power ${account.buying_power}",
                    order.ticker,
                    order.id,
                    "Order rejected"
                )
                return False, f"Insufficient buying power: need ${order_value}, have ${account.buying_power}"

            # All checks passed
            logger.info(f"Risk check passed for {order.ticker} order: ${order_value}")
            return True, "Risk check passed"

        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            self._log_risk_event(
                "RISK_CHECK_ERROR",
                "critical",
                f"Risk check failed with error: {e}",
                order.ticker,
                order.id,
                "Order rejected due to system error"
            )
            return False, f"Risk check error: {e}"

    def monitor_positions(self) -> list[RiskEvent]:
        """
        Monitor positions for risk violations.

        Returns:
            List of new risk events
        """
        new_events = []

        try:
            positions = self.position_tracker.get_all_positions()

            for position in positions:
                # Check position loss
                pnl_percentage = abs(position.pnl_percentage) / 100.0

                # Check if position needs stop loss
                if position.unrealized_pnl < 0 and pnl_percentage >= self.risk_parameters.stop_loss_percentage:
                    event = RiskEvent(
                        "STOP_LOSS_TRIGGERED",
                        "high",
                        f"Position {position.ticker} loss {position.pnl_percentage:.1f}% "
                        f"exceeds stop loss {self.risk_parameters.stop_loss_percentage:.1%}",
                        position.ticker
                    )

                    # Create stop loss order
                    self._create_stop_loss_order(position, event)
                    new_events.append(event)

                # Check for large unrealized losses
                elif position.unrealized_pnl < -self.risk_parameters.max_daily_loss / 2:
                    event = RiskEvent(
                        "LARGE_UNREALIZED_LOSS",
                        "medium",
                        f"Position {position.ticker} has large unrealized loss: ${position.unrealized_pnl}",
                        position.ticker
                    )
                    new_events.append(event)

            # Check total portfolio risk
            total_pnl = self.position_tracker.calculate_total_pnl()
            if total_pnl < -self.risk_parameters.max_daily_loss / 2:
                event = RiskEvent(
                    "PORTFOLIO_LOSS_WARNING",
                    "high",
                    f"Total unrealized loss ${total_pnl} approaching daily limit ${self.risk_parameters.max_daily_loss}",
                    action_taken="Portfolio monitoring increased"
                )
                new_events.append(event)

            # Add new events to tracking
            self.risk_events.extend(new_events)

            if new_events:
                logger.warning(f"Generated {len(new_events)} new risk events")

            return new_events

        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            return []

    def check_emergency_conditions(self, account: AccountInfo) -> bool:
        """
        Check for emergency conditions requiring immediate action.

        Args:
            account: Current account information

        Returns:
            True if emergency stop should be activated
        """
        try:
            # Check account balance emergency
            if account.cash < self.risk_parameters.min_account_balance / 2:
                self._activate_emergency_stop(
                    f"Account balance ${account.cash} critically low"
                )
                return True

            # Check total unrealized loss
            total_pnl = self.position_tracker.calculate_total_pnl()
            if total_pnl < -self.risk_parameters.max_daily_loss:
                self._activate_emergency_stop(
                    f"Total unrealized loss ${total_pnl} exceeds daily limit"
                )
                return True

            # Check if account is restricted
            if account.trading_blocked or account.account_blocked:
                self._activate_emergency_stop(
                    "Account trading restrictions detected"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking emergency conditions: {e}")
            return False

    def get_position_risk_score(self, ticker: str) -> float:
        """
        Calculate risk score for a position (0.0 to 1.0).

        Args:
            ticker: Stock symbol

        Returns:
            Risk score (0.0 = low risk, 1.0 = high risk)
        """
        position = self.position_tracker.get_position(ticker)
        if not position:
            return 0.0

        risk_factors = []

        # P&L risk
        pnl_percentage = abs(position.pnl_percentage) / 100.0
        pnl_risk = min(pnl_percentage / self.risk_parameters.stop_loss_percentage, 1.0)
        risk_factors.append(pnl_risk * 0.4)  # 40% weight

        # Position size risk
        size_risk = min(
            float(position.market_value / self.risk_parameters.max_position_size),
            1.0
        )
        risk_factors.append(size_risk * 0.3)  # 30% weight

        # Time risk (longer held = higher risk)
        days_held = (datetime.now() - position.entry_date).days
        time_risk = min(days_held / 30.0, 1.0)  # Max risk at 30 days
        risk_factors.append(time_risk * 0.2)  # 20% weight

        # Volatility risk (placeholder - would need market data)
        volatility_risk = 0.1  # Default low volatility risk
        risk_factors.append(volatility_risk * 0.1)  # 10% weight

        return sum(risk_factors)

    def get_risk_summary(self) -> dict:
        """
        Get comprehensive risk summary.

        Returns:
            Dictionary with risk metrics
        """
        positions = self.position_tracker.get_all_positions()
        total_pnl = self.position_tracker.calculate_total_pnl()

        # Calculate high-risk positions
        high_risk_positions = 0
        for position in positions:
            if self.get_position_risk_score(position.ticker) > 0.7:
                high_risk_positions += 1

        # Recent risk events
        recent_events = [
            event for event in self.risk_events
            if event.timestamp > datetime.now() - timedelta(hours=24)
        ]

        critical_events = [
            event for event in recent_events
            if event.severity == "critical"
        ]

        return {
            "emergency_stop_active": self.emergency_stop,
            "daily_loss": self.daily_loss,
            "daily_trade_count": self.daily_trade_count,
            "total_unrealized_pnl": total_pnl,
            "total_positions": len(positions),
            "high_risk_positions": high_risk_positions,
            "recent_risk_events": len(recent_events),
            "critical_events_24h": len(critical_events),
            "unresolved_events": len([e for e in self.risk_events if not e.resolved]),
            "risk_parameters": {
                "max_daily_loss": self.risk_parameters.max_daily_loss,
                "max_position_size": self.risk_parameters.max_position_size,
                "max_open_positions": self.risk_parameters.max_open_positions,
                "stop_loss_percentage": self.risk_parameters.stop_loss_percentage
            }
        }

    def _calculate_order_value(self, order: LiveOrder, account: AccountInfo) -> Decimal:
        """Calculate estimated order value."""
        if order.order_type == OrderType.MARKET:
            # Estimate market order value using current market price
            # This is conservative estimation
            estimated_price = order.price or Decimal(100)  # Default estimate
            return estimated_price * Decimal(order.quantity)
        elif order.price:
            return order.price * Decimal(order.quantity)
        else:
            return Decimal(0)

    def _calculate_portfolio_exposure(self, order: LiveOrder, account: AccountInfo) -> float:
        """Calculate portfolio exposure including pending order."""
        current_exposure = self.position_tracker.calculate_total_market_value()
        order_value = self._calculate_order_value(order, account)

        if order.side == OrderSide.BUY:
            total_exposure = current_exposure + order_value
        else:
            total_exposure = current_exposure

        return float(total_exposure / account.portfolio_value)

    def _is_closing_order(self, order: LiveOrder) -> bool:
        """Check if order is closing an existing position."""
        position = self.position_tracker.get_position(order.ticker)
        if not position:
            return False

        if position.is_long and order.side == OrderSide.SELL:
            return True
        elif position.is_short and order.side == OrderSide.BUY:
            return True

        return False

    def _create_stop_loss_order(self, position: LivePosition, risk_event: RiskEvent) -> None:
        """Create stop loss order for position."""
        try:
            # Calculate stop price
            if position.is_long:
                stop_price = position.avg_price * (1 - Decimal(self.risk_parameters.stop_loss_percentage))
            else:
                stop_price = position.avg_price * (1 + Decimal(self.risk_parameters.stop_loss_percentage))

            # Submit stop loss order
            stop_order = self.order_executor.submit_stop_loss_order(
                ticker=position.ticker,
                quantity=abs(position.quantity),
                stop_price=stop_price
            )

            if stop_order:
                risk_event.action_taken = f"Stop loss order created: {stop_order.id}"
                risk_event.order_id = stop_order.id
                logger.info(f"Created stop loss order for {position.ticker}: {stop_order.id}")
            else:
                risk_event.action_taken = "Failed to create stop loss order"
                logger.error(f"Failed to create stop loss order for {position.ticker}")

        except Exception as e:
            risk_event.action_taken = f"Stop loss creation failed: {e}"
            logger.error(f"Error creating stop loss order: {e}")

    def _activate_emergency_stop(self, reason: str) -> None:
        """Activate emergency stop."""
        self.emergency_stop = True

        self._log_risk_event(
            "EMERGENCY_STOP",
            "critical",
            f"Emergency stop activated: {reason}",
            action_taken="All trading halted"
        )

        logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")

        # Cancel all pending orders
        try:
            active_orders = self.order_executor.get_active_orders()
            for order in active_orders:
                self.order_executor.cancel_order(order.id or "")
        except Exception as e:
            logger.error(f"Error cancelling orders during emergency stop: {e}")

    def _reset_daily_counters_if_needed(self) -> None:
        """Reset daily counters if it's a new day."""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_loss = Decimal(0)
            self.daily_trade_count = 0
            self.last_reset_date = current_date
            logger.info("Daily risk counters reset")

    def _log_risk_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        ticker: str | None = None,
        order_id: str | None = None,
        action_taken: str | None = None
    ) -> None:
        """Log risk event."""
        event = RiskEvent(event_type, severity, message, ticker, order_id, action_taken)
        self.risk_events.append(event)

        # Log to trade logger as well
        self.trade_logger.log_risk_event(
            self.session.id,
            event_type,
            severity,
            message,
            ticker,
            order_id,
            action_taken
        )

        logger.warning(f"Risk event: {event_type} - {message}")

    def deactivate_emergency_stop(self, reason: str) -> bool:
        """
        Deactivate emergency stop (manual override).

        Args:
            reason: Reason for deactivation

        Returns:
            True if deactivated successfully
        """
        if not self.emergency_stop:
            return False

        self.emergency_stop = False

        self._log_risk_event(
            "EMERGENCY_STOP_DEACTIVATED",
            "medium",
            f"Emergency stop deactivated: {reason}",
            action_taken="Trading resumed"
        )

        logger.warning(f"Emergency stop deactivated: {reason}")
        return True

    def resolve_risk_event(self, event_index: int, resolution: str) -> bool:
        """
        Mark risk event as resolved.

        Args:
            event_index: Index of event to resolve
            resolution: Resolution description

        Returns:
            True if resolved successfully
        """
        if 0 <= event_index < len(self.risk_events):
            event = self.risk_events[event_index]
            event.resolved = True
            event.action_taken = f"{event.action_taken or ''} | Resolved: {resolution}"

            logger.info(f"Risk event resolved: {event.event_type} - {resolution}")
            return True

        return False
