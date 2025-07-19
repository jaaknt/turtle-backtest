# Turtle Strategy Backtester
Python library to backtest different trading strategies with US stocks

## Features
- download all relevant data free from different sources (Alpaca, Alpha Vantage, EODHD, Yahoo Finance)
- test strategies in local database

## Installation
```
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra dev

# Activate python virtualenv in bash
source ./.venv/bin/activate
```
There are special requirements for TA-lib installation - so look for [instructions](https://github.com/jaaknt/turtle-backtest/blob/main/.github/workflows/build.yml)

## Download Data

### Method 1: Using the Daily EOD Update Script (Recommended)

The `scripts/daily_eod_update.py` script provides a convenient command-line interface for downloading market data:

```bash
# Download data for a specific date
uv run python scripts/daily_eod_update.py --start-date 2024-12-01

# Download data for a date range
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --end-date 2024-12-07

# Dry run to see what would be updated without making changes
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --dry-run

# Enable verbose logging for detailed output
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --verbose

# Get help with all available options
uv run python scripts/daily_eod_update.py --help
```

**Key Features:**
- ✅ **Date validation** - Ensures correct YYYY-MM-DD format
- ✅ **Success validation** - Verifies data was downloaded correctly
- ✅ **Dry run mode** - Preview updates without making changes
- ✅ **Comprehensive logging** - Track progress and troubleshoot issues
- ✅ **Error handling** - Graceful handling of network and data issues

### Method 2: Programmatic API

For integration into other scripts, you can use the DataUpdateService class directly as shown in [main.py](https://github.com/jaaknt/turtle-backtest/blob/main/main.py):

```python
from turtle.service.data_update import DataUpdateService
from datetime import datetime

data_updater = DataUpdateService()
start_date = datetime(year=2017, month=1, day=1)
end_date = datetime(year=2024, month=12, day=7)

# Download USA Stocks symbol list (EODHD)
data_updater.update_symbol_list()

# Download USA Stocks company data (Yahoo Finance)
data_updater.update_company_list()

# Download USA Stocks daily OHLCV data (Alpaca)
# Note: exclude current date for complete data
data_updater.update_bars_history(start_date, end_date)
```

**Data Sources:**
- **Symbol lists**: EODHD API
- **Company fundamentals**: Yahoo Finance
- **OHLCV historical data**: Alpaca API

## Strategy Testing

### Strategy Runner Script

The `scripts/strategy_runner.py` script provides comprehensive strategy analysis with 4 different modes:

#### Mode 1: List - Get Tickers for Specific Date

Find all tickers that have trading signals on a specific date:

```bash
# Get tickers with Darvas Box signals on specific date
uv run python scripts/strategy_runner.py --mode list --date 2024-08-30 --strategy darvas_box

# Test Mars strategy
uv run python scripts/strategy_runner.py --mode list --date 2024-08-30 --strategy mars

# Test Momentum strategy with verbose output
uv run python scripts/strategy_runner.py --mode list --date 2024-08-30 --strategy momentum --verbose
```

**Output Example:**
```
Ticker list for 2024-08-30 (darvas_box strategy):
Found 15 tickers:
  AAPL
  MSFT
  NVDA
  ...
```

#### Mode 2: Count - Get Signal Counts for Date Range

Count how many signals each ticker generated over a date range:

```bash
# Count signals over a date range using Darvas Box strategy
uv run python scripts/strategy_runner.py --mode count --start-date 2024-08-28 --end-date 2024-08-30 --strategy darvas_box

# Test different strategies
uv run python scripts/strategy_runner.py --mode count --start-date 2024-08-01 --end-date 2024-08-31 --strategy mars
uv run python scripts/strategy_runner.py --mode count --start-date 2024-08-01 --end-date 2024-08-31 --strategy momentum
```

**Output Example:**
```
Ticker counts from 2024-08-28 to 2024-08-30 (darvas_box strategy):
Found 25 tickers with signals:
  NVDA: 3 signals
  AAPL: 2 signals
  MSFT: 1 signals
  ...
```

#### Mode 3: Signal - Check Individual Ticker Signal

Check if a specific ticker has a trading signal on a specific date:

```bash
# Check if AAPL has a Darvas Box signal on specific date
uv run python scripts/strategy_runner.py --mode signal --ticker AAPL --date 2024-08-30 --strategy darvas_box

# Test different tickers and strategies
uv run python scripts/strategy_runner.py --mode signal --ticker NVDA --date 2024-08-30 --strategy mars
uv run python scripts/strategy_runner.py --mode signal --ticker TSLA --date 2024-08-30 --strategy momentum
```

**Output Example:**
```
Trading signal check for AAPL on 2024-08-30 (darvas_box strategy):
  ✓ AAPL has a trading signal on 2024-08-30
```

#### Mode 4: Signal Count - Count Signals for Specific Ticker

Count how many signals a specific ticker generated over a date range:

```bash
# Count AAPL signals over date range
uv run python scripts/strategy_runner.py --mode signal_count --ticker AAPL --start-date 2024-08-01 --end-date 2024-08-31 --strategy darvas_box

# Test different tickers and strategies
uv run python scripts/strategy_runner.py --mode signal_count --ticker NVDA --start-date 2024-07-01 --end-date 2024-07-31 --strategy mars
uv run python scripts/strategy_runner.py --mode signal_count --ticker TSLA --start-date 2024-06-01 --end-date 2024-06-30 --strategy momentum
```

**Output Example:**
```
Signal count for AAPL from 2024-08-01 to 2024-08-31 (darvas_box strategy):
  AAPL: 7 signals
```

### Available Trading Strategies

1. **`darvas_box`** (default) - Darvas Box trend-following strategy
2. **`mars`** - Mars momentum strategy (@marsrides)  
3. **`momentum`** - Traditional momentum strategy

### Strategy Runner Options

```bash
# Get complete help with all options
uv run python scripts/strategy_runner.py --help

# Common options
--strategy {darvas_box,mars,momentum}    # Trading strategy (default: darvas_box)
--mode {list,count,signal,signal_count} # Analysis mode (default: list)
--date YYYY-MM-DD                       # Single date (for list/signal modes)
--start-date YYYY-MM-DD                 # Start date (for count/signal_count modes)  
--end-date YYYY-MM-DD                   # End date (for count/signal_count modes)
--ticker SYMBOL                         # Stock ticker (for signal/signal_count modes)
--verbose                               # Enable detailed logging
```

### Example Workflows

#### Complete Strategy Comparison
```bash
# Compare all strategies for the same date
uv run python scripts/strategy_runner.py --mode list --date 2024-08-30 --strategy darvas_box
uv run python scripts/strategy_runner.py --mode list --date 2024-08-30 --strategy mars  
uv run python scripts/strategy_runner.py --mode list --date 2024-08-30 --strategy momentum

# Compare signal counts over longer periods
uv run python scripts/strategy_runner.py --mode count --start-date 2024-08-01 --end-date 2024-08-31 --strategy darvas_box
uv run python scripts/strategy_runner.py --mode count --start-date 2024-08-01 --end-date 2024-08-31 --strategy mars
```

#### Individual Stock Analysis
```bash
# Deep dive into specific stock across strategies
uv run python scripts/strategy_runner.py --mode signal --ticker AAPL --date 2024-08-30 --strategy darvas_box
uv run python scripts/strategy_runner.py --mode signal --ticker AAPL --date 2024-08-30 --strategy mars
uv run python scripts/strategy_runner.py --mode signal --ticker AAPL --date 2024-08-30 --strategy momentum

# Analyze signal frequency for specific stock
uv run python scripts/strategy_runner.py --mode signal_count --ticker AAPL --start-date 2024-01-01 --end-date 2024-12-31 --strategy darvas_box
```
