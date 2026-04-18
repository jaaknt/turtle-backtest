# CLAUDE.md

Python-based financial trading strategy backtesting library for US stocks. Supports multiple strategies (Darvas Box, Mars, Momentum), portfolio management, and market data via EODHD API. Data stored in PostgreSQL.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.


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
- **Strategies**: `/turtle/strategy/trading/*.py` - Trading signal implementations
- **Exit Strategies**: `/turtle/strategy/exit/*.py` - Position exit logic
- **Portfolio**: `/turtle/portfolio/*.py` - Multi-position management
- **Services**: `/turtle/service/*.py` - Business logic orchestration

### Development Decision Tree

**Want to analyze market signals?** → Use `scripts/signal_runner.py --mode analyze`

**Want to test a strategy on one ticker?** → Use `scripts/backtest.py --ticker SYMBOL`

**Want to test portfolio performance?** → Use `scripts/portfolio_runner.py` with date range

**Need historical data?** → Use `scripts/download_eodhd_data.py` for bulk historical downloads

## MCP Servers

Configured in `.mcp.json`. Prefer these over CLI equivalents when the operation is supported (`github` over `gh`, `postgres` for direct queries). Use built-in Read/Edit/Grep/Glob tools instead of `filesystem` for code operations.

| Server | Purpose |
|--------|---------|
| `postgres` | Direct read-only SQL queries against `trading` db as `claude` user (`hetzner:5432`). Requires `DB_CLAUDE_PASSWORD` env var. |
| `github` | GitHub API — issues, PRs, commits, actions (prefer over `gh` CLI when supported). Requires `GITHUB_PERSONAL_ACCESS_TOKEN` env var. |
| `context7` | Fetch current library/framework docs |
| `filesystem` | File operations — prefer built-in Read/Edit/Grep/Glob instead |
| `playwright` | Browser automation and UI testing |
| `sequential-thinking` | Structured multi-step reasoning for complex multi-condition problems |
| `fetch` | HTTP fetch for external URLs |

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

## Architecture Overview

### Core Components
- **turtle/common/**: Shared enums and utilities
  - `enums.py`: `TimeFrameUnit` enum (DAY, WEEK)
  - `cli.py`: `iso_date_type` — argparse type helper for ISO date strings (YYYY-MM-DD)
  - `pandas_utils.py`: `safe_float_conversion` — safe pandas scalar → float coercion
- **turtle/strategy/factory.py**: Strategy factories for CLI scripts — canonical string → lambda factory mapping for trading, exit, and ranking strategies (`get_trading_strategy`, `get_exit_strategy`, `get_ranking_strategy`). Each entry is a `Callable[[], StrategyBase]` lambda that closes over the required dependencies, so concrete constructors are called directly rather than through the abstract base type.
- **turtle/repository/**: All database access (sync Engine reads + async Session writes)
  - `tables.py`: SQLAlchemy Core table definitions
  - `analytics.py`: `OhlcvAnalyticsRepository` — bulk OHLCV reads returning DataFrames (pandas/polars)
  - `symbol_group.py`: `SymbolGroupRepository` — symbol group reads/writes
  - `eodhd/`: `ExchangeRepository`, `TickerRepository`, `TickerQueryRepository`, `DailyBarsRepository`, `CompanyRepository`
- **turtle/strategy/trading/**: Trading signal implementations
  - `base.py`: TradingStrategy abstract base
  - `darvas_box.py`, `mars.py`, `momentum.py`, `market.py`
- **turtle/strategy/exit/**: Exit strategy implementations
  - `base.py`: ExitStrategy abstract base
  - `buy_and_hold.py`, `profit_loss.py`, `ema.py`, `macd.py`, `atr.py`, `trailing_percentage_loss.py`
- **turtle/backtest/**: Backtesting engine
  - `processor.py`, `portfolio_processor.py`, `benchmark_utils.py`
- **turtle/portfolio/**: Multi-position portfolio management
  - `manager.py`, `selector.py`, `analytics.py`
- **turtle/strategy/ranking/**: Signal ranking strategies — `momentum.py`, `volume_momentum.py`, `breakout_quality.py` (see [docs/strategy.md](docs/strategy.md))
- **turtle/client/**: External API clients
  - `eodhd.py`: EODHD API wrapper
- **turtle/config/**: Configuration management
  - `settings.py`: TOML + environment variable loader
  - `model.py`: Config dataclasses (`DatabaseConfig`, `AppConfig`, `DatabasePoolConfig`)
  - `logging.py`: Logging configuration
- **turtle/logger/**: JSON structured logging handler
- **turtle/schema/**: Pydantic models for external API responses
  - `eodhd/`: `exchange.py` → `Exchange`, `ticker.py` → `Ticker`, `company.py` → `Company`, `daily_bars.py` → `DailyBars`
- **turtle/service/**: Business logic orchestration layer

### Database
- **Schema**: `turtle` (PostgreSQL)
- **Tables**: `ticker`, `daily_bars`, `company`, `symbol_group`, `exchange`
- **Connection**: SQLAlchemy `Engine` (sync reads) + `AsyncSession` (async writes)

## Core Systems Overview

### Portfolio Management
- **PortfolioManager**: Position/cash management, daily snapshots, position sizing with min/max constraints
- **PortfolioSignalSelector**: Signal ranking and filtering, position limits, minimum ranking threshold
- **PortfolioAnalytics**: Performance metrics (Sharpe, Sortino, Max DD, win rate), benchmark comparison

### Configuration System
- **Settings**: TOML-based with environment variable overrides for secrets
- **Key Files**: `config/settings.toml`, `.env` (API keys, DB password)
- **Environment Variables**: `EODHD_API_KEY`, `DB_APP_PASSWORD` (required by app; see `turtle/config/settings.py`)
- **Database DSN**: `host=localhost port=5432 dbname=trading user=app_user`

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

1. **Create strategy file**: `turtle/strategy/trading/my_strategy.py`
2. **Extend TradingStrategy base class**:
   ```python
   from turtle.strategy.trading.base import TradingStrategy
   from turtle.strategy.trading.models import Signal

   class MyStrategy(TradingStrategy):
       def collect_data(self, ticker: str, start_date: date, end_date: date) -> bool:
           ...

       def calculate_indicators(self) -> None:
           ...

       def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
           # Your logic here
           return signals
   ```
3. **Add tests**: `tests/test_my_strategy.py`
4. **Wire via dependency injection**: Instantiate your strategy and pass it to the service constructor — see `scripts/signal_runner.py` (`get_trading_strategy`) for the canonical wiring pattern
5. **Test**: `uv run python scripts/signal_runner.py --strategy my_strategy --mode analyze`

## Examples Directory

| Example | Purpose | Command |
|---------|---------|---------|
| **backtesting.ipynb** | Interactive single-strategy backtesting with visualizations | `uv run jupyter notebook examples/backtesting.ipynb` |
| **portfolio_backtesting.ipynb** | Portfolio-level backtesting with multiple positions | `uv run jupyter notebook examples/portfolio_backtesting.ipynb` |
| **symbol_group.ipynb** | Managing custom symbol groups (watchlists) | `uv run jupyter notebook examples/symbol_group.ipynb` |
| **pandas.ipynb** | Data analysis and exploration | `uv run jupyter notebook examples/pandas.ipynb` |
| **portfolio_backtest_example.py** | Programmatic portfolio backtesting template | `uv run python examples/portfolio_backtest_example.py` |
| **portfolio_backtest_api_demo.py** | API-style portfolio backtesting demo | `uv run python examples/portfolio_backtest_api_demo.py` |

## Design Patterns & Principles

### Strategy Pattern (Abstract Base Classes)
All pluggable behaviours — signals, exits, rankings — share a common ABC interface. Services depend on the abstract type; concrete implementations are swapped at runtime without changing any service code. See `turtle/strategy/trading/base.py` (base) and `turtle/strategy/trading/darvas_box.py` (concrete). Same pattern in `turtle/strategy/exit/` and `turtle/strategy/ranking/`.

### Repository Pattern (Data Access)
All database operations live in `turtle/repository/`. No SQL outside this directory. Sync `Engine`-based repos handle reads; async `AsyncSession`-based repos handle writes. See `turtle/repository/analytics.py` (sync reads) and `turtle/repository/eodhd/` (async writes).

### Dependency Injection (Constructor Injection)
All dependencies are passed explicitly through constructors — no globals, no service locators. The connection pool flows from `Settings` → `Service` → `Repo`. See `turtle/service/signal_service.py`.

### Domain Models (Dataclasses vs Pydantic)
- **Dataclasses** for all internal domain objects (`Signal`, `Trade`, `Position`). Use `@property` for computed fields — no setters. See `turtle/strategy/trading/models.py`, `turtle/backtest/models.py`, `turtle/portfolio/models.py`.
- **Pydantic `BaseModel`** only for external API responses where field aliasing (`alias=`) is needed. See `Exchange`, `Ticker`, `Company` in `turtle/schema/`.

### Configuration (Factory Method)
`Settings.from_toml()` is the single entry point for all config. It loads TOML, validates required env vars (raises `ValueError` if missing — never falls back to TOML values for secrets), builds nested config objects, and creates the connection pool. See `turtle/config/settings.py`.

### Async Boundary
External API clients (`turtle/client/eodhd.py`) are `async`/`await` using `httpx.AsyncClient`. Services that orchestrate bulk API downloads (e.g. `turtle/service/eodhd_service.py`) may also be async when they need concurrent requests via `asyncio.gather`. Repos and backtesting logic must remain synchronous. Scripts may use `asyncio.run()` as the async entry point. Do not make repo methods async.

### Naming Conventions
| Construct | Convention | Example |
|-----------|-----------|---------|
| Classes | PascalCase | `DarvasBoxStrategy`, `OhlcvAnalyticsRepository` |
| Methods / variables | snake_case | `get_signals()`, `start_date` |
| Private methods | leading underscore | `_get_bars_history_db()` |
| Constants / enums | UPPER_SNAKE_CASE | `TimeFrameUnit.DAY` |
| Files | snake_case | `bars_history.py`, `darvas_box.py` |
| Folders / packages | singular snake_case | `turtle/service/`, `turtle/repository/` |

### Type Hints
All function signatures carry full type hints — parameters and return types. Use `X | None` (not `Optional[X]`), `list[X]` (not `List[X]`). No `Any` except at external API boundaries.

### Logging
One module-level logger per file via `logging.getLogger(__name__)`. Use `DEBUG` for decision points and data values; `WARNING`/`ERROR` for anomalies and failures. Never log secrets or API keys.

### Error Handling
Validate preconditions early and return `bool` (for data-collection methods) or raise `ValueError` with a descriptive message. No bare `except` clauses. No swallowed exceptions. Properties validate their preconditions before computing.

### Static Methods
Use `@staticmethod` for pure utility functions that belong logically to a class but require no instance state. See `DarvasBoxStrategy.check_local_max()` in `turtle/strategy/trading/darvas_box.py`.

## Testing

Tests organised by component in `tests/`:
- `test_darvas_box.py`: Darvas Box strategy logic
- `test_signal_processor.py`: Signal processing pipeline
- `test_portfolio.py`: Portfolio management and analytics
- `exit/test_macd_exit_strategy.py`: MACD exit strategy logic
- `exit/test_atr_exit_strategy.py`: ATR exit strategy logic
- `exit/test_ema_exit_strategy.py`: EMA exit strategy logic
- `exit/test_buy_and_hold_exit_strategy.py`: Buy and hold exit strategy logic
- `exit/test_profit_loss_exit_strategy.py`: Profit/loss exit strategy logic
- `exit/test_trailing_percentage_loss_exit_strategy.py`: Trailing percentage loss exit strategy logic
- `test_volume_momentum_ranking.py`: Volume momentum ranking strategy
- `test_breakout_quality_ranking.py`: Breakout quality ranking strategy
- `test_ohlcv_analytics_repository.py`: OhlcvAnalyticsRepository (pandas/polars reads)
- `test_repositories_eodhd.py`: EODHD repository classes (exchange, ticker, daily bars, company)
- `test_pandas_ta_ema.py`: pandas-ta EMA indicator
- `test_settings.py`: Configuration loading
- `test_api_token_filter.py`: API token filter logic

Shared fixtures live in `tests/conftest.py`. File-specific fixtures stay in the individual test file.

Run with `uv run pytest` or `uv run pytest tests/test_specific.py`.

## Dependencies & Resources

**Core Libraries**: pandas/numpy (data), polars (fast DataFrames), pandas-ta (technical analysis), pydantic (schema validation), alpaca-py (market data API), yfinance (Yahoo Finance), psycopg (PostgreSQL), backtesting (backtest framework), quantstats (performance analytics), streamlit (web UI), plotly/bokeh (visualization)

**Special Requirements**: Python 3.13+
