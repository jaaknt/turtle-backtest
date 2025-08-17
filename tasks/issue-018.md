# Refactor functions naming
The goal is to rename classes/methods to be semantically more correct
- @service/data_update.py -> @service/data_update_service.py
- @service/strategy_runner.py -> @service/strategy_runner_service.py
- PeriodReturnStrategy -> TradeExitStrategy

## Analysis and Implementation Plan

### Files requiring changes:

#### 1. File Renames
- `turtle/service/data_update.py` → `turtle/service/data_update_service.py`
- `turtle/service/strategy_runner.py` → `turtle/service/strategy_runner_service.py`

#### 2. Import Statement Updates for data_update_service (6 files):
- `main.py:1` - `from turtle.service.data_update import DataUpdateService`
- `scripts/daily_eod_update.py:1` - `from turtle.service.data_update import DataUpdateService`
- `README.md` - documentation reference
- `examples/symbol_group.ipynb` - notebook imports
- `examples/backtesting.ipynb` - notebook imports  
- `examples/pandas.ipynb` - notebook imports

#### 3. Import Statement Updates for strategy_runner_service (4 files):
- `main.py:1` - `from turtle.service.strategy_runner import StrategyRunnerService`
- `app.py:1` - `from turtle.service.strategy_runner import StrategyRunnerService`
- `scripts/strategy_runner.py:1` - `from turtle.service.strategy_runner import StrategyRunnerService`
- `examples/symbol_group.ipynb` - notebook imports

#### 4. Class Rename PeriodReturnStrategy → TradeExitStrategy (4 files):
- `turtle/performance/period_return.py:75` - main class definition
- `turtle/performance/strategy_performance.py:2` - import statement
- `turtle/performance/strategy_performance.py:45` - type annotation
- `examples/period_return_strategy_usage.py` - usage examples
- `tests/test_strategy_performance_tester_simple.py` - test references

#### 5. Child Class Inheritance Updates (3 classes):
- `BuyAndHoldStrategy(PeriodReturnStrategy)` → `BuyAndHoldStrategy(TradeExitStrategy)`
- `ProfitLossTargetStrategy(PeriodReturnStrategy)` → `ProfitLossTargetStrategy(TradeExitStrategy)`
- `EMAExitStrategy(PeriodReturnStrategy)` → `EMAExitStrategy(TradeExitStrategy)`

### Todo List:
1. [ ] Rename turtle/service/data_update.py to turtle/service/data_update_service.py
2. [ ] Rename turtle/service/strategy_runner.py to turtle/service/strategy_runner_service.py
3. [ ] Update import statements for data_update_service in 6 files (main.py, scripts/, examples/, README.md)
4. [ ] Update import statements for strategy_runner_service in 4 files (main.py, app.py, scripts/, examples/)
5. [ ] Rename PeriodReturnStrategy class to TradeExitStrategy in turtle/performance/period_return.py
6. [ ] Update PeriodReturnStrategy references to TradeExitStrategy in 4 files
7. [ ] Update class inheritance from PeriodReturnStrategy to TradeExitStrategy for child classes
8. [ ] Fix any typos found in the task file
9. [ ] Run tests to verify all changes work correctly