# Separate data update and strategy implementation to 2 different services

## Task
1. Refactor existing code @data_update.py by splitting it to 2 different services
   - DataUpdateService including all stocks update related services
   - StrategyRunnerService including all Strategy calls (momentum_stocks, get_buy_signals, )
2. In first iteration update also all depending code

## Analysis & Implementation Plan

### Current Structure Analysis
The current `DataUpdateService` service in `turtle/service/data_update.py` contains:

**Data Update Methods (should remain in DataUpdateService):**
- `update_symbol_list()` - Updates symbol data from EODHD API
- `update_company_list()` - Updates company data from Yahoo Finance
- `update_bars_history()` - Updates historical OHLCV data from Alpaca
- `get_company_list()` - Utility method to get company data
- `get_symbol_group_list()` - Utility method to get symbol groups

**Strategy-Related Methods (should move to StrategyRunnerService):**
- `momentum_stocks()` - Finds momentum stocks using strategy logic
- `get_buy_signals()` - Gets buy signals using strategy logic

**Strategy Instances (should move to StrategyRunnerService):**
- `market_data` (MarketData)
- `momentum_strategy` (MomentumStrategy)
- `darvas_box_strategy` (DarvasBoxStrategy)
- `mars_strategy` (MarsStrategy)

### Dependencies Analysis
1. **main.py** - Uses DataUpdateService for both data updates and strategy calls
   - `init_db()` uses data update methods
   - Commented code shows strategy usage
2. **app.py** - Uses DataUpdateService for strategy calls (`momentum_stocks`, `get_company_list`)
3. **scripts/daily_eod_update.py** - Uses DataUpdateService only for data updates (no changes needed)

### Implementation Plan
1. Create new `StrategyRunnerService` service in `turtle/service/strategy_runner.py`
2. Move strategy instances and methods from DataUpdateService to StrategyRunnerService
3. Update DataUpdateService to remove strategy-related code
4. Update main.py to use both services appropriately
5. Update app.py to use StrategyRunnerService for strategy calls
6. Test the refactored code to ensure functionality is preserved

### Benefits
- **Separation of Concerns**: Data updates vs strategy execution
- **Better Maintainability**: Each service has a single responsibility
- **Improved Testability**: Can test data operations and strategy logic separately
- **Cleaner Dependencies**: Reduced coupling between data and strategy logic


