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

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Refactor Etiquette

- Do NOT remove docstrings or comments when refactoring unless explicitly asked.
- Before large refactors, propose a brief plan (especially scope boundaries) and wait for confirmation.

## 6. Standard Workflow

- After non-trivial changes, run pytest and mypy before proposing a commit. Run mypy with no arguments (`uv run mypy`) — scanned paths are defined in `pyproject.toml` `[tool.mypy] files`.
- Use the PR review subagent workflow (parallel agents) before commit/push on multi-file changes.
- Polars for all new code. Pandas is intentionally retained in `turtlex/portfolio/analytics.py`, plus indirectly via `quantstats`. Don't introduce pandas elsewhere; flag any new pandas import in code review.

## Quick Start & Common Commands

### Most Common Operations

| Task | Command | Use When |
| ------ | --------- | ---------- |
| **Generate signals** | `uv run signal-runner list --start-date 2024-06-01 --end-date 2024-06-01` | Analyze trading opportunities |
| **Portfolio backtest** | `uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31` | Test multi-position strategy |
| **Single backtest** | `uv run backtest-runner --tickers AAPL --start-date 2024-01-01 --end-date 2024-01-01` | Test specific ticker |
| **Run tests** | `uv run pytest` | Verify code changes |
| **Test coverage** | `uv run pytest --cov=turtlex --cov-report=term-missing` | Find untested code paths |
| **Lint markdown docs** | `npx markdownlint-cli2` | Check README/CLAUDE.md/docs before committing (`--fix` to auto-fix) |
| **Run Bruno API smoke tests** | `uv run pytest -m bruno` | Verify live EODHD endpoints still match expectations (requires `npm install -g @usebruno/cli` + real `EODHD_API_KEY` in `bruno/eodhd/.env`) |
| **Start database** | `docker-compose up -d` | Before any data operations |

### Critical File Paths

- **Configuration**: `/config/settings.toml` + `.env` for API keys
- **Strategies**: `/turtlex/strategy/trading/*.py` - Trading signal implementations
- **Exit Strategies**: `/turtlex/strategy/exit/*.py` - Position exit logic
- **Portfolio**: `/turtlex/portfolio/*.py` - Multi-position management
- **Services**: `/turtlex/service/*.py` - Business logic orchestration
- **Domain models**: `/turtlex/model.py` - `Signal`, `Trade`, `Benchmark` dataclasses
- **Project docs**: `/docs/*.md` - `implementation.md`, `scripts.md`, `service.md`, `signal_runner.md`, `strategy.md`, `troubleshooting.md`
- **Database init & migrations**: `/db/init.sql`, `/db/init.sh`, `/db/migrations/`

### Development Decision Tree

**Want to analyze market signals?** → Use `uv run signal-runner list` (or `top` / `signal`)

**Want to test a strategy on one ticker?** → Use `uv run backtest-runner --tickers SYMBOL`

**Want to test portfolio performance?** → Use `uv run portfolio-runner` with date range

**Need historical data?** → Use `uv run download-eodhd-data` for bulk historical downloads

## MCP Servers

Configured in `.mcp.json`. Tool-selection rules are in [Tool Preferences](#tool-preferences) below.

| Server | Purpose |
| -------- | --------- |
| `postgres` | Direct read-only SQL queries against `trading` db as `claude` user (`hetzner:5432`). Requires `DB_CLAUDE_PASSWORD` env var. |
| `github` | GitHub API — issues, PRs, commits, actions (prefer over `gh` CLI when supported). Requires `GITHUB_PERSONAL_ACCESS_TOKEN` env var. |
| `context7` | Fetch current library/framework docs |
| `fetch` | HTTP fetch for external URLs |
| `codegraph` | Code-intelligence knowledge graph of this repo (indexed in `.codegraph/`) — one query returns a symbol's verbatim source plus its callers and call paths. |

## Tool Preferences

- For GitHub queries (PRs, issues, Actions, workflow runs), ALWAYS use the GitHub MCP server first. Only fall back to `gh` CLI or Bash if MCP lacks the needed tool.
- For Postgres queries, use the `mcp__postgres__query` tool with parameter name `sql` (not `query`).
- For library/framework documentation lookups, use context7 MCP rather than guessing or web search.
- For code analysis — locating a symbol, understanding how a class/function is used, tracing call paths, or assessing the blast radius of a change — use the `codegraph_explore` MCP tool (or the `codegraph explore` / `codegraph node` CLI if MCP isn't available) before grep/find or reading files one by one.

## Git Workflow

Trunk-based development — commit directly to `main`, no pull requests or feature branches.

## Development Setup

| Command | Purpose |
| --------- | --------- |
| `uv sync --extra lint` | Install dependencies |
| `source ./.venv/bin/activate` | Activate virtual environment |
| `docker-compose up -d` | Start PostgreSQL database |
| `uv run pytest` | Run all tests |
| `uv run alembic upgrade head` | Apply database migrations |

## Architecture Overview

### Repo Layout

Top-level dirs not detailed elsewhere: `db/` (schema + Alembic migrations), `docs/` (project docs), `examples/` (see [Examples Directory](#examples-directory)), `scripts/` (CLI entry points), `tests/` (mirrors source tree).

### Core Components

- **turtlex/common/**: Shared enums and utilities
  - `enums.py`: `TimeFrameUnit` enum (DAY, WEEK)
  - `cli.py`: `iso_date_type` — argparse type helper for ISO date strings (YYYY-MM-DD)
- **turtlex/model.py**: Core domain dataclasses (`Signal`, `Trade`, `Benchmark`, etc.) — single shared module; do not create per-package `models.py` files
- **turtlex/strategy/factory.py**: Strategy factories for CLI scripts — module-level registries (`TRADING_STRATEGIES`, `EXIT_STRATEGIES`, `RANKING_STRATEGIES`) hold the canonical string → class mapping for trading, exit, and ranking strategies; `get_trading_strategy` / `get_exit_strategy` / `get_ranking_strategy` instantiate from them with injected dependencies. CLIs derive their argparse `choices` from the registry keys — never hardcode strategy name lists in scripts.
- **turtlex/repository/**: All database access (sync Engine reads + async Session writes)
  - `tables.py`: SQLAlchemy Core table definitions + shared reference constants (`US_EXCHANGES`, `COMMON_STOCK_TYPE`)
  - `query/`: sync Engine-based analytical reads — `daily_bars.py` → `DailyBarsQueryRepository` (bulk OHLCV reads returning polars DataFrames), `ticker.py` → `TickerQueryRepository` (symbol groups, fundamentals-qualified lists)
  - `ingest/`: async Session-based repositories for the EODHD download path — `ExchangeRepository`, `TickerRepository`, `DailyBarsRepository`, `CompanyRepository`
- **turtlex/strategy/trading/**: Trading signal implementations
  - `base.py`: TradingStrategy abstract base
  - `darvas_box.py`, `mars.py`, `momentum.py`
- **turtlex/strategy/exit/**: Exit strategy implementations
  - `base.py`: ExitStrategy abstract base
  - `buy_and_hold.py`, `profit_loss.py`, `ema.py`, `macd.py`, `atr.py`, `trailing_percentage_loss.py`
- **turtlex/backtest/**: Backtesting engine
  - `processor.py`, `benchmark_utils.py`
- **turtlex/portfolio/**: Multi-position portfolio management
  - `manager.py`, `selector.py`, `analytics.py`
- **turtlex/strategy/ranking/**: Signal ranking strategies — `momentum.py`, `volume_momentum.py`, `breakout_quality.py`, `qullamaggie.py` (see [docs/strategy.md](docs/strategy.md))
- **turtlex/client/**: External API clients
  - `eodhd.py`: EODHD API wrapper
- **turtlex/config/**: Configuration management
  - `settings.py`: TOML + environment variable loader
  - `model.py`: Config dataclasses (`DatabaseConfig`, `AppConfig`, `DatabasePoolConfig`)
  - `logging.py`: Logging configuration
- **turtlex/schema/**: Pydantic models for external API responses (EODHD)
  - `exchange.py` → `Exchange`, `ticker.py` → `Ticker`, `company.py` → `Company`, `daily_bars.py` → `DailyBars`
- **turtlex/service/**: Business logic orchestration layer

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
- **Environment Variables**: `EODHD_API_KEY`, `DB_APP_PASSWORD` (required by app; see `turtlex/config/settings.py`)
- **Database DSN**: `host=localhost port=5432 dbname=trading user=app_user`

## Database Migrations

| Command | Purpose |
| --------- | --------- |
| `uv run alembic current` | Check current migration version |
| `uv run alembic history` | Show migration history |
| `uv run alembic upgrade head` | Apply all pending migrations |
| `uv run alembic downgrade -1` | Rollback one migration |
| `uv run alembic revision -m "description"` | Create new migration |

**Architecture**: Alembic standalone mode with raw SQL. Migrations in `db/migrations/versions/`. Version table in `public.alembic_version`. Target database selected via `DB_ENV` (`local` default, `hetzner` for the VPS).

## Development Workflows

### Adding a New Trading Strategy

1. **Create strategy file**: `turtlex/strategy/trading/my_strategy.py`
2. **Extend TradingStrategy base class**:

   ```python
   from turtlex.model import Signal
   from turtlex.strategy.trading.base import TradingStrategy

   class MyStrategy(TradingStrategy):
       def collect_data(self, ticker: str, start_date: date, end_date: date) -> bool:
           ...

       def calculate_indicators(self) -> None:
           ...

       def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
           # Your logic here
           return signals
   ```

3. **Add tests**: `tests/strategy/trading/test_my_strategy.py` (mirror the source tree)
4. **Register in the factory**: Add your class to the `TRADING_STRATEGIES` registry in `turtlex/strategy/factory.py` — all CLIs derive their `--trading-strategy` choices from it. For programmatic use, instantiate the class directly and pass it to the service constructor.
5. **Test**: `uv run signal-runner list --trading-strategy my_strategy --start-date 2024-06-01 --end-date 2024-06-01`

## Examples Directory

| Example | Purpose | Command |
| --------- | --------- | --------- |
| **portfolio_backtest_example.py** | Programmatic portfolio backtesting template | `uv run python examples/portfolio_backtest_example.py` |
| **portfolio_backtest_api_demo.py** | API-style portfolio backtesting demo | `uv run python examples/portfolio_backtest_api_demo.py` |

## Design Patterns & Principles

### Strategy Pattern (Abstract Base Classes)

All pluggable behaviours — signals, exits, rankings — share a common ABC interface. Services depend on the abstract type; concrete implementations are swapped at runtime without changing any service code. See `turtlex/strategy/trading/base.py` (base) and `turtlex/strategy/trading/darvas_box.py` (concrete). Same pattern in `turtlex/strategy/exit/` and `turtlex/strategy/ranking/`.

### Repository Pattern (Data Access)

All database operations live in `turtlex/repository/`. No SQL outside this directory. Sync `Engine`-based repos handle analytical reads; async `AsyncSession`-based repos serve the download path. See `turtlex/repository/query/` (sync reads) and `turtlex/repository/ingest/` (async writes plus the async ticker reads the download path needs).

### Dependency Injection (Constructor Injection)

All dependencies are passed explicitly through constructors — no globals, no service locators. The connection pool flows from `Settings` → `Service` → `Repo`. See `turtlex/service/signal_service.py`.

### Domain Models (Dataclasses vs Pydantic)

- **Dataclasses** for all internal domain objects (`Signal`, `Trade`, `Benchmark`, etc.). Use `@property` for computed fields — no setters. All shared domain models live in a single module: `turtlex/model.py` (no per-package `models.py`).
- **Pydantic `BaseModel`** only for external API responses where field aliasing (`alias=`) is needed. See `Exchange`, `Ticker`, `Company` in `turtlex/schema/`.

### Configuration (Factory Method)

`Settings.from_toml()` is the single entry point for all config. It loads TOML, validates required env vars (raises `ValueError` if missing — never falls back to TOML values for secrets), builds nested config objects, and creates the connection pool. See `turtlex/config/settings.py`.

### Async Boundary

Async is used only in the data-download path; analytical queries are always sync:

- **Async (downloads/writes)**: external API clients (`turtlex/client/eodhd.py`, `httpx.AsyncClient`), download-orchestration services (e.g. `turtlex/service/eodhd_service.py`, concurrent requests via `asyncio.gather`), and the `turtlex/repository/ingest/` write repositories (`AsyncSession`). Scripts may use `asyncio.run()` as the async entry point.
- **Sync (analytical reads)**: query repositories (`turtlex/repository/query/`) use a sync `Engine`; strategy, backtesting, and portfolio logic is synchronous. Do not make query repositories or backtest logic async.

### Naming Conventions

| Construct | Convention | Example |
| ----------- | ----------- | --------- |
| Classes | PascalCase | `DarvasBoxStrategy`, `DailyBarsQueryRepository` |
| Methods / variables | snake_case | `get_signals()`, `start_date` |
| Private methods | leading underscore | `_get_bars_history_db()` |
| Constants / enums | UPPER_SNAKE_CASE | `TimeFrameUnit.DAY` |
| Files | snake_case | `bars_history.py`, `darvas_box.py` |
| Folders / packages | singular snake_case | `turtlex/service/`, `turtlex/repository/` |

### Docstrings

All public methods (no leading underscore) must have a docstring explaining the purpose of the method and each parameter. Private methods (`_name`) do not require docstrings unless the logic is non-obvious.

### Type Hints

All function signatures carry full type hints — parameters and return types. Use `X | None` (not `Optional[X]`), `list[X]` (not `List[X]`). No `Any` except at external API boundaries.

### Logging

One module-level logger per file via `logging.getLogger(__name__)`. Use `DEBUG` for decision points and data values; `WARNING`/`ERROR` for anomalies and failures. Never log secrets or API keys.

### Error Handling

Validate preconditions early and return `bool` (for data-collection methods) or raise `ValueError` with a descriptive message. No bare `except` clauses. No swallowed exceptions. Properties validate their preconditions before computing.

### Static Methods

Use `@staticmethod` for pure utility functions that belong logically to a class but require no instance state. See `RankingStrategy._linear_rank()` in `turtlex/strategy/ranking/base.py`.

## Testing

Tests mirror the source tree under `tests/`:

- `strategy/trading/test_darvas_box.py`: Darvas Box strategy logic
- `strategy/trading/test_mars_strategy.py`: Mars strategy logic
- `strategy/trading/test_momentum_strategy_parity.py`: Momentum strategy (polars path)
- `strategy/ranking/test_breakout_quality_ranking.py`: Breakout quality ranking strategy
- `strategy/ranking/test_momentum_ranking.py`: Momentum ranking strategy
- `strategy/ranking/test_volume_momentum_ranking.py`: Volume momentum ranking strategy
- `strategy/exit/test_macd_exit_strategy.py`: MACD exit strategy logic
- `strategy/exit/test_atr_exit_strategy.py`: ATR exit strategy logic
- `strategy/exit/test_ema_exit_strategy.py`: EMA exit strategy logic
- `strategy/exit/test_buy_and_hold_exit_strategy.py`: Buy and hold exit strategy logic
- `strategy/exit/test_profit_loss_exit_strategy.py`: Profit/loss exit strategy logic
- `strategy/exit/test_trailing_percentage_loss_exit_strategy.py`: Trailing percentage loss exit strategy logic
- `strategy/test_factory.py`: Strategy factory
- `repository/query/test_daily_bars.py`: DailyBarsQueryRepository (polars reads)
- `repository/query/test_ticker.py`: TickerQueryRepository (symbol list and qualified-universe reads)
- `repository/ingest/test_exchange.py`, `test_ticker.py`, `test_daily_bars.py`, `test_company.py`: async ingest repository classes
- `portfolio/test_portfolio.py`: Portfolio management and analytics
- `backtest/test_signal_processor.py`: Signal processing pipeline
- `config/test_settings.py`: Configuration loading
- `cli/test_api_token_filter.py`: API token filter logic

Shared fixtures live in `tests/conftest.py`. File-specific fixtures stay in the individual test file.

Run with `uv run pytest` or `uv run pytest tests/strategy/trading/test_darvas_box.py`.

## Dependencies & Resources

**Core Libraries**: polars (primary DataFrame library), pandas/numpy (retained for quantstats boundary), pydantic (schema validation), httpx (async HTTP for EODHD client), psycopg (PostgreSQL), quantstats (performance analytics)

**Special Requirements**: Python 3.14+
