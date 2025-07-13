# Refactor strategy functions names to provide more abstract and meaningful names

## Task
1. In @turtle/strategy folder rename functions
   - validate_momentum -> is_trading_signal
   - validate_momentum_all_dates -> trading_signals_count
2. Replace also naming in dependent services/tests/Jupyter notebooks

## Analysis & Implementation Plan

### Code Analysis Results
The functions to be renamed are located in `/turtle/strategy/darvas_box.py`:

1. **`validate_momentum`** (line 283):
   - Returns boolean indicating if ticker has trading signal for specific date
   - Used in: `turtle/service/strategy_runner.py:61` and Jupyter notebook

2. **`validate_momentum_all_dates`** (line 296): 
   - Returns count of trading signals across date range
   - Used in: `turtle/service/strategy_runner.py:73` and Jupyter notebook

### Files Requiring Updates
- **Primary definition**: `/turtle/strategy/darvas_box.py`
- **Dependencies**: `/turtle/service/strategy_runner.py` 
- **Jupyter notebook**: `/examples/backtesting.ipynb`
- **No test files** found using these functions

### Implementation Plan

#### Phase 1: Update Function Definitions
- [x] Rename `validate_momentum` → `is_trading_signal` in `darvas_box.py:283`
- [x] Rename `validate_momentum_all_dates` → `trading_signals_count` in `darvas_box.py:296`

#### Phase 2: Update Dependencies  
- [x] Update function call in `strategy_runner.py:61` 
- [x] Update function call in `strategy_runner.py:73`

#### Phase 3: Update Jupyter Notebook
- [x] Update function calls in `examples/backtesting.ipynb` cells

#### Phase 4: Verification
- [x] Run tests to ensure no regressions (13 tests passed)
- [x] Test Jupyter notebook functionality
- [x] Verify no remaining old function name references

## ✅ Task Completed

All function names have been successfully refactored:
- `validate_momentum` → `is_trading_signal` 
- `validate_momentum_all_dates` → `trading_signals_count`

Updated locations:
- Primary definitions in `/turtle/strategy/darvas_box.py`
- Function calls in `/turtle/service/strategy_runner.py`
- Notebook cells in `/examples/backtesting.ipynb`
- Updated code comments to reflect new naming

All tests pass and no remaining references to old function names exist in the codebase.
