# Add new file @strategy/models.py with dataclass

> **Note**: This document references the original package structure. As of recent refactoring:
> - `turtle/strategy/` has been renamed to `turtle/signal/`
> - `trading_strategy.py` has been renamed to `base.py`
> - Exit strategies have been moved from `turtle/backtest/exit_strategy.py` to separate files in `turtle/exit/`
The goal is to add new dataclass
@dataclass
class Signal:
    """Ticker signals
     
    Attributes:
        ticker (str): Stock symbol code
        date (datetime): Date when the signal was generated
    ...
    """

    ticker: str
    date: datetime

Refactor get_trading_signals to return List[Signal]

## Implementation Plan

### Analysis Summary:
- **Current State**: `get_trading_signals` methods return `List[Tuple[str, datetime]]`
- **Target State**: Refactor to return `List[Signal]` using a new Signal dataclass
- **Impact**: Only `trading_signals_count` methods use `get_trading_signals` internally, so this is a safe refactor
- **Pattern**: Follow existing dataclass patterns from `turtle/data/models.py` and `turtle/performance/models.py`

### Todo List:
- [x] Fix docstring formatting in task file (missing proper Attributes description) (COMPLETED)
- [x] Create `turtle/strategy/models.py` with Signal dataclass following project conventions (COMPLETED)
- [x] Update abstract `TradingStrategy.get_trading_signals` return type to `List[Signal]` (COMPLETED)
- [x] Update `DarvasBoxStrategy.get_trading_signals` to return `List[Signal]` objects (COMPLETED)
- [x] Update `MarsStrategy.get_trading_signals` to return `List[Signal]` objects (COMPLETED)
- [x] Update `MomentumStrategy.get_trading_signals` to return `List[Signal]` objects (COMPLETED)
- [x] Run pytest to ensure no regressions (COMPLETED - All 54 tests pass)
- [x] Run linting tools to fix any style issues (COMPLETED - No linting tools configured)

### Key Changes Required:
1. **New Models File**: Create `turtle/strategy/models.py` with Signal dataclass
2. **Import Updates**: Add Signal import to all strategy files
3. **Return Type Change**: Update all get_trading_signals methods from `List[Tuple[str, datetime]]` to `List[Signal]`
4. **Object Creation**: Change from `[(ticker, date), ...]` to `[Signal(ticker=ticker, date=date), ...]`
5. **Backward Compatibility**: `trading_signals_count` methods use `len(signals)` so no changes needed there

### Files to Modify:
- `tasks/issue-022.md` (documentation)
- `turtle/strategy/models.py` (new file)
- `turtle/strategy/trading_strategy.py` (abstract method)
- `turtle/strategy/darvas_box.py` (implementation)
- `turtle/strategy/mars.py` (implementation)
- `turtle/strategy/momentum.py` (implementation)

## ✅ **Implementation Completed Successfully!**

### **Summary of Changes:**
1. **✅ Created new Signal dataclass** in `turtle/strategy/models.py` 
2. **✅ Updated abstract method** in `TradingStrategy` to return `List[Signal]`
3. **✅ Refactored all 3 implementations**:
   - DarvasBoxStrategy: `[(ticker, date), ...]` → `[Signal(ticker=ticker, date=date), ...]`
   - MarsStrategy: `[(ticker, date), ...]` → `[Signal(ticker=ticker, date=date), ...]`
   - MomentumStrategy: `[(ticker, date), ...]` → `[Signal(ticker=ticker, date=date), ...]`
4. **✅ Backward compatibility maintained**: `trading_signals_count` methods still work via `len(signals)`
5. **✅ All tests passing**: No regressions introduced

### **Benefits Achieved:**
- **Better Type Safety**: Structured Signal objects instead of tuples
- **Improved Readability**: `signal.ticker` and `signal.date` instead of `signal[0]` and `signal[1]`
- **Future Extensibility**: Easy to add more fields to Signal class
- **Consistent Patterns**: Follows project's existing dataclass conventions
