import pytest
import pandas as pd
from datetime import datetime
from typing import Any
from unittest.mock import Mock

from turtle.backtest.processor import SignalProcessor
from turtle.signal.models import Signal
from turtle.backtest.models import ClosedTrade, Trade
from turtle.backtest.benchmark_utils import calculate_benchmark
from turtle.exit import BuyAndHoldExitStrategy
from turtle.common.enums import TimeFrameUnit


class TestSignalProcessor:
    """Test SignalProcessor functionality."""

    @pytest.fixture
    def mock_bars_history(self) -> Mock:
        """Create a mock BarsHistoryRepo."""
        return Mock()

    @pytest.fixture
    def sample_signal(self) -> Signal:
        """Create a sample signal for testing."""
        return Signal(ticker="TEST", date=datetime(2024, 1, 15), ranking=75)

    @pytest.fixture
    def sample_ticker_data(self) -> pd.DataFrame:
        """Create sample OHLCV data for ticker."""
        dates = pd.date_range("2024-01-16", periods=10, freq="D")
        data = {
            "hdate": dates,
            "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            "high": [102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
            "close": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "volume": [1000000] * 10,
        }
        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def sample_spy_data(self) -> pd.DataFrame:
        """Create sample SPY benchmark data."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        data = {
            "open": [400.0 + i for i in range(30)],
            "high": [402.0 + i for i in range(30)],
            "low": [399.0 + i for i in range(30)],
            "close": [401.0 + i for i in range(30)],
            "volume": [1000000] * 30,
        }
        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def sample_qqq_data(self) -> pd.DataFrame:
        """Create sample QQQ benchmark data."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        data = {
            "open": [300.0 + i * 0.5 for i in range(30)],
            "high": [302.0 + i * 0.5 for i in range(30)],
            "low": [299.0 + i * 0.5 for i in range(30)],
            "close": [301.0 + i * 0.5 for i in range(30)],
            "volume": [1000000] * 30,
        }
        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def exit_strategy(self) -> Mock:
        """Create a mock exit strategy."""
        strategy = Mock(spec=BuyAndHoldExitStrategy)
        return strategy

    def test_initialization(self, mock_bars_history: Mock, exit_strategy: Mock) -> None:
        """Test SignalProcessor initialization."""
        max_holding_period = 30

        processor = SignalProcessor(
            max_holding_period=max_holding_period,
            bars_history=mock_bars_history,
            exit_strategy=exit_strategy,
            benchmark_tickers=["SPY", "QQQ"],
            time_frame_unit=TimeFrameUnit.DAY,
        )

        assert processor.max_holding_period == max_holding_period
        assert processor.bars_history == mock_bars_history
        assert processor.exit_strategy == exit_strategy
        assert processor.benchmark_tickers == ["SPY", "QQQ"]
        assert processor.time_frame_unit == TimeFrameUnit.DAY


    def test_run_without_ticker_data(self, mock_bars_history: Mock, exit_strategy: Mock, sample_signal: Signal) -> None:
        """Test that run() returns None when no ticker data is available."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Mock get_ticker_history to return empty DataFrame for ticker data
        mock_bars_history.get_ticker_history.return_value = pd.DataFrame()

        result = processor.run(sample_signal)
        assert result is None

    def test_calculate_entry_data_success(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
        sample_ticker_data: pd.DataFrame,
    ) -> None:
        """Test successful entry data calculation."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Mock get_ticker_history to return sample data
        mock_bars_history.get_ticker_history.return_value = sample_ticker_data

        entry = processor.calculate_entry_data(sample_signal)

        assert entry is not None
        assert entry.date == pd.Timestamp(datetime(2024, 1, 16))
        assert entry.price == 100.0
        assert entry.reason == "next_day_open"

    def test_calculate_entry_data_no_data(self, mock_bars_history: Mock, exit_strategy: Mock, sample_signal: Signal) -> None:
        """Test entry data calculation when no data available."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Mock get_ticker_history to return empty DataFrame
        mock_bars_history.get_ticker_history.return_value = pd.DataFrame()

        result = processor.calculate_entry_data(sample_signal)
        assert result is None

    def test_calculate_entry_data_invalid_price(self, mock_bars_history: Mock, exit_strategy: Mock, sample_signal: Signal) -> None:
        """Test entry data calculation with invalid opening price."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Create data with invalid opening price
        dates = pd.date_range("2024-01-16", periods=1, freq="D")
        invalid_data = pd.DataFrame(
            {
                "open": [0.0],  # Invalid price
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=dates,
        )

        mock_bars_history.get_ticker_history.return_value = invalid_data

        with pytest.raises(ValueError, match="Invalid entry price"):
            processor.calculate_entry_data(sample_signal)

    def test_calculate_exit_data_success(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
        sample_ticker_data: pd.DataFrame,
    ) -> None:
        """Test successful exit data calculation."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Mock the exit strategy to return a result
        mock_result = Trade(ticker="AAPL", date=datetime(2024, 1, 20), price=105.0, reason="period_end")
        exit_strategy.calculate_exit.return_value = mock_result
        mock_bars_history.get_ticker_history.return_value = sample_ticker_data

        entry_date = datetime(2024, 1, 16)
        entry_price = 100.0

        exit = processor.calculate_exit_data(sample_signal, entry_date, entry_price)

        assert exit.date == datetime(2024, 1, 20)
        assert exit.price == 105.0
        assert exit.reason == "period_end"

    def test_calculate_exit_data_strategy_fails(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
        sample_ticker_data: pd.DataFrame,
    ) -> None:
        """Test exit data calculation when strategy fails."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Mock strategy to return None
        exit_strategy.calculate_exit.return_value = None
        mock_bars_history.get_ticker_history.return_value = sample_ticker_data

        entry_date = datetime(2024, 1, 16)
        entry_price = 100.0

        with pytest.raises(ValueError, match="Exit strategy failed"):
            processor.calculate_exit_data(sample_signal, entry_date, entry_price)

    def test_calculate_return_pct(self, mock_bars_history: Mock, exit_strategy: Mock) -> None:
        """Test return percentage calculation."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Test positive return
        return_pct = processor._calculate_return_pct(100.0, 105.0)
        assert return_pct == 5.0

        # Test negative return
        return_pct = processor._calculate_return_pct(100.0, 95.0)
        assert return_pct == -5.0

        # Test zero return
        return_pct = processor._calculate_return_pct(100.0, 100.0)
        assert return_pct == 0.0

    def test_calculate_return_pct_invalid_entry_price(self, mock_bars_history: Mock, exit_strategy: Mock) -> None:
        """Test return percentage calculation with invalid entry price."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        with pytest.raises(ValueError, match="Invalid entry price"):
            processor._calculate_return_pct(0.0, 105.0)

    def test_calculate_single_benchmark_return_success(
        self,
        sample_spy_data: pd.DataFrame,
    ) -> None:
        """Test single benchmark return calculation."""
        entry_date = datetime(2024, 1, 16)
        exit_date = datetime(2024, 1, 20)

        benchmark = calculate_benchmark(sample_spy_data, "SPY", entry_date, exit_date)

        # Entry price should be open on 2024-01-16 (index 15): 415.0
        # Exit price should be close on 2024-01-20 (index 19): 420.0
        # Return: ((420 - 415) / 415) * 100 = ~1.20%
        assert benchmark is not None
        assert benchmark.ticker == "SPY"
        assert abs(benchmark.return_pct - 1.2048192771084338) < 0.01

    def test_calculate_single_benchmark_return_empty_data(self) -> None:
        """Test benchmark return calculation with empty data."""
        empty_df = pd.DataFrame()
        benchmark = calculate_benchmark(empty_df, "SPY", datetime(2024, 1, 16), datetime(2024, 1, 20))

        assert benchmark is None

    def test_calculate_benchmark_returns(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_spy_data: pd.DataFrame,
        sample_qqq_data: pd.DataFrame,
    ) -> None:
        """Test calculation of both benchmark returns."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Mock the get_ticker_history calls for benchmark data
        def mock_get_ticker_history(ticker: str, start: datetime, end: datetime, timeframe: TimeFrameUnit) -> pd.DataFrame:
            if ticker == "SPY":
                return sample_spy_data
            elif ticker == "QQQ":
                return sample_qqq_data
            return pd.DataFrame()

        mock_bars_history.get_ticker_history.side_effect = mock_get_ticker_history

        entry_date = datetime(2024, 1, 16)
        exit_date = datetime(2024, 1, 20)

        benchmarks = processor._calculate_benchmark_returns(entry_date, exit_date)

        assert isinstance(benchmarks, list)
        assert len(benchmarks) == 2

        # Check QQQ benchmark
        qqq_benchmark = next(b for b in benchmarks if b.ticker == "QQQ")
        assert isinstance(qqq_benchmark.return_pct, float)
        assert qqq_benchmark.return_pct > 0  # Should be positive given our sample data trend

        # Check SPY benchmark
        spy_benchmark = next(b for b in benchmarks if b.ticker == "SPY")
        assert isinstance(spy_benchmark.return_pct, float)
        assert spy_benchmark.return_pct > 0  # Should be positive given our sample data trend

    def test_run_full_integration(
        self,
        mock_bars_history: Mock,
        sample_signal: Signal,
        sample_ticker_data: pd.DataFrame,
        sample_spy_data: pd.DataFrame,
        sample_qqq_data: pd.DataFrame,
    ) -> None:
        """Test full run() method integration."""
        exit_strategy = BuyAndHoldExitStrategy(mock_bars_history)

        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        # Setup mock data
        def mock_get_ticker_history(
            ticker: str, start: datetime, end: datetime, timeframe: TimeFrameUnit | None = None, **kwargs: Any
        ) -> pd.DataFrame:
            if ticker == "TEST":
                return sample_ticker_data
            elif ticker == "SPY":
                return sample_spy_data
            elif ticker == "QQQ":
                return sample_qqq_data
            return pd.DataFrame()

        mock_bars_history.get_ticker_history.side_effect = mock_get_ticker_history

        # Run the processor (benchmarks will be initialized automatically)
        result = processor.run(sample_signal)

        # Verify result structure
        assert isinstance(result, ClosedTrade)
        assert result.signal == sample_signal
        assert isinstance(result.entry, Trade)
        assert isinstance(result.exit, Trade)
        assert isinstance(result.realized_pct, float)
        assert isinstance(result.benchmark_list, list)
        assert len(result.benchmark_list) == 2

        # Verify benchmark structure
        tickers = {b.ticker for b in result.benchmark_list}
        assert tickers == {"QQQ", "SPY"}
        for benchmark in result.benchmark_list:
            assert isinstance(benchmark.return_pct, float)

        # Verify some basic constraints
        assert result.entry.price > 0
        assert result.exit.price > 0
        assert result.entry.date >= pd.Timestamp(sample_signal.date)

        # Verify holding_days property
        expected_holding_days = (result.exit.date - result.entry.date).days
        assert result.holding_days == expected_holding_days
        assert isinstance(result.holding_days, int)
        assert result.holding_days >= 0


class TestSignalProcessorEdgeCases:
    """Test edge cases and error scenarios."""

    def test_weekend_entry_date(self) -> None:
        """Test signal processing when signal date is on weekend."""
        # This would test that we correctly find next trading day
        # Implementation would depend on how your data handles weekends
        pass

    def test_holiday_entry_date(self) -> None:
        """Test signal processing around market holidays."""
        # This would test handling of market holidays
        # Implementation would depend on your data source
        pass

    def test_missing_benchmark_data_partial(self) -> None:
        """Test when only one benchmark has data."""
        # This would test graceful handling when SPY or QQQ data is missing
        pass

    def test_extreme_date_ranges(self) -> None:
        """Test with edge case date ranges."""
        # Test very short date ranges, future dates, etc.
        pass
