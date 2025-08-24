# Refactor @turtle/performance
The goal is to refactor existing logic in this folder
- rename @turtle/performance to @turtle/backtest
- in models.py define class 

@dataclass
class SignalResult:
    signal: Signal             # Signal that is input for calculation
    entry_date: datetime       # Date when position was entered
    entry_price: float         # Price at which position was entered
    exit_date: datetime        # Date when position was exited
    exit_price: float          # Price at which position was exited
    exit_reason: str           # Reason for exit (e.g., 'period_end', 'profit_target', 'stop_loss', 'ema_exit')
    return_pct: float          # Percentage return between entry_price and exit_price 
    return_pct_qqq: float      # QQQ benchmark percentage return for the same period 
    return_pct_spy: float      # SPY benchmark percentage return for the same period

## Analysis and Plan

### Current Structure
The `turtle/performance/` folder contains:
- `__init__.py` - Package initialization with docstring
- `models.py` - Data models including existing SignalResult, PerformanceResult, TestSummary, RankingPerformance
- `period_return.py` - Period return calculation strategies and classes
- `strategy_performance.py` - Main StrategyPerformanceTester class

### Files That Import from turtle.performance
The following files need their imports updated:
- `tests/test_period_return_integration.py`
- `tests/test_period_return.py` 
- `tests/test_strategy_performance_tester_simple.py`
- `turtle/service/strategy_performance_service.py`

### Refactoring Plan

1. **Create new turtle/backtest folder** - Copy all files from turtle/performance to turtle/backtest
2. **Update internal imports** - Fix imports within the backtest module files
3. **Update external imports** - Fix all imports in test files and service files  
4. **Update existing SignalResult class** - The current SignalResult class already exists but needs to be updated to match the specification exactly
5. **Remove old performance folder** - Clean up by removing the old turtle/performance folder
6. **Run tests** - Ensure all tests pass with the new structure
7. **Run linting** - Fix any linting errors with mypy and ruff

