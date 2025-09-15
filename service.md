# Services

This document describes the core service classes that provide the business logic layer for the turtle backtest library.

## DataUpdateService

The `DataUpdateService` is responsible for data ingestion and management operations. It handles downloading and storing market data from multiple external APIs into the PostgreSQL database.

**Key Features:**
- Downloads symbol lists from EODHD API for US markets
- Retrieves company fundamental data from Yahoo Finance
- Fetches historical OHLCV (Open, High, Low, Close, Volume) data from Alpaca API
- Manages database connections using connection pooling
- Supports configurable time frame units (DAY, WEEK, MONTH)

**Primary Methods:**
- `update_symbol_list()` - Downloads and stores US stock symbols
- `update_company_list()` - Retrieves company information for all symbols
- `update_bars_history(start_date, end_date)` - Downloads historical price data for date range
- `get_company_list(symbol_list)` - Returns company data as DataFrame
- `get_symbol_group_list(symbol_group)` - Retrieves custom symbol groupings

**Usage:**
```python
data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
data_updater.update_symbol_list()
data_updater.update_company_list()
data_updater.update_bars_history(start_date, end_date)
```

## SignalService

The `SignalService` provides strategy execution capabilities for running trading strategies against historical market data. It serves as a wrapper around trading strategy implementations.

> **Note**: As of recent refactoring, the underlying TradingStrategy interface has been updated:
> - `is_trading_signal` → `has_signal` (in base class)
> - `get_trading_signals` → `get_signals` (in base class)
> - `collect_historical_data` → `collect_data` (in base class)
> - `trading_signals_count` method removed from base class
> The SignalService wrapper methods maintain their original names for backward compatibility.

**Key Features:**
- Executes trading strategies on US stock symbols
- Checks for trading signals on specific dates
- Counts trading signals across date ranges
- Supports multiple trading strategy implementations
- Provides ranking and filtering of trading opportunities

**Primary Methods:**
- `get_tickers_list(date_to_check)` - Returns list of tickers with trading signals on specified date
- `is_trading_signal(ticker, date_to_check)` - Checks if specific ticker has signal on date
- `trading_signals_count(ticker, start_date, end_date)` - Counts signals for ticker over date range
- `get_trading_signals(ticker, start_date, end_date)` - Gets list of Signal objects for ticker over date range
- `get_tickers_count(start_date, end_date)` - Returns signal counts for all tickers
- `get_company_list(symbol_list)` - Retrieves company data for symbol list

**Usage:**
```python
strategy_runner = SignalService(time_frame_unit=TimeFrameUnit.DAY)
signals = strategy_runner.get_trading_signals("AAPL", start_date, end_date)
has_signal = strategy_runner.is_trading_signal("AAPL", target_date)
```

## StrategyPerformanceService

The `StrategyPerformanceService` orchestrates comprehensive strategy backtesting and performance analysis across multiple symbols and time periods. It provides detailed statistical analysis of trading strategy effectiveness.

**Key Features:**
- Comprehensive backtesting framework with multiple holding periods
- Statistical performance analysis including win rates, average returns, and risk metrics
- Benchmark comparison against market indices (QQQ, SPY)
- Support for multiple exit strategies (EMA-based, profit/loss targets)
- Flexible output formats (console, CSV, JSON)
- Factory method for creating instances from strategy names

**Available Strategies:**
- `darvas_box` - Darvas Box trend-following strategy
- `mars` - Mars momentum strategy
- `momentum` - Traditional momentum strategy

**Primary Methods:**
- `run_test(symbols, symbol_filter, max_symbols)` - Execute complete performance test
- `print_results(test_summary, output_format)` - Display results in specified format
- `save_results(test_summary, filename, output_format)` - Save results to file
- `from_strategy_name(strategy_name, ...)` - Factory method for creating service instances

**Performance Metrics:**
- Total and valid signal counts
- Average, best, and worst returns
- Win rates and success percentages
- Benchmark comparisons
- Period-based analysis (3d, 1w, 2w, 1m)

**Usage:**
```python
# Create service for specific strategy
service = StrategyPerformanceService.from_strategy_name(
    "darvas_box",
    signal_start_date=datetime(2024, 1, 1),
    signal_end_date=datetime(2024, 12, 31)
)

# Run comprehensive test
results = service.run_test(max_symbols=100)

# Display results
service.print_results(results, output_format="console")
service.save_results(results, "results.csv", output_format="csv")
```

**Output Formats:**
- **Console**: Human-readable formatted output with tables
- **CSV**: Structured data suitable for spreadsheet analysis
- **JSON**: Machine-readable format for programmatic processing