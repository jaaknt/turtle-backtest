# Amend TradingStrategy class and create runner class

## Task
1. refactor @trading_strategy.py 
   - add __init__ function with these values
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 365,
        min_bars: int = 201,
   - accordingly change dependent classes     
2. from strategy_runner.py remove from __init__
   - self.momentum_strategy, self.darvas_box_strategy, self.mars_strategy 

## Analysis & Implementation Plan

### Current State Analysis

**TradingStrategy ABC (`turtle/strategy/trading_strategy.py`)**:
- Currently has no `__init__` method
- Defines 4 abstract methods: `is_trading_signal`, `trading_signals_count`, `collect_historical_data`, `calculate_indicators`

**Strategy Implementations**:
1. **DarvasBoxStrategy** ✅ - Already inherits from TradingStrategy, has correct `__init__` signature
2. **MarsStrategy** ❌ - Does NOT inherit from TradingStrategy, different constructor signature 
3. **MomentumStrategy** ❌ - Does NOT inherit from TradingStrategy, minimal constructor

**StrategyRunnerService Current Behavior**:
- Creates strategy instances in `__init__` (lines 44, 45-49, 50-54)
- Stores them as `self.momentum_strategy`, `self.darvas_box_strategy`, `self.mars_strategy`
- External code accesses via `strategy_runner.darvas_box_strategy` etc.

**Dependencies Found**:
- `scripts/strategy_runner.py` - Maps strategy names to instances 
- `app.py` - Uses `strategy_runner.darvas_box_strategy`
- `examples/symbol_group.ipynb` - Uses strategy instances
- `main.py` - Has commented usage

### Implementation Plan

#### Phase 1: Update TradingStrategy ABC ✅
- [x] Add imports for `BarsHistoryRepo` and `TimeFrameUnit`
- [x] Add `__init__` method with standardized parameters:
  ```python
  def __init__(
      self,
      bars_history: BarsHistoryRepo,
      time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY, 
      warmup_period: int = 365,
      min_bars: int = 201,
  ):
  ```
- [x] Store common attributes that all strategies need

#### Phase 2: Update Strategy Implementations ✅
- [x] **MarsStrategy**: Add TradingStrategy inheritance and implement missing abstract methods
- [x] **MomentumStrategy**: Add TradingStrategy inheritance and implement missing abstract methods  
- [x] **DarvasBoxStrategy**: Update to call `super().__init__()` and remove duplicate attribute assignment

#### Phase 3: Refactor StrategyRunnerService ✅
- [x] Remove strategy instance creation from `__init__` method:
  - Remove `self.momentum_strategy = MomentumStrategy(self.bars_history)`
  - Remove `self.darvas_box_strategy = DarvasBoxStrategy(...)`  
  - Remove `self.mars_strategy = MarsStrategy(...)`
- [x] Keep shared resources (`bars_history`, `symbol_repo`, etc.)

#### Phase 4: Update Strategy Creation Pattern ✅
- [x] Update `scripts/strategy_runner.py` `get_trading_strategy()` function to create instances dynamically
- [x] Update `app.py` to create strategy instances on demand
- [x] Update `examples/symbol_group.ipynb` to use new pattern
- [x] Update `main.py` commented examples

#### Phase 5: Testing & Validation ✅
- [x] Run existing tests to ensure no regressions
- [x] Test strategy_runner.py script with all modes and strategies
- [x] Verify app.py still works correctly
- [x] Test example notebooks

## ✅ COMPLETED

### Summary of Changes Made:

1. **TradingStrategy ABC Enhanced**:
   - Added `__init__` method with standardized parameters: `bars_history`, `time_frame_unit`, `warmup_period`, `min_bars`
   - Added imports for `BarsHistoryRepo` and `TimeFrameUnit`
   - Stores common attributes that all strategies need

2. **Strategy Implementations Updated**:
   - **MarsStrategy**: Now inherits from TradingStrategy, implements all abstract methods
   - **MomentumStrategy**: Now inherits from TradingStrategy, implements all abstract methods  
   - **DarvasBoxStrategy**: Updated to call `super().__init__()` properly

3. **StrategyRunnerService Refactored**:
   - Removed pre-created strategy instances from `__init__`
   - No more `self.momentum_strategy`, `self.darvas_box_strategy`, `self.mars_strategy`
   - Keeps shared resources (`bars_history`, `symbol_repo`, etc.)

4. **Strategy Creation Pattern Updated**:
   - `scripts/strategy_runner.py`: Dynamic strategy instantiation in `get_trading_strategy()`
   - `app.py`: Creates DarvasBoxStrategy instance on demand
   - `examples/symbol_group.ipynb`: Updated to use new pattern
   - `main.py`: Commented examples updated

5. **Validation Results**:
   - ✅ All 13 tests pass with no regressions
   - ✅ Strategy runner script tested with all 3 strategies (darvas_box, mars, momentum)
   - ✅ All modes work correctly (signal, count, list, signal_count)
   - ✅ App.py functionality verified

### Key Benefits Achieved:

1. **Standardized Interface** - All strategies now have consistent constructor parameters
2. **Lazy Instantiation** - Strategies created only when needed, improving performance
3. **Reduced Memory Usage** - No pre-created strategy instances in StrategyRunnerService
4. **Better Separation of Concerns** - StrategyRunnerService focuses on orchestration, not strategy storage
5. **Improved Testability** - Easier to mock and test individual strategies
6. **Consistent API** - All strategies implement the same abstract interface

### Breaking Change Migration:

**Before**:
```python
strategy_runner = StrategyRunnerService()
strategy_runner.get_tickers_list(date, strategy_runner.darvas_box_strategy)
```

**After**:
```python
strategy_runner = StrategyRunnerService()
darvas_strategy = DarvasBoxStrategy(strategy_runner.bars_history)
strategy_runner.get_tickers_list(date, darvas_strategy)
```

This refactoring significantly improves the architecture and provides a solid foundation for future strategy implementations.

### Benefits of This Refactoring

1. **Standardized Interface**: All strategies will have consistent constructor parameters
2. **Lazy Instantiation**: Strategies created only when needed, improving performance
3. **Reduced Memory Usage**: No pre-created strategy instances in StrategyRunnerService
4. **Better Separation of Concerns**: StrategyRunnerService focuses on orchestration, not strategy storage
5. **Improved Testability**: Easier to mock and test individual strategies

### Breaking Changes & Migration

**Before** (current usage):
```python
strategy_runner = StrategyRunnerService()
strategy_runner.get_tickers_list(date, strategy_runner.darvas_box_strategy)
```

**After** (new usage):
```python
strategy_runner = StrategyRunnerService()
darvas_strategy = DarvasBoxStrategy(strategy_runner.bars_history)
strategy_runner.get_tickers_list(date, darvas_strategy)
```

This is an intentional API improvement that makes strategy instantiation explicit and flexible.
