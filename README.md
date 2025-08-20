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

Use the `scripts/daily_eod_update.py` script for convenient command-line data downloads. See [scripts.md](scripts.md#daily_eod_updatepy) for complete documentation and usage examples.

### Method 2: Programmatic API

For integration into other scripts, you can use the DataUpdateService class directly as shown in [main.py](https://github.com/jaaknt/turtle-backtest/blob/main/main.py):

```python
from turtle.service.data_update_service import DataUpdateService
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

For comprehensive strategy analysis and performance testing, use the command-line scripts:

- **`scripts/strategy_runner.py`** - Strategy analysis with 4 modes (list/count/signal/signal_count)
- **`scripts/strategy_performance.py`** - Performance backtesting with metrics and benchmarks

See [scripts.md](scripts.md) for complete documentation, usage examples, and all available options.

## Services

For detailed information about the core service classes that provide the business logic layer, see [service.md](service.md).
