"""Tests for MACDExitStrategy."""

import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import Mock

from turtle.exit import MACDExitStrategy
from turtle.backtest.models import Trade
from turtle.data.bars_history import BarsHistoryRepo


class TestMACDExitStrategy:
    """Test cases for MACDExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        """Create a mock BarsHistoryRepo for testing."""
        mock_bars_history = Mock(spec=BarsHistoryRepo)
        return mock_bars_history

    def test_init(self) -> None:
        """Test MACDExitStrategy initialization."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)

        # Test that it has the required attributes from parent
        assert hasattr(strategy, 'bars_history')
        assert strategy.bars_history == mock_bars_history

    def test_empty_data(self) -> None:
        """Test handling of empty data."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(empty_data)

    def test_initialize(self) -> None:
        """Test strategy initialization."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)

        ticker = "AAPL"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        strategy.initialize(ticker, start_date, end_date, fastperiod=8, slowperiod=21, signalperiod=5)

        assert strategy.ticker == ticker
        assert strategy.start_date == start_date
        assert strategy.end_date == end_date
        assert strategy.fastperiod == 8
        assert strategy.slowperiod == 21
        assert strategy.signalperiod == 5

    def test_calculate_indicators(self) -> None:
        """Test calculate_indicators method."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)

        # Set up mock data
        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
        mock_data = pd.DataFrame({
            "close": [100.0 + i * 0.5 for i in range(60)],
            "high": [101.0 + i * 0.5 for i in range(60)],
            "low": [99.0 + i * 0.5 for i in range(60)],
            "open": [100.0 + i * 0.5 for i in range(60)],
            "volume": [1000000] * 60
        }, index=dates)

        mock_bars_history.get_ticker_history.return_value = mock_data

        # Initialize strategy
        strategy.initialize("AAPL", datetime(2024, 1, 15), datetime(2024, 1, 31))

        # Test calculate_indicators
        result = strategy.calculate_indicators()

        assert isinstance(result, pd.DataFrame)
        assert "macd_line" in result.columns
        assert "macd_signal" in result.columns
        assert not result.empty

    def test_calculate_exit_with_signal(self) -> None:
        """Test calculate_exit method with MACD signal data."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)

        # Create test data with MACD indicators where close drops below signal
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        data = pd.DataFrame({
            "close": [100.0, 101.0, 102.0, 101.5, 100.5, 99.0, 98.0, 97.0, 96.0, 95.0],
            "macd_signal": [99.0, 100.0, 101.0, 101.0, 101.0, 100.0, 99.0, 98.0, 97.0, 96.0],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "below_signal"
        # Should exit when close first goes below macd_signal (at index 4)
        assert result.date == dates[4]
        assert result.price == 100.5

    def test_calculate_exit_period_end(self) -> None:
        """Test calculate_exit when no signal is triggered."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)

        # Create test data where close stays above signal
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame({
            "close": [100.0, 101.0, 102.0, 103.0, 104.0],
            "macd_signal": [99.0, 100.0, 101.0, 102.0, 103.0],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == 104.0

    def test_default_initialization_parameters(self) -> None:
        """Test strategy with default MACD parameters."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = MACDExitStrategy(mock_bars_history)

        # Test default initialization
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31))

        # Check default parameters
        assert strategy.fastperiod == 12
        assert strategy.slowperiod == 26
        assert strategy.signalperiod == 9
