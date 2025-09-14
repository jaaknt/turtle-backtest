# Add ABC to be implemented by different strategies

> **Note**: This document references the original package structure. As of recent refactoring:
> - `turtle/strategy/` has been renamed to `turtle/signal/`
> - `trading_strategy.py` has been renamed to `base.py`
> - Exit strategies have been moved from `turtle/backtest/exit_strategy.py` to separate files in `turtle/exit/`

## Task
1. Add new ABC trading_strategy.py that has 2 functions
   - is_trading_signal (parameters same as in @darvas_box.py)
   - trading_signals_count (parameters same as in @darvas_box.py)
2. @darvas_box.py implements this interface

## Analysis & Implementation Plan

### Code Analysis Results
Current strategy structure analysis:

1. **DarvasBoxStrategy** (`darvas_box.py`):
   - `is_trading_signal(self, ticker: str, date_to_check: datetime) -> bool`
   - `trading_signals_count(self, ticker: str, start_date: datetime, end_date: datetime) -> int`

2. **Other strategies** (mars.py, momentum.py, market.py):
   - Have different method signatures and structures
   - No common interface currently exists

3. **Strategy patterns observed**:
   - All strategies use `BarsHistoryRepo` for data access
   - Common initialization with `time_frame_unit`, `warmup_period`
   - Data collection via `collect()` method pattern

### Implementation Plan

#### Phase 1: Create Abstract Base Class
- [x] Create `/turtle/strategy/trading_strategy.py` with ABC interface
- [x] Define abstract methods: `is_trading_signal` and `trading_signals_count`
- [x] Include proper type hints and documentation

#### Phase 2: Implement Interface in DarvasBoxStrategy  
- [x] Import the ABC in `darvas_box.py`
- [x] Make `DarvasBoxStrategy` inherit from `TradingStrategy`
- [x] Verify existing methods match interface requirements

#### Phase 3: Update Strategy Imports
- [x] Update `__init__.py` to export the new ABC
- [x] Check if other files need to import the new interface

#### Phase 4: Verification
- [x] Run tests to ensure no regressions (13 tests passed)
- [x] Verify type checking passes (no diagnostics found)
- [x] Test that DarvasBoxStrategy properly implements interface

## ✅ Task Completed

Successfully implemented ABC interface for trading strategies:

### Created Files:
- **`/turtle/strategy/trading_strategy.py`**: Abstract base class with `TradingStrategy` interface
- **Updated `/turtle/strategy/__init__.py`**: Exports the new ABC and all strategy classes

### Modified Files:
- **`/turtle/strategy/darvas_box.py`**: Now inherits from `TradingStrategy` interface
  - Existing `is_trading_signal()` and `trading_signals_count()` methods already match interface
  - No code changes needed, just added inheritance

### Interface Definition:
```python
class TradingStrategy(ABC):
    @abstractmethod
    def is_trading_signal(self, ticker: str, date_to_check: datetime) -> bool:
        """Check if there is a trading signal for a specific ticker on a given date."""
        
    @abstractmethod  
    def trading_signals_count(self, ticker: str, start_date: datetime, end_date: datetime) -> int:
        """Count the number of trading signals for a ticker within a date range."""
```

### Verification Results:
- ✅ All tests pass (13/13)
- ✅ No type checking errors  
- ✅ `DarvasBoxStrategy` properly implements the interface
- ✅ Interface ready for other strategies to implement
