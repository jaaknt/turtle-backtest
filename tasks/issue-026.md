# New class SignalProcessor in @turtle/backtest/processor.py

> **Note**: This document references the original package structure. As of recent refactoring:
> - `turtle/strategy/` has been renamed to `turtle/signal/`
> - `trading_strategy.py` has been renamed to `base.py`
> - Exit strategies have been moved from `turtle/backtest/exit_strategy.py` to separate files in `turtle/exit/`
The SignalProcessor class responsibility is
- calculate entry date and price based on Signal
  - entry_date = next trading date after Signal.date
  - entry_price = opening price of ticker on entry_date
- calculate exit_date, exit_price, exit_reason based on ExitStrategy
- calculate return_pct based on entry_price and exit_price
- calculate return_pct_qqq based on entry_price (open) and exit_price (close) of QQQ for same period
- calculate return_pct_spy based on entry_price (open) and exit_price (close) of SPY for same period

```
class SignalProcessor():
    def __init__(
        self,
        start_date: datetime, # minimum date for OHLCV history
        end_date: datetime, # maximum date for OHLCV history
        bars_history: BarsHistoryRepo,
        exit_strategy: ExitStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ):
    ... 

    def initialize(self):
        self.df_spy = self.bars_history.get_ticker_history(
            "SPY",
            self.start_date,
            self.end_date,
            self.time_frame_unit,
        )
        self.df_qqq = self.bars_history.get_ticker_history(
            "QQQ",
            self.start_date,
            self.end_date,
            self.time_frame_unit,
        )

    def run(self, signal: Signal) -> SignalResult:
       ...
       executes all logic in private subfunctions to calculate
       all SignalResult values described above
       ... 
 ```    

## Analysis and Plan

### Current Architecture Understanding
After examining the codebase, I identified the following key components:

- **Signal class** (`turtle/strategy/models.py`): Contains `ticker`, `date`, and `ranking` fields
- **SignalResult class** (`turtle/backtest/models.py`): The target output with all required fields
- **TradeExitStrategy** (`turtle/backtest/period_return.py`): Abstract base class with concrete implementations:
  - `BuyAndHoldStrategy`: Exit at period end
  - `ProfitLossTargetStrategy`: Exit on profit target or stop loss
  - `EMAExitStrategy`: Exit when price goes below EMA
- **BarsHistoryRepo** (`turtle/data/bars_history.py`): Data access with `get_ticker_history()` method
- **TimeFrameUnit** (`turtle/common/enums.py`): Enum for time frame units (DAY, WEEK)

### Implementation Plan

1. **Create SignalProcessor class** in `turtle/backtest/processor.py`:
   - Constructor with required dependencies
   - `initialize()` method to pre-load benchmark data (SPY, QQQ)
   - `run(signal: Signal) -> SignalResult` method as main entry point
   - Private methods for each calculation step

2. **Core calculation methods**:
   - `_calculate_entry_data(signal: Signal) -> tuple[datetime, float]`
   - `_calculate_exit_data(signal: Signal, entry_date: datetime, entry_price: float) -> tuple[datetime, float, str]`
   - `_calculate_return_pct(entry_price: float, exit_price: float) -> float`
   - `_calculate_benchmark_returns(entry_date: datetime, exit_date: datetime) -> tuple[float, float]`

3. **Error handling and edge cases**:
   - Handle missing ticker data
   - Handle weekends/holidays for entry date calculation
   - Handle benchmark data gaps
   - Validate date ranges

4. **Integration points**:
   - Use existing `TradeExitStrategy` interface
   - Return properly populated `SignalResult` instance
   - Leverage existing `BarsHistoryRepo` for data access

5. **Testing strategy**:
   - Unit tests for each private method
   - Integration tests with different exit strategies
   - Edge case testing (missing data, holidays, etc.)
   - Benchmark calculation accuracy tests

### Dependencies
- `turtle/strategy/models.Signal`
- `turtle/backtest/models.SignalResult`
- `turtle/backtest/period_return.TradeExitStrategy`
- `turtle/data/bars_history.BarsHistoryRepo`
- `turtle/common/enums.TimeFrameUnit`
