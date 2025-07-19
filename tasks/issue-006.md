# Amend TradingStrategy class

## Task
1. refactor strategy_runner.py 
   - def momentum_stocks(self, start_date: datetime) -> List[str]: ->
     def momentum_stocks(self, date_to_check: datetime, trading_strategy: TradingStrategy) -> List[str]:
      - remove self.market_data.spy_momentum(start_date) check
      - use trading_strategy to call is_trading_signal
   - get_buy_signals(self, start_date: datetime, end_date: datetime) -> List[Tuple] -> 
     get_buy_signals(self, start_date: datetime, end_date: datetime, trading_strategy: TradingStrategy) -> List[Tuple]
      - use trading_strategy to call trading_signals_count
2. fix all tests/scripts/documentation and dependencies

## Analysis & Implementation Plan

### Code Analysis Results
Current `StrategyRunnerService` class dependencies and usage:

1. **Method Signatures to Change**:
   - `momentum_stocks(self, start_date: datetime) -> List[str]`
   - `get_buy_signals(self, start_date: datetime, end_date: datetime) -> List[Tuple]`

2. **Current Dependencies Found**:
   - **app.py:15**: `strategy_runner.momentum_stocks(end_date)`
   - **main.py:66**: `strategy_runner.momentum_stocks(end_date)` (commented)
   - **main.py:69**: `strategy_runner.get_buy_signals(start_date, end_date)` (commented)
   - **examples/symbol_group.ipynb**: `data_updater.get_buy_signals(start_date, end_date)`

3. **Current Hard-coded Strategy Usage**:
   - Both methods currently use `self.darvas_box_strategy` directly
   - `momentum_stocks()` includes `self.market_data.spy_momentum(start_date)` check
   - Need to make these generic to accept any `TradingStrategy`

4. **Import Requirements**:
   - Need to import `TradingStrategy` from `turtle.strategy.trading_strategy`

### Implementation Plan

#### Phase 1: Update StrategyRunnerService Method Signatures
- [x] Add `TradingStrategy` import to `strategy_runner.py`
- [x] Update `momentum_stocks()` method signature and implementation
- [x] Update `get_buy_signals()` method signature and implementation
- [x] Remove `spy_momentum()` check from `momentum_stocks()`

#### Phase 2: Update Dependencies - Scripts and Apps
- [x] Update `app.py` to pass strategy parameter to method calls
- [x] Update `main.py` method calls (currently commented but need to be future-ready)
- [x] Update `examples/symbol_group.ipynb` notebook

#### Phase 3: Update Service Layer and Notebooks
- [x] Update `examples/symbol_group.ipynb` to use `StrategyRunnerService` instead of `DataUpdateService`
- [x] Update notebook to pass strategy parameter to new method signatures
- [x] Note: `DataUpdateService` no longer has `get_buy_signals()` after issue-002 refactoring

#### Phase 4: Verification
- [x] Run tests to ensure no regressions (13 tests passed)
- [x] Test updated apps and scripts work correctly (app.py starts without errors)
- [x] Verify type checking passes (no diagnostics found)
- [x] Test notebook functionality (updated to use new API)

## ✅ Task Completed

Successfully refactored StrategyRunnerService to accept TradingStrategy parameters for better flexibility:

### Enhanced Method Signatures:
```python
def momentum_stocks(self, date_to_check: datetime, trading_strategy: TradingStrategy) -> List[str]:
    """Find momentum stocks using any trading strategy implementation."""

def get_buy_signals(self, start_date: datetime, end_date: datetime, trading_strategy: TradingStrategy) -> List[Tuple]:
    """Get buy signals using any trading strategy implementation."""
```

### Updated Files:
- **`/turtle/service/strategy_runner.py`**: Refactored both methods to accept TradingStrategy parameter
- **`/app.py`**: Updated to pass `strategy_runner.darvas_box_strategy` as parameter
- **`/main.py`**: Updated commented method calls for future compatibility 
- **`/examples/symbol_group.ipynb`**: Updated to use `StrategyRunnerService` instead of `DataUpdateService` and new API

### Key Changes:
1. **Removed Market Condition Check**: Eliminated `spy_momentum()` check from `momentum_stocks()`
2. **Strategy Flexibility**: Can now use any strategy (Darvas, Mars, Momentum, etc.)
3. **Polymorphic Design**: Leverages TradingStrategy ABC interface
4. **Cleaner Separation**: Strategy logic separated from market condition checks

### Verification Results:
- ✅ All tests pass (13/13)
- ✅ Type checking clean (no diagnostics)
- ✅ Apps start without errors
- ✅ Notebook updated to use new API

### Benefits Achieved:
- **Strategy Flexibility**: Can easily switch between different trading strategies
- **Better Testability**: Easier to test with different strategy implementations
- **Separation of Concerns**: Removed hardcoded strategy dependencies
- **Polymorphic Interface**: Proper utilization of TradingStrategy ABC

### Benefits of This Refactoring:
- **Strategy Flexibility**: Can use any trading strategy (Darvas, Mars, Momentum, etc.)
- **Separation of Concerns**: Removes market condition checks from strategy runner
- **Better Testability**: Easier to test with different strategy implementations
- **Polymorphism**: Leverages the TradingStrategy ABC interface effectively
