# Add new method to abstract class TradingStrategy and implement it in all implementations
The goal is to add method get_trading_signals to TradingStrategy class
and implement it in all TradingStrategy implementations. It must return
ticker and signal datetime tuples for start_date, end_date period
    @abstractmethod
    def get_trading_signals(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> List[Tuple[str, datetime]]:
Refactor trading_signals_count to call this new method internally

## Implementation Plan

### Todo List:
- [x] Fix return type typo in task file (COMPLETED)
- [x] Add Tuple import and get_trading_signals abstract method to TradingStrategy class (COMPLETED)
- [x] Implement get_trading_signals in DarvasBoxStrategy and refactor trading_signals_count (COMPLETED)
- [x] Implement get_trading_signals in MarsStrategy and refactor trading_signals_count (COMPLETED)
- [x] Implement get_trading_signals in MomentumStrategy and refactor trading_signals_count (COMPLETED)
- [x] Run pytest to ensure no regressions (COMPLETED - All 54 tests pass)
- [x] Run linting tools to fix any style issues (COMPLETED - No linting tools configured in project)

### Key Changes:
1. **Fixed typo**: Return type corrected to `List[Tuple[str, datetime]]`
2. **Abstract method**: Add `get_trading_signals` to base TradingStrategy class
3. **Implementation**: Add method to all strategy subclasses (DarvasBox, Mars, Momentum)
4. **Refactoring**: Modify `trading_signals_count` methods to use new `get_trading_signals` internally
5. **Testing**: Ensure all changes work correctly and maintain backward compatibility
