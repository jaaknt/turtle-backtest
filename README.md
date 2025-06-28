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

## Download data
There are examples in [main.py](https://github.com/jaaknt/turtle-backtest/blob/main/main.py)
- Download USA Stocks symbol list (EODHD)
- Download USA Stocks company data (Yahoo)
- Download USA Stocks daily data (Alpaca)

```
data_updater = DataUpdate()
start_date: datetime = datetime(year=2017, month=1, day=1)  # 
end_date: datetime = datetime(year=2024, month=8, day=30)  # 

# Download USA Stocks symbol list
data_updater.update_symbol_list()

# Download USA Stocks company data (Yahoo)
data_updater.update_company_list()

# Download USA Stocks daily data
# !! exclude current date
data_updater.update_bars_history(start_date, end_date)

```
