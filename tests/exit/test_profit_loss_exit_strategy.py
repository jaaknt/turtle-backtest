"""Tests for ProfitLossExitStrategy."""

from datetime import datetime
from turtle.model import Trade
from turtle.strategy.exit import ProfitLossExitStrategy
from turtle.repository.analytics import OhlcvAnalyticsRepository
from unittest.mock import Mock

import pandas as pd
import pytest


class TestProfitLossExitStrategy:
    """Test cases for ProfitLossExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        mock_bars_history = Mock(spec=OhlcvAnalyticsRepository)
        return mock_bars_history

    def test_init(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)

        assert hasattr(strategy, "bars_history")
        assert strategy.bars_history == mock_bars_history

    def test_initialize_defaults(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31))

        assert strategy.ticker == "AAPL"
        assert strategy.profit_target == 10.0
        assert strategy.stop_loss == 5.0

    def test_initialize_custom_targets(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31), profit_target=20.0, stop_loss=8.0)

        assert strategy.profit_target == 20.0
        assert strategy.stop_loss == 8.0

    def test_empty_data(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(pd.DataFrame())

    def test_calculate_indicators(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)

        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        mock_data = pd.DataFrame(
            {
                "close": [100.0 + i for i in range(10)],
                "open": [100.0 + i for i in range(10)],
                "high": [101.0 + i for i in range(10)],
                "low": [99.0 + i for i in range(10)],
                "volume": [1000000] * 10,
            },
            index=dates,
        )
        mock_bars_history.get_ticker_history.return_value = mock_data

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 10))
        result = strategy.calculate_indicators()

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_calculate_exit_profit_target(self) -> None:
        """Exit when high hits the profit target."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)
        # Entry open = 100, profit_target=10% → profit price = 110
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), profit_target=10.0, stop_loss=5.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "close": [101.0, 102.0, 103.0, 104.0, 105.0],
                "high":  [102.0, 103.0, 111.0, 112.0, 113.0],  # hits 110 on day 2
                "low":   [99.0, 100.0, 101.0, 102.0, 103.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "profit_target"
        assert result.date == dates[2]
        assert result.price == pytest.approx(110.0)

    def test_calculate_exit_stop_loss(self) -> None:
        """Exit when low hits the stop loss."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)
        # Entry open = 100, stop_loss=5% → stop price = 95
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), profit_target=10.0, stop_loss=5.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 99.0, 98.0, 97.0, 96.0],
                "close": [99.0, 98.0, 97.0, 96.0, 95.0],
                "high":  [101.0, 100.0, 99.0, 98.0, 97.0],
                "low":   [98.0, 97.0, 94.0, 93.0, 92.0],  # hits 95 on day 2
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "stop_loss"
        assert result.date == dates[2]
        assert result.price == pytest.approx(95.0)

    def test_calculate_exit_profit_before_loss(self) -> None:
        """When both targets hit the same day, profit wins if high comes first (profit_date <= loss_date)."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)
        # Entry open = 100, profit=10% → 110, stop=5% → 95
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 3), profit_target=10.0, stop_loss=5.0)

        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 100.0, 100.0],
                "close": [100.0, 100.0, 100.0],
                "high":  [105.0, 111.0, 105.0],  # profit hit on day 1
                "low":   [99.0, 94.0, 99.0],      # loss hit on day 1 too
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        # Both hit on dates[1]; profit_date == loss_date → profit wins
        assert result.reason == "profit_target"
        assert result.date == dates[1]

    def test_calculate_exit_loss_before_profit(self) -> None:
        """When stop hits before profit target, stop loss is used."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), profit_target=10.0, stop_loss=5.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 99.0, 98.0, 97.0, 96.0],
                "close": [99.0, 98.0, 97.0, 112.0, 95.0],
                "high":  [101.0, 100.0, 99.0, 115.0, 97.0],  # profit hit on day 3
                "low":   [98.0, 97.0, 94.0, 96.0, 92.0],     # stop hit on day 2
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert result.reason == "stop_loss"
        assert result.date == dates[2]

    def test_calculate_exit_period_end(self) -> None:
        """Neither target is hit — exit at period end."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ProfitLossExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), profit_target=10.0, stop_loss=5.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        # Entry open=100, profit=110, stop=95; lows stay above 95, highs stay below 110
        data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 101.0, 100.0],
                "close": [101.0, 102.0, 103.0, 102.0, 101.0],
                "high":  [103.0, 104.0, 105.0, 104.0, 103.0],
                "low":   [99.0, 100.0, 101.0, 100.0, 99.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == 101.0
