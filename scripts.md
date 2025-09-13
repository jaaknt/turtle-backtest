# Scripts

This document describes the command-line scripts that provide convenient interfaces for common operations using the turtle backtest services.

## daily_eod_update.py

The `daily_eod_update.py` script provides a command-line interface for updating the database with end-of-day market data. It's designed for daily operations to keep the database current with the latest market data.

**Key Features:**
- Updates OHLCV historical data for all US symbols
- Supports single date or date range updates
- Built-in validation to ensure successful data retrieval
- Dry-run mode for testing without making changes
- Comprehensive logging with optional verbose output
- Trading day calculations (excludes weekends)

**Usage:**
```bash
# Update data for specific date (required --start-date parameter)
uv run python scripts/daily_eod_update.py --start-date 2024-12-01

# Update data for date range
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --end-date 2024-12-07

# Dry run to preview updates without making changes
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --dry-run

# Enable detailed logging
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --verbose
```

**Options:**
- `--start-date` (required) - Start date in YYYY-MM-DD format
- `--end-date` (optional) - End date in YYYY-MM-DD format, defaults to start-date
- `--dry-run` - Show what would be updated without making changes
- `--verbose` - Enable detailed logging output

**Data Validation:**
- Verifies data was successfully retrieved for sample symbols
- Checks at least 80% success rate for validation to pass
- Provides detailed feedback on update success/failure

## signal_runner.py

The `signal_runner.py` script provides comprehensive strategy analysis capabilities with four distinct analysis modes for examining trading signals across different time periods and symbols.

**Analysis Modes:**

### Mode 1: List - Get Tickers with Signals
Find all tickers that have trading signals for a date range:
```bash
uv run python scripts/signal_runner.py --mode list --start-date 2024-08-01 --end-date 2024-08-31 --trading_strategy darvas_box
```

### Mode 2: Signal - Check Individual Ticker Signal
Check if a specific ticker has a trading signal:
```bash
uv run python scripts/signal_runner.py --mode signal --tickers AAPL --start-date 2024-08-01 --end-date 2024-08-31 --trading_strategy darvas_box
```

### Mode 3: Top - Get Top Trading Signals
Get the top trading signals for a date range:
```bash
uv run python scripts/signal_runner.py --mode top --start-date 2024-08-01 --end-date 2024-08-31 --trading_strategy darvas_box
```

**Available Strategies:**
- `darvas_box` (default) - Darvas Box trend-following strategy
- `mars` - Mars momentum strategy (@marsrides)
- `momentum` - Traditional momentum strategy

**Common Options:**
- `--trading_strategy` - Trading strategy to use (default: darvas_box)
- `--mode` - Analysis mode (default: list)
- `--start-date` - Start date for analysis (YYYY-MM-DD format, required)
- `--end-date` - End date for analysis (YYYY-MM-DD format, required)
- `--tickers` - Stock ticker symbols (required for signal mode)
- `--max-tickers` - Maximum number of tickers to test (default: 10000)
- `--verbose` - Enable detailed logging

## strategy_performance.py

The `strategy_performance.py` script performs comprehensive strategy backtesting by analyzing historical signals and calculating performance metrics over specified holding periods.

**Key Features:**
- Comprehensive performance analysis with multiple metrics
- Benchmark comparison against market indices (QQQ, SPY)
- Multiple holding period analysis
- Flexible output formats (console, CSV, JSON)
- Support for custom symbol lists and limits
- Dry-run mode for testing configuration

**Usage:**
```bash
# Test Darvas Box strategy for January 2024
uv run python scripts/strategy_performance.py --strategy darvas_box --start-date 2024-01-01 --end-date 2024-01-31

# Test with custom holding period and limited symbols
uv run python scripts/strategy_performance.py --strategy mars --start-date 2024-01-01 --end-date 2024-03-31 --max-holding-period 2W --max-symbols 50

# Save results to CSV file
uv run python scripts/strategy_performance.py --strategy momentum --start-date 2024-01-01 --end-date 2024-02-29 --output csv --save results.csv

# Test specific symbols only
uv run python scripts/strategy_performance.py --strategy darvas_box --start-date 2024-01-01 --end-date 2024-01-31 --symbols "AAPL,MSFT,NVDA"
```

**Required Options:**
- `--strategy` - Strategy to test (darvas_box, mars, momentum)
- `--start-date` - Start date for signal generation (YYYY-MM-DD)
- `--end-date` - End date for signal generation (YYYY-MM-DD)

**Optional Parameters:**
- `--max-holding-period` - Maximum holding period (default: 1M, format: 3d, 1W, 2W, 1M)
- `--symbols` - Comma-separated list of specific symbols to test
- `--max-symbols` - Maximum number of symbols to test
- `--time-frame` - Time frame for analysis (DAY, WEEK, default: DAY)
- `--output` - Output format (console, csv, json, default: console)
- `--save` - Save results to specified filename
- `--verbose` - Enable detailed logging
- `--dry-run` - Show configuration without running test

**Performance Metrics:**
- Total and valid signal counts
- Average, best, and worst returns
- Win rates and success percentages
- Benchmark performance comparisons
- Period-based analysis results