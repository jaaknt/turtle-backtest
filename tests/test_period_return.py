import pytest
import pandas as pd
from datetime import datetime, timedelta
from turtle.performance.period_return import (
    PeriodReturn, 
    BuyAndHoldStrategy, 
    ProfitLossTargetStrategy, 
    EMAExitStrategy,
    PeriodReturnResult
)


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    data = {
        'open': [100 + i * 0.5 for i in range(30)],
        'high': [102 + i * 0.5 for i in range(30)],
        'low': [98 + i * 0.5 for i in range(30)],
        'close': [101 + i * 0.5 for i in range(30)],
        'volume': [1000000] * 30,
        'ema_20': [99 + i * 0.3 for i in range(30)],  # EMA trending up but below close
        'ema_5': [100 + i * 0.4 for i in range(30)],   # Short EMA
        'ema_50': [98 + i * 0.2 for i in range(30)]    # Long EMA
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def declining_data():
    """Create sample declining OHLCV data for testing stop loss."""
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    data = {
        'open': [100 - i * 2 for i in range(20)],
        'high': [102 - i * 2 for i in range(20)],
        'low': [98 - i * 2 for i in range(20)],
        'close': [101 - i * 2 for i in range(20)],
        'volume': [1000000] * 20
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def volatile_data():
    """Create volatile data that goes above EMA then below."""
    dates = pd.date_range('2024-01-01', periods=40, freq='D')
    # Start high, then decline below EMA
    prices = [100] * 25 + [95] * 15  # Drop below EMA after day 25
    data = {
        'open': prices,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'close': prices,
        'volume': [1000000] * 40,
        'ema_20': [98] * 40,  # EMA below close for first 25 days, above for last 15
        'ema_5': [99] * 40,   # Short-term EMA
        'ema_50': [97] * 40   # Long-term EMA
    }
    return pd.DataFrame(data, index=dates)


class TestBuyAndHoldStrategy:
    
    def test_calculate_return_basic(self, sample_data):
        """Test basic buy and hold return calculation."""
        strategy = BuyAndHoldStrategy()
        entry_price = 100.0
        entry_date = datetime(2024, 1, 5)
        target_date = datetime(2024, 1, 15)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert isinstance(result, PeriodReturnResult)
        assert result.exit_reason == 'period_end'
        assert result.return_pct > 0  # Should be positive due to increasing prices
        
    def test_calculate_return_no_data(self, sample_data):
        """Test when no data is available."""
        strategy = BuyAndHoldStrategy()
        entry_price = 100.0
        entry_date = datetime(2025, 1, 1)  # Future date
        target_date = datetime(2025, 1, 15)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert result is None


class TestProfitLossTargetStrategy:
    
    def test_profit_target_hit(self, sample_data):
        """Test when profit target is reached."""
        strategy = ProfitLossTargetStrategy(profit_target=5.0, stop_loss=10.0)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 30)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'profit_target'
        assert result.return_pct >= 5.0
        
    def test_stop_loss_hit(self, declining_data):
        """Test when stop loss is triggered."""
        strategy = ProfitLossTargetStrategy(profit_target=20.0, stop_loss=5.0)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 20)
        
        result = strategy.calculate_return(declining_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'stop_loss'
        assert result.return_pct <= -5.0
        
    def test_period_end_no_trigger(self, sample_data):
        """Test when neither profit nor loss target is hit."""
        strategy = ProfitLossTargetStrategy(profit_target=50.0, stop_loss=50.0)  # Very high thresholds
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 10)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'period_end'
        
    def test_stop_loss_before_profit_target(self):
        """Test when stop loss is hit before profit target by date."""
        # Create data where stop loss happens first, then profit
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        prices = [100, 95, 90, 85, 115, 120, 125, 130, 135, 140]  # Drop first, then rise
        data = {
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * 10
        }
        df = pd.DataFrame(data, index=dates)
        
        strategy = ProfitLossTargetStrategy(profit_target=10.0, stop_loss=10.0)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 10)
        
        result = strategy.calculate_return(df, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'stop_loss'
        assert result.return_pct <= -10.0
        # Should exit on day when 90 hit (10% loss = 10% stop loss)
        assert result.exit_date.day == 3  # 2024-01-03
        
    def test_profit_target_before_stop_loss(self):
        """Test when profit target is hit before stop loss by date."""
        # Create data where profit happens first, then loss would happen
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        prices = [100, 105, 115, 120, 80, 70, 60, 50, 40, 30]  # Rise first, then fall
        data = {
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * 10
        }
        df = pd.DataFrame(data, index=dates)
        
        strategy = ProfitLossTargetStrategy(profit_target=10.0, stop_loss=10.0)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 10)
        
        result = strategy.calculate_return(df, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'profit_target'
        assert result.return_pct >= 10.0
        # Should exit on day when 115 hit (15% gain > 10% profit target)
        assert result.exit_date.day == 3  # 2024-01-03
        
    def test_both_targets_same_day(self):
        """Test when both targets could be hit on the same day - first one chronologically wins."""
        # Create data where both profit and loss targets are hit on same day
        # We'll use intraday scenario: price drops early (hitting stop loss), then recovers (hitting profit)
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        # Day 1: price goes from 100 to 89 (11% loss - hits stop loss)
        # Day 2: price goes to 112 (12% gain - would hit profit, but stop loss already triggered)
        prices = [100, 89, 112, 115, 120]
        data = {
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * 5
        }
        df = pd.DataFrame(data, index=dates)
        
        strategy = ProfitLossTargetStrategy(profit_target=10.0, stop_loss=10.0)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 5)
        
        result = strategy.calculate_return(df, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'stop_loss'  # Stop loss hit first chronologically
        assert result.return_pct == -11.0  # 89/100 - 1 = -0.11 = -11%
        assert result.exit_date.day == 2  # 2024-01-02


class TestEMAExitStrategy:
    
    def test_ema_exit_triggered(self, volatile_data):
        """Test when price goes below EMA."""
        strategy = EMAExitStrategy(ema_period=20)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 2, 9)  # 40 days later
        
        result = strategy.calculate_return(volatile_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'ema_exit'
        
    def test_ema_no_exit(self, sample_data):
        """Test when price never goes below EMA."""
        strategy = EMAExitStrategy(ema_period=5)  # Short EMA period
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 10)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert result.exit_reason == 'period_end'
        
    def test_missing_ema_column_raises_error(self, sample_data):
        """Test that missing EMA column raises ValueError."""
        strategy = EMAExitStrategy(ema_period=100)  # ema_100 column doesn't exist
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 10)
        
        with pytest.raises(ValueError) as exc_info:
            strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert "Required EMA column 'ema_100' not found in data" in str(exc_info.value)
        assert "Available columns:" in str(exc_info.value)
        assert "Please ensure the data contains pre-calculated EMA values" in str(exc_info.value)
        
    def test_ema_with_existing_column(self, sample_data):
        """Test that EMA strategy works when the required column exists."""
        strategy = EMAExitStrategy(ema_period=20)  # ema_20 column exists in sample_data
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 15)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        assert result is not None
        assert isinstance(result, PeriodReturnResult)
        # Since close prices are always above EMA in sample_data, should exit at period end
        assert result.exit_reason == 'period_end'
        
    def test_ema_strategy_with_data_without_ema_columns(self):
        """Test that EMA strategy raises error when data doesn't have EMA columns."""
        # Create data without EMA columns
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        data_without_ema = {
            'open': [100 + i for i in range(10)],
            'high': [102 + i for i in range(10)],
            'low': [98 + i for i in range(10)],
            'close': [101 + i for i in range(10)],
            'volume': [1000000] * 10
        }
        df_no_ema = pd.DataFrame(data_without_ema, index=dates)
        
        strategy = EMAExitStrategy(ema_period=20)
        entry_price = 100.0
        entry_date = datetime(2024, 1, 1)
        target_date = datetime(2024, 1, 10)
        
        with pytest.raises(ValueError) as exc_info:
            strategy.calculate_return(df_no_ema, entry_price, entry_date, target_date)
        
        error_msg = str(exc_info.value)
        assert "Required EMA column 'ema_20' not found in data" in error_msg
        assert "Available columns: ['open', 'high', 'low', 'close', 'volume']" in error_msg
        assert "Please ensure the data contains pre-calculated EMA values" in error_msg


class TestPeriodReturn:
    
    def test_strategy_initialization(self):
        """Test strategy initialization and validation."""
        # Valid strategies
        pr1 = PeriodReturn('buy_and_hold')
        assert pr1.strategy_name == 'buy_and_hold'
        
        pr2 = PeriodReturn('profit_loss_target', profit_target=15.0, stop_loss=3.0)
        assert pr2.strategy_name == 'profit_loss_target'
        
        pr3 = PeriodReturn('ema_exit', ema_period=10)
        assert pr3.strategy_name == 'ema_exit'
        
        # Invalid strategy
        with pytest.raises(ValueError):
            PeriodReturn('invalid_strategy')
            
    def test_get_available_strategies(self):
        """Test getting list of available strategies."""
        strategies = PeriodReturn.get_available_strategies()
        assert 'buy_and_hold' in strategies
        assert 'profit_loss_target' in strategies
        assert 'ema_exit' in strategies
        assert len(strategies) == 3
        
    def test_strategy_integration(self, sample_data):
        """Test that all strategies work through main interface."""
        entry_price = 100.0
        entry_date = datetime(2024, 1, 5)
        target_date = datetime(2024, 1, 15)
        
        strategies_to_test = [
            ('buy_and_hold', {}),
            ('profit_loss_target', {'profit_target': 10.0, 'stop_loss': 5.0}),
            ('ema_exit', {'ema_period': 5})
        ]
        
        for strategy_name, kwargs in strategies_to_test:
            if strategy_name == 'ema_exit':
                # For EMA strategy, we need data with EMA columns
                pr = PeriodReturn(strategy_name, **kwargs)
                result = pr.calculate_return(sample_data, entry_price, entry_date, target_date)
            else:
                pr = PeriodReturn(strategy_name, **kwargs)
                result = pr.calculate_return(sample_data, entry_price, entry_date, target_date)
            
            assert result is not None, f"Strategy {strategy_name} failed"
            assert isinstance(result, PeriodReturnResult)
            assert result.exit_reason in ['period_end', 'profit_target', 'stop_loss', 'ema_exit']
            assert isinstance(result.return_pct, float)
            assert isinstance(result.exit_price, float)
            assert isinstance(result.exit_date, datetime)


class TestPeriodReturnResult:
    
    def test_result_attributes(self):
        """Test PeriodReturnResult dataclass."""
        result = PeriodReturnResult(
            return_pct=10.5,
            exit_price=110.5,
            exit_date=datetime(2024, 1, 15),
            exit_reason='profit_target'
        )
        
        assert result.return_pct == 10.5
        assert result.exit_price == 110.5
        assert result.exit_date == datetime(2024, 1, 15)
        assert result.exit_reason == 'profit_target'


class TestEdgeCases:
    
    def test_zero_entry_price(self, sample_data):
        """Test handling of zero entry price."""
        strategy = BuyAndHoldStrategy()
        entry_price = 0.0
        entry_date = datetime(2024, 1, 5)
        target_date = datetime(2024, 1, 15)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        # Should handle gracefully and return valid result
        assert result is not None
        
    def test_negative_entry_price(self, sample_data):
        """Test handling of negative entry price."""
        strategy = BuyAndHoldStrategy()
        entry_price = -100.0
        entry_date = datetime(2024, 1, 5)
        target_date = datetime(2024, 1, 15)
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        # Should handle gracefully
        assert result is not None
        
    def test_entry_after_target_date(self, sample_data):
        """Test when entry date is after target date."""
        strategy = BuyAndHoldStrategy()
        entry_price = 100.0
        entry_date = datetime(2024, 1, 15)
        target_date = datetime(2024, 1, 5)  # Before entry date
        
        result = strategy.calculate_return(sample_data, entry_price, entry_date, target_date)
        
        # Should return None or handle gracefully
        assert result is None or isinstance(result, PeriodReturnResult)