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

```bash
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

1. **Configure API Keys and secrets**
    Copy .env.example -> .env and add your database password and EODHD Api key.

    ```text
    DB_PASSWORD=
    EODHD_API_KEY=
    ```

2. **Run the Download Script:**
    Run the `download-eodhd-data` command to fetch and store exchange data in your local PostgreSQL database:

    ```bash
    uv run download-eodhd-data --data exchange
    ```

    This script will fetch the latest list of exchanges and upsert them into the `turtle.exchange` table.

### Downloading Data

Use the `download-eodhd-data` command for bulk data downloads:

```bash
# Download US ticker list
uv run download-eodhd-data --data us_ticker

# Download historical data with a ticker limit (useful for testing)
uv run download-eodhd-data --data history --ticker-limit 10

# Download historical data for a specific date range
uv run download-eodhd-data --data history --start-date 2024-01-01 --end-date 2024-12-31
```

**Data Sources:**

- **Symbol lists**: EODHD API
- **Company fundamentals**: EODHD API
- **OHLCV historical data**: EODHD API

## Strategy Testing

For comprehensive strategy analysis and performance testing, use the command-line scripts:

- **`signal-runner`** (console script) - Signal analysis with multiple modes (list/signal/top)
- **`scripts/backtest.py`** - Complete signal-to-exit backtesting with configurable strategies
- **`scripts/portfolio_runner.py`** - Portfolio-level backtesting with capital constraints

See [docs/scripts.md](docs/scripts.md) for complete documentation, usage examples, and all available options.

## Services

For detailed information about the core service classes that provide the business logic layer, see [docs/service.md](docs/service.md).

## Deployment

For a guide on deploying to a Hetzner VPS (server sizing, PostgreSQL setup, systemd timers, backups), see [docs/implementation.md](docs/implementation.md).

## Architecture & Design Decisions

### Layered Architecture

```text
scripts/               ← CLI entry points (argparse, asyncio.run)
turtlex/service/       ← Business logic orchestration
turtlex/strategy/trading/         ← Trading signal strategies
turtlex/strategy/exit/           ← Exit strategies
turtlex/strategy/ranking/        ← Signal ranking strategies
turtlex/portfolio/      ← Multi-position portfolio management
turtlex/backtest/       ← Backtesting engine
turtlex/repository/   ← Repository pattern (all SQL lives here)
turtlex/model.py        ← Domain model dataclasses
turtlex/client/        ← External API clients (async)
turtlex/config/         ← Configuration loading
turtlex/common/         ← Shared utilities (iso_date_type)
turtlex/strategy/factory.py    ← Strategy factory functions (string → class mapping for CLI)
```

### Key Design Patterns

**Strategy Pattern** — All pluggable behaviours (signals, exits, rankings) implement a shared abstract base class. Services depend on the abstract type; concrete implementations are swapped at runtime. See `turtlex/strategy/trading/base.py` and `turtlex/strategy/trading/darvas_box.py`.

**Repository Pattern** — All database access is isolated in `turtlex/repository/`. No SQL outside this layer. Sync `Engine`-based repos handle reads; async `AsyncSession`-based repos handle writes.

**Dependency Injection** — All dependencies flow through constructors. The connection pool is built once in `Settings.from_toml()` and passed explicitly through `Service → Repo`. No globals or service locators.

**Configuration via Factory Method** — `Settings.from_toml()` is the single entry point for all config. It loads `config/settings.toml`, validates required environment variables (raises `ValueError` if missing — secrets are never read from TOML), and builds the connection pool.

### Async Boundary

External API clients (`turtlex/client/`) are `async`/`await` using `httpx.AsyncClient`. Services that need concurrent API requests use `asyncio.gather`. **Repositories and backtesting logic are strictly synchronous.** Scripts use `asyncio.run()` as the async entry point.

### Domain Models

- **Dataclasses** for all internal domain objects (`Signal`, `Trade`, `Position`, `Bar`). Computed fields use `@property`; no setters.
- **Pydantic `BaseModel`** only for external API responses where field aliasing is needed (e.g. `Exchange`, `Ticker` in `turtlex/schema/`).

### Database

PostgreSQL via SQLAlchemy — sync `Engine` for read-heavy analytical queries, async `AsyncSession` for bulk writes. All tables live in the `turtle` schema. Table definitions in `turtlex/repository/tables.py`. Migrations managed by Alembic in standalone mode with raw SQL (`db/migrations/versions/`).

### Adding a New Strategy

1. Create `turtlex/strategy/trading/my_strategy.py` extending `TradingStrategy`
2. Implement `generate_signals(ticker, bars_data, **kwargs) -> list[Signal]`
3. Register in `turtlex/strategy/factory.py` (`get_trading_strategy` dict)
4. Add tests in `tests/test_my_strategy.py`
