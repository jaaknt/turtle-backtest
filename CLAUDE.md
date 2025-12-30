# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based financial trading strategy backtesting library for US stocks. The system supports multiple trading strategies including Darvas Box, Mars, Momentum, and Market strategies. Data is sourced from Alpaca, Yahoo Finance, and EODHD APIs and stored in PostgreSQL.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync --extra dev --extra lint

# Activate virtual environment
source ./.venv/bin/activate

# Start PostgreSQL database
docker-compose up -d

# Stop database
docker-compose down
```

### Running the Application
```bash
# Run daily EOD data update (requires start date)
uv run python scripts/daily_eod_update.py --start-date 2025-06-28

# Run daily EOD update with options
uv run python scripts/daily_eod_update.py --start-date 2025-06-28 --dry-run --verbose
uv run python scripts/daily_eod_update.py --start-date 2025-06-25 --end-date 2025-06-28

# Download symbol list from EODHD
uv run python scripts/daily_eod_update.py --mode symbols

# Download company data from Yahoo Finance
uv run python scripts/daily_eod_update.py --mode companies

# Download historical data from EODHD (all US stocks)
uv run python scripts/download_eodhd_data.py

# Download historical data - test with 10 stocks
uv run python scripts/download_eodhd_data.py --stocks-limit 10

# Download historical data - test with 50 stocks
uv run python scripts/download_eodhd_data.py --stocks-limit 50

# Run Streamlit web interface
uv run streamlit run app.py

# Run Jupyter notebooks for analysis
uv run jupyter notebook examples/
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_darvas_box.py

# Run with verbose output
uv run pytest -v
```

## Architecture Overview

### Core Components
- **turtle/data/**: Repository pattern for data access (PostgreSQL)
  - `bars_history.py`: OHLCV historical data
  - `company.py`: Company fundamental data
  - `symbol.py`: Stock symbol management
  - `symbol_group.py`: Custom symbol groupings
- **turtle/signal/**: Trading signal implementations (renamed from strategy)
  - `base.py`: TradingStrategy abstract base class (renamed from trading_strategy.py)
  - `darvas_box.py`: Darvas Box trend-following strategy
  - `mars.py`: Mars momentum strategy (@marsrides)
  - `momentum.py`: Traditional momentum strategy
  - `market.py`: General market analysis
  - `models.py`: Signal data models
- **turtle/exit/**: Exit strategy implementations (refactored from monolithic file)
  - `base.py`: ExitStrategy abstract base class
  - `buy_and_hold.py`: BuyAndHoldExitStrategy
  - `profit_loss.py`: ProfitLossExitStrategy with profit targets and stop losses
  - `ema.py`: EMAExitStrategy based on exponential moving average
  - `macd.py`: MACDExitStrategy using MACD technical indicators
  - `atr.py`: ATRExitStrategy with volatility-based stop losses
- **turtle/backtest/**: Backtesting and signal processing
  - `models.py`: SignalResult and performance data models
  - `period_return.py`: Period return strategies (BuyAndHold, ProfitLoss)
  - `strategy_performance.py`: Strategy performance testing framework
  - `processor.py`: SignalProcessor for converting signals to results
- **turtle/service/**: Business logic layer
  - `data_update.py`: Main service for data ingestion and strategy execution

### Database Schema
- **Schema**: `turtle`
- **Key Tables**: `ticker`, `bars_history`, `company`, `symbol_group`
- **Connection**: PostgreSQL via psycopg with connection pooling

### Data Sources
- **Alpaca API**: Historical OHLCV data
- **Yahoo Finance**: Company fundamental data
- **EODHD**: Symbol lists and metadata

## Key Configuration

### Environment Variables (.env)
Required API keys and database connection strings should be stored in `.env` file:
- Alpaca API credentials
- EODHD API key
- Database connection parameters

### Database Connection
Default DSN: `"host=localhost port=5432 dbname=trading user=postgres password=postgres361"`

### Time Frames
Configurable via `TimeFrameUnit` enum: `DAY`, `WEEK`, `MONTH`

## Working with Strategies

### Adding New Strategies
1. Create new file in `turtle/signal/` (signal generation)
2. Implement strategy logic with entry/exit signals extending TradingStrategy base class
3. For custom exit strategies, create file in `turtle/exit/` extending ExitStrategy base class
4. Add integration to `DataUpdateService` service
5. Create corresponding test file in `tests/`

### Strategy Testing
- Use `examples/backtesting.ipynb` for interactive backtesting
- Strategies integrate with the `backtesting` library
- Performance metrics and visualization via plotly

## Data Management

### Daily Data Updates
For daily operations, use the dedicated daily update script with multiple modes:
```bash
# Update OHLCV data for specific date (default bars mode)
uv run python scripts/daily_eod_update.py --start-date 2024-06-28

# Update OHLCV data for date range
uv run python scripts/daily_eod_update.py --start-date 2024-06-25 --end-date 2024-06-28

# Download symbol list from EODHD
uv run python scripts/daily_eod_update.py --mode symbols

# Download company data from Yahoo Finance
uv run python scripts/daily_eod_update.py --mode companies

# Dry run to see what would be updated
uv run python scripts/daily_eod_update.py --start-date 2024-06-28 --dry-run --verbose
```

The daily update script supports multiple modes:
- **bars mode** (default): Requires `--start-date` parameter, updates OHLCV data for all symbols
- **symbols mode**: Downloads USA stocks symbol list from EODHD (no dates required)
- **companies mode**: Downloads company data from Yahoo Finance (no dates required)
- Includes validation to ensure data was successfully retrieved
- Provides detailed logging and error handling
- Supports dry-run mode for testing
- Flexible date parameters: `--start-date` (required for bars mode) and optional `--end-date`

### Bulk Data Updates
The `DataUpdateService` service handles bulk data operations:
```python
data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
data_updater.update_symbol_list()        # Download symbol list
data_updater.update_company_list()       # Download company data
data_updater.update_bars_history(start_date, end_date)  # Download OHLCV data
```

### Symbol Groups
Custom stock groupings (e.g., NASDAQ-100) can be created and managed via the `symbol_group` repository for targeted backtesting.

## Database Migrations

The project uses Alembic for database schema migrations. All migrations are located in `db/migrations/versions/` and are managed through the `scripts/db_migrate.py` management script.

### Migration Commands
```bash
# Check current migration status
uv run alembic current

# Show migration history
uv run alembic history

# Apply all pending migrations
uv run alembic upgrade head

# Apply migrations up to specific revision
uv run alembic upgrade <revision>

# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision>

# Create new migration
uv run alembic revision -m "description"

# Or use management script wrapper
python scripts/db_migrate.py upgrade
python scripts/db_migrate.py downgrade -1
python scripts/db_migrate.py current
python scripts/db_migrate.py history
python scripts/db_migrate.py create "add_new_column"
```

### Migration Architecture
- **Configuration**: `alembic.ini` (timezone=UTC, file naming templates)
- **Environment**: `db/migrations/env.py` (loads settings from config/settings.toml)
- **Version Table**: Stored in `turtle.alembic_version` schema
- **Migration Mode**: Standalone (no SQLAlchemy ORM models, raw SQL only)
- **Database Features**: Supports TimescaleDB hypertables, compression policies, triggers

### Creating New Migrations
1. Create migration file: `uv run alembic revision -m "description"`
2. Implement `upgrade()` and `downgrade()` functions with raw SQL
3. Set search path: `op.execute("SET search_path TO turtle, public")`
4. Test migration: `uv run alembic upgrade head`
5. Verify rollback: `uv run alembic downgrade -1`

### Migration Best Practices
- Use `IF EXISTS` and `IF NOT EXISTS` for idempotent operations
- Include descriptive comments on tables and columns
- Test both upgrade and downgrade paths
- Use proper TimescaleDB functions (create_hypertable, add_compression_policy)
- Maintain migration dependency chain through revision IDs

## Dependencies

### Core Libraries
- **pandas/numpy**: Data manipulation and analysis
- **pandas-ta/ta-lib**: Technical analysis indicators
- **alpaca-py**: Alpaca API integration
- **yfinance**: Yahoo Finance data
- **psycopg**: PostgreSQL database connectivity
- **backtesting**: Strategy backtesting framework
- **streamlit**: Web interface
- **plotly**: Data visualization

### Special Installation Notes
- **TA-lib**: Requires special installation steps (see .github/workflows/build.yml)
- **Python 3.13+**: Required for optimal performance

## Design patterns
- All functionality must be encapsulated in classes, only exception is /scripts, app.py
### Single Responsibility Principle
Each class should have one clear purpose and reason to change. If you can't describe what a class does in a single
sentence without using "and," it's probably doing too much.
### Encapsulation and Data Hiding
Keep internal state private and expose behavior through well-defined methods. 
Use properties for controlled access to data.
### Immutability Where Appropriate
Make objects immutable when possible to reduce bugs and enable safe sharing between threads.
### Method Design
Methods should be small, focused, and have clear names. Avoid long parameter lists and 
prefer returning new objects over modifying state when possible.
### Dataclasses
Use dataclasses to define business objects and use them to exchange information and also define class boundaries
Keep dataclasses in models.py and all classes that use them in separate files

## Testing Strategy
Tests are organized by component:
- `test_bars_history.py`: Historical data operations
- `test_company.py`: Company data operations  
- `test_darvas_box.py`: Darvas Box strategy logic
- `test_models.py`: Data model validation
- `test_symbol.py`: Symbol management

Use pytest fixtures for database setup and teardown in tests.

## Linting
Use mypy and ruff tools configured in pyproject.toml 