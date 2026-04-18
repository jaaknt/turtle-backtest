# Turtle Strategy Backtester
Python library to backtest different trading strategies with US stocks

## Features
- Download all relevant data from EODHD API (exchanges, tickers, company fundamentals, OHLCV history)
- Trading strategies: Darvas Box, Mars, Momentum
- Exit strategies: Buy and Hold, Profit/Loss, EMA, MACD, ATR, Trailing Percentage Loss
- Ranking strategies: Momentum, Volume Momentum, Breakout Quality
- Single-ticker backtesting with benchmark comparison
- Portfolio-level backtesting with capital constraints and position sizing
- HTML tearsheet generation with performance analytics

## Installation
```
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra dev

# Activate python virtualenv in bash
source ./.venv/bin/activate
```

## Development

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
    uv run python scripts/download_eodhd_data.py --data exchange
    ```
    This script will fetch the latest list of exchanges and upsert them into the `turtle.exchange` table.

### Downloading Data

Use the `scripts/download_eodhd_data.py` script for bulk data downloads:

```bash
# Download US ticker list
uv run python scripts/download_eodhd_data.py --data us_ticker

# Download historical data with a ticker limit (useful for testing)
uv run python scripts/download_eodhd_data.py --data history --ticker-limit 10

# Download historical data for a specific date range
uv run python scripts/download_eodhd_data.py --data history --start-date 2024-01-01 --end-date 2024-12-31
```

**Data Sources:**
- **Symbol lists**: EODHD API
- **Company fundamentals**: EODHD API
- **OHLCV historical data**: EODHD API

## Strategy Testing

For comprehensive strategy analysis and performance testing, use the command-line scripts:

- **`scripts/signal_runner.py`** - Signal analysis with multiple modes (list/signal/top)
- **`scripts/backtest.py`** - Complete signal-to-exit backtesting with configurable strategies
- **`scripts/portfolio_runner.py`** - Portfolio-level backtesting with capital constraints

See [docs/scripts.md](docs/scripts.md) for complete documentation, usage examples, and all available options.

## Services

For detailed information about the core service classes that provide the business logic layer, see [docs/service.md](docs/service.md).

## Deployment

For a guide on deploying to a Hetzner VPS (server sizing, PostgreSQL setup, systemd timers, backups), see [docs/implementation.md](docs/implementation.md).

## Architecture & Design Decisions

### Layered Architecture

```
scripts/               ← CLI entry points (argparse, asyncio.run)
turtle/service/       ← Business logic orchestration
turtle/strategy/trading/         ← Trading signal strategies
turtle/strategy/exit/           ← Exit strategies
turtle/strategy/ranking/        ← Signal ranking strategies
turtle/portfolio/      ← Multi-position portfolio management
turtle/backtest/       ← Backtesting engine
turtle/repository/   ← Repository pattern (all SQL lives here)
turtle/data/           ← Domain model dataclasses
turtle/client/        ← External API clients (async)
turtle/config/         ← Configuration loading
turtle/common/         ← Shared utilities (iso_date_type, safe_float_conversion)
turtle/strategy/factory.py    ← Strategy factory functions (string → class mapping for CLI)
```

### Key Design Patterns

**Strategy Pattern** — All pluggable behaviours (signals, exits, rankings) implement a shared abstract base class. Services depend on the abstract type; concrete implementations are swapped at runtime. See `turtle/strategy/trading/base.py` and `turtle/strategy/trading/darvas_box.py`.

**Repository Pattern** — All database access is isolated in `turtle/repository/`. No SQL outside this layer. Sync `Engine`-based repos handle reads; async `AsyncSession`-based repos handle writes.

**Dependency Injection** — All dependencies flow through constructors. The connection pool is built once in `Settings.from_toml()` and passed explicitly through `Service → Repo`. No globals or service locators.

**Configuration via Factory Method** — `Settings.from_toml()` is the single entry point for all config. It loads `config/settings.toml`, validates required environment variables (raises `ValueError` if missing — secrets are never read from TOML), and builds the connection pool.

### Async Boundary

External API clients (`turtle/client/`) are `async`/`await` using `httpx.AsyncClient`. Services that need concurrent API requests use `asyncio.gather`. **Repositories and backtesting logic are strictly synchronous.** Scripts use `asyncio.run()` as the async entry point.

### Domain Models

- **Dataclasses** for all internal domain objects (`Signal`, `Trade`, `Position`, `Bar`). Computed fields use `@property`; no setters.
- **Pydantic `BaseModel`** only for external API responses where field aliasing is needed (e.g. `Exchange`, `Ticker` in `turtle/schema/`).

### Database

PostgreSQL via SQLAlchemy — sync `Engine` for read-heavy analytical queries, async `AsyncSession` for bulk writes. All tables live in the `turtle` schema. Table definitions in `turtle/repository/tables.py`. Migrations managed by Alembic in standalone mode with raw SQL (`db/migrations/versions/`).

### Adding a New Strategy

1. Create `turtle/strategy/trading/my_strategy.py` extending `TradingStrategy`
2. Implement `generate_signals(ticker, bars_data, **kwargs) -> list[Signal]`
3. Register in `turtle/strategy/factory.py` (`get_trading_strategy` dict)
4. Add tests in `tests/test_my_strategy.py`
