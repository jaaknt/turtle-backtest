# CLAUDE.md

Python-based financial trading strategy backtesting library for US stocks. Supports multiple strategies (Darvas Box, Mars, Momentum), portfolio management, and market data via EODHD API. Data stored in PostgreSQL.

## Quick Start & Common Commands

### Most Common Operations
| Task | Command | Use When |
|------|---------|----------|
| **Generate signals** | `uv run python scripts/signal_runner.py --start-date 2024-06-01 --end-date 2024-06-01 --mode analyze` | Analyze trading opportunities |
| **Portfolio backtest** | `uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31` | Test multi-position strategy |
| **Single backtest** | `uv run python scripts/backtest.py --ticker AAPL --start-date 2024-01-01` | Test specific ticker |
| **Run tests** | `uv run pytest` | Verify code changes |
| **Start database** | `docker-compose up -d` | Before any data operations |

### Critical File Paths
- **Configuration**: `/config/settings.toml` + `.env` for API keys
- **Strategies**: `/turtle/signal/*.py` - Trading signal implementations
- **Exit Strategies**: `/turtle/exit/*.py` - Position exit logic
- **Portfolio**: `/turtle/portfolio/*.py` - Multi-position management
- **Services**: `/turtle/services/*.py` - Business logic orchestration

### Development Decision Tree

**Want to analyze market signals?** → Use `scripts/signal_runner.py --mode analyze`

**Want to test a strategy on one ticker?** → Use `scripts/backtest.py --ticker SYMBOL`

**Want to test portfolio performance?** → Use `scripts/portfolio_runner.py` with date range

**Need historical data?** → Use `scripts/download_eodhd_data.py` for bulk historical downloads

## Git Workflow

Trunk-based development — commit directly to `main`, no pull requests or feature branches.

## Development Setup

| Command | Purpose |
|---------|---------|
| `uv sync --extra dev --extra lint` | Install dependencies |
| `source ./.venv/bin/activate` | Activate virtual environment |
| `docker-compose up -d` | Start PostgreSQL database |
| `uv run pytest` | Run all tests |
| `uv run alembic upgrade head` | Apply database migrations |

## Scripts Quick Reference

| Script | Purpose | Key Parameters | Example |
|--------|---------|----------------|---------|
| **download_eodhd_data.py** | Bulk historical download | `--ticker-limit`, `--start-date`, `--end-date` | `uv run python scripts/download_eodhd_data.py --ticker-limit 10` |
| **signal_runner.py** | Generate/analyze signals | `--strategy`, `--mode` (analyze/csv/db) | `uv run python scripts/signal_runner.py --start-date 2024-06-01 --end-date 2024-06-01 --strategy darvas_box --mode analyze` |
| **backtest.py** | Single ticker backtest | `--ticker`, `--signal-strategy`, `--exit-strategy` | `uv run python scripts/backtest.py --ticker AAPL --start-date 2024-01-01 --end-date 2024-12-31 --signal-strategy darvas_box --exit-strategy profit_loss` |
| **portfolio_runner.py** | Portfolio backtest | `--trading-strategy`, `--ranking-strategy`, `--initial-capital`, `--output-file` | `uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --output-file results.html` |

**Use `--help` flag with any script for complete parameter documentation.**

## Architecture Overview

### Core Components
- **turtle/data/**: Shared domain models (`models.py` — dataclasses for `Symbol`, `SymbolGroup`, `Bar`)
- **turtle/repositories/**: All database access (sync Engine reads + async Session writes)
  - `tables.py`: SQLAlchemy Core table definitions
  - `analytics.py`: `OhlcvAnalyticsRepository` — bulk OHLCV reads returning DataFrames (pandas/polars)
  - `symbol_group.py`: `SymbolGroupRepository` — symbol group reads/writes
  - `eodhd/`: `ExchangeRepository`, `TickerRepository`, `TickerQueryRepository`, `DailyBarsRepository`, `CompanyRepository`
- **turtle/signal/**: Trading signal implementations
  - `base.py`: TradingStrategy abstract base
  - `darvas_box.py`, `mars.py`, `momentum.py`, `market.py`
- **turtle/exit/**: Exit strategy implementations
  - `base.py`: ExitStrategy abstract base
  - `buy_and_hold.py`, `profit_loss.py`, `ema.py`, `macd.py`, `atr.py`
- **turtle/backtest/**: Backtesting engine
  - `processor.py`, `portfolio_processor.py`, `benchmark_utils.py`
- **turtle/portfolio/**: Multi-position portfolio management
  - `manager.py`, `selector.py`, `analytics.py`
- **turtle/ranking/**: Signal ranking strategies
  - `momentum.py`, `volume_momentum.py`
- **turtle/clients/**: External API clients
  - `eodhd.py`: EODHD API wrapper
- **turtle/config/**: Configuration management
  - `settings.py`: TOML + environment variable loader
- **turtle/services/**: Business logic orchestration layer

### Database
- **Schema**: `turtle` (PostgreSQL)
- **Tables**: `ticker`, `daily_bars`, `company`, `symbol_group`, `exchange`
- **Connection**: SQLAlchemy `Engine` (sync reads) + `AsyncSession` (async writes)

### Data Sources
- **EODHD**: Symbol lists, historical OHLCV data, company fundamentals

## Core Systems Overview

### Portfolio Management
- **PortfolioManager**: Position/cash management, daily snapshots, position sizing with min/max constraints
- **PortfolioSignalSelector**: Signal ranking and filtering, position limits, minimum ranking threshold
- **PortfolioAnalytics**: Performance metrics (Sharpe, Sortino, Max DD, win rate), benchmark comparison

### Configuration System
- **Settings**: TOML-based with environment variable overrides for secrets
- **Key Files**: `config/settings.toml`, `.env` (API keys, DB password)
- **Environment Variables**: `EODHD_API_KEY`, `DB_PASSWORD`
- **Database DSN**: `host=localhost port=5432 dbname=trading user=postgres`

### Service Layer
| Service | Purpose | Key Methods | Used By |
|---------|---------|-------------|---------|
| **SignalService** | Signal generation and export | `generate_signals()`, `filter_by_ranking()` | `signal_runner.py` |
| **BacktestService** | Single-ticker backtesting | `run_backtest()`, `calculate_metrics()` | `backtest.py` |
| **PortfolioService** | Multi-position portfolio backtest | `run_portfolio_backtest()`, `generate_tearsheet()`, `calculate_benchmark_comparison()` | `portfolio_runner.py` |
| **EODHDService** | EODHD API operations | `fetch_eod_data()`, `fetch_ticker_list()`, `validate_response()` | `DataUpdateService` |

### Ranking System
Filters and prioritizes signals for portfolio selection. Returns scores 0-100 (higher = stronger signal).

**Available Strategies:**
- **MomentumRanking**: Price momentum over lookback period (default: 20 days)
- **VolumeMomentumRanking**: Combined price + volume momentum (weights: 0.7 price, 0.3 volume)

**Usage in portfolio backtesting:** Applied by `PortfolioSignalSelector` with configurable `min_ranking` threshold.

## Database Migrations

| Command | Purpose |
|---------|---------|
| `uv run alembic current` | Check current migration version |
| `uv run alembic history` | Show migration history |
| `uv run alembic upgrade head` | Apply all pending migrations |
| `uv run alembic downgrade -1` | Rollback one migration |
| `uv run alembic revision -m "description"` | Create new migration |

**Architecture**: Alembic standalone mode with raw SQL. Migrations in `db/migrations/versions/`. Version table in `turtle.alembic_version`.

## Development Workflows

### Adding a New Trading Strategy

1. **Create strategy file**: `turtle/signal/my_strategy.py`
2. **Extend TradingStrategy base class**:
   ```python
   from turtle.signal.base import TradingStrategy
   from turtle.signal.models import Signal

   class MyStrategy(TradingStrategy):
       def generate_signals(self, ticker: str, bars_data: pd.DataFrame, **kwargs) -> list[Signal]:
           # Your logic here
           return signals
   ```
3. **Add tests**: `tests/test_my_strategy.py`
4. **Register in SignalService**: Add to strategy mapping in `turtle/services/signal_service.py`
5. **Test**: `uv run python scripts/signal_runner.py --strategy my_strategy --mode analyze`

### Running Portfolio Backtests

**Basic workflow:**
```bash
# 1. Update data
uv run python scripts/download_eodhd_data.py --start-date 2024-01-01 --end-date 2024-12-31

# 2. Generate signals (optional - validate)
uv run python scripts/signal_runner.py --start-date 2024-01-01 --end-date 2024-01-31 --strategy darvas_box --mode analyze

# 3. Run backtest
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --output-file results.html

# 4. Review results
open reports/results.html
```

**Advanced options**: Use `--ranking-strategy`, `--exit-strategy`, `--initial-capital`, `--position-min-amount`, `--min-signal-ranking` to customize.

## Examples Directory

| Example | Purpose | Command |
|---------|---------|---------|
| **backtesting.ipynb** | Interactive single-strategy backtesting with visualizations | `uv run jupyter notebook examples/backtesting.ipynb` |
| **portfolio_backtesting.ipynb** | Portfolio-level backtesting with multiple positions | `uv run jupyter notebook examples/portfolio_backtesting.ipynb` |
| **symbol_group.ipynb** | Managing custom symbol groups (watchlists) | `uv run jupyter notebook examples/symbol_group.ipynb` |
| **pandas.ipynb** | Data analysis and exploration | `uv run jupyter notebook examples/pandas.ipynb` |
| **portfolio_backtest_example.py** | Programmatic portfolio backtesting template | `uv run python examples/portfolio_backtest_example.py` |
| **portfolio_backtest_api_demo.py** | API-style portfolio backtesting demo | `uv run python examples/portfolio_backtest_api_demo.py` |

## Troubleshooting Quick Reference

| Problem | Quick Fix | Details |
|---------|-----------|---------|
| **Database connection failed** | `docker-compose ps` to verify postgres running, check `.env` credentials | Verify DB exists with `psql -U postgres -l`, test port 5432 access |
| **API rate limiting** | Use `--ticker-limit 10` for testing, verify API keys in `.env` | Check EODHD_API_KEY active, typical limit 20 req/sec |
| **No signals generated** | Verify data exists: `SELECT COUNT(*) FROM turtle.daily_bars WHERE symbol='AAPL'`, enable `--verbose` | Check ticker has sufficient history, validate strategy parameters |
| **Portfolio backtest errors** | Lower `--min-signal-ranking`, verify `initial_capital >= position_max_amount * max_positions` | Ensure signals exist for date range, validate benchmark data (SPY/QQQ) |
| **Slow queries/high memory** | Add indexes: `CREATE INDEX idx_daily_bars_symbol_date ON turtle.daily_bars(symbol, date)`, use `--ticker-limit` | Process data in batches |
| **Migration failures** | `uv run alembic current` to check version, `uv run alembic downgrade -1` to rollback | Review `turtle.alembic_version` table, test upgrade/downgrade paths |

**For detailed troubleshooting**: Check logs in `logs/` directory, use `--verbose` flag, consult script `--help` output.

## Design Patterns & Principles

### Strategy Pattern (Abstract Base Classes)
All pluggable behaviours — signals, exits, rankings — share a common ABC interface. Services depend on the abstract type; concrete implementations are swapped at runtime without changing any service code. See `turtle/signal/base.py` (base) and `turtle/signal/darvas_box.py` (concrete). Same pattern in `turtle/exit/` and `turtle/ranking/`.

### Repository Pattern (Data Access)
All database operations live in `turtle/repositories/`. No SQL outside this directory. Sync `Engine`-based repos handle reads; async `AsyncSession`-based repos handle writes. See `turtle/repositories/analytics.py` (sync reads) and `turtle/repositories/eodhd/` (async writes).

### Dependency Injection (Constructor Injection)
All dependencies are passed explicitly through constructors — no globals, no service locators. The connection pool flows from `Settings` → `Service` → `Repo`. See `turtle/services/signal_service.py`.

### Domain Models (Dataclasses vs Pydantic)
- **Dataclasses** for all internal domain objects (`Signal`, `Trade`, `Position`, `Bar`). Use `@property` for computed fields — no setters. See `turtle/signal/models.py`, `turtle/data/models.py`.
- **Pydantic `BaseModel`** only for external API responses where field aliasing (`alias=`) is needed. See `Exchange`, `Ticker`, `Company` in `turtle/schemas/`.

### Configuration (Factory Method)
`Settings.from_toml()` is the single entry point for all config. It loads TOML, validates required env vars (raises `ValueError` if missing — never falls back to TOML values for secrets), builds nested config objects, and creates the connection pool. See `turtle/config/settings.py`.

### Async Boundary
External API clients (`turtle/clients/eodhd.py`) are `async`/`await` using `httpx.AsyncClient`. Services that orchestrate bulk API downloads (e.g. `turtle/services/eodhd_service.py`) may also be async when they need concurrent requests via `asyncio.gather`. Repos and backtesting logic must remain synchronous. Scripts may use `asyncio.run()` as the async entry point. Do not make repo methods async.

### Naming Conventions
| Construct | Convention | Example |
|-----------|-----------|---------|
| Classes | PascalCase | `DarvasBoxStrategy`, `OhlcvAnalyticsRepository` |
| Methods / variables | snake_case | `get_signals()`, `start_date` |
| Private methods | leading underscore | `_get_bars_history_db()` |
| Constants / enums | UPPER_SNAKE_CASE | `TimeFrameUnit.DAY` |
| Files | snake_case | `bars_history.py`, `darvas_box.py` |

### Type Hints
All function signatures carry full type hints — parameters and return types. Use `X | None` (not `Optional[X]`), `list[X]` (not `List[X]`). No `Any` except at external API boundaries.

### Logging
One module-level logger per file via `logging.getLogger(__name__)`. Use `DEBUG` for decision points and data values; `WARNING`/`ERROR` for anomalies and failures. Never log secrets or API keys.

### Error Handling
Validate preconditions early and return `bool` (for data-collection methods) or raise `ValueError` with a descriptive message. No bare `except` clauses. No swallowed exceptions. Properties validate their preconditions before computing.

### Static Methods
Use `@staticmethod` for pure utility functions that belong logically to a class but require no instance state. See `DarvasBoxStrategy.check_local_max()` in `turtle/signal/darvas_box.py`.

## Testing

Tests organised by component in `tests/`:
- `test_models.py`: Data model validation
- `test_darvas_box.py`: Darvas Box strategy logic
- `test_signal_processor.py`: Signal processing pipeline
- `test_portfolio.py`: Portfolio management and analytics
- `test_macd_exit_strategy.py`: MACD exit strategy logic
- `test_atr_exit_strategy.py`: ATR exit strategy logic
- `test_volume_momentum_ranking.py`: Volume momentum ranking strategy
- `test_ohlcv_analytics_repository.py`: OhlcvAnalyticsRepository (pandas/polars reads)
- `test_repositories_eodhd.py`: EODHD repository classes (exchange, ticker, daily bars, company)
- `test_pandas_ta_ema.py`: pandas-ta EMA indicator
- `test_settings.py`: Configuration loading

Shared fixtures live in `tests/conftest.py`. File-specific fixtures stay in the individual test file.

Run with `uv run pytest` or `uv run pytest tests/test_specific.py`.

## Dependencies & Resources

**Core Libraries**: pandas/numpy (data), pandas-ta (technical analysis), alpaca-py (market data API), yfinance (Yahoo Finance), psycopg (PostgreSQL), backtesting (backtest framework), streamlit (web UI), plotly (visualization)

**Special Requirements**: Python 3.13+

**Configuration**: Environment setup via `.env` file, TOML-based settings in `config/settings.toml`

**Additional Documentation**: Full API details in code docstrings, complete examples in `examples/` directory
