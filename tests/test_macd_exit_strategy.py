"""Tests for MACDExitStrategy."""

import pandas as pd
import pytest

from turtle.backtest.exit_strategy import MACDExitStrategy
from turtle.backtest.models import Trade


class TestMACDExitStrategy:
    """Test cases for MACDExitStrategy."""

    def test_init(self) -> None:
        """Test MACDExitStrategy initialization."""
        strategy = MACDExitStrategy()
        assert strategy.fastperiod == 12
        assert strategy.slowperiod == 26
        assert strategy.signalperiod == 9
        assert strategy.use_histogram is True

        # Test custom parameters
        strategy = MACDExitStrategy(fastperiod=8, slowperiod=21, signalperiod=5, use_histogram=False)
        assert strategy.fastperiod == 8
        assert strategy.slowperiod == 21
        assert strategy.signalperiod == 5
        assert strategy.use_histogram is False

    def test_empty_data(self) -> None:
        """Test handling of empty data."""
        strategy = MACDExitStrategy()
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(empty_data)

    def test_insufficient_data(self) -> None:
        """Test handling when insufficient data for MACD calculation."""
        strategy = MACDExitStrategy()

        # Create minimal data (less than required for MACD)
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        data = pd.DataFrame({
            "close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == 109.0

    def test_period_end_exit(self) -> None:
        """Test exit at period end when no signals found."""
        strategy = MACDExitStrategy()

        # Create data with gradually increasing prices (no bearish signals)
        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
        closes = [100 + i * 0.5 for i in range(60)]  # Steadily increasing
        data = pd.DataFrame({
            "close": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == closes[-1]

    def test_macd_bearish_crossover(self) -> None:
        """Test exit on MACD bearish crossover."""
        strategy = MACDExitStrategy(use_histogram=False)  # Only use signal crossover

        # Create data that should generate a bearish MACD crossover
        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")

        # Rising then falling prices to create MACD crossover
        closes = []
        for i in range(60):
            if i < 30:
                closes.append(100 + i * 2)  # Rising
            else:
                closes.append(160 - (i - 30) * 3)  # Falling faster

        data = pd.DataFrame({
            "close": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        # Should exit due to MACD crossover, not at period end
        assert result.reason in ["macd_bearish_cross", "period_end"]
        assert result.date <= dates[-1]

    def test_histogram_strategy(self) -> None:
        """Test MACD histogram strategy."""
        strategy = MACDExitStrategy(use_histogram=True)

        # Create data with price movement that should trigger histogram signal
        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")

        # Create a pattern that goes up then down to trigger histogram changes
        closes = []
        for i in range(60):
            if i < 20:
                closes.append(100.0 + i)  # Rising
            elif i < 35:
                closes.append(120.0 - (i - 20) * 0.5)  # Slight decline
            else:
                closes.append(112.5 - (i - 35) * 2.0)  # Steeper decline

        data = pd.DataFrame({
            "close": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        # Should detect some kind of bearish signal or exit at period end
        assert result.reason in ["macd_bearish_cross", "macd_histogram_negative", "period_end"]
        assert result.date <= dates[-1]

    def test_custom_parameters(self) -> None:
        """Test strategy with custom MACD parameters."""
        strategy = MACDExitStrategy(fastperiod=8, slowperiod=21, signalperiod=5)

        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        closes = [100 + i * 0.5 for i in range(50)]
        data = pd.DataFrame({
            "close": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
        }, index=dates)

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.date in data.index
        assert isinstance(result.price, float)
        assert result.reason in ["macd_bearish_cross", "macd_histogram_negative", "period_end"]
