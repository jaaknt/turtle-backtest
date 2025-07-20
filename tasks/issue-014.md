# Create different strategies to calculate period profit that can be switched on different trading strategies
The goal is to have different strategies to test period profit. Solution must support approach that based 
on predefined period algorithm must be able to:
  - take profit after 10% profit or sell after 5% drawdown (whichever comes first) or sell at period end
  - sell when closes below 20 days EMA or at period end
  - buy and hold whole period
  - other examples must be easy to add

Create new class in turtle/tester directory that implements different strategies to calculate period profit

## Task
1. Create class period_return.py with parameters:
   - pandas DataFrame with OHLC data for particular stock
   - period return strategy name
2. Replace models.py get_return_for_period with this new class implementation

## Analysis and Plan

### Current Implementation Analysis
- `SignalResult.get_return_for_period()` in `turtle/tester/models.py:28-45` currently calculates simple buy-and-hold return: `((closing_price - entry_price) / entry_price) * 100`
- Used in `StrategyPerformanceTester` (lines 284, 361) to calculate performance metrics
- Takes period_name as input and uses pre-calculated closing prices from `period_results` dict

### Implementation Plan

#### 1. Create PeriodReturn class (`turtle/tester/period_return.py`)
- **Input parameters:**
  - `data`: pandas DataFrame with OHLCV data for the stock
  - `entry_price`: float - entry price of the position
  - `entry_date`: datetime - entry date
  - `target_date`: datetime - target end date for the period
  - `strategy_name`: str - name of the period return strategy
  
- **Strategy implementations:**
  - `buy_and_hold`: Current implementation (closing price at period end)
  - `profit_loss_target`: Take 10% profit or 5% drawdown, whichever comes first
  - `ema_exit`: Sell when price closes below 20-day EMA
  - Base strategy interface for easy extension

#### 2. Update SignalResult class (`turtle/tester/models.py`)
- Modify `get_return_for_period()` to use new PeriodReturn class
- Need access to full OHLCV data, not just closing price
- Update method signature to accept strategy_name parameter

#### 3. Update StrategyPerformanceTester integration
- Modify `_process_signal()` to pass additional data to SignalResult
- Update performance calculation to work with new period return strategies
- Ensure backward compatibility with existing test periods

#### 4. Testing and validation
- Create unit tests for new PeriodReturn strategies
- Verify integration with existing StrategyPerformanceTester
- Test with sample data to ensure correct calculations

### Implementation Strategy
1. Start with PeriodReturn class with buy_and_hold strategy (matches current behavior)
2. Add profit_loss_target strategy 
3. Add ema_exit strategy
4. Update SignalResult integration
5. Test and validate all strategies work correctly


