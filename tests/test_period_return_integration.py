import pytest
import pandas as pd
from datetime import datetime
from turtle.backtest.models import LegacySignalResult
from turtle.backtest.period_return import PeriodReturnResult


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    data = {
        'open': [100 + i * 0.5 for i in range(30)],
        'high': [102 + i * 0.5 for i in range(30)],
        'low': [98 + i * 0.5 for i in range(30)],
        'close': [101 + i * 0.5 for i in range(30)],
        'volume': [1000000] * 30
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def signal_result_with_period_data(sample_ohlcv_data: pd.DataFrame) -> LegacySignalResult:
    """Create a LegacySignalResult with period data for testing."""
    entry_date = datetime(2024, 1, 5)
    target_date = datetime(2024, 1, 15)

    period_data = {
        '1W': {
            'target_date': target_date,
            'data': sample_ohlcv_data
        }
    }

    return LegacySignalResult(
        ticker='TEST',
        signal_date=datetime(2024, 1, 4),
        entry_price=102.5,
        entry_date=entry_date,
        period_results={'1W': 107.0},  # Legacy closing price
        ranking=75,
        period_data=period_data
    )


@pytest.fixture
def legacy_signal_result() -> LegacySignalResult:
    """Create a legacy LegacySignalResult without period data."""
    return LegacySignalResult(
        ticker='TEST',
        signal_date=datetime(2024, 1, 4),
        entry_price=102.5,
        entry_date=datetime(2024, 1, 5),
        period_results={'1W': 107.0},  # Legacy closing price
        ranking=75,
        period_data=None  # No period data - should fall back to legacy
    )


class TestPeriodReturnIntegration:

    def test_signal_result_with_buy_and_hold_strategy(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test LegacySignalResult with new buy_and_hold strategy."""
        return_pct = signal_result_with_period_data.get_return_for_period('1W', 'buy_and_hold')

        assert return_pct is not None
        assert isinstance(return_pct, float)
        assert return_pct > 0  # Should be positive due to increasing prices

    def test_signal_result_with_profit_loss_target_strategy(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test LegacySignalResult with profit_loss_target strategy."""
        return_pct = signal_result_with_period_data.get_return_for_period(
            '1W', 'profit_loss_target', profit_target=5.0, stop_loss=3.0
        )

        assert return_pct is not None
        assert isinstance(return_pct, float)

    def test_signal_result_with_ema_exit_strategy(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test LegacySignalResult with ema_exit strategy."""
        return_pct = signal_result_with_period_data.get_return_for_period(
            '1W', 'ema_exit', ema_period=5
        )

        assert return_pct is not None
        assert isinstance(return_pct, float)

    def test_signal_result_detailed_result(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test getting detailed period return result."""
        result = signal_result_with_period_data.get_return_result_for_period('1W', 'buy_and_hold')

        assert result is not None
        assert isinstance(result, PeriodReturnResult)
        assert result.exit_reason == 'period_end'
        assert isinstance(result.return_pct, float)
        assert isinstance(result.exit_price, float)
        assert isinstance(result.exit_date, datetime)

    def test_legacy_fallback(self, legacy_signal_result: LegacySignalResult) -> None:
        """Test backward compatibility with legacy LegacySignalResult."""
        return_pct = legacy_signal_result.get_return_for_period('1W', 'buy_and_hold')

        assert return_pct is not None
        # Should fall back to legacy calculation: ((107.0 - 102.5) / 102.5) * 100
        expected = ((107.0 - 102.5) / 102.5) * 100
        assert abs(return_pct - expected) < 0.001

    def test_strategy_comparison(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Compare returns between different strategies."""
        buy_hold_return = signal_result_with_period_data.get_return_for_period('1W', 'buy_and_hold')
        profit_loss_return = signal_result_with_period_data.get_return_for_period(
            '1W', 'profit_loss_target', profit_target=10.0, stop_loss=5.0
        )
        ema_return = signal_result_with_period_data.get_return_for_period(
            '1W', 'ema_exit', ema_period=5
        )

        # All should return valid numbers
        assert all(r is not None for r in [buy_hold_return, profit_loss_return, ema_return])
        assert all(isinstance(r, float) for r in [buy_hold_return, profit_loss_return, ema_return])

    def test_invalid_strategy_name(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test handling of invalid strategy name."""
        return_pct = signal_result_with_period_data.get_return_for_period('1W', 'invalid_strategy')

        # Should fall back to legacy calculation
        assert return_pct is not None
        expected = ((107.0 - 102.5) / 102.5) * 100
        assert abs(return_pct - expected) < 0.001

    def test_missing_period_data(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test when requested period is not available."""
        return_pct = signal_result_with_period_data.get_return_for_period('2W', 'buy_and_hold')

        # Should return None since '2W' period data doesn't exist
        assert return_pct is None


class TestBackwardCompatibility:

    def test_default_strategy_parameter(self, signal_result_with_period_data: LegacySignalResult) -> None:
        """Test that default strategy is buy_and_hold."""
        return_pct = signal_result_with_period_data.get_return_for_period('1W')

        assert return_pct is not None
        assert isinstance(return_pct, float)

    def test_legacy_method_signature(self, legacy_signal_result: LegacySignalResult) -> None:
        """Test that legacy method signature still works."""
        # This should work without specifying strategy
        return_pct = legacy_signal_result.get_return_for_period('1W')

        assert return_pct is not None
        expected = ((107.0 - 102.5) / 102.5) * 100
        assert abs(return_pct - expected) < 0.001


class TestStrategyDemonstration:
    """Demonstrate the different strategies working."""

    def test_profit_target_vs_buy_hold(self) -> None:
        """Demonstrate profit target strategy vs buy and hold."""
        # Create data that hits profit target early
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        data = {
            'open': [100] + [110] * 19,  # Big jump on day 2
            'high': [102] + [112] * 19,
            'low': [98] + [108] * 19,
            'close': [101] + [111] * 19,  # 10% gain on day 2
            'volume': [1000000] * 20
        }
        df = pd.DataFrame(data, index=dates)

        signal_result = LegacySignalResult(
            ticker='DEMO',
            signal_date=datetime(2024, 1, 1),
            entry_price=100.0,
            entry_date=datetime(2024, 1, 1),
            period_results={'2W': 111.0},
            ranking=80,
            period_data={'2W': {'target_date': datetime(2024, 1, 15), 'data': df}}
        )

        # Buy and hold would hold for full period
        buy_hold_return = signal_result.get_return_for_period('2W', 'buy_and_hold')

        # Profit target should exit early at 10% gain
        profit_target_return = signal_result.get_return_for_period(
            '2W', 'profit_loss_target', profit_target=10.0, stop_loss=5.0
        )

        # Get detailed results
        buy_hold_result = signal_result.get_return_result_for_period('2W', 'buy_and_hold')
        profit_target_result = signal_result.get_return_result_for_period(
            '2W', 'profit_loss_target', profit_target=10.0, stop_loss=5.0
        )

        assert buy_hold_return is not None
        assert profit_target_return is not None

        # Both should have positive returns
        assert buy_hold_return > 0
        assert profit_target_return >= 10.0  # Should hit profit target

        # Profit target should exit earlier
        assert profit_target_result is not None
        assert buy_hold_result is not None
        assert profit_target_result.exit_reason == 'profit_target'
        assert buy_hold_result.exit_reason == 'period_end'
        assert profit_target_result.exit_date < buy_hold_result.exit_date
