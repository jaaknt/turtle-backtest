"""Tests for portfolio backtesting functionality."""

import pytest
from datetime import datetime

from turtle.portfolio.models import Position, PortfolioState
from turtle.portfolio.manager import PortfolioManager
from turtle.portfolio.selector import PortfolioSignalSelector
from turtle.signal.models import Signal
from turtle.backtest.models import ClosedTrade, Trade, Benchmark


def create_mock_closed_trade(ticker: str, entry_date: datetime, entry_price: float) -> ClosedTrade:
    """Create a mock ClosedTrade for testing purposes."""
    signal = Signal(ticker=ticker, date=entry_date, ranking=85)
    entry = Trade(ticker=ticker, date=entry_date, price=entry_price, reason="signal")
    exit = Trade(ticker=ticker, date=entry_date, price=entry_price * 1.1, reason="profit_target")  # 10% profit
    benchmarks = [Benchmark(ticker="SPY", return_pct=5.0, entry_date=entry_date, exit_date=entry_date)]

    return ClosedTrade(
        signal=signal,
        entry=entry,
        exit=exit,
        benchmark_list=benchmarks
    )


class TestPortfolioModels:
    """Test portfolio data models."""

    def test_position_update_price(self) -> None:
        """Test position price update calculations."""
        entry_date = datetime(2024, 1, 1)

        from turtle.backtest.models import Trade
        entry_trade = Trade(ticker="AAPL", date=entry_date, price=100.0, reason="signal")
        open_exit_trade = Trade(ticker="AAPL", date=entry_date, price=100.0, reason="open")

        position = Position(
            entry=entry_trade,
            exit=open_exit_trade,
            current_price=100.0,
            position_size=10,
        )

        # Test initial values
        assert position.ticker == "AAPL"
        assert position.entry.date == entry_date
        assert position.entry.price == 100.0
        assert position.position_size == 10
        assert position.current_price == 100.0
        # With exit price = 100 and current price = 100, unrealized_pnl should be 0
        assert position.unrealized_pnl == 0.0  # (100 - 100) * 10 = 0

        # Test price update functionality by directly updating current_price
        position.current_price = 110.0
        assert position.current_price == 110.0
        # Now unrealized_pnl should be positive since current_price > entry.price
        assert position.unrealized_pnl == 100.0  # (110 - 100) * 10 = 100

        # Test current value calculation
        assert position.current_value == 1100.0  # 110.0 * 10

        # Test holding period calculation
        assert position.holding_period_days == 0  # same day entry and exit

    def test_portfolio_state_properties(self) -> None:
        """Test portfolio state calculated properties."""
        entry_date = datetime(2024, 1, 1)
        closed_trade1 = create_mock_closed_trade("AAPL", entry_date, 100.0)
        closed_trade2 = create_mock_closed_trade("GOOGL", entry_date, 200.0)

        state = PortfolioState(
            daily_snapshots=[],
            closed_trades=[closed_trade1, closed_trade2],
        )

        # Test basic properties
        assert len(state.closed_trades) == 2
        assert len(state.daily_snapshots) == 0


class TestPortfolioManager:
    """Test portfolio manager functionality."""

    def test_portfolio_manager_initialization(self) -> None:
        """Test portfolio manager initialization."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            position_min_amount=1000.0,
            position_max_amount=2000.0,
        )

        assert manager.initial_capital == 10000.0
        assert manager.position_min_amount == 1000.0
        assert manager.position_max_amount == 2000.0
        assert manager.start_date == start_date
        assert manager.end_date == end_date
        assert len(manager.state.daily_snapshots) == 0
        assert len(manager.state.closed_trades) == 0

    def test_can_open_new_position(self) -> None:
        """Test position opening validation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            position_min_amount=500.0,
            position_max_amount=3000.0,
        )

        # Create initial snapshot to have cash available
        manager.record_daily_snapshot(start_date)

        # Test position size calculation limits
        assert manager.position_min_amount == 500.0
        assert manager.position_max_amount == 3000.0

    def test_calculate_position_size(self) -> None:
        """Test position size calculation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            position_max_amount=1000.0,
        )

        # Create initial snapshot
        manager.record_daily_snapshot(start_date)

        # Create trade entry
        from turtle.backtest.models import Trade
        trade = Trade(ticker="AAPL", date=datetime(2024, 1, 1), price=100.0, reason="signal")
        shares = manager.calculate_position_size(trade)

        assert shares == 10  # $1000 / $100 = 10 shares

    def test_open_position(self) -> None:
        """Test opening a new position."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            position_max_amount=1000.0,
        )

        # Create initial snapshot
        manager.record_daily_snapshot(start_date)

        from turtle.backtest.models import Trade
        entry = Trade(ticker="AAPL", date=datetime(2024, 1, 2), price=100.0, reason="signal")
        exit_trade = Trade(ticker="AAPL", date=datetime(2024, 1, 10), price=110.0, reason="profit_target")
        position_size = manager.calculate_position_size(entry)
        position = manager.open_position(entry, exit_trade, position_size)

        assert position is not None
        assert position.ticker == "AAPL"
        assert position.position_size == 10
        assert position.entry.price == 100.0
        assert manager.current_snapshot.cash == 9000.0

    def test_close_position(self) -> None:
        """Test closing an existing position."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            position_max_amount=1000.0,
        )

        # Create initial snapshot and open position
        manager.record_daily_snapshot(start_date)

        from turtle.backtest.models import Trade
        entry = Trade(ticker="AAPL", date=datetime(2024, 1, 2), price=100.0, reason="signal")
        exit_trade = Trade(ticker="AAPL", date=datetime(2024, 1, 10), price=110.0, reason="profit_target")
        position_size = manager.calculate_position_size(entry)
        manager.open_position(entry, exit_trade, position_size)

        # Close position - use different exit trade
        actual_exit_trade = Trade(ticker="AAPL", date=datetime(2024, 1, 10), price=110.0, reason="profit_target")
        manager.close_position(actual_exit_trade, position_size)

        # Verify position was closed
        # With new Position structure, remove_position uses current_value (exit price)
        assert manager.current_snapshot.cash == 10100.0  # Initial 10000 - 1000 + 1100 = 10100
        # Check position is not in current snapshot
        positions = manager.current_snapshot.positions
        assert not any(p.ticker == "AAPL" for p in positions)

    def test_record_daily_snapshot(self) -> None:
        """Test daily snapshot recording."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
        )

        snapshot1 = manager.record_daily_snapshot(datetime(2024, 1, 1))
        assert snapshot1.total_value == 10000.0

        snapshot2 = manager.record_daily_snapshot(datetime(2024, 1, 2))
        assert snapshot2.total_value == 10000.0


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
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=10000.0,
        position_min_amount=500.0,
        position_max_amount=1000.0,
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
