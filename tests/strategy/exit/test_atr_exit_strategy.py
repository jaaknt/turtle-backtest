"""Tests for ATRExitStrategy."""

from datetime import date, datetime
from turtle.model import Trade
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.exit import ATRExitStrategy
from unittest.mock import Mock

import polars as pl
import pytest


class TestATRExitStrategy:
    """Test cases for ATRExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        """Create a mock bars history repo for testing."""
        mock_bars_history = Mock(spec=OhlcvAnalyticsRepository)
        return mock_bars_history

    def test_init(self) -> None:
        """Test ATRExitStrategy initialization."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        assert hasattr(strategy, "bars_history")
        assert strategy.bars_history == mock_bars_history

    def test_empty_data(self) -> None:
        """Test handling of empty data."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(pl.DataFrame())

    def test_initialize(self) -> None:
        """Test strategy initialization."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        ticker = "AAPL"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        strategy.initialize(ticker, start_date, end_date)
        assert strategy.ticker == ticker
        assert strategy.start_date == start_date
        assert strategy.end_date == end_date
        assert strategy.atr_period == 14
        assert strategy.atr_multiplier == 2.0

        strategy.initialize(ticker, start_date, end_date, atr_period=20, atr_multiplier=1.5)
        assert strategy.atr_period == 20
        assert strategy.atr_multiplier == 1.5

    def test_calculate_indicators(self) -> None:
        """Test calculate_indicators method."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        mock_data = pl.DataFrame(
            {
                "date": [date(2024, 1, 1 + i) if i < 31 else date(2024, 2, i - 30) for i in range(60)],
                "close": [100.0 + i * 0.5 for i in range(60)],
                "high": [102.0 + i * 0.5 for i in range(60)],
                "low": [98.0 + i * 0.5 for i in range(60)],
                "open": [100.0 + i * 0.5 for i in range(60)],
                "volume": [1000000] * 60,
            }
        )
        mock_bars_history.get_bars_pl.return_value = mock_data

        strategy.initialize("AAPL", datetime(2024, 1, 15), datetime(2024, 1, 31))
        result = strategy.calculate_indicators()

        assert isinstance(result, pl.DataFrame)
        assert "atr" in result.columns
        assert not result.is_empty()

    def test_calculate_exit_missing_atr(self) -> None:
        """Test calculate_exit with missing ATR column."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(5)],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [98.0, 99.0, 100.0, 101.0, 102.0],
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        with pytest.raises(ValueError, match="ATR column not found"):
            strategy.calculate_exit(data)

    def test_calculate_exit_with_stop_hit(self) -> None:
        """Test calculate_exit when ATR stop loss is hit."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), atr_period=14, atr_multiplier=2.0)

        # With entry open=100, ATR=1.0, multiplier=2.0: initial_stop = 100 - 2.0 = 98.0
        # cummax_high: [101, 101, 101, 101, 101]; potential_stop: [99, 99, 99, 99, 99]
        # trailing_stop after cummax+clip(98): [99, 99, 99, 99, 99]
        # close: [99, 98, 97, 96, 95] → first close < 99 is day 1 (98 < 99)
        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(5)],
                "open": [100.0, 99.0, 98.0, 97.0, 96.0],
                "close": [99.0, 98.0, 97.0, 96.0, 95.0],
                "high": [101.0, 100.0, 99.0, 98.0, 97.0],
                "low": [98.0, 96.0, 94.0, 92.0, 90.0],
                "atr": [1.0, 1.0, 1.0, 1.0, 1.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "atr_trailing_stop"
        assert result.date == datetime(2024, 1, 2)
        assert result.price < 100.0

    def test_calculate_exit_period_end(self) -> None:
        """Test calculate_exit when no stop is hit."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = ATRExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5), atr_period=14, atr_multiplier=2.0)

        # With entry=100, ATR=1.0, multiplier=2.0: stop = 98.0; lowest close is 101 → never hit
        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(5)],
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "close": [101.0, 102.0, 103.0, 104.0, 105.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "atr": [1.0, 1.0, 1.0, 1.0, 1.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.reason == "period_end"
        assert result.date == datetime(2024, 1, 5)
        assert result.price == 105.0

    def test_different_atr_multipliers(self) -> None:
        """Test strategy with different ATR multipliers."""
        mock_bars_history = self.create_mock_bars_history()

        strategy_loose = ATRExitStrategy(mock_bars_history)
        strategy_loose.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 3), atr_period=14, atr_multiplier=3.0)

        strategy_tight = ATRExitStrategy(mock_bars_history)
        strategy_tight.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 3), atr_period=14, atr_multiplier=1.0)

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(3)],
                "open": [100.0, 99.0, 98.0],
                "close": [99.0, 98.0, 97.0],
                "high": [101.0, 100.0, 99.0],
                "low": [98.0, 96.0, 95.0],
                "atr": [2.0, 2.0, 2.0],
            }
        )

        # Loose stop: 100 - (3.0 * 2.0) = 94.0 (not hit, close[0]=99 > 94)
        result_loose = strategy_loose.calculate_exit(data)
        assert result_loose.reason == "period_end"

        # Tight stop: 100 - (1.0 * 2.0) = 98.0; trailing_stop=cummax([101-2,101-2,101-2])=[99,99,99]
        # close: [99,98,97] → close[1]=98 < 99 → exit
        result_tight = strategy_tight.calculate_exit(data)
        assert result_tight.reason == "atr_trailing_stop"
        assert result_tight.price <= 100.0
