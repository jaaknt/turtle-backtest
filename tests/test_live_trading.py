"""Tests for live trading functionality."""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import Mock, patch

from turtle.trade.models import (
    LiveOrder, LivePosition, OrderSide, OrderType, OrderStatus,
    RiskParameters, TradingSession, ExecutionReport, AccountInfo
)
from turtle.trade.client import AlpacaTradingClient
from turtle.trade.order_executor import OrderExecutor
from turtle.trade.position_tracker import PositionTracker
from turtle.trade.risk_manager import RiskManager
from turtle.trade.trade_logger import TradeLogger
from turtle.trade.manager import LiveTradingManager


class TestLiveOrder:
    """Test LiveOrder model."""

    def test_live_order_creation(self) -> None:
        """Test creating a live order."""
        order = LiveOrder(
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )

        assert order.ticker == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 100
        assert order.status == OrderStatus.PENDING
        assert not order.is_complete
        assert not order.is_filled

    def test_order_completion_status(self) -> None:
        """Test order completion status."""
        order = LiveOrder(
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            status=OrderStatus.FILLED
        )

        assert order.is_complete
        assert order.is_filled

    def test_fill_value_calculation(self) -> None:
        """Test fill value calculation."""
        order = LiveOrder(
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_price=Decimal("150.00"),
            filled_quantity=100
        )

        assert order.fill_value == Decimal("15000.00")


class TestLivePosition:
    """Test LivePosition model."""

    def test_live_position_creation(self) -> None:
        """Test creating a live position."""
        position = LivePosition(
            ticker="AAPL",
            quantity=100,
            avg_price=Decimal("150.00"),
            market_price=Decimal("155.00"),
            cost_basis=Decimal("15000.00"),
            entry_date=datetime.now()
        )

        assert position.ticker == "AAPL"
        assert position.quantity == 100
        assert position.is_long
        assert not position.is_short
        assert position.market_value == Decimal("15500.00")

    def test_short_position(self) -> None:
        """Test short position."""
        position = LivePosition(
            ticker="AAPL",
            quantity=-100,
            avg_price=Decimal("150.00"),
            market_price=Decimal("145.00"),
            cost_basis=Decimal("-15000.00"),
            entry_date=datetime.now()
        )

        assert not position.is_long
        assert position.is_short
        assert position.market_value == Decimal("14500.00")

    def test_pnl_percentage(self) -> None:
        """Test P&L percentage calculation."""
        position = LivePosition(
            ticker="AAPL",
            quantity=100,
            avg_price=Decimal("150.00"),
            market_price=Decimal("165.00"),
            cost_basis=Decimal("15000.00"),
            entry_date=datetime.now(),
            unrealized_pnl=Decimal("1500.00")
        )

        assert position.pnl_percentage == 10.0  # 1500/15000 * 100


class TestRiskParameters:
    """Test RiskParameters model."""

    def test_risk_parameters_validation(self) -> None:
        """Test risk parameters validation."""
        # Valid parameters
        params = RiskParameters(
            max_portfolio_exposure=0.8,
            risk_per_trade=0.02
        )
        params.validate()  # Should not raise

        # Invalid exposure
        with pytest.raises(ValueError):
            invalid_params = RiskParameters(max_portfolio_exposure=1.5)
            invalid_params.validate()

        # Invalid risk per trade
        with pytest.raises(ValueError):
            invalid_params = RiskParameters(risk_per_trade=1.5)
            invalid_params.validate()


class TestOrderExecutor:
    """Test OrderExecutor functionality."""

    @pytest.fixture
    def mock_trading_client(self) -> Mock:
        """Mock trading client."""
        client = Mock(spec=AlpacaTradingClient)
        return client

    @pytest.fixture
    def mock_trade_logger(self) -> Mock:
        """Mock trade logger."""
        logger = Mock(spec=TradeLogger)
        return logger

    @pytest.fixture
    def order_executor(self, mock_trading_client: Any, mock_trade_logger: Any) -> OrderExecutor:
        """Create OrderExecutor instance."""
        return OrderExecutor(mock_trading_client, mock_trade_logger)

    def test_submit_market_order(self, order_executor: Any, mock_trading_client: Any) -> None:
        """Test submitting market order."""
        # Mock successful order submission
        mock_order = LiveOrder(
            id="order_123",
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            status=OrderStatus.SUBMITTED
        )
        mock_trading_client.submit_order.return_value = mock_order

        # Submit order
        result = order_executor.submit_market_order("AAPL", OrderSide.BUY, 100)

        assert result is not None
        assert result.id == "order_123"
        assert result.ticker == "AAPL"
        mock_trading_client.submit_order.assert_called_once()

    def test_cancel_order(self, order_executor: Any, mock_trading_client: Any) -> None:
        """Test cancelling order."""
        mock_trading_client.cancel_order.return_value = True

        # Add order to tracking
        order = LiveOrder(
            id="order_123",
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        order_executor.active_orders["order_123"] = order

        result = order_executor.cancel_order("order_123")

        assert result is True
        assert order_executor.active_orders["order_123"].status == OrderStatus.CANCELED
        mock_trading_client.cancel_order.assert_called_once_with("order_123")


class TestRiskManager:
    """Test RiskManager functionality."""

    @pytest.fixture
    def risk_parameters(self) -> RiskParameters:
        """Create risk parameters."""
        return RiskParameters(
            max_position_size=Decimal("10000"),
            max_portfolio_exposure=0.8,
            max_daily_loss=Decimal("1000"),
            max_open_positions=10
        )

    @pytest.fixture
    def mock_position_tracker(self) -> Mock:
        """Mock position tracker."""
        return Mock(spec=PositionTracker)

    @pytest.fixture
    def mock_order_executor(self) -> Mock:
        """Mock order executor."""
        return Mock(spec=OrderExecutor)

    @pytest.fixture
    def mock_trade_logger(self) -> Mock:
        """Mock trade logger."""
        return Mock(spec=TradeLogger)

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Mock trading session."""
        session = Mock(spec=TradingSession)
        session.id = "test_session_id"
        return session

    @pytest.fixture
    def risk_manager(self, risk_parameters: Any, mock_position_tracker: Any, mock_order_executor: Any, mock_trade_logger: Any, mock_session: Any) -> RiskManager:
        """Create RiskManager instance."""
        return RiskManager(
            risk_parameters,
            mock_position_tracker,
            mock_order_executor,
            mock_trade_logger,
            mock_session
        )

    def test_order_risk_check_passes(self, risk_manager: Any) -> None:
        """Test order risk check passes."""
        order = LiveOrder(
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=50,
            price=Decimal("150.00")
        )

        account = AccountInfo(
            account_id="test_account",
            equity=Decimal("50000"),
            cash=Decimal("20000"),
            buying_power=Decimal("25000"),
            portfolio_value=Decimal("50000")
        )

        # Mock no existing positions
        risk_manager.position_tracker.get_all_positions.return_value = []
        risk_manager.position_tracker.calculate_total_market_value.return_value = Decimal("0")

        approved, reason = risk_manager.check_order_risk(order, account)

        assert approved is True
        assert reason == "Risk check passed"

    def test_order_risk_check_insufficient_balance(self, risk_manager: Any) -> None:
        """Test order rejection due to insufficient balance."""
        order = LiveOrder(
            ticker="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            price=Decimal("150.00")
        )

        account = AccountInfo(
            account_id="test_account",
            equity=Decimal("1000"),  # Below minimum
            cash=Decimal("1000"),
            buying_power=Decimal("1000"),
            portfolio_value=Decimal("1000")
        )

        approved, reason = risk_manager.check_order_risk(order, account)

        assert approved is False
        assert "below minimum" in reason


class TestPositionTracker:
    """Test PositionTracker functionality."""

    @pytest.fixture
    def mock_trading_client(self) -> Mock:
        """Mock trading client."""
        return Mock(spec=AlpacaTradingClient)

    @pytest.fixture
    def mock_trade_logger(self) -> Mock:
        """Mock trade logger."""
        return Mock(spec=TradeLogger)

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Mock trading session."""
        session = Mock(spec=TradingSession)
        session.id = "test_session_id"
        return session

    @pytest.fixture
    def position_tracker(self, mock_trading_client: Any, mock_trade_logger: Any, mock_session: Any) -> PositionTracker:
        """Create PositionTracker instance."""
        return PositionTracker(mock_trading_client, mock_trade_logger, mock_session)

    def test_process_execution_new_position(self, position_tracker: Any) -> None:
        """Test processing execution for new position."""
        execution = ExecutionReport(
            order_id="order_123",
            execution_id="exec_123",
            ticker="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            price=Decimal("150.00"),
            timestamp=datetime.now()
        )

        position_tracker.process_execution(execution)

        assert "AAPL" in position_tracker.positions
        position = position_tracker.positions["AAPL"]
        assert position.quantity == 100
        assert position.avg_price == Decimal("150.00")

    def test_calculate_total_pnl(self, position_tracker: Any) -> None:
        """Test calculating total P&L."""
        # Add test positions
        position1 = LivePosition(
            ticker="AAPL",
            quantity=100,
            avg_price=Decimal("150.00"),
            market_price=Decimal("155.00"),
            cost_basis=Decimal("15000.00"),
            entry_date=datetime.now(),
            unrealized_pnl=Decimal("500.00")
        )

        position2 = LivePosition(
            ticker="MSFT",
            quantity=50,
            avg_price=Decimal("300.00"),
            market_price=Decimal("295.00"),
            cost_basis=Decimal("15000.00"),
            entry_date=datetime.now(),
            unrealized_pnl=Decimal("-250.00")
        )

        position_tracker.positions["AAPL"] = position1
        position_tracker.positions["MSFT"] = position2

        total_pnl = position_tracker.calculate_total_pnl()
        assert total_pnl == Decimal("250.00")


class TestLiveTradingManager:
    """Test LiveTradingManager functionality."""

    @pytest.fixture
    def risk_parameters(self) -> RiskParameters:
        """Create risk parameters."""
        return RiskParameters()

    @patch('turtle.trade.manager.AlpacaTradingClient')
    @patch('turtle.trade.manager.TradeLogger')
    def test_manager_initialization(self, mock_logger_class: Any, mock_client_class: Any, risk_parameters: Any) -> None:
        """Test LiveTradingManager initialization."""
        manager = LiveTradingManager(
            api_key="test_key",
            secret_key="test_secret",
            strategy_name="TestStrategy",
            risk_parameters=risk_parameters,
            db_dsn="test_dsn",
            paper_trading=True
        )

        assert manager.strategy_name == "TestStrategy"
        assert manager.paper_trading is True
        assert manager.is_running is False

    def test_signal_processing(self) -> None:
        """Test processing trading signals."""
        # This would require more extensive mocking
        # and is better suited for integration tests
        pass


class TestIntegration:
    """Integration tests for live trading system."""

    def test_end_to_end_signal_flow(self) -> None:
        """Test complete signal-to-execution flow."""
        # This would test the complete flow:
        # Signal generation → Risk check → Order submission → Position tracking
        # Requires database and API mocking
        pass

    def test_emergency_stop_functionality(self) -> None:
        """Test emergency stop across all components."""
        # Test that emergency stop properly:
        # - Cancels all orders
        # - Stops new orders
        # - Updates session state
        pass


# Example usage and integration tests would go here
if __name__ == "__main__":
    pytest.main([__file__])
