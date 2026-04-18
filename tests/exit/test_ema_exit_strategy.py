"""Tests for EMAExitStrategy."""

from datetime import datetime
from turtle.backtest.models import Trade
from turtle.strategy.exit import EMAExitStrategy
from turtle.repository.analytics import OhlcvAnalyticsRepository
from unittest.mock import Mock

import pandas as pd
import pytest


class TestEMAExitStrategy:
    """Test cases for EMAExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        mock_bars_history = Mock(spec=OhlcvAnalyticsRepository)
        return mock_bars_history

    def test_init(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)

        assert hasattr(strategy, "bars_history")
        assert strategy.bars_history == mock_bars_history

    def test_initialize_defaults(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31))

        assert strategy.ticker == "AAPL"
        assert strategy.ema_period == 20

    def test_initialize_custom_period(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31), ema_period=50)

        assert strategy.ema_period == 50

    def test_empty_data(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(pd.DataFrame())

    def test_calculate_indicators(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)

        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
        mock_data = pd.DataFrame(
            {
                "close": [100.0 + i * 0.5 for i in range(60)],
                "open": [100.0 + i * 0.5 for i in range(60)],
                "high": [101.0 + i * 0.5 for i in range(60)],
                "low": [99.0 + i * 0.5 for i in range(60)],
                "volume": [1000000] * 60,
            },
            index=dates,
        )
        mock_bars_history.get_ticker_history.return_value = mock_data

        strategy.initialize("AAPL", datetime(2024, 1, 15), datetime(2024, 1, 31))
        result = strategy.calculate_indicators()

        assert isinstance(result, pd.DataFrame)
        assert "ema" in result.columns
        assert not result.empty

    def test_calculate_exit_stop_loss(self) -> None:
        """Exit when close drops below EMA."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5))

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        # close drops below ema on day 2 (index 2)
        data = pd.DataFrame(
            {
                "close": [105.0, 104.0, 98.0, 97.0, 96.0],
                "ema":   [100.0, 101.0, 102.0, 103.0, 104.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "stop_loss"
        assert result.date == dates[2]
        assert result.price == 98.0

    def test_calculate_exit_period_end(self) -> None:
        """No exit when close stays above EMA throughout."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5))

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "close": [105.0, 106.0, 107.0, 108.0, 109.0],
                "ema":   [100.0, 101.0, 102.0, 103.0, 104.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == 109.0

    def test_calculate_exit_first_day_stop(self) -> None:
        """Exit triggers on the very first day if close is already below EMA."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = EMAExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5))

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "close": [95.0, 96.0, 97.0, 98.0, 99.0],
                "ema":   [100.0, 101.0, 102.0, 103.0, 104.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert result.reason == "stop_loss"
        assert result.date == dates[0]
        assert result.price == 95.0
