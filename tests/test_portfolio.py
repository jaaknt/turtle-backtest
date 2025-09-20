"""Tests for portfolio backtesting functionality."""

import pytest
from datetime import datetime

from turtle.portfolio.models import Position, PortfolioState
from turtle.portfolio.manager import PortfolioManager
from turtle.portfolio.selector import PortfolioSignalSelector
from turtle.signal.models import Signal


class TestPortfolioModels:
    """Test portfolio data models."""

    def test_position_update_price(self) -> None:
        """Test position price update calculations."""
        position = Position(
            ticker="AAPL",
            entry_date=datetime(2024, 1, 1),
            entry_price=100.0,
            shares=10,
            entry_signal_ranking=85,
        )

        # Test price increase
        position.update_current_price(110.0)
        assert position.current_price == 110.0
        assert position.current_value == 1100.0
        assert position.unrealized_pnl == 100.0
        assert position.unrealized_pnl_pct == 10.0

        # Test price decrease
        position.update_current_price(90.0)
        assert position.current_price == 90.0
        assert position.current_value == 900.0
        assert position.unrealized_pnl == -100.0
        assert position.unrealized_pnl_pct == -10.0

    def test_portfolio_state_properties(self) -> None:
        """Test portfolio state calculated properties."""
        # Create sample positions
        position1 = Position("AAPL", datetime(2024, 1, 1), 100.0, 10, 85, 110.0, 1100.0, 100.0, 10.0)
        position2 = Position("GOOGL", datetime(2024, 1, 1), 200.0, 5, 90, 220.0, 1100.0, 100.0, 10.0)

        state = PortfolioState(
            cash=5000.0,
            positions={"AAPL": position1, "GOOGL": position2},
            total_value=7200.0,
            daily_snapshots=[],
            closed_positions=[],
        )

        assert state.positions_value == 2200.0
        assert state.positions_count == 2
        assert state.available_cash_for_new_position == 5000.0

        state.update_total_value()
        assert state.total_value == 7200.0


class TestPortfolioManager:
    """Test portfolio manager functionality."""

    def test_portfolio_manager_initialization(self) -> None:
        """Test portfolio manager initialization."""
        manager = PortfolioManager(
            initial_capital=10000.0,
            position_size_amount=1000.0,
        )

        assert manager.initial_capital == 10000.0
        assert manager.position_size_amount == 1000.0
        assert manager.state.cash == 10000.0
        assert manager.state.total_value == 10000.0
        assert len(manager.state.positions) == 0

    def test_can_open_new_position(self) -> None:
        """Test position opening validation."""
        manager = PortfolioManager(initial_capital=10000.0, min_cash_reserve=500.0)

        # Should be able to open positions
        assert manager.can_open_new_position(1000.0) is True
        assert manager.can_open_new_position(9000.0) is True

        # Should not be able to open position exceeding available cash
        assert manager.can_open_new_position(10000.0) is False

    def test_calculate_position_size(self) -> None:
        """Test position size calculation."""
        manager = PortfolioManager(position_size_amount=1000.0)

        signal = Signal(ticker="AAPL", date=datetime(2024, 1, 1), ranking=85)
        shares, total_cost = manager.calculate_position_size(signal, 100.0)

        assert shares == 10
        assert total_cost == 1000.0

    def test_open_position(self) -> None:
        """Test opening a new position."""
        manager = PortfolioManager(initial_capital=10000.0, position_size_amount=1000.0)

        signal = Signal(ticker="AAPL", date=datetime(2024, 1, 1), ranking=85)
        position = manager.open_position(signal, datetime(2024, 1, 2), 100.0)

        assert position is not None
        assert position.ticker == "AAPL"
        assert position.shares == 10
        assert position.entry_price == 100.0
        assert manager.state.cash == 9000.0
        assert "AAPL" in manager.state.positions

    def test_close_position(self) -> None:
        """Test closing an existing position."""
        manager = PortfolioManager(initial_capital=10000.0, position_size_amount=1000.0)

        # Open position first
        signal = Signal(ticker="AAPL", date=datetime(2024, 1, 1), ranking=85)
        manager.open_position(signal, datetime(2024, 1, 2), 100.0)

        # Close position
        closed_position = manager.close_position(
            ticker="AAPL",
            exit_date=datetime(2024, 1, 10),
            exit_price=110.0,
            exit_reason="profit_target",
        )

        assert closed_position is not None
        assert closed_position.realized_pnl == 100.0
        assert closed_position.realized_pnl_pct == 10.0
        assert manager.state.cash == 10100.0
        assert "AAPL" not in manager.state.positions
        assert len(manager.state.closed_positions) == 1

    def test_record_daily_snapshot(self) -> None:
        """Test daily snapshot recording."""
        manager = PortfolioManager(initial_capital=10000.0)

        snapshot1 = manager.record_daily_snapshot(datetime(2024, 1, 1))
        assert snapshot1.total_value == 10000.0
        assert snapshot1.daily_return == 0.0

        # Simulate portfolio value change
        manager.state.total_value = 10100.0
        snapshot2 = manager.record_daily_snapshot(datetime(2024, 1, 2))
        assert snapshot2.daily_return == 1.0
        assert snapshot2.daily_pnl == 100.0


class TestPortfolioSignalSelector:
    """Test portfolio signal selector functionality."""

    def test_signal_selector_initialization(self) -> None:
        """Test signal selector initialization."""
        selector = PortfolioSignalSelector(
            max_positions=10,
            min_ranking=70,
        )

        assert selector.max_positions == 10
        assert selector.min_ranking == 70

    def test_select_entry_signals(self) -> None:
        """Test entry signal selection."""
        selector = PortfolioSignalSelector(max_positions=10, min_ranking=70)

        # Create test signals
        signals = [
            Signal("AAPL", datetime(2024, 1, 1), 90),
            Signal("GOOGL", datetime(2024, 1, 1), 85),
            Signal("MSFT", datetime(2024, 1, 1), 80),
            Signal("TSLA", datetime(2024, 1, 1), 75),
            Signal("AMZN", datetime(2024, 1, 1), 65),  # Below threshold
        ]

        current_positions = {"NVDA"}  # Already holding
        available_positions = 3

        selected = selector.select_entry_signals(
            signals, current_positions, available_positions, datetime(2024, 1, 1)
        )

        assert len(selected) == 3
        assert selected[0].ticker == "AAPL"  # Highest ranking
        assert selected[1].ticker == "GOOGL"
        assert selected[2].ticker == "MSFT"

    def test_filter_signals_by_quality(self) -> None:
        """Test signal quality filtering."""
        selector = PortfolioSignalSelector(min_ranking=70)

        signals = [
            Signal("AAPL", datetime(2024, 1, 1), 90),
            Signal("GOOGL", datetime(2024, 1, 1), 65),  # Below threshold
            Signal("MSFT", datetime(2024, 1, 1), 75),
        ]

        filtered = selector.filter_signals_by_quality(signals)
        assert len(filtered) == 2
        assert "GOOGL" not in [s.ticker for s in filtered]

    def test_validate_signal_quality(self) -> None:
        """Test individual signal validation."""
        selector = PortfolioSignalSelector(min_ranking=70)

        valid_signal = Signal("AAPL", datetime(2024, 1, 1), 85)
        invalid_signal = Signal("GOOGL", datetime(2024, 1, 1), 65)

        assert selector.validate_signal_quality(valid_signal) is True
        assert selector.validate_signal_quality(invalid_signal) is False


class TestPortfolioIntegration:
    """Integration tests for portfolio components."""

    def test_portfolio_workflow(self) -> None:
        """Test complete portfolio workflow integration."""
        # This would be a more comprehensive test that requires
        # actual data and strategy components
        pass


@pytest.fixture
def sample_signals() -> list[Signal]:
    """Fixture providing sample signals for testing."""
    return [
        Signal("AAPL", datetime(2024, 1, 1), 90),
        Signal("GOOGL", datetime(2024, 1, 1), 85),
        Signal("MSFT", datetime(2024, 1, 1), 80),
        Signal("TSLA", datetime(2024, 1, 1), 75),
        Signal("AMZN", datetime(2024, 1, 1), 70),
    ]


@pytest.fixture
def portfolio_manager() -> PortfolioManager:
    """Fixture providing configured portfolio manager."""
    return PortfolioManager(
        initial_capital=10000.0,
        position_size_amount=1000.0,
        min_cash_reserve=500.0,
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
