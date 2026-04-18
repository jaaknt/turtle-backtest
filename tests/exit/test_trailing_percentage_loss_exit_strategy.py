"""Tests for TrailingPercentageLossExitStrategy."""

from datetime import datetime
from turtle.backtest.models import Trade
from turtle.exit import TrailingPercentageLossExitStrategy
from turtle.repository.analytics import OhlcvAnalyticsRepository
from unittest.mock import Mock

import pandas as pd
import pytest


class TestTrailingPercentageLossExitStrategy:
    """Test cases for TrailingPercentageLossExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        mock_bars_history = Mock(spec=OhlcvAnalyticsRepository)
        return mock_bars_history

    def test_init(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)

        assert hasattr(strategy, "bars_history")
        assert strategy.bars_history == mock_bars_history

    def test_initialize_defaults(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31))

        assert strategy.ticker == "AAPL"
        assert strategy.percentage_loss == 10.0

    def test_initialize_custom_percentage(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31), percentage_loss=5.0)

        assert strategy.percentage_loss == 5.0

    def test_empty_data(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(pd.DataFrame())

    def test_calculate_indicators(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)

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

    def test_calculate_exit_stop_triggered(self) -> None:
        """Stop triggered when close drops more than percentage_loss% from max close."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)
        # Entry open=100, percentage_loss=10% → initial stop=90
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), percentage_loss=10.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 110.0, 120.0, 115.0, 100.0],
                # Max close rises to 120, stop becomes 120*0.9=108; day 4 close=100 < 108
                "close": [105.0, 112.0, 120.0, 115.0, 100.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "trailing_percentage_stop"
        assert result.date == dates[4]
        assert result.price == pytest.approx(100.0)

    def test_calculate_exit_period_end(self) -> None:
        """No exit when close never drops below trailing stop."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), percentage_loss=10.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        # Steadily rising — close never drops 10% from its running max
        data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "close": [101.0, 102.0, 103.0, 104.0, 105.0],
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == dates[-1]
        assert result.price == pytest.approx(105.0)

    def test_initial_stop_acts_as_floor(self) -> None:
        """Initial stop (based on entry open) is the minimum trailing stop floor."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)
        # Entry open=100, 10% → initial stop=90
        # If close[0]=85 (a gap-down open), cummax_close=85, 85*0.9=76.5 < 90 → floor clips to 90
        # close[0]=85 < 90 → stop triggered on day 0
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 3), percentage_loss=10.0)

        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 90.0, 88.0],
                "close": [85.0, 90.0, 88.0],  # day 0 close < initial stop of 90
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert result.reason == "trailing_percentage_stop"
        assert result.date == dates[0]

    def test_trailing_stop_only_moves_up(self) -> None:
        """After a price peak, the stop stays at the peak-derived level even as price falls."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = TrailingPercentageLossExitStrategy(mock_bars_history)
        # Entry open=100, 20% loss → initial stop=80
        # After close of 150, stop rises to 150*0.8=120 and stays there
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), percentage_loss=20.0)

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 140.0, 130.0, 125.0, 119.0],
                "close": [140.0, 150.0, 130.0, 125.0, 119.0],
                # stop after day 1: max_close=150, stop=120
                # day 4 close=119 < 120 → exit
            },
            index=dates,
        )

        result = strategy.calculate_exit(data)

        assert result.reason == "trailing_percentage_stop"
        assert result.date == dates[4]
        assert result.price == pytest.approx(119.0)

    def test_tighter_percentage_exits_sooner(self) -> None:
        """A tighter percentage exits earlier than a looser one on the same data."""
        mock_bars_history = self.create_mock_bars_history()

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 110.0, 120.0, 115.0, 108.0],
                "close": [110.0, 120.0, 118.0, 112.0, 108.0],
            },
            index=dates,
        )

        strategy_tight = TrailingPercentageLossExitStrategy(mock_bars_history)
        strategy_tight.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), percentage_loss=5.0)

        strategy_loose = TrailingPercentageLossExitStrategy(mock_bars_history)
        strategy_loose.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), percentage_loss=20.0)

        result_tight = strategy_tight.calculate_exit(data)
        result_loose = strategy_loose.calculate_exit(data)

        # Tight stop should trigger; loose stop should not (or trigger later)
        assert result_tight.reason == "trailing_percentage_stop"
        assert result_loose.reason in ("period_end", "trailing_percentage_stop")
        if result_loose.reason == "trailing_percentage_stop":
            assert result_tight.date <= result_loose.date
