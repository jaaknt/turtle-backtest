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
> - `has_signal` method removed completely
> - `get_trading_signals` → `get_signals` (renamed throughout)
> - `collect_historical_data` → `collect_data` (in base class)
> - `trading_signals_count` method removed completely
> The SignalService wrapper methods maintain their original names for backward compatibility.

**Key Features:**
- Executes trading strategies on US stock symbols
- Checks for trading signals on specific dates
- Counts trading signals across date ranges
- Supports multiple trading strategy implementations
- Provides ranking and filtering of trading opportunities

**Primary Methods:**
- `get_tickers_list(date_to_check)` - Returns list of tickers with trading signals on specified date
- `get_signals(ticker, start_date, end_date)` - Gets list of Signal objects for ticker over date range
- `get_tickers_count(start_date, end_date)` - Returns signal counts for all tickers
- `get_company_list(symbol_list)` - Retrieves company data for symbol list

**Usage:**
```python
strategy_runner = SignalService(time_frame_unit=TimeFrameUnit.DAY)
signals = strategy_runner.get_signals("AAPL", start_date, end_date)
signals = strategy_runner.get_signals("AAPL", target_date, target_date)
has_signal = len(signals) > 0
```

## ~~StrategyPerformanceService~~ (Removed)

~~The `StrategyPerformanceService` orchestrated comprehensive strategy backtesting and performance analysis across multiple symbols and time periods. This service has been removed as part of codebase simplification.~~

**Previously Available Features:**
- ~~Comprehensive backtesting framework with multiple holding periods~~
- ~~Statistical performance analysis including win rates, average returns, and risk metrics~~
- ~~Benchmark comparison against market indices (QQQ, SPY)~~
- ~~Support for multiple exit strategies (EMA-based, profit/loss targets)~~
- ~~Flexible output formats (console, CSV, JSON)~~

**Note:** For strategy testing and backtesting, use the individual strategy classes directly with the `SignalService` and manual analysis tools.