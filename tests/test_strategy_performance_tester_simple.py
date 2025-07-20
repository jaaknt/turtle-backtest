import pytest
import pandas as pd
from datetime import datetime

from turtle.tester.strategy_performance import StrategyPerformanceTester
from turtle.tester.period_return import BuyAndHoldStrategy, ProfitLossTargetStrategy, EMAExitStrategy
from turtle.tester.models import SignalResult


class TestStrategyPerformanceTesterBasic:
    """Test basic functionality of StrategyPerformanceTester with period return strategies."""
    
    def test_initialization_with_default_strategy(self):
        """Test that StrategyPerformanceTester initializes with default BuyAndHoldStrategy."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7)]
        
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods
        )
        
        assert isinstance(tester.period_return_strategy, BuyAndHoldStrategy)
        assert tester.period_return_strategy_kwargs == {}
        
    def test_initialization_with_custom_strategy(self):
        """Test initialization with custom PeriodReturnStrategy."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7)]
        
        custom_period_strategy = ProfitLossTargetStrategy(profit_target=15.0, stop_loss=8.0)
        
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods,
            period_return_strategy=custom_period_strategy
        )
        
        assert isinstance(tester.period_return_strategy, ProfitLossTargetStrategy)
        assert tester.period_return_strategy.profit_target == 15.0
        assert tester.period_return_strategy.stop_loss == 8.0
        
    def test_initialization_with_ema_strategy(self):
        """Test initialization with EMAExitStrategy."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7)]
        
        custom_period_strategy = EMAExitStrategy(ema_period=25)
        
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods,
            period_return_strategy=custom_period_strategy
        )
        
        assert isinstance(tester.period_return_strategy, EMAExitStrategy)
        assert tester.period_return_strategy.ema_period == 25
        
    def test_period_return_strategy_kwargs(self):
        """Test that strategy kwargs are stored correctly."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7)]
        
        kwargs = {'profit_target': 20.0, 'stop_loss': 5.0}
        
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods,
            period_return_strategy_kwargs=kwargs
        )
        
        assert tester.period_return_strategy_kwargs == kwargs
        
    def test_calculate_signal_return_with_period_data(self):
        """Test _calculate_signal_return method with period data."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7)]
        
        period_strategy = ProfitLossTargetStrategy(profit_target=10.0, stop_loss=5.0)
        
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods,
            period_return_strategy=period_strategy
        )
        
        # Create sample period data where profit target is hit
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        prices = [100, 105, 115, 120, 125, 130, 135, 140, 145, 150]  # Rising trend
        data = {
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * 10
        }
        period_df = pd.DataFrame(data, index=dates)
        
        # Create signal result with period data
        signal_result = SignalResult(
            ticker='TEST',
            signal_date=datetime(2024, 1, 1),
            entry_price=100.0,
            entry_date=datetime(2024, 1, 1),
            period_results={'1W': 120.0},  # Legacy result
            ranking=75,
            period_data={'1W': {'target_date': datetime(2024, 1, 8), 'data': period_df}}
        )
        
        # Calculate return using the profit/loss strategy
        return_pct = tester._calculate_signal_return(signal_result, '1W')
        
        assert return_pct is not None
        # Should exit early due to profit target (115 = 15% gain > 10% target)
        assert return_pct >= 10.0
        # Should be around 15% since profit target triggers at 115
        assert abs(return_pct - 15.0) < 1.0
        
    def test_calculate_signal_return_fallback_to_legacy(self):
        """Test fallback to SignalResult method when no period data."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7)]
        
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods
        )
        
        # Create signal result without period data (legacy format)
        signal_result = SignalResult(
            ticker='TEST',
            signal_date=datetime(2024, 1, 1),
            entry_price=100.0,
            entry_date=datetime(2024, 1, 5),
            period_results={'1W': 115.0},  # Legacy closing price
            ranking=75,
            period_data=None  # No period data - should fallback
        )
        
        # Should fall back to legacy calculation
        return_pct = tester._calculate_signal_return(signal_result, '1W')
        
        assert return_pct is not None
        assert return_pct == 15.0  # (115 - 100) / 100 * 100
        
    def test_backward_compatibility(self):
        """Test that existing code patterns still work."""
        from unittest.mock import Mock
        
        mock_strategy = Mock()
        mock_bars_history = Mock()
        test_periods = [pd.Timedelta(days=7), pd.Timedelta(days=14)]
        
        # Old way - no period return strategy specified
        tester = StrategyPerformanceTester(
            strategy=mock_strategy,
            bars_history=mock_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            test_periods=test_periods
        )
        
        # Should default to BuyAndHoldStrategy
        assert isinstance(tester.period_return_strategy, BuyAndHoldStrategy)
        
        # Should have empty kwargs
        assert tester.period_return_strategy_kwargs == {}
        
        # Should have the same basic attributes as before
        assert tester.strategy == mock_strategy
        assert tester.bars_history == mock_bars_history
        assert tester.test_periods == test_periods


class TestStrategyComparison:
    """Test that different strategies produce different results."""
    
    def test_different_strategies_different_behaviors(self):
        """Test that different period return strategies have different characteristics."""
        
        # Create test data where strategies would behave differently
        dates = pd.date_range('2024-01-01', periods=15, freq='D')
        # Volatile data: drop, then recover
        prices = [100, 95, 90, 85, 95, 105, 115, 125, 135, 145, 150, 155, 160, 165, 170]
        data = {
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * 15
        }
        test_df = pd.DataFrame(data, index=dates)
        
        # Test different strategies
        buy_hold = BuyAndHoldStrategy()
        profit_loss = ProfitLossTargetStrategy(profit_target=10.0, stop_loss=10.0)
        
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 15)
        
        # Calculate returns with different strategies
        buy_hold_result = buy_hold.calculate_return(test_df, entry_price, entry_date, target_date)
        profit_loss_result = profit_loss.calculate_return(test_df, entry_price, entry_date, target_date)
        
        # Both should return valid results
        assert buy_hold_result is not None
        assert profit_loss_result is not None
        
        # They should have different exit reasons
        assert buy_hold_result.exit_reason == 'period_end'
        # Profit/loss should trigger stop loss due to early drop to 85 (-15%)
        assert profit_loss_result.exit_reason == 'stop_loss'
        
        # Returns should be different
        assert buy_hold_result.return_pct != profit_loss_result.return_pct
        
        # Buy and hold should have higher return (buys at 100, sells at 170 = +70%)
        # Profit/loss should have negative return (buys at 100, sells at 85 = -15%)
        assert buy_hold_result.return_pct > profit_loss_result.return_pct
        assert profit_loss_result.return_pct < 0


if __name__ == "__main__":
    pytest.main([__file__])