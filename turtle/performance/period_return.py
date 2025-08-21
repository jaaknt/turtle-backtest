from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
import pandas as pd


def _safe_float_from_pandas(value: Any) -> float:
    """Safely extract a float value from pandas data."""
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    return float(value)


@dataclass
class PeriodReturnResult:
    """
    Result of period return calculation.
    
    Attributes:
        return_pct: Percentage return achieved
        exit_price: Price at which position was exited
        exit_date: Date when position was exited
        exit_reason: Reason for exit (e.g., 'period_end', 'profit_target', 'stop_loss', 'ema_exit')
        entry_date: Date when position was entered
        entry_price: Price at which position was entered
        return_pct_qqq: QQQ benchmark percentage return for the same period
        return_pct_spy: SPY benchmark percentage return for the same period
    """
    return_pct: float
    exit_price: float
    exit_date: datetime
    exit_reason: str
    entry_date: Optional[datetime] = None
    entry_price: Optional[float] = None
    return_pct_qqq: Optional[float] = None
    return_pct_spy: Optional[float] = None


class TradeExitStrategy(ABC):
    """
    Abstract base class for period return calculation strategies.
    """
    
    @abstractmethod
    def calculate_return(
        self,
        data: pd.DataFrame,
        entry_price: float,
        entry_date: datetime,
        target_date: datetime
    ) -> Optional[PeriodReturnResult]:
        """
        Calculate period return based on strategy-specific logic.
        
        Args:
            data: DataFrame with OHLCV data (index should be datetime)
            entry_price: Price at which position was entered
            entry_date: Date when position was entered
            target_date: Target end date for the period
            
        Returns:
            PeriodReturnResult or None if calculation failed
        """
        pass


class BuyAndHoldStrategy(TradeExitStrategy):
    """
    Simple buy and hold strategy - exit at period end.
    """
    
    def calculate_return(
        self,
        data: pd.DataFrame,
        entry_price: float,
        entry_date: datetime,
        target_date: datetime
    ) -> Optional[PeriodReturnResult]:
        """Calculate return by holding until target date."""
        try:
            # Convert dates to pandas timestamps for comparison
            entry_ts = pd.Timestamp(entry_date)
            target_ts = pd.Timestamp(target_date)
            
            # Filter data from entry date onwards up to target date
            mask = (data.index >= entry_ts) & (data.index <= target_ts)
            period_data = data[mask]
            
            if period_data.empty:
                # Try to find data on or after entry date within reasonable range
                mask = data.index >= entry_ts
                period_data = data[mask]
                if period_data.empty:
                    return None
            
            # Find closest trading day to target date within the available data
            if len(period_data) == 1:
                closest_idx = period_data.index[0]
            else:
                # Find the closest date to target_date
                # Convert to numpy array for proper abs() operation
                time_diffs = (period_data.index - target_ts).to_numpy()
                abs_diffs = abs(time_diffs)
                min_diff_idx = int(abs_diffs.argmin())
                closest_idx = period_data.index[min_diff_idx]
            
            exit_price = _safe_float_from_pandas(period_data.loc[closest_idx, 'close'])
            exit_date = pd.Timestamp(closest_idx).to_pydatetime()
            
            # Handle edge cases for entry price
            if entry_price <= 0:
                # For zero or negative entry price, just return the absolute change
                return_pct = 0.0 if entry_price == 0 else float('inf')
            else:
                return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            return PeriodReturnResult(
                return_pct=return_pct,
                exit_price=exit_price,
                exit_date=exit_date,
                exit_reason='period_end',
                entry_date=entry_date,
                entry_price=entry_price
            )
            
        except Exception:
            return None


class ProfitLossTargetStrategy(TradeExitStrategy):
    """
    Exit when 10% profit target or 5% stop loss is hit, whichever comes first.
    """
    
    def __init__(self, profit_target: float = 10.0, stop_loss: float = 5.0):
        """
        Initialize with profit and loss targets.
        
        Args:
            profit_target: Profit target percentage (default 10%)
            stop_loss: Stop loss percentage (default 5%)
        """
        self.profit_target = profit_target
        self.stop_loss = stop_loss
    
    def calculate_return(
        self,
        data: pd.DataFrame,
        entry_price: float,
        entry_date: datetime,
        target_date: datetime
    ) -> Optional[PeriodReturnResult]:
        """Calculate return with profit/loss targets."""
        try:
            # Filter data from entry date onwards up to target date
            mask = (data.index >= entry_date) & (data.index <= target_date)
            period_data = data[mask].copy()
            
            if period_data.empty:
                return None
            
            # Calculate daily returns
            period_data['return_pct'] = ((period_data['close'] - entry_price) / entry_price) * 100
            
            # Find first profit target hit
            profit_hits = period_data[period_data['return_pct'] >= self.profit_target]
            first_profit_date = profit_hits.index[0] if not profit_hits.empty else None
            
            # Find first stop loss hit
            loss_hits = period_data[period_data['return_pct'] <= -self.stop_loss]
            first_loss_date = loss_hits.index[0] if not loss_hits.empty else None
            
            # Determine which target was hit first (if any)
            if first_profit_date is not None and first_loss_date is not None:
                # Both targets hit - use whichever came first
                if first_profit_date <= first_loss_date:
                    exit_idx = first_profit_date
                    exit_reason = 'profit_target'
                else:
                    exit_idx = first_loss_date
                    exit_reason = 'stop_loss'
            elif first_profit_date is not None:
                # Only profit target hit
                exit_idx = first_profit_date
                exit_reason = 'profit_target'
            elif first_loss_date is not None:
                # Only stop loss hit
                exit_idx = first_loss_date
                exit_reason = 'stop_loss'
            else:
                # Neither target hit - exit at period end
                exit_idx = period_data.index[-1]
                exit_reason = 'period_end'
            
            # Calculate exit values
            exit_price = _safe_float_from_pandas(period_data.loc[exit_idx, 'close'])
            exit_date = pd.Timestamp(exit_idx).to_pydatetime()
            return_pct = _safe_float_from_pandas(period_data.loc[exit_idx, 'return_pct'])
            
            return PeriodReturnResult(
                return_pct=return_pct,
                exit_price=exit_price,
                exit_date=exit_date,
                exit_reason=exit_reason,
                entry_date=entry_date,
                entry_price=entry_price
            )
            
        except Exception:
            return None


class EMAExitStrategy(TradeExitStrategy):
    """
    Exit when price closes below EMA or at period end.
    
    Note: This strategy assumes that the EMA column already exists in the data
    (e.g., 'ema_10', 'ema_20', etc.). If the column doesn't exist, an error will be raised.
    """
    
    def __init__(self, ema_period: int = 20):
        """
        Initialize with EMA period.
        
        Args:
            ema_period: Period for EMA to look for in data (default 20 days)
                       Will look for column named 'ema_{ema_period}' in the DataFrame
        """
        self.ema_period = ema_period
        self.ema_column = f'ema_{ema_period}'
    
    def calculate_return(
        self,
        data: pd.DataFrame,
        entry_price: float,
        entry_date: datetime,
        target_date: datetime
    ) -> Optional[PeriodReturnResult]:
        """Calculate return with EMA exit logic."""
        # Check if required EMA column exists
        if self.ema_column not in data.columns:
            raise ValueError(
                f"Required EMA column '{self.ema_column}' not found in data. "
                f"Available columns: {list(data.columns)}. "
                f"Please ensure the data contains pre-calculated EMA values."
            )
        
        try:
            # Filter data from entry date onwards up to target date
            mask = (data.index >= entry_date) & (data.index <= target_date)
            period_data = data[mask].copy()
            
            if period_data.empty:
                return None
            
            # Find first day where close is below EMA
            below_ema = period_data[period_data['close'] < period_data[self.ema_column]]
            
            if not below_ema.empty:
                # Exit on first close below EMA
                exit_idx = below_ema.index[0]
                exit_price = _safe_float_from_pandas(period_data.loc[exit_idx, 'close'])
                exit_date = pd.Timestamp(exit_idx).to_pydatetime()
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                
                return PeriodReturnResult(
                    return_pct=return_pct,
                    exit_price=exit_price,
                    exit_date=exit_date,
                    exit_reason='ema_exit',
                    entry_date=entry_date,
                    entry_price=entry_price
                )
            
            # Price never went below EMA, exit at period end
            last_idx = period_data.index[-1]
            exit_price = _safe_float_from_pandas(period_data.loc[last_idx, 'close'])
            exit_date = pd.Timestamp(last_idx).to_pydatetime()
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            return PeriodReturnResult(
                return_pct=return_pct,
                exit_price=exit_price,
                exit_date=exit_date,
                exit_reason='period_end',
                entry_date=entry_date,
                entry_price=entry_price
            )
            
        except Exception as e:
            # Re-raise our ValueError, but catch other exceptions
            if isinstance(e, ValueError) and "EMA column" in str(e):
                raise
            return None


class PeriodReturn:
    """
    Main class for calculating period returns using different strategies.
    """
    
    STRATEGIES = {
        'buy_and_hold': BuyAndHoldStrategy,
        'profit_loss_target': ProfitLossTargetStrategy,
        'ema_exit': EMAExitStrategy,
    }
    
    def __init__(self, strategy_name: str = 'buy_and_hold', **strategy_kwargs: Any) -> None:
        """
        Initialize with specified strategy.
        
        Args:
            strategy_name: Name of the strategy to use
            **strategy_kwargs: Additional arguments for strategy initialization
        """
        if strategy_name not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(self.STRATEGIES.keys())}")
        
        strategy_class = self.STRATEGIES[strategy_name]
        self.strategy = strategy_class(**strategy_kwargs)
        self.strategy_name = strategy_name
    
    def calculate_return(
        self,
        data: pd.DataFrame,
        entry_price: float,
        entry_date: datetime,
        target_date: datetime
    ) -> Optional[PeriodReturnResult]:
        """
        Calculate period return using the configured strategy.
        
        Args:
            data: DataFrame with OHLCV data (index should be datetime)
            entry_price: Price at which position was entered
            entry_date: Date when position was entered
            target_date: Target end date for the period
            
        Returns:
            PeriodReturnResult or None if calculation failed
        """
        from typing import cast
        result = self.strategy.calculate_return(data, entry_price, entry_date, target_date)
        return cast(Optional[PeriodReturnResult], result)
    
    @classmethod
    def get_available_strategies(cls) -> list[str]:
        """Get list of available strategy names."""
        return list(cls.STRATEGIES.keys())