# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based financial trading strategy backtesting library for US stocks. The system supports multiple trading strategies including Darvas Box, Mars, Momentum, and Market strategies. Data is sourced from Alpaca, Yahoo Finance, and EODHD APIs and stored in PostgreSQL.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync --extra dev

# Activate virtual environment
source ./.venv/bin/activate

# Start PostgreSQL database
docker-compose up -d

# Stop database
docker-compose down
```

### Running the Application
```bash
# Run main data update/strategy execution
uv run python main.py

# Run daily EOD data update (requires start date)
uv run python scripts/daily_eod_update.py --start-date 2025-06-28

# Run daily EOD update with options
uv run python scripts/daily_eod_update.py --start-date 2025-06-28 --dry-run --verbose
uv run python scripts/daily_eod_update.py --start-date 2025-06-25 --end-date 2025-06-28

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
- **turtle/strategy/**: Trading strategy implementations
  - `darvas_box.py`: Darvas Box trend-following strategy
  - `mars.py`: Mars momentum strategy (@marsrides)
  - `momentum.py`: Traditional momentum strategy
  - `market.py`: General market analysis
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
Default DSN: `"host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"`

### Time Frames
Configurable via `TimeFrameUnit` enum: `DAY`, `WEEK`, `MONTH`

## Working with Strategies

### Adding New Strategies
1. Create new file in `turtle/strategy/`
2. Implement strategy logic with entry/exit signals
3. Add integration to `DataUpdateService` service
4. Create corresponding test file in `tests/`

### Strategy Testing
- Use `examples/backtesting.ipynb` for interactive backtesting
- Strategies integrate with the `backtesting` library
- Performance metrics and visualization via plotly

## Data Management

### Daily Data Updates
For daily operations, use the dedicated daily update script:
```bash
# Update specific single date (start-date is required)
uv run python scripts/daily_eod_update.py --start-date 2024-06-28

# Dry run to see what would be updated
uv run python scripts/daily_eod_update.py --start-date 2024-06-28 --dry-run --verbose

# Update date range
uv run python scripts/daily_eod_update.py --start-date 2024-06-25 --end-date 2024-06-28
```

The daily update script:
- Requires `--start-date` parameter to specify the target date
- Updates OHLCV data for all symbols for a single date or date range
- Includes validation to ensure data was successfully retrieved
- Provides detailed logging and error handling
- Supports dry-run mode for testing
- Flexible date parameters: `--start-date` (required) and optional `--end-date`

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
- **Python 3.12+**: Required for optimal performance

## Testing Strategy

Tests are organized by component:
- `test_bars_history.py`: Historical data operations
- `test_company.py`: Company data operations  
- `test_darvas_box.py`: Darvas Box strategy logic
- `test_models.py`: Data model validation
- `test_symbol.py`: Symbol management

Use pytest fixtures for database setup and teardown in tests.