"""Tests for ATRExitStrategy."""

import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import Mock

from turtle.exit import ATRExitStrategy
from turtle.backtest.models import Trade
from turtle.data.bars_history import BarsHistoryRepo


class TestATRExitStrategy:
    """Test cases for ATRExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        """Create a mock BarsHistoryRepo for testing."""
        mock_bars_history = Mock(spec=BarsHistoryRepo)
        return mock_bars_history

    def test_init(self) -> None:
        """Test ATRExitStrategy initialization."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        # Test that it has the required attributes from parent
        assert hasattr(strategy, 'bars_history')
        assert strategy.bars_history == mock_bars_history

    def test_empty_data(self) -> None:
        """Test handling of empty data."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(empty_data)

    def test_initialize(self) -> None:
        """Test strategy initialization."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        ticker = "AAPL"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        # Test with default parameters
        strategy.initialize(ticker, start_date, end_date)
        assert strategy.ticker == ticker
        assert strategy.start_date == start_date
        assert strategy.end_date == end_date
        assert strategy.atr_period == 14
        assert strategy.atr_multiplier == 2.0

        # Test with custom parameters
        strategy.initialize(ticker, start_date, end_date, atr_period=20, atr_multiplier=1.5)
        assert strategy.atr_period == 20
        assert strategy.atr_multiplier == 1.5

    def test_calculate_indicators(self) -> None:
        """Test calculate_indicators method."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        # Set up mock data
        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
        mock_data = pd.DataFrame({
            "close": [100.0 + i * 0.5 for i in range(60)],
            "high": [102.0 + i * 0.5 for i in range(60)],
            "low": [98.0 + i * 0.5 for i in range(60)],
            "open": [100.0 + i * 0.5 for i in range(60)],
            "volume": [1000000] * 60
        }, index=dates)

        mock_bars_history.get_ticker_history.return_value = mock_data

        # Initialize strategy
        strategy.initialize("AAPL", datetime(2024, 1, 15), datetime(2024, 1, 31))

        # Test calculate_indicators
        result = strategy.calculate_indicators()

        assert isinstance(result, pd.DataFrame)
        assert "atr" in result.columns
        assert not result.empty

    def test_calculate_exit_missing_atr(self) -> None:
        """Test calculate_exit with missing ATR column."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        # Create data without ATR column
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame({
            "close": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [102.0, 103.0, 104.0, 105.0, 106.0],
            "low": [98.0, 99.0, 100.0, 101.0, 102.0],
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        }, index=dates)

        with pytest.raises(ValueError, match="ATR column not found"):
            strategy.calculate_exit(data)

    def test_calculate_exit_with_stop_hit(self) -> None:
        """Test calculate_exit when ATR stop loss is hit."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)
        strategy.atr_multiplier = 2.0  # Set multiplier for predictable test

        # Create test data where stop loss will be hit
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame({
            "open": [100.0, 99.0, 98.0, 97.0, 96.0],  # Entry at 100
            "close": [99.0, 98.0, 97.0, 96.0, 95.0],
            "high": [101.0, 100.0, 99.0, 98.0, 97.0],
            "low": [98.0, 96.0, 94.0, 92.0, 90.0],   # Low drops significantly
            "atr": [1.0, 1.0, 1.0, 1.0, 1.0],       # Constant ATR of 1.0
        }, index=dates)

        # With entry=100, ATR=1.0, multiplier=2.0: stop = 100 - (2.0 * 1.0) = 98.0
        # Close on day 2 (97.0) is first to be < stop (98.0), so should exit on day 2

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "atr_stop_loss"
        assert result.date == dates[2]  # First day when close < stop
        assert result.price == 98.0  # Stop price

    def test_calculate_exit_period_end(self) -> None:
        """Test calculate_exit when no stop is hit."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)
        strategy.atr_multiplier = 2.0

        # Create test data where stop loss is never hit
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame({
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],  # Entry at 100
            "close": [101.0, 102.0, 103.0, 104.0, 105.0],
            "high": [102.0, 103.0, 104.0, 105.0, 106.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],    # Never drops below stop
            "atr": [1.0, 1.0, 1.0, 1.0, 1.0],            # ATR = 1.0
        }, index=dates)

        # With entry=100, ATR=1.0, multiplier=2.0: stop = 98.0
        # Lowest low is 99.0, which is above stop, so should hold to end

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == 105.0  # Close price of last day

    def test_different_atr_multipliers(self) -> None:
        """Test strategy with different ATR multipliers."""
        mock_bars_history = self.create_mock_bars_history()

        # Test with high multiplier (looser stop)
        strategy_loose = ATRExitStrategy(mock_bars_history)
        strategy_loose.atr_multiplier = 3.0

        # Test with low multiplier (tighter stop)
        strategy_tight = ATRExitStrategy(mock_bars_history)
        strategy_tight.atr_multiplier = 1.0

        # Create test data
        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame({
            "open": [100.0, 99.0, 98.0],
            "close": [99.0, 98.0, 97.0],
            "high": [101.0, 100.0, 99.0],
            "low": [98.0, 96.0, 95.0],  # Low of 96.0 on day 1
            "atr": [2.0, 2.0, 2.0],    # ATR = 2.0
        }, index=dates)

        # Loose stop: 100 - (3.0 * 2.0) = 94.0 (not hit, low=96.0)
        result_loose = strategy_loose.calculate_exit(data)
        assert result_loose.reason == "period_end"

        # Tight stop: 100 - (1.0 * 2.0) = 98.0 (hit, low=96.0 < 98.0)
        result_tight = strategy_tight.calculate_exit(data)
        assert result_tight.reason == "atr_stop_loss"
        assert result_tight.price == 98.0
