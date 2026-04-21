"""Tests for BuyAndHoldExitStrategy."""

from datetime import date, datetime
from turtle.model import Trade
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.exit import BuyAndHoldExitStrategy
from unittest.mock import Mock

import polars as pl
import pytest


class TestBuyAndHoldExitStrategy:
    """Test cases for BuyAndHoldExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        mock_bars_history = Mock(spec=OhlcvAnalyticsRepository)
        return mock_bars_history

    def test_init(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)

        assert hasattr(strategy, "bars_history")
        assert strategy.bars_history == mock_bars_history

    def test_initialize(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)

        ticker = "AAPL"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        strategy.initialize(ticker, start_date, end_date)

        assert strategy.ticker == ticker
        assert strategy.start_date == start_date
        assert strategy.end_date == end_date

    def test_empty_data(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)

        with pytest.raises(ValueError, match="No valid data available"):
            strategy.calculate_exit(pl.DataFrame())

    def test_calculate_indicators(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)

        mock_data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(10)],
                "close": [100.0 + i for i in range(10)],
                "open": [100.0 + i for i in range(10)],
                "high": [101.0 + i for i in range(10)],
                "low": [99.0 + i for i in range(10)],
                "volume": [1000000] * 10,
            }
        )
        mock_bars_history.get_bars_pl.return_value = mock_data

        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 10))
        result = strategy.calculate_indicators()

        assert isinstance(result, pl.DataFrame)
        assert not result.is_empty()

    def test_calculate_exit_returns_last_close(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 5))

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(5)],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "open": [99.0, 100.0, 101.0, 102.0, 103.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [98.0, 99.0, 100.0, 101.0, 102.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.ticker == "AAPL"
        assert result.reason == "period_end"
        assert result.date == datetime(2024, 1, 5)
        assert result.price == 104.0

    def test_calculate_exit_single_row(self) -> None:
        """Exit on a single-row DataFrame returns that row's close."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("MSFT", datetime(2024, 6, 1), datetime(2024, 6, 1))

        data = pl.DataFrame(
            {"date": [date(2024, 6, 1)], "close": [250.0], "open": [248.0], "high": [251.0], "low": [247.0]}
        )

        result = strategy.calculate_exit(data)

        assert result.price == 250.0
        assert result.date == datetime(2024, 6, 1)
        assert result.reason == "period_end"
