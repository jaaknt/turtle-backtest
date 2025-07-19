# Create new service to test strategies profit in different periods
The goal is to test different strategies in the past data
  - generate signals for period in the past (e.g. 1 week). Period is parameter to StrategyTester class 
  - get stock opening price of the next day after signal was generated
  - compare it with closing price after 3 days, 1week, 2week, 1month
  - print percentage in price change (e.g. opening price vs closing price after x period)

## Task
1. Create service @service/strategy_tester.py with parameters
   - strategy class
   - signal start date
   - signal end date
   - list of pandas.Timedelta values
2. Implementation should be in classes in @turtle/tester directory
3. Add @scripts/strategy_tester.py to execute @service/strategy_tester.py services from commandline

## Analysis & Implementation Plan

### Codebase Analysis
After analyzing the existing codebase, I understand the following structure:

1. **Strategy Pattern**: All strategies inherit from `TradingStrategy` ABC with key methods:
   - `is_trading_signal(ticker, date)`: Check if signal exists on specific date
   - `trading_signals_count(ticker, start_date, end_date)`: Count signals in date range
   - `collect_historical_data()`: Fetch OHLCV data with warmup period
   - `calculate_indicators()`: Compute technical indicators

2. **Data Layer**: `BarsHistoryRepo` provides OHLCV data from PostgreSQL database
   - `get_ticker_history()`: Returns pandas DataFrame with OHLCV data
   - Data sourced from Alpaca API and stored in `turtle.bars_history` table

3. **Service Pattern**: Services like `DataUpdate` and `StrategyRunner` orchestrate business logic
   - Use ConnectionPool for database connections
   - Follow consistent patterns for initialization and execution

4. **Script Pattern**: Command-line scripts in `/scripts` directory
   - Use argparse for CLI parameters
   - Load environment variables with dotenv
   - Follow logging configuration patterns

### Implementation Plan

#### Phase 1: Create Core Tester Classes
1. **Create `/turtle/tester/__init__.py`** - Initialize tester package
2. **Create `/turtle/tester/strategy_performance.py`** - Core performance testing logic
   - Class: `StrategyPerformanceTester`
   - Methods:
     - `__init__(strategy, start_date, end_date, test_periods)`
     - `generate_signals()`: Find all trading signals in date range
     - `calculate_performance()`: Calculate returns for each test period
     - `get_results()`: Return performance statistics

3. **Create `/turtle/tester/models.py`** - Data models for test results
   - `SignalResult`: Store signal date, ticker, entry price
   - `PerformanceResult`: Store performance metrics per period
   - `TestSummary`: Aggregate results across all signals

#### Phase 2: Create Service Layer
4. **Create `/turtle/service/strategy_tester.py`** - Service orchestrating strategy testing
   - Class: `StrategyTesterService`
   - Parameters:
     - `strategy_class`: Strategy class to test
     - `signal_start_date`: Start date for signal generation
     - `signal_end_date`: End date for signal generation  
     - `test_periods`: List of pandas.Timedelta values (3 days, 1 week, 2 weeks, 1 month)
   - Methods:
     - `run_test()`: Execute complete strategy test
     - `_get_symbol_list()`: Get symbols to test
     - `_test_strategy_performance()`: Test strategy on single symbol
     - `_generate_report()`: Create summary report

#### Phase 3: Create Command Line Interface
5. **Create `/scripts/strategy_tester.py`** - CLI script
   - Arguments:
     - `--strategy`: Strategy name (darvas_box, mars, momentum)
     - `--start-date`: Signal generation start date
     - `--end-date`: Signal generation end date
     - `--periods`: Test periods (default: 3d,1w,2w,1m)
     - `--symbols`: Optional symbol filter
     - `--output`: Output format (console, csv, json)

#### Implementation Details

**Signal Processing Flow:**
1. For each symbol in symbol list:
   - Generate trading signals in specified date range
   - For each signal found:
     - Record signal date and ticker
     - Get opening price of next trading day (entry price)
     - Calculate closing prices after each test period
     - Compute percentage returns: `(close_price - open_price) / open_price * 100`

**Test Periods Handling:**
- Use pandas business day calendar for period calculations
- Handle weekends/holidays appropriately
- Skip periods that extend beyond available data

**Output Format:**
```
Strategy: DarvasBoxStrategy
Test Period: 2024-01-01 to 2024-03-31
Signals Found: 45

Period Performance:
3 Days:   Avg: +2.3%  Win Rate: 67%  Best: +15.2%  Worst: -8.1%
1 Week:   Avg: +4.1%  Win Rate: 71%  Best: +28.7%  Worst: -12.4%
2 Weeks:  Avg: +6.8%  Win Rate: 69%  Best: +41.3%  Worst: -18.9%
1 Month:  Avg: +9.2%  Win Rate: 64%  Best: +52.1%  Worst: -25.7%
```

**Dependencies:**
- pandas for data manipulation and period calculations
- Existing turtle modules (data repos, strategy classes)
- argparse for CLI interface
- Database connection through existing ConnectionPool pattern

