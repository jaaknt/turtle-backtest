# Amend TradingStrategy class and create runner class

> **Note**: This document references the original package structure. As of recent refactoring:
> - `turtle/strategy/` has been renamed to `turtle/signal/`
> - `trading_strategy.py` has been renamed to `base.py`
> - Exit strategies have been moved from `turtle/backtest/exit_strategy.py` to separate files in `turtle/exit/`

## Task
1. refactor strategy_runner.py 
   - rename momentum_stocks -> get_tickers_list 
   - rename get_buy_signals -> get_tickers_count
   - add 2 functions that are wrappers to TradingStrategy.is_trading_signal and trading_signals_count
2. Create new script @scripts/strategy_runner.py similar to data_update.py
   - parameters start_date, end_date, strategy
   - calls StrategyRunnerService.get_tickers_list or StrategyRunnerService.get_tickers_count with parameters and prints list to console

## Analysis & Implementation Plan

### Code Analysis Results
Current `StrategyRunnerService` class methods and dependencies:

1. **Methods to Rename**:
   - `momentum_stocks(date_to_check, trading_strategy) -> List[str]` → `get_tickers_list`
   - `get_buy_signals(start_date, end_date, trading_strategy) -> List[Tuple]` → `get_tickers_count`

2. **Current Dependencies Found**:
   - **app.py:16**: `strategy_runner.momentum_stocks(end_date, strategy_runner.darvas_box_strategy)`
   - **main.py:66**: `strategy_runner.momentum_stocks(end_date, strategy_runner.darvas_box_strategy)` (commented)
   - **main.py:69**: `strategy_runner.get_buy_signals(start_date, end_date, strategy_runner.darvas_box_strategy)` (commented)
   - **examples/symbol_group.ipynb**: `strategy_runner.get_buy_signals(start_date, end_date, strategy_runner.darvas_box_strategy)`

3. **Wrapper Functions Needed**:
   - Wrapper for `TradingStrategy.is_trading_signal()` 
   - Wrapper for `TradingStrategy.trading_signals_count()`

4. **Script Structure Analysis**:
   - Based on `scripts/daily_eod_update.py` pattern
   - Need argument parser for start_date, end_date, strategy
   - Need logging setup and error handling
   - Need strategy selection (darvas_box, mars, momentum)

### Implementation Plan

#### Phase 1: Rename StrategyRunnerService Methods ✅
- [x] Rename `momentum_stocks` → `get_tickers_list` in `strategy_runner.py`
- [x] Rename `get_buy_signals` → `get_tickers_count` in `strategy_runner.py`
- [x] Add wrapper functions for TradingStrategy methods

#### Phase 2: Update Dependencies ✅
- [x] Update `app.py` method call to use new name
- [x] Update `main.py` commented method calls for future compatibility
- [x] Update `examples/symbol_group.ipynb` to use new method names

#### Phase 3: Create Strategy Runner Script ✅
- [x] Create `scripts/strategy_runner.py` with argument parsing
- [x] Add strategy selection logic (darvas_box, mars, momentum)
- [x] Implement date parsing and validation
- [x] Add logging setup and error handling
- [x] Add main function to call StrategyRunnerService methods and print results

#### Phase 4: Verification ✅
- [x] Run tests to ensure no regressions
- [x] Test new script with different parameters
- [x] Verify type checking passes
- [x] Test updated apps and notebooks work correctly

## ✅ COMPLETED

### Summary of Changes Made:

1. **StrategyRunnerService Method Refactoring**:
   - Renamed `momentum_stocks()` → `get_tickers_list()` in `turtle/service/strategy_runner.py:56`
   - Renamed `get_buy_signals()` → `get_tickers_count()` in `turtle/service/strategy_runner.py:74`
   - Added wrapper functions:
     - `is_trading_signal()` in `turtle/service/strategy_runner.py:66`
     - `trading_signals_count()` in `turtle/service/strategy_runner.py:70`

2. **Dependencies Updated**:
   - Updated `app.py:16` to use `get_tickers_list()`
   - Updated commented method calls in `main.py:66,69` for future compatibility
   - Updated `examples/symbol_group.ipynb` cell 4 to use `get_tickers_count()`

3. **New Command-Line Script**:
   - Created `scripts/strategy_runner.py` with comprehensive CLI interface
   - Supports both list mode (`--mode list --date YYYY-MM-DD`) and count mode (`--mode count --start-date YYYY-MM-DD --end-date YYYY-MM-DD`)
   - Strategy selection via `--strategy` parameter (darvas_box, mars, momentum)
   - Robust error handling, logging, and argument validation
   - Follows same patterns as existing `scripts/daily_eod_update.py`

4. **Verification Results**:
   - All 13 tests pass with no regressions
   - New script tested successfully with different parameters
   - Type checking verified (no import errors)
   - Updated applications and notebooks import and initialize correctly

### Usage Examples:

```bash
# Get ticker list for specific date using Darvas Box strategy
uv run python scripts/strategy_runner.py --date 2024-08-30 --strategy darvas_box --mode list

# Get ticker counts for date range using Mars strategy
uv run python scripts/strategy_runner.py --start-date 2024-08-28 --end-date 2024-08-30 --strategy mars --mode count

# Show help
uv run python scripts/strategy_runner.py --help
```

### Benefits of This Refactoring:
- **Better Naming**: Method names more accurately reflect their purpose
- **Command Line Tool**: Easy to run strategy analysis from command line
- **Strategy Flexibility**: Script can work with different trading strategies
- **Consistent Patterns**: Follows same pattern as existing scripts
