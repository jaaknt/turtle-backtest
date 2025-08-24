# Rename service and script
- turtle/service/strategy_runner_service.py -> turtle/service/signal_service.py
- StrategyRunnerService -> SignalService
- scripts/strategy_runner.py -> scripts/signal_runner.py

## Implementation Plan

### Phase 1: File Renaming
1. **Rename main service file**: `turtle/service/strategy_runner_service.py` → `turtle/service/signal_service.py`
2. **Rename main script file**: `scripts/strategy_runner.py` → `scripts/signal_runner.py`

### Phase 2: Class and Import Updates
1. **Update class name in signal_service.py**: `StrategyRunnerService` → `SignalService`
2. **Update all import statements** in the following files:
   - `main.py`: Import and usage references
   - `turtle/backtest/processor.py`: Import statement
   - `scripts/signal_runner.py` (renamed): Import and class usage
   - `tests/test_bars_history.py`: Import statement
   - `tests/test_company.py`: Import statement
   - `tests/test_darvas_box.py`: Import and usage
   - `tests/test_models.py`: Import statement
   - `tests/test_signal_processor.py`: Import and usage
   - `tests/test_symbol.py`: Import statement

### Phase 3: Reference Updates
1. **Update class instantiation and usage** in:
   - `main.py`: Variable names and class instantiation
   - `scripts/signal_runner.py`: Class instantiation and variable names
   - `tests/test_darvas_box.py`: Test class instantiation
   - `tests/test_signal_processor.py`: Test class instantiation

### Phase 4: Documentation Updates
1. **Update docstrings and comments** that reference old names
2. **Update CLI help text** in `scripts/signal_runner.py`
3. **Update any README or documentation files** if they reference the old names

### Files Affected (Total: 17+ files)
- **Core files to rename**: 2 files
- **Files with import updates**: 9 files
- **Files with class usage updates**: 4 files
- **Documentation updates**: Variable based on findings

### Validation Steps
1. **Run import tests**: Verify all imports resolve correctly
2. **Run unit tests**: Ensure all tests pass with new names
3. **Run linting**: Fix any linting issues introduced
4. **Functional testing**: Verify scripts and services work correctly