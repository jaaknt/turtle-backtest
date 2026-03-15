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

### EODHD Exchange Data

To download exchange data from EODHD, you first need to configure your EODHD API key.

1.  **Configure EODHD API Key:**
    Open `config/settings.toml` and replace `"YOUR_EODHD_API_KEY"` with your actual EODHD API key:

    ```toml
    [app]
    # ...
    eodhd.api_key = "YOUR_EODHD_API_KEY"
    # ...
    ```

2.  **Run the Download Script:**
    Execute the `scripts/download_eodhd_data.py` script to fetch and store exchange data in your local PostgreSQL database:

    ```bash
    uv run python scripts/download_eodhd_data.py
    ```
    This script will fetch the latest list of exchanges and upsert them into the `turtle.exchange` table.

### Method 1: Using the Daily EOD Update Script (Recommended)

Use the `scripts/daily_eod_update.py` script for convenient command-line data downloads with multiple update modes:

```bash
# Download symbol list from EODHD
uv run python scripts/daily_eod_update.py --mode symbols

# Download company data from Yahoo Finance
uv run python scripts/daily_eod_update.py --mode companies

# Download OHLCV data for specific date (default mode)
uv run python scripts/daily_eod_update.py --start-date 2024-12-01

# Download OHLCV data for date range
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --end-date 2024-12-07
```

See [docs/scripts.md](docs/scripts.md#daily_eod_updatepy) for complete documentation and usage examples.

### Method 2: Programmatic API

For integration into other scripts, you can use the DataUpdateService class directly:

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

- **`scripts/signal_runner.py`** - Signal analysis with multiple modes (list/signal/top)
- **`scripts/backtest.py`** - Complete signal-to-exit backtesting with configurable strategies
- **`scripts/strategy_performance.py`** - Performance backtesting with metrics and benchmarks

See [docs/scripts.md](docs/scripts.md) for complete documentation, usage examples, and all available options.

## Services

For detailed information about the core service classes that provide the business logic layer, see [docs/service.md](docs/service.md).

## Architecture & Design Decisions

### Layered Architecture

```
scripts/          ← CLI entry points (argparse, asyncio.run)
turtle/service/   ← Business logic orchestration
turtle/signal/    ← Trading signal strategies
turtle/exit/      ← Exit strategies
turtle/ranking/   ← Signal ranking strategies
turtle/portfolio/ ← Multi-position portfolio management
turtle/backtest/  ← Backtesting engine
turtle/data/      ← Repository pattern (all SQL lives here)
turtle/clients/   ← External API clients (async)
turtle/config/    ← Configuration loading
```

### Key Design Patterns

**Strategy Pattern** — All pluggable behaviours (signals, exits, rankings) implement a shared abstract base class. Services depend on the abstract type; concrete implementations are swapped at runtime. See `turtle/signal/base.py` and `turtle/signal/darvas_box.py`.

**Repository Pattern** — All database access is isolated in `turtle/data/`. No SQL outside this layer. Private `_get_*` methods fetch raw rows; public methods return typed domain objects.

**Dependency Injection** — All dependencies flow through constructors. The connection pool is built once in `Settings.from_toml()` and passed explicitly through `Service → Repo`. No globals or service locators.

**Configuration via Factory Method** — `Settings.from_toml()` is the single entry point for all config. It loads `config/settings.toml`, validates required environment variables (raises `ValueError` if missing — secrets are never read from TOML), and builds the connection pool.

### Async Boundary

External API clients (`turtle/clients/`) are `async`/`await` using `httpx.AsyncClient`. Services that need concurrent API requests use `asyncio.gather`. **Repositories and backtesting logic are strictly synchronous.** Scripts use `asyncio.run()` as the async entry point.

### Domain Models

- **Dataclasses** for all internal domain objects (`Signal`, `Trade`, `Position`, `Bar`). Computed fields use `@property`; no setters.
- **Pydantic `BaseModel`** only for external API responses where field aliasing is needed (e.g. `Exchange`, `Ticker` in `turtle/data/models.py`).

### Database

PostgreSQL with `psycopg` and a connection pool (size 10). All tables live in the `turtle` schema. Migrations managed by Alembic in standalone mode with raw SQL (`db/migrations/versions/`).

### Adding a New Strategy

1. Create `turtle/signal/my_strategy.py` extending `TradingStrategy`
2. Implement `generate_signals(ticker, bars_data, **kwargs) -> list[Signal]`
3. Register in `turtle/service/signal_service.py`
4. Add tests in `tests/test_my_strategy.py`
