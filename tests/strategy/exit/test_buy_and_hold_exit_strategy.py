"""Tests for BuyAndHoldExitStrategy."""

from datetime import date, timedelta
from unittest.mock import Mock

import polars as pl
import pytest

from turtlex.model import Trade
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.strategy.exit import BuyAndHoldExitStrategy


class TestBuyAndHoldExitStrategy:
    """Test cases for BuyAndHoldExitStrategy."""

    def create_mock_bars_history(self) -> Mock:
        mock_bars_history = Mock(spec=DailyBarsQueryRepository)
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
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        strategy.initialize(ticker, start_date, end_date)

        assert strategy.ticker == ticker
        assert strategy.start_date == start_date
        assert strategy.end_date == end_date
        assert strategy.holding_days == 30

    def test_initialize_custom_holding_days(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)

        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 12, 31), holding_days=5)

        assert strategy.holding_days == 5

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
                "adjusted_close": [100.0 + i for i in range(10)],
                "open": [100.0 + i for i in range(10)],
                "high": [101.0 + i for i in range(10)],
                "low": [99.0 + i for i in range(10)],
                "volume": [1000000] * 10,
            }
        )
        mock_bars_history.get_bars_pl.return_value = mock_data

        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 1, 10))
        result = strategy.calculate_indicators()

        assert isinstance(result, pl.DataFrame)
        assert not result.is_empty()

    def test_calculate_exit_returns_last_close(self) -> None:
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 1, 5))

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(5)],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "adjusted_close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "open": [99.0, 100.0, 101.0, 102.0, 103.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [98.0, 99.0, 100.0, 101.0, 102.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert isinstance(result, Trade)
        assert result.ticker == "AAPL"
        assert result.reason == "period_end"
        assert result.date == date(2024, 1, 5)
        assert result.price == 104.0

    def test_calculate_exit_single_row(self) -> None:
        """Exit on a single-row DataFrame returns that row's close."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("MSFT", date(2024, 6, 1), date(2024, 6, 1))

        data = pl.DataFrame(
            {"date": [date(2024, 6, 1)], "close": [250.0], "adjusted_close": [250.0], "open": [248.0], "high": [251.0], "low": [247.0]}
        )

        result = strategy.calculate_exit(data)

        assert result.price == 250.0
        assert result.date == date(2024, 6, 1)
        assert result.reason == "period_end"

    def test_calculate_exit_after_holding_days(self) -> None:
        """Data spanning past the cutoff exits at the first bar on/after start + holding_days."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 3, 31))

        # Daily bars from 2024-01-01 to 2024-02-14; cutoff is 2024-01-31
        days = [date(2024, 1, 1) + timedelta(days=i) for i in range(45)]
        data = pl.DataFrame(
            {
                "date": days,
                "close": [100.0 + i for i in range(45)],
                "adjusted_close": [100.0 + i for i in range(45)],
                "open": [100.0 + i for i in range(45)],
                "high": [101.0 + i for i in range(45)],
                "low": [99.0 + i for i in range(45)],
            }
        )

        result = strategy.calculate_exit(data)

        assert result.date == date(2024, 1, 31)
        assert result.price == 130.0
        assert result.reason == "holding_period"

    def test_calculate_exit_cutoff_on_non_trading_day(self) -> None:
        """A cutoff falling in a bar gap exits at the next available bar."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 3, 31), holding_days=10)

        # Cutoff 2024-01-11 has no bar; next bar is 2024-01-13
        data = pl.DataFrame(
            {
                "date": [date(2024, 1, 2), date(2024, 1, 5), date(2024, 1, 10), date(2024, 1, 13), date(2024, 1, 15)],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "adjusted_close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "open": [99.0, 100.0, 101.0, 102.0, 103.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [98.0, 99.0, 100.0, 101.0, 102.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert result.date == date(2024, 1, 13)
        assert result.price == 103.0
        assert result.reason == "holding_period"

    def test_calculate_exit_custom_holding_days(self) -> None:
        """A short holding_days exits early instead of at period end."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 1, 10), holding_days=5)

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(10)],
                "close": [100.0 + i for i in range(10)],
                "adjusted_close": [100.0 + i for i in range(10)],
                "open": [100.0 + i for i in range(10)],
                "high": [101.0 + i for i in range(10)],
                "low": [99.0 + i for i in range(10)],
            }
        )

        result = strategy.calculate_exit(data)

        assert result.date == date(2024, 1, 6)
        assert result.price == 105.0
        assert result.reason == "holding_period"

    def test_calculate_exit_uses_adjusted_close_not_raw_close(self) -> None:
        """A 2:1 split mid-window: the exit is priced on adjusted_close, not the raw close."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 3, 31), holding_days=10)

        # Raw close halves on 2024-01-11 (the split); adjusted_close stays on one basis.
        data = pl.DataFrame(
            {
                "date": [date(2024, 1, 2), date(2024, 1, 8), date(2024, 1, 11), date(2024, 1, 15)],
                "close": [200.0, 210.0, 105.0, 110.0],
                "adjusted_close": [100.0, 105.0, 105.0, 110.0],
                "open": [199.0, 209.0, 104.0, 109.0],
                "high": [201.0, 211.0, 106.0, 111.0],
                "low": [198.0, 208.0, 103.0, 108.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert result.date == date(2024, 1, 11)
        assert result.price == 105.0  # adjusted_close, which equals raw close only by coincidence here
        assert result.reason == "holding_period"

    def test_calculate_exit_prefers_adjusted_close_when_it_differs(self) -> None:
        """Where adjusted_close and close differ on the exit bar, the adjusted value wins."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 1, 31), holding_days=5)

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, 2), date(2024, 1, 9)],
                "close": [100.0, 200.0],
                "adjusted_close": [50.0, 96.0],
                "open": [99.0, 199.0],
                "high": [101.0, 201.0],
                "low": [98.0, 198.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert result.date == date(2024, 1, 9)
        assert result.price == 96.0
        assert result.reason == "holding_period"

    def test_calculate_exit_data_ends_before_cutoff(self) -> None:
        """Data ending before the cutoff exits at the last bar with reason period_end."""
        mock_bars_history = self.create_mock_bars_history()
        strategy = BuyAndHoldExitStrategy(mock_bars_history)
        strategy.initialize("AAPL", date(2024, 1, 1), date(2024, 1, 5))

        data = pl.DataFrame(
            {
                "date": [date(2024, 1, i + 1) for i in range(5)],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "adjusted_close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "open": [99.0, 100.0, 101.0, 102.0, 103.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [98.0, 99.0, 100.0, 101.0, 102.0],
            }
        )

        result = strategy.calculate_exit(data)

        assert result.date == date(2024, 1, 5)
        assert result.price == 104.0
        assert result.reason == "period_end"
