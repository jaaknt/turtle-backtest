# CLAUDE.md

Python-based financial trading strategy backtesting library for US stocks. Supports multiple strategies (Darvas Box, Mars, Momentum), portfolio management, and live trading via Alpaca API. Data from EODHD/Yahoo Finance stored in PostgreSQL.

## Quick Start & Common Commands

### Most Common Operations
| Task | Command | Use When |
|------|---------|----------|
| **Update data** | `uv run python scripts/daily_eod_update.py --start-date 2024-06-28` | Daily data refresh |
| **Generate signals** | `uv run python scripts/signal_runner.py --start-date 2024-06-01 --end-date 2024-06-01 --mode analyze` | Analyze trading opportunities |
| **Portfolio backtest** | `uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31` | Test multi-position strategy |
| **Single backtest** | `uv run python scripts/backtest.py --ticker AAPL --start-date 2024-01-01` | Test specific ticker |
| **Run tests** | `uv run pytest` | Verify code changes |
| **Start database** | `docker-compose up -d` | Before any data operations |

### Critical File Paths
- **Configuration**: `/config/settings.toml` + `.env` for API keys
- **Strategies**: `/turtle/signal/*.py` - Trading signal implementations
- **Exit Strategies**: `/turtle/exit/*.py` - Position exit logic
- **Live Trading**: `/turtle/trade/*.py` - Production trading system
- **Portfolio**: `/turtle/portfolio/*.py` - Multi-position management
- **Services**: `/turtle/service/*.py` - Business logic orchestration

### Development Decision Tree

**Want to analyze market signals?** → Use `scripts/signal_runner.py --mode analyze`

**Want to test a strategy on one ticker?** → Use `scripts/backtest.py --ticker SYMBOL`

**Want to test portfolio performance?** → Use `scripts/portfolio_runner.py` with date range

**Want to trade live?** → ⚠️ Use `scripts/setup_live_trading.py --paper-trading` FIRST

**Need historical data?** → Use `scripts/download_eodhd_data.py` for bulk or `scripts/daily_eod_update.py` for daily

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
| **daily_eod_update.py** | Daily data updates | `--start-date`, `--mode` (bars/symbols/companies) | `uv run python scripts/daily_eod_update.py --start-date 2024-06-28` |
| **download_eodhd_data.py** | Bulk historical download | `--ticker-limit`, `--start-date`, `--end-date` | `uv run python scripts/download_eodhd_data.py --ticker-limit 10` |
| **signal_runner.py** | Generate/analyze signals | `--strategy`, `--mode` (analyze/csv/sheets/db) | `uv run python scripts/signal_runner.py --start-date 2024-06-01 --end-date 2024-06-01 --strategy darvas_box --mode analyze` |
| **backtest.py** | Single ticker backtest | `--ticker`, `--signal-strategy`, `--exit-strategy` | `uv run python scripts/backtest.py --ticker AAPL --start-date 2024-01-01 --end-date 2024-12-31 --signal-strategy darvas_box --exit-strategy profit_loss` |
| **portfolio_runner.py** | Portfolio backtest | `--trading-strategy`, `--ranking-strategy`, `--initial-capital`, `--output-file` | `uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --output-file results.html` |
| **setup_live_trading.py** | ⚠️ Initialize live trading | `--strategy`, `--paper-trading`, `--max-position-size`, `--max-daily-loss` | `uv run python scripts/setup_live_trading.py --strategy darvas_box --paper-trading` |

**Use `--help` flag with any script for complete parameter documentation.**

## Architecture Overview

### Core Components
- **turtle/data/**: Repository pattern for data access (PostgreSQL)
  - `bars_history.py`, `company.py`, `symbol.py`, `symbol_group.py`
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
- **turtle/trade/**: ⚠️ Live trading system (SAFETY CRITICAL)
  - `manager.py`, `client.py`, `order_executor.py`, `position_tracker.py`, `risk_manager.py`, `trade_logger.py`
- **turtle/google/**: Google Sheets integration
  - `signal_exporter.py`, `client.py`, `auth.py`
- **turtle/clients/**: External API clients
  - `eodhd.py`: EODHD API wrapper
- **turtle/config/**: Configuration management
  - `settings.py`: TOML + environment variable loader
- **turtle/service/**: Business logic orchestration layer

### Database
- **Schema**: `turtle` (PostgreSQL)
- **Tables**: `ticker`, `bars_history`, `company`, `symbol_group`, `trading_sessions`, `live_orders`
- **Connection**: psycopg with connection pooling (pool size: 10)

### Data Sources
- **EODHD**: Symbol lists, historical OHLCV data
- **Alpaca**: Live trading API
- **Yahoo Finance**: Company fundamentals

## Live Trading System ⚠️

**SAFETY NOTICE**: This system trades real money. **ALWAYS** start with paper trading and test for minimum 2 weeks before using real capital.

### Architecture
```
Signal Generation → LiveTradingManager → RiskManager (checks) → OrderExecutor → Alpaca API
                                      ↓
                          PositionTracker (monitoring) → TradeLogger (audit trail)
```

### Core Components
- **LiveTradingManager**: Orchestrates trading session, coordinates all components
- **AlpacaTradingClient**: Alpaca API abstraction (market orders, positions, account info)
- **RiskManager**: Pre-trade checks (position size, daily loss, portfolio exposure limits)
- **OrderExecutor**: Order lifecycle management (submit, track, handle fills/rejections)
- **PositionTracker**: Real-time position monitoring and P&L calculation
- **TradeLogger**: Database persistence for audit trail and performance analysis

### Safety Checklist
- [ ] Paper trading flag set (`paper_trading=True`)
- [ ] Risk parameters configured (max position size, daily loss limit, portfolio exposure)
- [ ] API credentials in `.env` file
- [ ] Database accessible
- [ ] Minimum 2 weeks paper trading completed
- [ ] Emergency stop procedure reviewed

### Emergency Procedures
1. **Stop trading**: Ctrl+C or call `manager.stop_session()`
2. **Cancel orders**: Via Alpaca interface or `client.cancel_order(order_id)`
3. **Close positions**: Via Alpaca interface or API liquidation
4. **Review logs**: `tail -f logs/live_trading.log`
5. **Check database**: Query `turtle.trading_sessions` and `turtle.live_orders`

## Core Systems Overview

### Portfolio Management
- **PortfolioManager**: Position/cash management, daily snapshots, position sizing with min/max constraints
- **PortfolioSignalSelector**: Signal ranking and filtering, position limits, minimum ranking threshold
- **PortfolioAnalytics**: Performance metrics (Sharpe, Sortino, Max DD, win rate), benchmark comparison

### Configuration System
- **Settings**: TOML-based with environment variable overrides for secrets
- **Key Files**: `config/settings.toml`, `.env` (API keys, DB password)
- **Environment Variables**: `EODHD_API_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `DB_PASSWORD`
- **Database DSN**: `host=localhost port=5432 dbname=trading user=postgres`

### Service Layer
| Service | Purpose | Key Methods | Used By |
|---------|---------|-------------|---------|
| **DataUpdateService** | Data ingestion from EODHD/Alpaca/Yahoo | `update_symbol_list()`, `update_bars_history()`, `update_company_list()` | `daily_eod_update.py`, `download_eodhd_data.py` |
| **SignalService** | Signal generation and export | `generate_signals()`, `filter_by_ranking()`, `export_to_sheets()` | `signal_runner.py` |
| **BacktestService** | Single-ticker backtesting | `run_backtest()`, `calculate_metrics()` | `backtest.py` |
| **PortfolioService** | Multi-position portfolio backtest | `run_portfolio_backtest()`, `generate_tearsheet()`, `calculate_benchmark_comparison()` | `portfolio_runner.py` |
| **LiveTradingService** | Live trading orchestration | `start_trading_session()`, `process_daily_signals()`, `monitor_positions()` | `setup_live_trading.py` |
| **EODHDService** | EODHD API operations | `fetch_eod_data()`, `fetch_ticker_list()`, `validate_response()` | `DataUpdateService` |

### Ranking System
Filters and prioritizes signals for portfolio selection. Returns scores 0-100 (higher = stronger signal).

**Available Strategies:**
- **MomentumRanking**: Price momentum over lookback period (default: 20 days)
- **VolumeMomentumRanking**: Combined price + volume momentum (weights: 0.7 price, 0.3 volume)

**Usage in portfolio backtesting:** Applied by `PortfolioSignalSelector` with configurable `min_ranking` threshold.

### Google Sheets Integration
- **Authentication**: OAuth2 (user credentials) or Service Account (automated)
- **SignalExporter**: Export signals to Google Sheets with formatting
- **Setup**: Enable Google Sheets API → Create credentials → Set `GOOGLE_APPLICATION_CREDENTIALS` env var
- **Usage**: `scripts/signal_runner.py --mode sheets --sheet-name "June Signals"`

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
4. **Register in SignalService**: Add to strategy mapping in `turtle/service/signal_service.py`
5. **Test**: `uv run python scripts/signal_runner.py --strategy my_strategy --mode analyze`

### Running Portfolio Backtests

**Basic workflow:**
```bash
# 1. Update data
uv run python scripts/daily_eod_update.py --start-date 2024-01-01 --end-date 2024-12-31

# 2. Generate signals (optional - validate)
uv run python scripts/signal_runner.py --start-date 2024-01-01 --end-date 2024-01-31 --strategy darvas_box --mode analyze

# 3. Run backtest
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --output-file results.html

# 4. Review results
open reports/results.html
```

**Advanced options**: Use `--ranking-strategy`, `--exit-strategy`, `--initial-capital`, `--position-min-amount`, `--min-signal-ranking` to customize.

### Setting Up Live Trading (Safety-First)

1. **Verify paper trading**: `paper_trading = true` in `config/settings.toml`
2. **Configure risk**: `uv run python scripts/setup_live_trading.py --strategy darvas_box --max-position-size 5000 --max-daily-loss 200 --paper-trading`
3. **Monitor first session**: Watch logs (`tail -f logs/live_trading.log`), verify Alpaca orders are paper trading
4. **Test minimum 2 weeks** paper trading before considering live capital
5. **Live transition** (only after success): Change `paper_trading=false`, start with minimal capital, conservative limits

## Examples Directory

| Example | Purpose | Command |
|---------|---------|---------|
| **backtesting.ipynb** | Interactive single-strategy backtesting with visualizations | `uv run jupyter notebook examples/backtesting.ipynb` |
| **portfolio_backtesting.ipynb** | Portfolio-level backtesting with multiple positions | `uv run jupyter notebook examples/portfolio_backtesting.ipynb` |
| **symbol_group.ipynb** | Managing custom symbol groups (watchlists) | `uv run jupyter notebook examples/symbol_group.ipynb` |
| **pandas.ipynb** | Data analysis and exploration | `uv run jupyter notebook examples/pandas.ipynb` |
| **portfolio_backtest_example.py** | Programmatic portfolio backtesting template | `uv run python examples/portfolio_backtest_example.py` |
| **portfolio_backtest_api_demo.py** | API-style portfolio backtesting demo | `uv run python examples/portfolio_backtest_api_demo.py` |
| **live_trading_example.py** | ⚠️ Live trading setup (paper trading only!) | `uv run python examples/live_trading_example.py` |
| **google_sheets_test.py** | Google Sheets integration test | `uv run python examples/google_sheets_test.py` |

## Troubleshooting Quick Reference

| Problem | Quick Fix | Details |
|---------|-----------|---------|
| **Database connection failed** | `docker-compose ps` to verify postgres running, check `.env` credentials | Verify DB exists with `psql -U postgres -l`, test port 5432 access |
| **API rate limiting** | Use `--ticker-limit 10` for testing, verify API keys in `.env` | Check EODHD_API_KEY active, typical limit 20 req/sec |
| **No signals generated** | Verify data exists: `SELECT COUNT(*) FROM turtle.bars_history WHERE ticker='AAPL'`, enable `--verbose` | Check ticker has sufficient history, validate strategy parameters |
| **Portfolio backtest errors** | Lower `--min-signal-ranking`, verify `initial_capital >= position_max_amount * max_positions` | Ensure signals exist for date range, validate benchmark data (SPY/QQQ) |
| **Live trading orders not executing** | Verify market hours, check `paper_trading=True` in settings, review `logs/risk_manager.log` | Check API credentials match paper/live mode, test with minimal setup |
| **Google Sheets authentication failed** | Delete `token.json` (OAuth2) or verify `GOOGLE_APPLICATION_CREDENTIALS` path (Service Account) | Enable Google Sheets API in Cloud Console, share spreadsheet with service account |
| **Slow queries/high memory** | Add indexes: `CREATE INDEX idx_bars_ticker_date ON turtle.bars_history(ticker, date)`, use `--ticker-limit` | Increase `pool_size` in settings.toml, process data in batches |
| **Migration failures** | `uv run alembic current` to check version, `uv run alembic downgrade -1` to rollback | Review `turtle.alembic_version` table, test upgrade/downgrade paths |

**For detailed troubleshooting**: Check logs in `logs/` directory, use `--verbose` flag, consult script `--help` output.

## Design Patterns & Testing

### Design Principles
- **Single Responsibility**: Each class has one clear purpose and reason to change
- **Encapsulation**: Keep internal state private, expose behavior through methods
- **Immutability**: Make objects immutable when possible for thread safety
- **Method Design**: Small, focused methods with clear names
- **Dataclasses**: Use for business objects in `models.py`, keep separate from classes using them

### Testing Strategy
Tests organized by component:
- `test_bars_history.py`: Historical data operations
- `test_company.py`: Company data operations
- `test_darvas_box.py`: Darvas Box strategy logic
- `test_models.py`: Data model validation
- `test_symbol.py`: Symbol management

Use pytest fixtures for database setup/teardown. Run with `uv run pytest` or `uv run pytest tests/test_specific.py`.

## Dependencies & Resources

**Core Libraries**: pandas/numpy (data), pandas-ta/ta-lib (technical analysis), alpaca-py (trading API), yfinance (Yahoo Finance), psycopg (PostgreSQL), backtesting (backtest framework), streamlit (web UI), plotly (visualization)

**Special Requirements**: Python 3.13+, TA-lib requires special installation (see `.github/workflows/build.yml`)

**Configuration**: Environment setup via `.env` file, TOML-based settings in `config/settings.toml`

**Additional Documentation**: Full API details in code docstrings, complete examples in `examples/` directory, detailed workflows in backup: `CLAUDE.md.backup`
