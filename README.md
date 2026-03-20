# Turtle Strategy Backtester
Python library to backtest different trading strategies with US stocks

## Features
- download all relevant data from EODHD API
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

## Setup

```bash
# Start PostgreSQL database
docker-compose up -d

# Apply database migrations
uv run alembic upgrade head
```

## Download Data

### EODHD Exchange Data

To download exchange data from EODHD, you first need to configure your EODHD API key.

1.  **Configure API Keys and secrets**
    Copy .env.example -> .env and add your database password and EODHD Api key.
    ```
    DB_PASSWORD=
    EODHD_API_KEY=
    ```

2.  **Run the Download Script:**
    Execute the `scripts/download_eodhd_data.py` script to fetch and store exchange data in your local PostgreSQL database:

    ```bash
    uv run python scripts/download_eodhd_data.py
    ```
    This script will fetch the latest list of exchanges and upsert them into the `turtle.exchange` table.

### Downloading Historical Data

Use the `scripts/download_eodhd_data.py` script for bulk historical downloads:

```bash
# Download all data
uv run python scripts/download_eodhd_data.py

# Download with a ticker limit (useful for testing)
uv run python scripts/download_eodhd_data.py --ticker-limit 10

# Download for a specific date range
uv run python scripts/download_eodhd_data.py --start-date 2024-01-01 --end-date 2024-12-31
```

**Data Sources:**
- **Symbol lists**: EODHD API
- **Company fundamentals**: EODHD API
- **OHLCV historical data**: EODHD API

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
