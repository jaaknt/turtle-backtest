# Rename strategy_tester to strategy_performance
The goal is to rename "tester" to "performance" in development files

## Current Issues
- Directory name `turtle/tester` doesn't clearly indicate it's for performance analysis
- Class names using "Tester" are misleading - they perform analysis, not testing
- File names should be more descriptive of their purpose

## Proposed Changes
  - `turtle/tester/` → `turtle/performance/`
  - `turtle/service/strategy_tester.py` → `turtle/service/strategy_performance_service.py`
  - `scripts/strategy_tester.py` → `scripts/strategy_performance.py`
  - class `StrategyTesterService` → `StrategyPerformanceService`
  - Update all import statements and references

## Analysis Results
After analyzing the codebase, the following components need to be renamed:

### Directories
- `turtle/tester/` (contains: `__init__.py`, `models.py`, `period_return.py`, `strategy_performance.py`)

### Files to Rename
1. `turtle/service/strategy_tester.py` → `turtle/service/strategy_performance_service.py`
2. `scripts/strategy_tester.py` → `scripts/strategy_performance.py`

### Classes to Rename
- `StrategyTesterService` → `StrategyPerformanceService`

### Import Statements to Update (12 files affected)
- All `from turtle.tester` imports need to become `from turtle.performance`
- All references to `strategy_tester` module need updating

### Files with Import References
1. `turtle/service/strategy_tester.py`
2. `turtle/tester/models.py` 
3. `turtle/tester/strategy_performance.py`
4. `tests/test_period_return.py`
5. `tests/test_period_return_integration.py`
6. `tests/test_strategy_performance_tester_simple.py`
7. `examples/period_return_strategy_usage.py`
8. `scripts/strategy_tester.py`

### Documentation Updates
- Task files referencing old names
- README.md references
- Example usage documentation

## Implementation Plan

### Step 1: Directory Rename
- Rename `turtle/tester/` to `turtle/performance/`

### Step 2: File Renames  
- `turtle/service/strategy_tester.py` → `turtle/service/strategy_performance_service.py`
- `scripts/strategy_tester.py` → `scripts/strategy_performance.py`

### Step 3: Class Renames
- `StrategyTesterService` → `StrategyPerformanceService`

### Step 4: Update Import Statements
- Replace all `turtle.tester` with `turtle.performance`
- Update strategy_tester module references

### Step 5: Update Tests and Examples  
- Fix import statements in test files
- Update example usage files

### Step 6: Documentation Updates
- Update README.md references
- Update task documentation

### Step 7: Verification
- Run all tests to ensure nothing is broken
- Verify imports work correctly

