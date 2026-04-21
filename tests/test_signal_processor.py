from datetime import date, datetime, timedelta
from turtle.backtest.benchmark_utils import calculate_benchmark
from turtle.backtest.processor import SignalProcessor
from turtle.common.enums import TimeFrameUnit
from turtle.model import FutureTrade, Signal, Trade
from turtle.strategy.exit import BuyAndHoldExitStrategy
from typing import Any
from unittest.mock import Mock

import polars as pl
import pytest


class TestSignalProcessor:
    """Test SignalProcessor functionality."""

    @pytest.fixture
    def mock_bars_history(self) -> Mock:
        """Create a mock bars history repo."""
        return Mock()

    @pytest.fixture
    def sample_signal(self) -> Signal:
        """Create a sample signal for testing."""
        return Signal(ticker="TEST", date=datetime(2024, 1, 15), ranking=75)

    @pytest.fixture
    def sample_ticker_data(self) -> pl.DataFrame:
        """Create sample OHLCV data for ticker."""
        dates = [date(2024, 1, 16) + timedelta(days=i) for i in range(10)]
        return pl.DataFrame(
            {
                "date": dates,
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
                "volume": [1000000] * 10,
            }
        )

    @pytest.fixture
    def sample_spy_data(self) -> pl.DataFrame:
        """Create sample SPY benchmark data."""
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(30)]
        return pl.DataFrame(
            {
                "date": dates,
                "open": [400.0 + i for i in range(30)],
                "high": [402.0 + i for i in range(30)],
                "low": [399.0 + i for i in range(30)],
                "close": [401.0 + i for i in range(30)],
                "volume": [1000000] * 30,
            }
        )

    @pytest.fixture
    def sample_qqq_data(self) -> pl.DataFrame:
        """Create sample QQQ benchmark data."""
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(30)]
        return pl.DataFrame(
            {
                "date": dates,
                "open": [300.0 + i * 0.5 for i in range(30)],
                "high": [302.0 + i * 0.5 for i in range(30)],
                "low": [299.0 + i * 0.5 for i in range(30)],
                "close": [301.0 + i * 0.5 for i in range(30)],
                "volume": [1000000] * 30,
            }
        )

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

        mock_bars_history.get_bars_pl.return_value = pl.DataFrame()

        result = processor.run(sample_signal)
        assert result is None

    def test_calculate_entry_data_success(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
        sample_ticker_data: pl.DataFrame,
    ) -> None:
        """Test successful entry data calculation."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        mock_bars_history.get_bars_pl.return_value = sample_ticker_data

        entry = processor.calculate_entry_data(sample_signal)

        assert entry is not None
        assert entry.date == datetime(2024, 1, 16)
        assert entry.price == 100.0
        assert entry.reason == "next_day_open"

    def test_calculate_entry_data_no_data(self, mock_bars_history: Mock, exit_strategy: Mock, sample_signal: Signal) -> None:
        """Test entry data calculation when no data available."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        mock_bars_history.get_bars_pl.return_value = pl.DataFrame()

        result = processor.calculate_entry_data(sample_signal)
        assert result is None

    def test_calculate_entry_data_invalid_price(self, mock_bars_history: Mock, exit_strategy: Mock, sample_signal: Signal) -> None:
        """Test entry data calculation with invalid opening price."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        invalid_data = pl.DataFrame(
            {
                "date": [date(2024, 1, 16)],
                "open": [0.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            }
        )

        mock_bars_history.get_bars_pl.return_value = invalid_data

        with pytest.raises(ValueError, match="Invalid entry price"):
            processor.calculate_entry_data(sample_signal)

    def test_calculate_exit_data_success(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
        sample_ticker_data: pl.DataFrame,
    ) -> None:
        """Test successful exit data calculation."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        mock_result = Trade(ticker="AAPL", date=datetime(2024, 1, 20), price=105.0, reason="period_end")
        exit_strategy.calculate_exit.return_value = mock_result
        mock_bars_history.get_bars_pl.return_value = sample_ticker_data

        entry_date = datetime(2024, 1, 16)
        entry_price = 100.0

        exit = processor.calculate_exit_data(sample_signal, entry_date, entry_price)

        assert exit.date == datetime(2024, 1, 20)
        assert exit.price == 105.0
        assert exit.reason == "period_end"

    def test_calculate_exit_data_no_historical_data(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
    ) -> None:
        """Test exit data calculation when get_bars_pl returns empty DataFrame."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        mock_bars_history.get_bars_pl.return_value = pl.DataFrame()

        with pytest.raises(ValueError, match="No historical data available"):
            processor.calculate_exit_data(sample_signal, datetime(2024, 1, 16), 100.0)

    def test_calculate_benchmark_empty_after_entry_filter(self) -> None:
        """Test benchmark returns None when all data precedes entry date."""
        past_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(10)]
        past_df = pl.DataFrame(
            {
                "date": past_dates,
                "open": [400.0 + i for i in range(10)],
                "high": [402.0 + i for i in range(10)],
                "low": [399.0 + i for i in range(10)],
                "close": [401.0 + i for i in range(10)],
                "volume": [1000000] * 10,
            }
        )
        result = calculate_benchmark(past_df, "SPY", datetime(2024, 2, 1), datetime(2024, 2, 5))
        assert result is None

    def test_calculate_benchmark_empty_after_exit_filter(self) -> None:
        """Test benchmark returns None when all data follows exit date."""
        future_dates = [date(2024, 3, 1) + timedelta(days=i) for i in range(10)]
        future_df = pl.DataFrame(
            {
                "date": future_dates,
                "open": [400.0 + i for i in range(10)],
                "high": [402.0 + i for i in range(10)],
                "low": [399.0 + i for i in range(10)],
                "close": [401.0 + i for i in range(10)],
                "volume": [1000000] * 10,
            }
        )
        result = calculate_benchmark(future_df, "SPY", datetime(2024, 1, 1), datetime(2024, 1, 10))
        assert result is None

    def test_calculate_exit_data_strategy_fails(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_signal: Signal,
        sample_ticker_data: pl.DataFrame,
    ) -> None:
        """Test exit data calculation when strategy fails."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        exit_strategy.calculate_exit.return_value = None
        mock_bars_history.get_bars_pl.return_value = sample_ticker_data

        entry_date = datetime(2024, 1, 16)
        entry_price = 100.0

        with pytest.raises(ValueError, match="Exit strategy failed"):
            processor.calculate_exit_data(sample_signal, entry_date, entry_price)

    def test_calculate_return_pct(self, mock_bars_history: Mock, exit_strategy: Mock) -> None:
        """Test return percentage calculation."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        assert processor._calculate_return_pct(100.0, 105.0) == 5.0
        assert processor._calculate_return_pct(100.0, 95.0) == -5.0
        assert processor._calculate_return_pct(100.0, 100.0) == 0.0

    def test_calculate_return_pct_invalid_entry_price(self, mock_bars_history: Mock, exit_strategy: Mock) -> None:
        """Test return percentage calculation with invalid entry price."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        with pytest.raises(ValueError, match="Invalid entry price"):
            processor._calculate_return_pct(0.0, 105.0)

    def test_calculate_single_benchmark_return_success(
        self,
        sample_spy_data: pl.DataFrame,
    ) -> None:
        """Test single benchmark return calculation."""
        entry_date = datetime(2024, 1, 16)
        exit_date = datetime(2024, 1, 20)

        benchmark = calculate_benchmark(sample_spy_data, "SPY", entry_date, exit_date)

        # Entry price: open on 2024-01-16 (index 15): 415.0
        # Exit price: close on 2024-01-20 (index 19): 420.0
        # Return: ((420 - 415) / 415) * 100 = ~1.20%
        assert benchmark is not None
        assert benchmark.ticker == "SPY"
        assert abs(benchmark.return_pct - 1.2048192771084338) < 0.01

    def test_calculate_single_benchmark_return_empty_data(self) -> None:
        """Test benchmark return calculation with empty data."""
        benchmark = calculate_benchmark(pl.DataFrame(), "SPY", datetime(2024, 1, 16), datetime(2024, 1, 20))

        assert benchmark is None

    def test_calculate_benchmark_returns(
        self,
        mock_bars_history: Mock,
        exit_strategy: Mock,
        sample_spy_data: pl.DataFrame,
        sample_qqq_data: pl.DataFrame,
    ) -> None:
        """Test calculation of both benchmark returns."""
        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        def mock_get_bars_pl(ticker: str, start: Any, end: Any, timeframe: Any = None) -> pl.DataFrame:
            if ticker == "SPY":
                return sample_spy_data
            elif ticker == "QQQ":
                return sample_qqq_data
            return pl.DataFrame()

        mock_bars_history.get_bars_pl.side_effect = mock_get_bars_pl

        entry_date = datetime(2024, 1, 16)
        exit_date = datetime(2024, 1, 20)

        benchmarks = processor._calculate_benchmark_returns(entry_date, exit_date)

        assert isinstance(benchmarks, list)
        assert len(benchmarks) == 2

        qqq_benchmark = next(b for b in benchmarks if b.ticker == "QQQ")
        assert isinstance(qqq_benchmark.return_pct, float)
        assert qqq_benchmark.return_pct > 0

        spy_benchmark = next(b for b in benchmarks if b.ticker == "SPY")
        assert isinstance(spy_benchmark.return_pct, float)
        assert spy_benchmark.return_pct > 0

    def test_run_full_integration(
        self,
        mock_bars_history: Mock,
        sample_signal: Signal,
        sample_spy_data: pl.DataFrame,
        sample_qqq_data: pl.DataFrame,
    ) -> None:
        """Test full run() method integration."""
        exit_strategy = BuyAndHoldExitStrategy(mock_bars_history)

        processor = SignalProcessor(
            max_holding_period=30, bars_history=mock_bars_history, exit_strategy=exit_strategy, benchmark_tickers=["SPY", "QQQ"]
        )

        ticker_data = pl.DataFrame(
            {
                "date": [date(2024, 1, 16) + timedelta(days=i) for i in range(10)],
                "open": [100.0 + i for i in range(10)],
                "high": [102.0 + i for i in range(10)],
                "low": [99.0 + i for i in range(10)],
                "close": [101.0 + i for i in range(10)],
                "volume": [1000000] * 10,
            }
        )

        def mock_get_bars_pl(ticker: str, start: Any, end: Any, timeframe: Any = None, **kwargs: Any) -> pl.DataFrame:
            if ticker == "TEST":
                return ticker_data
            elif ticker == "SPY":
                return sample_spy_data
            elif ticker == "QQQ":
                return sample_qqq_data
            return pl.DataFrame()

        mock_bars_history.get_bars_pl.side_effect = mock_get_bars_pl

        result = processor.run(sample_signal)

        assert isinstance(result, FutureTrade)
        assert result.signal == sample_signal
        assert isinstance(result.entry, Trade)
        assert isinstance(result.exit, Trade)
        assert isinstance(result.realized_pct, float)
        assert isinstance(result.benchmark_list, list)
        assert len(result.benchmark_list) == 2

        tickers = {b.ticker for b in result.benchmark_list}
        assert tickers == {"QQQ", "SPY"}
        for benchmark in result.benchmark_list:
            assert isinstance(benchmark.return_pct, float)

        assert result.entry.price > 0
        assert result.exit.price > 0
        assert result.entry.date >= sample_signal.date

        expected_holding_days = (result.exit.date - result.entry.date).days
        assert result.holding_days == expected_holding_days
        assert isinstance(result.holding_days, int)
        assert result.holding_days >= 0


