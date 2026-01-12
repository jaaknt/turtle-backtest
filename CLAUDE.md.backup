# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based financial trading strategy backtesting library for US stocks. The system supports multiple trading strategies including Darvas Box, Mars, Momentum, and Market strategies. Data is sourced from Alpaca, Yahoo Finance, and EODHD APIs and stored in PostgreSQL.

## Table of Contents
- [Quick Start & Common Commands](#quick-start--common-commands)
- [Development Environment Setup](#development-commands)
- [Core Architecture](#architecture-overview)
  - [Data Layer & Configuration](#core-data-layer--configuration-system)
  - [Trading Signals & Ranking](#trading-signal-system--ranking-system)
  - [Exit Strategies](#exit-strategy-system)
  - [Backtesting Engine](#backtesting-engine)
  - [Portfolio Management](#portfolio-management-system)
  - [Live Trading System](#live-trading-system)
  - [Google Sheets Integration](#google-sheets-integration)
  - [Service Layer](#service-layer)
- [Scripts Reference](#scripts-reference)
- [Examples & Notebooks](#examples--notebooks)
- [Database Architecture & Migrations](#database-migrations)
- [Development Workflows](#development-workflows)
- [Design Patterns & Testing](#design-patterns--testing-strategy)
- [Troubleshooting](#troubleshooting)

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

**Want to analyze market signals?**
→ Use `scripts/signal_runner.py --mode analyze`

**Want to test a strategy on one ticker?**
→ Use `scripts/backtest.py --ticker SYMBOL`

**Want to test portfolio performance?**
→ Use `scripts/portfolio_runner.py` with date range

**Want to trade live?**
⚠️ Use `scripts/setup_live_trading.py --paper-trading` FIRST
→ Never start with real money

**Need historical data?**
→ Use `scripts/download_eodhd_data.py` for bulk download
→ Use `scripts/daily_eod_update.py` for daily updates

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

# Download historical data from EODHD (all US stocks, default date range: 2000-01-01 to 2025-12-30)
uv run python scripts/download_eodhd_data.py

# Download historical data - test with 10 tickers
uv run python scripts/download_eodhd_data.py --ticker-limit 10

# Download historical data - custom date range
uv run python scripts/download_eodhd_data.py --start-date 2024-01-01 --end-date 2024-12-31

# Download historical data - test with limited tickers and custom date range
uv run python scripts/download_eodhd_data.py --ticker-limit 10 --start-date 2024-06-01 --end-date 2024-06-30

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

## Scripts Reference

### Data Management Scripts

#### daily_eod_update.py
**Purpose**: Daily data updates with multiple operation modes.

**Modes:**
- `bars` (default): Update OHLCV data for specific date
- `symbols`: Download USA stocks symbol list from EODHD
- `companies`: Download company data from Yahoo Finance

**Common usage:**
```bash
# Update daily bars (default mode)
uv run python scripts/daily_eod_update.py --start-date 2024-06-28

# Update date range
uv run python scripts/daily_eod_update.py --start-date 2024-06-25 --end-date 2024-06-28

# Download symbol list
uv run python scripts/daily_eod_update.py --mode symbols

# Download company data
uv run python scripts/daily_eod_update.py --mode companies

# Dry run (test without changes)
uv run python scripts/daily_eod_update.py --start-date 2024-06-28 --dry-run --verbose
```

**Parameters:**
- `--start-date`: Start date (YYYY-MM-DD) - required for bars mode
- `--end-date`: End date (YYYY-MM-DD) - optional
- `--mode`: Operation mode (bars, symbols, companies)
- `--dry-run`: Test mode, no database changes
- `--verbose`: Detailed logging

#### download_eodhd_data.py
**Purpose**: Bulk historical data download from EODHD.

**Features:**
- Downloads all US stocks by default
- Supports custom date ranges
- Ticker limit for testing
- Default range: 2000-01-01 to 2025-12-30

**Common usage:**
```bash
# Download all US stocks (full history)
uv run python scripts/download_eodhd_data.py

# Test with 10 tickers
uv run python scripts/download_eodhd_data.py --ticker-limit 10

# Custom date range
uv run python scripts/download_eodhd_data.py --start-date 2024-01-01 --end-date 2024-12-31

# Test with limited tickers and custom range
uv run python scripts/download_eodhd_data.py --ticker-limit 10 --start-date 2024-06-01 --end-date 2024-06-30
```

**Parameters:**
- `--ticker-limit`: Maximum number of tickers to download (for testing)
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--verbose`: Detailed progress logging

**Use cases:**
- Initial database population
- Historical data refresh
- Testing data pipelines

### Analysis & Backtesting Scripts

#### signal_runner.py
**Purpose**: Generate and analyze trading signals with multiple output modes.

**Modes:**
- `analyze`: Display signal summaries and statistics (default)
- `csv`: Export signals to CSV file
- `sheets`: Export to Google Sheets
- `db`: Store signals in database

**Common usage:**
```bash
# Analyze signals for date range
uv run python scripts/signal_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --strategy darvas_box --mode analyze

# Analyze specific date
uv run python scripts/signal_runner.py \
  --start-date 2024-06-01 --end-date 2024-06-01 \
  --strategy mars --mode analyze --verbose

# Export to Google Sheets
uv run python scripts/signal_runner.py \
  --start-date 2024-06-01 --end-date 2024-06-01 \
  --strategy darvas_box --mode sheets --sheet-name "June Signals"

# Export to CSV
uv run python scripts/signal_runner.py \
  --start-date 2024-06-01 --end-date 2024-06-30 \
  --strategy momentum --mode csv --output signals.csv

# Test with specific tickers
uv run python scripts/signal_runner.py \
  --start-date 2024-06-01 --end-date 2024-06-01 \
  --tickers AAPL MSFT GOOGL --mode analyze --verbose
```

**Parameters:**
- `--start-date`: Analysis start date (YYYY-MM-DD) - required
- `--end-date`: Analysis end date (YYYY-MM-DD) - required
- `--strategy`: Trading strategy (darvas_box, mars, momentum, market)
- `--mode`: Output mode (analyze, csv, sheets, db)
- `--tickers`: Specific tickers to analyze (space-separated)
- `--sheet-name`: Google Sheets sheet name (sheets mode only)
- `--output`: Output filename (csv mode only)
- `--verbose`: Detailed logging

**Output (analyze mode):**
- Signal count by ticker
- Date range coverage
- Signal statistics
- Top signals by ranking

#### backtest.py
**Purpose**: Test specific signal/exit strategy combinations on individual tickers.

**Common usage:**
```bash
# Backtest single ticker
uv run python scripts/backtest.py \
  --ticker AAPL \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --signal-strategy darvas_box \
  --exit-strategy profit_loss

# Backtest with different exit strategy
uv run python scripts/backtest.py \
  --ticker MSFT \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --signal-strategy mars \
  --exit-strategy ema --verbose

# Backtest multiple tickers
uv run python scripts/backtest.py \
  --tickers AAPL MSFT GOOGL \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --signal-strategy momentum \
  --exit-strategy macd
```

**Parameters:**
- `--ticker`: Single ticker to backtest
- `--tickers`: Multiple tickers (space-separated)
- `--start-date`: Backtest start date (YYYY-MM-DD) - required
- `--end-date`: Backtest end date (YYYY-MM-DD) - required
- `--signal-strategy`: Trading signal strategy (darvas_box, mars, momentum)
- `--exit-strategy`: Exit strategy (buy_and_hold, profit_loss, ema, macd, atr)
- `--verbose`: Detailed output with trade-by-trade results

**Output:**
- Trade history with entry/exit dates and prices
- Performance metrics (total return, win rate, Sharpe ratio)
- Maximum drawdown
- Trade statistics

**Use cases:**
- Strategy parameter tuning
- Comparing exit strategies
- Individual stock analysis
- Strategy validation

#### portfolio_runner.py
**Purpose**: Run portfolio-level backtests with multiple positions and ranking.

**Common usage:**
```bash
# Basic portfolio backtest
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31

# Advanced backtest with custom parameters
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --trading-strategy mars \
  --exit-strategy profit_loss \
  --ranking-strategy volume_momentum \
  --initial-capital 50000 \
  --position-min-amount 2000 \
  --position-max-amount 4000 \
  --min-signal-ranking 80 \
  --output-file mars_2024.html \
  --verbose

# Test specific tickers
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --tickers AAPL MSFT GOOGL NVDA TSLA \
  --trading-strategy darvas_box \
  --verbose

# Custom benchmark comparison
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --benchmark-tickers SPY QQQ IWM \
  --output-file results.html
```

**Parameters:**
- `--start-date`: Backtest start date (YYYY-MM-DD) - required
- `--end-date`: Backtest end date (YYYY-MM-DD) - required
- `--trading-strategy`: Signal strategy (darvas_box, mars, momentum) - default: darvas_box
- `--exit-strategy`: Exit strategy (buy_and_hold, profit_loss, ema, macd, atr) - default: buy_and_hold
- `--ranking-strategy`: Ranking strategy (momentum, volume_momentum) - default: momentum
- `--initial-capital`: Starting capital - default: 30000
- `--position-min-amount`: Minimum position size - default: 1500
- `--position-max-amount`: Maximum position size - default: 3000
- `--min-signal-ranking`: Minimum ranking threshold (0-100) - default: 70
- `--max-tickers`: Maximum tickers to test - default: 10000
- `--tickers`: Specific tickers (space-separated) - optional
- `--benchmark-tickers`: Custom benchmarks - default: SPY QQQ
- `--output-file`: HTML tearsheet filename (saved in reports/) - optional
- `--verbose`: Detailed logging

**Output:**
- Portfolio performance metrics (Sharpe, Sortino, Max DD)
- Trade statistics and win rate
- Benchmark comparison
- HTML tearsheet with charts (if --output-file specified)
- Equity curve and drawdown visualization

**Use cases:**
- Portfolio strategy testing
- Capital allocation optimization
- Multi-position backtest validation
- Performance reporting

### Live Trading Scripts

#### setup_live_trading.py
**Purpose**: Initialize and configure live trading system.

**⚠️ SAFETY WARNING**: Always test with paper trading before using real money.

**Common usage:**
```bash
# Setup with paper trading (RECOMMENDED for testing)
uv run python scripts/setup_live_trading.py \
  --strategy darvas_box \
  --paper-trading

# Configure risk parameters
uv run python scripts/setup_live_trading.py \
  --strategy mars \
  --max-position-size 10000 \
  --max-daily-loss 500 \
  --max-portfolio-exposure 0.9 \
  --paper-trading

# Setup with specific universe
uv run python scripts/setup_live_trading.py \
  --strategy momentum \
  --universe AAPL MSFT GOOGL AMZN NVDA \
  --max-position-size 5000 \
  --paper-trading

# Advanced configuration
uv run python scripts/setup_live_trading.py \
  --strategy darvas_box \
  --max-position-size 8000 \
  --max-daily-loss 400 \
  --max-portfolio-exposure 0.85 \
  --max-positions 10 \
  --paper-trading \
  --verbose
```

**Parameters:**
- `--strategy`: Trading strategy name (darvas_box, mars, momentum) - required
- `--paper-trading`: Use paper trading mode (HIGHLY RECOMMENDED)
- `--max-position-size`: Maximum $ per position - default: 10000
- `--max-daily-loss`: Daily loss limit $ - default: 500
- `--max-portfolio-exposure`: Max % of capital deployed - default: 0.9
- `--max-positions`: Maximum concurrent positions - default: 10
- `--universe`: Trading universe tickers (space-separated) - optional
- `--verbose`: Detailed setup logging

**Setup checklist:**
1. ✅ Paper trading flag set
2. ✅ Risk parameters configured
3. ✅ API credentials in .env file
4. ✅ Database accessible
5. ✅ Logging directory exists
6. ✅ Emergency stop procedure reviewed

**Configuration files:**
- `.env`: API credentials (ALPACA_API_KEY, ALPACA_SECRET_KEY)
- `config/settings.toml`: Trading configuration
- Risk parameters: Set via command line or code

**Safety best practices:**
- **ALWAYS** use `--paper-trading` flag for testing
- Test for minimum 2 weeks paper trading
- Start with small position sizes
- Set conservative daily loss limits
- Monitor logs continuously
- Have emergency stop plan ready

**Use cases:**
- Initial live trading setup
- Paper trading testing
- Risk parameter configuration
- Trading universe definition

### Database Management Scripts

#### db_migrate.py
**Purpose**: Database migration management wrapper for Alembic.

**Common usage:**
```bash
# Check current migration
python scripts/db_migrate.py current

# Show migration history
python scripts/db_migrate.py history

# Apply all pending migrations
python scripts/db_migrate.py upgrade

# Rollback one migration
python scripts/db_migrate.py downgrade -1

# Create new migration
python scripts/db_migrate.py create "add_new_column"
```

**Note**: See [Database Migrations](#database-migrations) section for detailed migration documentation.

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
  - `portfolio_processor.py`: Portfolio-level backtest processing
  - `benchmark_utils.py`: Benchmark comparison utilities
- **turtle/portfolio/**: Portfolio management and analytics
  - `manager.py`: PortfolioManager for position and cash management
  - `selector.py`: PortfolioSignalSelector for signal filtering and ranking
  - `analytics.py`: PortfolioAnalytics for performance metrics calculation
  - `models.py`: Portfolio state and metrics data models
- **turtle/ranking/**: Signal ranking strategies
  - `base.py`: RankingStrategy abstract base class
  - `momentum.py`: MomentumRanking strategy
  - `volume_momentum.py`: VolumeMomentumRanking strategy
- **turtle/trade/**: Live trading system (⚠️ SAFETY CRITICAL)
  - `manager.py`: LiveTradingManager - main orchestrator
  - `client.py`: AlpacaTradingClient - Alpaca API wrapper
  - `order_executor.py`: OrderExecutor - order lifecycle management
  - `position_tracker.py`: PositionTracker - real-time position monitoring
  - `risk_manager.py`: RiskManager - pre-trade risk checks and limits
  - `trade_logger.py`: TradeLogger - database persistence and audit trail
  - `models.py`: Trading models (TradingSession, LiveOrder, RiskParameters)
- **turtle/google/**: Google Sheets integration
  - `signal_exporter.py`: SignalExporter - export signals to Google Sheets
  - `client.py`: GoogleSheetsClient - Google Sheets API wrapper
  - `auth.py`: Authentication (OAuth2 and Service Account support)
  - `models.py`: Google Sheets integration models
- **turtle/clients/**: External API clients
  - `eodhd.py`: EODHD API client wrapper
- **turtle/config/**: Configuration management
  - `settings.py`: Settings loader with TOML and environment variable support
  - `model.py`: Configuration dataclasses (DatabaseConfig, AppConfig)
  - `logging.py`: Logging configuration
- **turtle/service/**: Business logic layer
  - `data_update_service.py`: Data ingestion and updates
  - `signal_service.py`: Trading signal generation
  - `backtest_service.py`: Single-signal backtesting
  - `portfolio_service.py`: Portfolio-level backtesting
  - `live_trading_service.py`: Live trading orchestration
  - `eodhd_service.py`: EODHD data operations

### Database Schema
- **Schema**: `turtle`
- **Key Tables**: `ticker`, `bars_history`, `company`, `symbol_group`
- **Connection**: PostgreSQL via psycopg with connection pooling

### Data Sources
- **Alpaca API**: Historical OHLCV data
- **Yahoo Finance**: Company fundamental data
- **EODHD**: Symbol lists and metadata

## Live Trading System (turtle/trade/)

### ⚠️ SAFETY NOTICE
**This system trades real money. Always start with paper trading and thoroughly test before using real capital.**

### Architecture Overview
The live trading system provides production-ready infrastructure for executing trading strategies in real-time through the Alpaca API. It consists of 7 coordinated components that handle the complete signal-to-execution pipeline with comprehensive risk management.

```
Signal Generation
      ↓
LiveTradingManager (Orchestrator)
      ↓
RiskManager (Pre-trade checks)
      ├→ Position size limits
      ├→ Daily loss limits
      └→ Portfolio exposure limits
      ↓
OrderExecutor (Order management)
      ├→ AlpacaTradingClient (Broker API)
      └→ Order lifecycle tracking
      ↓
PositionTracker (Real-time monitoring)
      ├→ P&L calculation
      └→ Position updates
      ↓
TradeLogger (Database persistence)
      └→ Audit trail + performance analysis
```

### Core Components

#### 1. LiveTradingManager (manager.py)
**Main orchestrator for live trading operations.**

**Key responsibilities:**
- Coordinates all trading components
- Manages trading session lifecycle
- Processes signals through risk checks
- Handles portfolio state management

**Initialization:**
```python
from turtle.trade import LiveTradingManager, RiskParameters

manager = LiveTradingManager(
    api_key="your_alpaca_key",
    secret_key="your_alpaca_secret",
    strategy_name="darvas_box",
    risk_parameters=RiskParameters(
        max_position_size=10000,
        max_daily_loss=500,
        max_portfolio_exposure=0.9
    ),
    db_dsn="postgresql://...",
    paper_trading=True,  # ALWAYS True for testing
    universe=["AAPL", "MSFT", "GOOGL"]  # Optional: limit trading universe
)
```

**Key methods:**
- `start_session()`: Initialize trading session
- `process_signals(signals)`: Convert signals to orders with risk checks
- `stop_session()`: Gracefully stop trading and cleanup
- `get_portfolio_state()`: Current positions and cash

#### 2. AlpacaTradingClient (client.py)
**Abstraction layer for Alpaca API communication.**

**Key methods:**
- `submit_order(symbol, qty, side, order_type)`: Submit order to Alpaca
- `get_account()`: Retrieve account information and buying power
- `get_positions()`: Get all open positions
- `get_orders()`: Retrieve order history
- `cancel_order(order_id)`: Cancel pending order
- `is_market_open()`: Check if market is currently open

**Features:**
- Automatic market hours validation
- Connection state management
- Error handling and retries
- Paper/live trading mode switching

#### 3. OrderExecutor (order_executor.py)
**Manages order lifecycle from submission to fill.**

**Key responsibilities:**
- Submit orders through AlpacaTradingClient
- Track order status (pending, filled, cancelled, rejected)
- Handle partial fills
- Order timeout management
- Error handling and logging

**Order types supported:**
- Market orders (immediate execution)
- Limit orders (price-specific execution)
- Stop orders (stop-loss triggers)

#### 4. PositionTracker (position_tracker.py)
**Real-time monitoring of open positions.**

**Key responsibilities:**
- Tracks all open positions
- Updates market prices in real-time
- Calculates unrealized P&L
- Maintains position history
- Monitors position limits

**Position information:**
- Entry price and current price
- Quantity and market value
- Unrealized profit/loss
- Position age (days held)

#### 5. RiskManager (risk_manager.py)
**Pre-trade risk checks and portfolio protection.**

**Risk controls:**
- **Position size limits**: Prevents oversized positions
- **Daily loss limits**: Stops trading if daily loss threshold reached
- **Portfolio exposure limits**: Maximum % of capital in positions
- **Symbol limits**: Maximum positions per symbol
- **Concentration limits**: Maximum % in single position

**Risk parameters configuration:**
```python
risk_params = RiskParameters(
    max_position_size=10000,        # Max $ per position
    max_daily_loss=500,             # Stop trading if lose $500 in day
    max_portfolio_exposure=0.9,     # Max 90% of capital deployed
    max_positions=10,               # Maximum concurrent positions
    max_position_concentration=0.2  # Max 20% in single position
)
```

**Pre-trade checks performed:**
- Sufficient buying power
- Position size within limits
- Daily loss not exceeded
- Portfolio exposure acceptable
- No duplicate positions (if configured)

#### 6. TradeLogger (trade_logger.py)
**Persistent storage of all trading activity.**

**Logged information:**
- All order submissions and fills
- Position openings and closings
- P&L realized and unrealized
- Risk check results
- Trading session metadata

**Database tables:**
- `trading_sessions`: Session-level information
- `live_orders`: All orders (filled, cancelled, rejected)
- `trade_log`: Complete trade history

**Benefits:**
- Complete audit trail
- Performance analysis
- Debugging and troubleshooting
- Regulatory compliance
- Strategy refinement data

#### 7. Models (models.py)
**Data models for live trading.**

**Key models:**
- **TradingSession**: Session state and performance tracking
  - session_id, start_time, end_time
  - total_pnl, trades_count
  - strategy_name, paper_trading flag

- **LiveOrder**: Order representation with status
  - order_id, symbol, side (buy/sell)
  - quantity, filled_qty
  - order_type, status
  - submitted_at, filled_at

- **AccountInfo**: Alpaca account snapshot
  - buying_power, cash, portfolio_value
  - equity, last_update

- **RiskParameters**: Risk management configuration
  - All limit values and thresholds

- **Enums**: OrderSide, OrderType, OrderStatus

### Usage Workflow

**1. Initial Setup (Development)**
```bash
# Set up paper trading configuration
uv run python scripts/setup_live_trading.py \
  --strategy darvas_box \
  --paper-trading \
  --max-position-size 5000 \
  --max-daily-loss 200
```

**2. Generate Signals**
```python
from turtle.signal import DarvasBoxStrategy

strategy = DarvasBoxStrategy()
signals = strategy.generate_signals(bars_data, params)
```

**3. Initialize Live Trading**
```python
manager = LiveTradingManager(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    strategy_name="darvas_box",
    risk_parameters=risk_params,
    db_dsn=settings.database.dsn,
    paper_trading=True  # CRITICAL: Always True for testing
)

# Start trading session
session = manager.start_session()
```

**4. Process Signals Through Risk Checks**
```python
# Signals are checked by RiskManager before execution
executed_orders = manager.process_signals(signals)

# Check results
for order in executed_orders:
    if order.status == OrderStatus.FILLED:
        logger.info(f"Order filled: {order.symbol} {order.filled_qty}@{order.filled_price}")
    elif order.status == OrderStatus.REJECTED:
        logger.warning(f"Order rejected: {order.symbol} - {order.rejection_reason}")
```

**5. Monitor Positions**
```python
# Get current portfolio state
portfolio = manager.get_portfolio_state()

print(f"Cash: ${portfolio.cash}")
print(f"Positions: {len(portfolio.positions)}")
print(f"Total P&L: ${portfolio.total_pnl}")

# Monitor individual positions
for position in portfolio.positions:
    print(f"{position.symbol}: {position.quantity}@{position.entry_price}")
    print(f"  Current: ${position.current_price}, P&L: ${position.unrealized_pnl}")
```

**6. Stop Trading**
```python
# Gracefully stop trading session
manager.stop_session()
```

### Safety Checklist

Before using live trading, verify:
- [ ] **Paper trading tested**: Minimum 2 weeks paper trading with strategy
- [ ] **Risk parameters set**: Conservative limits configured
- [ ] **Monitoring setup**: Log monitoring and alerting configured
- [ ] **Emergency procedures**: Know how to stop trading immediately
- [ ] **Position limits**: Max position size appropriate for account size
- [ ] **Daily loss limit**: Set to acceptable daily risk amount
- [ ] **Market hours verified**: Understand when orders will execute
- [ ] **API credentials**: Verified and tested in paper environment
- [ ] **Database logging**: Confirmed all trades being logged
- [ ] **Code reviewed**: All trading logic reviewed and tested

### Emergency Procedures

**If something goes wrong:**

1. **Stop Trading Immediately**
   - Press Ctrl+C in terminal running live trading
   - Or call `manager.stop_session()` if accessible

2. **Cancel All Pending Orders**
   ```python
   client = manager.trading_client
   open_orders = client.get_orders(status='open')
   for order in open_orders:
       client.cancel_order(order.id)
   ```

3. **Close All Positions (If Necessary)**
   - Log into Alpaca web interface
   - Manually close positions through broker interface
   - Or use liquidation API call (last resort)

4. **Review Logs**
   ```bash
   tail -f logs/live_trading.log
   ```

5. **Check Database for Trade History**
   ```sql
   SELECT * FROM turtle.trading_sessions ORDER BY start_time DESC LIMIT 1;
   SELECT * FROM turtle.live_orders WHERE session_id = 'xxx';
   ```

### Configuration Requirements

**Environment Variables (.env)**
```bash
# Alpaca API Credentials
ALPACA_API_KEY="your_api_key"
ALPACA_SECRET_KEY="your_secret_key"

# Database
DB_PASSWORD="your_db_password"
```

**Settings (config/settings.toml)**
```toml
[app.alpaca]
api_key = "placeholder"  # Override with env var
secret_key = "placeholder"  # Override with env var
paper_trading = true  # CRITICAL: true for testing
base_url = "https://paper-api.alpaca.markets"  # Paper trading URL
```

### Monitoring & Logging

**Log Locations:**
- `logs/live_trading.log`: All trading activity
- `logs/risk_manager.log`: Risk check results
- `logs/order_executor.log`: Order execution details

**Key Metrics to Monitor:**
- Fill rate: % of orders successfully filled
- Rejection rate: % of orders rejected by risk checks
- Average slippage: Difference between expected and actual fill prices
- Position count: Number of concurrent positions
- Daily P&L: Running profit/loss for the day
- Buying power: Available capital for new positions

**Alerting (Recommended):**
- Alert on daily loss limit approaching (e.g., 80% of limit)
- Alert on order rejections
- Alert on position tracking errors
- Alert on API connection failures

### Common Pitfalls

**1. Not Using Paper Trading**
- **Problem**: Testing strategies with real money
- **Solution**: Always set `paper_trading=True` for testing

**2. Insufficient Risk Parameters**
- **Problem**: No daily loss limit or position size limits
- **Solution**: Always configure RiskParameters with conservative limits

**3. Ignoring Market Hours**
- **Problem**: Attempting to trade when market is closed
- **Solution**: Use `is_market_open()` check before processing signals

**4. Not Monitoring Logs**
- **Problem**: Missing order rejections or errors
- **Solution**: Set up log monitoring and alerting

**5. Overlapping Sessions**
- **Problem**: Running multiple trading sessions simultaneously
- **Solution**: Ensure only one LiveTradingManager instance active

**6. Missing Database Logging**
- **Problem**: No trade history for analysis
- **Solution**: Verify TradeLogger is configured and database accessible

**7. Hardcoded Credentials**
- **Problem**: API keys in code
- **Solution**: Use environment variables via .env file

### Related Scripts
- `scripts/setup_live_trading.py` - Initialize and configure live trading
- See: [Scripts Reference](#scripts-reference) for details

### Related Examples
- `examples/live_trading_example.py` - Complete setup example
- See: [Examples & Notebooks](#examples--notebooks) for details

## Portfolio Management System (turtle/portfolio/)

### Purpose
Manages multi-position portfolios with fixed capital allocation, position sizing, and comprehensive performance analytics for backtesting scenarios.

### Core Components

#### PortfolioManager (manager.py)
**Manages portfolio positions, cash allocation, and daily state tracking.**

**Key responsibilities:**
- Opens and closes positions with dynamic sizing
- Enforces capital constraints (min/max position amounts)
- Tracks daily portfolio snapshots for performance analysis
- Integrates slippage modeling for realistic backtests

**Initialization:**
```python
from turtle.portfolio import PortfolioManager
from datetime import datetime

manager = PortfolioManager(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=30000.0,           # Starting capital
    position_min_amount=1500.0,        # Minimum position size
    position_max_amount=3000.0         # Maximum position size
)
```

**Key methods:**
- `open_position(signal, price)`: Open new position
- `close_position(ticker, price, date)`: Close existing position
- `update_daily_snapshot(date)`: Record daily portfolio state
- `get_current_positions()`: List all open positions
- `available_cash()`: Cash available for new positions

**Position Sizing Logic:**
- Calculates position size based on available cash
- Respects min/max position amount constraints
- Accounts for existing positions
- Prevents over-allocation of capital

#### PortfolioSignalSelector (selector.py)
**Filters and ranks signals for portfolio selection.**

**Key responsibilities:**
- Applies ranking strategies to prioritize signals
- Manages position limits (max concurrent positions)
- Prevents over-concentration
- Filters by minimum ranking threshold

**Usage:**
```python
from turtle.portfolio import PortfolioSignalSelector
from turtle.ranking import MomentumRanking

selector = PortfolioSignalSelector(
    max_positions=10,              # Max concurrent positions
    min_ranking=70                 # Minimum signal ranking to consider
)

ranking_strategy = MomentumRanking(lookback_period=20)

# Select top signals for portfolio
selected_signals = selector.select_signals(
    all_signals,
    current_positions=portfolio.get_current_positions(),
    ranking_strategy=ranking_strategy,
    bars_data=historical_data
)
```

**Selection process:**
1. Apply ranking strategy to all signals
2. Filter by minimum ranking threshold
3. Remove signals for existing positions
4. Sort by ranking (highest first)
5. Select top N signals (up to max_positions limit)

#### PortfolioAnalytics (analytics.py)
**Calculates comprehensive performance metrics.**

**Key metrics:**
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Average Win/Loss**: Mean profit vs mean loss
- **Total Return**: Overall portfolio return
- **Annual Return**: Annualized return percentage

**Benchmark comparison:**
- Compare against SPY (S&P 500)
- Compare against QQQ (NASDAQ-100)
- Custom benchmark ticker support

**Usage:**
```python
from turtle.portfolio import PortfolioAnalytics

analytics = PortfolioAnalytics(portfolio_state=manager.state)

# Calculate metrics
metrics = analytics.calculate_metrics(
    benchmark_ticker="SPY",
    risk_free_rate=0.02  # 2% annual risk-free rate
)

print(f"Total Return: {metrics.total_return:.2%}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"Win Rate: {metrics.win_rate:.2%}")

# Generate equity curve
equity_curve = analytics.calculate_equity_curve()

# Compare to benchmark
comparison = analytics.compare_to_benchmark("SPY", spy_data)
print(f"Outperformance: {comparison.excess_return:.2%}")
```

### Portfolio Models (portfolio/models.py)

**PortfolioState**: Complete portfolio state container
```python
@dataclass
class PortfolioState:
    daily_snapshots: list[DailyPortfolioSnapshot]
    future_trades: list[Trade]
```

**DailyPortfolioSnapshot**: Daily cash and position snapshot
```python
@dataclass
class DailyPortfolioSnapshot:
    date: datetime
    cash: float
    positions: list[Position]
    total_value: float
```

**Position**: Individual position with P&L tracking
```python
@dataclass
class Position:
    ticker: str
    quantity: int
    entry_price: float
    entry_date: datetime
    current_price: float
    unrealized_pnl: float
```

**PortfolioMetrics**: Performance calculation results
```python
@dataclass
class PortfolioMetrics:
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    avg_win: float
    avg_loss: float
    total_trades: int
```

### Usage Example: Complete Portfolio Backtest

```python
from turtle.portfolio import PortfolioManager, PortfolioSignalSelector, PortfolioAnalytics
from turtle.signal import DarvasBoxStrategy
from turtle.ranking import MomentumRanking
from turtle.exit import ProfitLossExitStrategy
from datetime import datetime

# 1. Initialize components
portfolio = PortfolioManager(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=30000,
    position_min_amount=1500,
    position_max_amount=3000
)

selector = PortfolioSignalSelector(max_positions=10, min_ranking=70)
ranking_strategy = MomentumRanking(lookback_period=20)
signal_strategy = DarvasBoxStrategy()
exit_strategy = ProfitLossExitStrategy(profit_target=0.20, stop_loss=0.10)

# 2. Load historical data
bars_data = load_bars_history(start_date, end_date, tickers)

# 3. Generate signals
signals = signal_strategy.generate_signals(bars_data)

# 4. Select top signals using ranking
selected_signals = selector.select_signals(
    signals,
    portfolio.get_current_positions(),
    ranking_strategy,
    bars_data
)

# 5. Execute portfolio logic (open/close positions)
for date in trading_days:
    # Check exit conditions for open positions
    for position in portfolio.get_current_positions():
        if exit_strategy.should_exit(position, bars_data):
            portfolio.close_position(position.ticker, current_price, date)

    # Open new positions from selected signals
    for signal in selected_signals:
        if portfolio.available_cash() >= portfolio.position_min_amount:
            portfolio.open_position(signal, current_price)

    # Update daily snapshot
    portfolio.update_daily_snapshot(date)

# 6. Calculate performance metrics
analytics = PortfolioAnalytics(portfolio.state)
metrics = analytics.calculate_metrics(benchmark_ticker="SPY")

print(f"Portfolio Performance:")
print(f"  Total Return: {metrics.total_return:.2%}")
print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"  Win Rate: {metrics.win_rate:.2%}")
print(f"  Total Trades: {metrics.total_trades}")
```

### Related Services
- `turtle/service/portfolio_service.py` - Orchestrates complete portfolio backtests
- See: [Service Layer](#service-layer) for details

### Related Scripts
- `scripts/portfolio_runner.py` - CLI for portfolio backtesting with all parameters
- See: [Scripts Reference](#scripts-reference) for details

## Configuration System (turtle/config/)

### Overview
TOML-based configuration with environment variable overrides for sensitive data. The configuration system loads settings from `config/settings.toml` and securely injects API keys and passwords from environment variables.

### Configuration Files

#### turtle/config/settings.py
**Settings loader with TOML parsing and environment variable injection.**

**Usage:**
```python
from turtle.config.settings import Settings

# Load settings from default location
settings = Settings.from_toml("./config/settings.toml")

# Access configuration
db_pool = settings.pool
api_key = settings.app.eodhd.api_key
alpaca_key = settings.app.alpaca.api_key
```

**Features:**
- Loads TOML configuration file
- Overrides sensitive values with environment variables
- Creates database connection pool
- Validates configuration on load

#### turtle/config/model.py
**Configuration dataclasses.**

**DatabaseConfig**: Database connection parameters
```python
@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    schema: str
    pool_size: int
```

**AppConfig**: Application configuration
```python
@dataclass
class AppConfig:
    name: str
    environment: str
    eodhd: EODHDConfig
    alpaca: AlpacaConfig
```

#### turtle/config/logging.py
**Logging configuration and setup.**

Configures:
- Log levels per module
- Log file locations
- Log format and rotation
- Console and file handlers

### Configuration File Structure (config/settings.toml)

```toml
[app]
name = "turtle-backtest"
environment = "development"

[app.eodhd]
api_key = "placeholder"  # ⚠️ Override with EODHD_API_KEY env var
base_url = "https://eodhd.com/api"
rate_limit = 20  # requests per second

[app.alpaca]
api_key = "placeholder"  # ⚠️ Override with ALPACA_API_KEY env var
secret_key = "placeholder"  # ⚠️ Override with ALPACA_SECRET_KEY env var
paper_trading = true  # CRITICAL: true for testing, false for live
base_url = "https://paper-api.alpaca.markets"

[database]
host = "localhost"
port = 5432
name = "trading"
user = "postgres"
password = "placeholder"  # ⚠️ Override with DB_PASSWORD env var
schema = "turtle"
pool_size = 10
pool_timeout = 30
```

### Environment Variables (.env)

**Required for production use:**
```bash
# EODHD Data Provider
EODHD_API_KEY="your_eodhd_api_key_here"

# Alpaca Trading API
ALPACA_API_KEY="your_alpaca_api_key"
ALPACA_SECRET_KEY="your_alpaca_secret_key"

# Database
DB_PASSWORD="your_database_password"
```

**Optional environment variables:**
```bash
# Override database connection
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="trading"
DB_USER="postgres"

# Logging
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE="logs/app.log"
```

### Environment Variable Precedence
1. **Environment variables** (highest priority) - from `.env` file or system
2. **settings.toml values** - default configuration
3. **Code defaults** - hardcoded fallbacks

### Setup Instructions

**1. Create .env file in project root:**
```bash
# Copy template
cp .env.example .env

# Edit with your actual credentials
nano .env
```

**2. Secure the .env file:**
```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env
```

**3. Verify configuration loads:**
```python
from turtle.config.settings import Settings

settings = Settings.from_toml()
print(f"Environment: {settings.app.environment}")
print(f"DB Pool: {settings.pool}")
# API keys will be loaded from env vars
```

### Database Connection
**Default DSN**: `"host=localhost port=5432 dbname=trading user=postgres password=postgres361"`

**Connection pooling:**
- Pool size: 10 connections (configurable in settings.toml)
- Pool timeout: 30 seconds
- Automatic connection recycling
- Thread-safe connection management

**Usage:**
```python
from turtle.config.settings import Settings

settings = Settings.from_toml()

# Get connection from pool
with settings.pool.connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM turtle.ticker LIMIT 10")
        results = cur.fetchall()
```

### Time Frames
Configurable via `TimeFrameUnit` enum in `turtle/common/enums.py`:
- **DAY**: Daily bars
- **WEEK**: Weekly bars
- **MONTH**: Monthly bars

**Usage:**
```python
from turtle.common.enums import TimeFrameUnit

# Use in data operations
data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
```

### Best Practices

**Security:**
- ✅ **Never commit .env** to version control
- ✅ **Use environment variables** for all secrets
- ✅ **Rotate API keys** periodically
- ✅ **Use different keys** for dev/staging/prod
- ❌ **Never hardcode** API keys or passwords in code
- ❌ **Never log** sensitive configuration values

**Configuration Management:**
- Use `settings.toml` for non-sensitive defaults
- Override sensitive values via environment variables
- Keep separate `.env` files for different environments
- Document all configuration options
- Validate configuration on application startup

**Development vs Production:**
```toml
# Development (settings.toml)
[app]
environment = "development"

[app.alpaca]
paper_trading = true  # Always use paper trading in dev
base_url = "https://paper-api.alpaca.markets"

# Production (override via env vars)
# In production .env file:
# APP_ENVIRONMENT="production"
# ALPACA_PAPER_TRADING="false"
# ALPACA_BASE_URL="https://api.alpaca.markets"
```

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

## Service Layer (turtle/service/)

### Architecture Pattern
Services orchestrate complex workflows across multiple repositories and systems. Each service encapsulates a specific business capability, providing a high-level API for common operations.

**Service responsibilities:**
- Coordinate multiple repositories and data sources
- Implement business logic and workflows
- Handle error scenarios and validation
- Provide transaction management
- Abstract complexity from scripts and applications

### Available Services

#### 1. DataUpdateService (data_update_service.py)
**Purpose**: Data ingestion and updates from external sources (EODHD, Alpaca, Yahoo Finance).

**Key methods:**
- `update_symbol_list()`: Download USA stock symbols from EODHD
  - Fetches complete list of US exchange tickers
  - Stores in `ticker` table with exchange information
  - Updates existing symbols, adds new ones

- `update_company_list()`: Fetch company data from Yahoo Finance
  - Downloads fundamental data (sector, industry, market cap)
  - Enriches ticker data with company information
  - Handles API rate limiting and retries

- `update_bars_history(start_date, end_date)`: Download OHLCV historical data
  - Fetches price data from EODHD API
  - Supports date range specification
  - Batch processing for large ticker lists
  - Validates data quality before storage

- `update_ticker_data()`: Fetch extended ticker information
  - Downloads additional ticker metadata
  - Market capitalization, shares outstanding
  - Sector and industry classifications

**Usage scenarios:**
- Daily EOD data updates (via `scripts/daily_eod_update.py`)
- Bulk historical data downloads (via `scripts/download_eodhd_data.py`)
- Initial database population
- Data refresh and maintenance

**Example:**
```python
from turtle.service import DataUpdateService
from turtle.common.enums import TimeFrameUnit
from datetime import datetime

service = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)

# Update symbol list
service.update_symbol_list()

# Download historical data
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
service.update_bars_history(start_date, end_date)
```

#### 2. SignalService (signal_service.py)
**Purpose**: Trading signal generation from strategies with optional ranking and export.

**Key methods:**
- `generate_signals(strategy, start_date, end_date, tickers)`: Generate trading signals
  - Applies strategy to historical data
  - Returns signals with entry dates and prices
  - Supports ticker filtering

- `filter_by_ranking(signals, ranking_strategy, min_ranking)`: Apply ranking filters
  - Ranks signals using specified strategy
  - Filters by minimum ranking threshold
  - Returns prioritized signal list

- `export_to_sheets(signals, spreadsheet_id, sheet_name)`: Export to Google Sheets
  - Formats signals for Google Sheets
  - Handles authentication
  - Creates or updates sheet

**Usage scenarios:**
- Signal analysis and review (via `scripts/signal_runner.py`)
- Automated signal generation pipelines
- Signal export for external analysis
- Strategy development and testing

**Example:**
```python
from turtle.service import SignalService
from turtle.signal import DarvasBoxStrategy
from turtle.ranking import MomentumRanking

service = SignalService()
strategy = DarvasBoxStrategy()
ranking_strategy = MomentumRanking(lookback_period=20)

# Generate and rank signals
signals = service.generate_signals(
    strategy=strategy,
    start_date=datetime(2024, 6, 1),
    end_date=datetime(2024, 6, 30),
    tickers=["AAPL", "MSFT", "GOOGL"]
)

ranked_signals = service.filter_by_ranking(
    signals=signals,
    ranking_strategy=ranking_strategy,
    min_ranking=70
)

# Export to Google Sheets
service.export_to_sheets(
    signals=ranked_signals,
    spreadsheet_id="your_spreadsheet_id",
    sheet_name="June 2024 Signals"
)
```

#### 3. BacktestService (backtest_service.py)
**Purpose**: Single-signal backtesting (signal-to-exit strategy combination testing).

**Key methods:**
- `run_backtest(ticker, signal_strategy, exit_strategy, start_date, end_date)`: Execute backtest
  - Tests specific ticker with signal and exit strategy
  - Returns complete trade history
  - Calculates performance metrics

- `calculate_metrics(backtest_results)`: Performance metrics calculation
  - Total return, Sharpe ratio
  - Win rate, average win/loss
  - Maximum drawdown
  - Trade statistics

**Usage scenarios:**
- Strategy parameter optimization
- Signal/exit strategy combination testing
- Individual ticker analysis
- Strategy validation (via `scripts/backtest.py`)

**Example:**
```python
from turtle.service import BacktestService
from turtle.signal import DarvasBoxStrategy
from turtle.exit import ProfitLossExitStrategy

service = BacktestService()

results = service.run_backtest(
    ticker="AAPL",
    signal_strategy=DarvasBoxStrategy(),
    exit_strategy=ProfitLossExitStrategy(profit_target=0.20, stop_loss=0.10),
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

metrics = service.calculate_metrics(results)
print(f"Total Return: {metrics.total_return:.2%}")
print(f"Win Rate: {metrics.win_rate:.2%}")
```

#### 4. PortfolioService (portfolio_service.py)
**Purpose**: Portfolio-level backtesting with multiple positions and ranking strategies.

**Key methods:**
- `run_portfolio_backtest(config)`: Multi-ticker portfolio simulation
  - Manages multiple concurrent positions
  - Applies ranking for signal selection
  - Enforces position limits and capital constraints
  - Tracks daily portfolio snapshots

- `generate_tearsheet(portfolio_results, output_file)`: HTML performance report
  - Comprehensive performance visualization
  - Equity curve, drawdown chart
  - Trade statistics and metrics
  - Benchmark comparison

- `calculate_benchmark_comparison(portfolio, benchmark_ticker)`: Compare to market indices
  - Compares portfolio to SPY, QQQ, or custom benchmark
  - Calculates alpha and beta
  - Risk-adjusted performance metrics

**Usage scenarios:**
- Portfolio strategy testing (via `scripts/portfolio_runner.py`)
- Multi-position backtesting
- Capital allocation optimization
- Strategy performance reporting

**Example:**
```python
from turtle.service import PortfolioService
from turtle.signal import MarsStrategy
from turtle.exit import EMAExitStrategy
from turtle.ranking import VolumeMomentumRanking

service = PortfolioService()

config = {
    "start_date": datetime(2024, 1, 1),
    "end_date": datetime(2024, 12, 31),
    "signal_strategy": MarsStrategy(),
    "exit_strategy": EMAExitStrategy(period=50),
    "ranking_strategy": VolumeMomentumRanking(),
    "initial_capital": 30000,
    "position_min_amount": 1500,
    "position_max_amount": 3000,
    "min_signal_ranking": 70,
    "max_tickers": 100
}

results = service.run_portfolio_backtest(config)

# Generate HTML tearsheet
service.generate_tearsheet(
    portfolio_results=results,
    output_file="reports/mars_strategy_2024.html"
)

# Compare to benchmark
comparison = service.calculate_benchmark_comparison(results, "SPY")
print(f"Alpha: {comparison.alpha:.2%}")
print(f"Outperformance: {comparison.excess_return:.2%}")
```

#### 5. LiveTradingService (live_trading_service.py)
**Purpose**: Orchestrates live trading sessions with full risk management.

**Key methods:**
- `start_trading_session(config)`: Initialize live trading
  - Creates LiveTradingManager with configuration
  - Sets up risk parameters
  - Initializes database logging
  - Validates API connectivity

- `process_daily_signals(session, signals)`: Daily signal processing
  - Filters signals through risk checks
  - Executes approved orders
  - Updates position tracking
  - Logs all activity

- `monitor_positions(session)`: Real-time position monitoring
  - Tracks P&L for open positions
  - Checks exit conditions
  - Monitors risk limits
  - Generates alerts if needed

**Usage scenarios:**
- Production trading automation
- Paper trading testing
- Live trading setup (via `scripts/setup_live_trading.py`)
- Automated daily trading workflows

**Example:**
```python
from turtle.service import LiveTradingService
from turtle.trade.models import RiskParameters

service = LiveTradingService()

config = {
    "strategy_name": "darvas_box",
    "api_key": os.getenv("ALPACA_API_KEY"),
    "secret_key": os.getenv("ALPACA_SECRET_KEY"),
    "risk_parameters": RiskParameters(
        max_position_size=10000,
        max_daily_loss=500,
        max_portfolio_exposure=0.9
    ),
    "paper_trading": True,  # ALWAYS True for testing
    "universe": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
}

# Start trading session
session = service.start_trading_session(config)

# Process signals (typically in daily loop)
signals = generate_daily_signals()  # From SignalService
service.process_daily_signals(session, signals)

# Monitor positions
service.monitor_positions(session)
```

#### 6. EODHDService (eodhd_service.py)
**Purpose**: EODHD API operations and data handling with validation.

**Key methods:**
- `fetch_eod_data(ticker, start_date, end_date)`: Download end-of-day price data
  - Retrieves OHLCV data from EODHD API
  - Handles API rate limiting
  - Returns validated data

- `fetch_ticker_list(exchange)`: Get available tickers
  - Downloads ticker list for specified exchange
  - Filters by exchange (US, NYSE, NASDAQ)
  - Returns ticker metadata

- `validate_response(response)`: Response validation and error handling
  - Checks API response status
  - Validates data completeness
  - Handles API errors gracefully
  - Provides detailed error messages

**Usage scenarios:**
- Data download operations
- API abstraction for other services
- Data validation pipelines
- Error handling and retry logic

**Example:**
```python
from turtle.service import EODHDService
from datetime import datetime

service = EODHDService(api_key=os.getenv("EODHD_API_KEY"))

# Fetch EOD data
data = service.fetch_eod_data(
    ticker="AAPL.US",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Fetch ticker list
tickers = service.fetch_ticker_list(exchange="US")
print(f"Found {len(tickers)} US tickers")
```

### Service Selection Guide

| Need | Use This Service | Script/Example |
|------|-----------------|----------------|
| **Daily data updates** | DataUpdateService | `scripts/daily_eod_update.py` |
| **Generate signals** | SignalService | `scripts/signal_runner.py` |
| **Test single strategy** | BacktestService | `scripts/backtest.py` |
| **Test portfolio** | PortfolioService | `scripts/portfolio_runner.py` |
| **Live trading** | LiveTradingService | `scripts/setup_live_trading.py` |
| **EODHD data operations** | EODHDService | Used by DataUpdateService |

### Service Integration Patterns

**Pattern 1: Data Pipeline**
```
EODHDService → DataUpdateService → Database
```

**Pattern 2: Signal Generation**
```
Database → SignalService → (Optional) Google Sheets
```

**Pattern 3: Backtesting**
```
Database → BacktestService/PortfolioService → Performance Report
```

**Pattern 4: Live Trading**
```
Database → SignalService → LiveTradingService → Alpaca API
```

### Best Practices

**Service Usage:**
- Always use services for complex operations (don't bypass to repositories)
- Services handle transactions and error scenarios
- Services provide consistent logging and monitoring
- Services abstract external API complexity

**Error Handling:**
- Services return structured results with success/failure indicators
- Check service return values before proceeding
- Services log errors automatically
- Use service-level retries for transient failures

**Testing:**
- Test services with mock repositories
- Use dependency injection for testability
- Services should be stateless when possible
- Integration tests for service workflows

## Ranking System (turtle/ranking/)

### Purpose
Filters and prioritizes trading signals based on relative strength metrics. Used in portfolio backtesting to select top signals when position limits apply.

### Base Class
**RankingStrategy** (base.py)
- Abstract interface for ranking implementations
- `calculate_ranking(signals, bars_data)` method returns signals with ranking scores (0-100)
- Higher scores indicate stronger signals

### Available Strategies

#### MomentumRanking (momentum.py)
**Ranks signals by price momentum over lookback period.**

**Parameters:**
- `lookback_period`: Days to calculate momentum (default: 20)
- `scoring_method`: "percentile" or "absolute"

**Algorithm:**
- Calculates price change over lookback period
- Normalizes to 0-100 scale
- Higher momentum = higher ranking

**Usage:**
```python
from turtle.ranking import MomentumRanking

ranking = MomentumRanking(lookback_period=20, scoring_method="percentile")
ranked_signals = ranking.calculate_ranking(signals, bars_data)

# Filter by minimum ranking
top_signals = [s for s in ranked_signals if s.ranking >= 70]
```

**Best for:**
- Trend-following strategies
- Momentum-based entry signals
- High-conviction trades

#### VolumeMomentumRanking (volume_momentum.py)
**Combines price momentum with volume confirmation.**

**Parameters:**
- `price_weight`: Weight for price momentum (default: 0.7)
- `volume_weight`: Weight for volume momentum (default: 0.3)
- `lookback_period`: Days for calculation (default: 20)

**Algorithm:**
- Calculates price momentum score
- Calculates volume momentum score (volume trend)
- Weighted combination: `ranking = (price_momentum * 0.7) + (volume_momentum * 0.3)`

**Usage:**
```python
from turtle.ranking import VolumeMomentumRanking

ranking = VolumeMomentumRanking(
    price_weight=0.7,
    volume_weight=0.3,
    lookback_period=20
)

ranked_signals = ranking.calculate_ranking(signals, bars_data)
```

**Best for:**
- Volume-confirmation strategies
- Avoiding low-liquidity signals
- Breakout strategies

### Usage in Portfolio Backtesting

```python
from turtle.portfolio import PortfolioSignalSelector
from turtle.ranking import MomentumRanking

# Initialize selector with ranking
selector = PortfolioSignalSelector(
    max_positions=10,
    min_ranking=70
)

ranking_strategy = MomentumRanking(lookback_period=20)

# Select top signals
selected_signals = selector.select_signals(
    all_signals=signals,
    current_positions=portfolio.get_current_positions(),
    ranking_strategy=ranking_strategy,
    bars_data=historical_data
)

# Result: Top 10 signals with ranking >= 70
```

### Creating Custom Ranking Strategies

**1. Create new file**: `turtle/ranking/my_ranking.py`

**2. Extend RankingStrategy**:
```python
from turtle.ranking.base import RankingStrategy
from turtle.signal.models import Signal

class MyRankingStrategy(RankingStrategy):
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def calculate_ranking(
        self,
        signals: list[Signal],
        bars_data: dict
    ) -> list[Signal]:
        """
        Calculate ranking score (0-100) for each signal.

        Returns:
            Signals with ranking attribute added
        """
        ranked_signals = []

        for signal in signals:
            # Your ranking logic here
            score = self._calculate_score(signal, bars_data)

            # Normalize to 0-100
            signal.ranking = max(0, min(100, score))
            ranked_signals.append(signal)

        return ranked_signals

    def _calculate_score(self, signal, bars_data):
        # Implementation-specific logic
        pass
```

**3. Use in portfolio backtesting**:
```python
from turtle.ranking.my_ranking import MyRankingStrategy

ranking = MyRankingStrategy(param1=value1, param2=value2)
# Use with PortfolioSignalSelector
```

### Related Components
- **PortfolioSignalSelector**: Uses rankings for signal selection
- **PortfolioService**: Integrates ranking into backtests
- **scripts/portfolio_runner.py**: `--ranking-strategy` parameter

## Google Sheets Integration (turtle/google/)

### Purpose
Export trading signals to Google Sheets for analysis, sharing, and collaboration.

### Components

#### SignalExporter (signal_exporter.py)
**Main interface for exporting signals to Google Sheets.**

**Key methods:**
- `export_signals(signals, spreadsheet_id, sheet_name)`: Write signals to sheet
  - Formats signals for spreadsheet display
  - Creates headers and data rows
  - Handles large signal lists

- `format_signals(signals)`: Convert Signal objects to sheet format
  - Extracts key signal attributes
  - Formats dates and numbers
  - Adds ranking information

- `create_header()`: Generate column headers
  - Ticker, Date, Signal Type
  - Entry Price, Ranking
  - Strategy Name

**Usage:**
```python
from turtle.google import SignalExporter

exporter = SignalExporter(
    credentials_path="credentials.json",
    spreadsheet_id="your_spreadsheet_id"
)

exporter.export_signals(
    signals=trading_signals,
    sheet_name="2024-06-01 Signals"
)
```

#### GoogleSheetsClient (client.py)
**Google Sheets API wrapper.**

**Key methods:**
- `write_to_sheet(spreadsheet_id, sheet_name, data)`: Write data to specified sheet
  - Handles authentication
  - Creates sheet if doesn't exist
  - Batch writes for efficiency

- `clear_sheet(spreadsheet_id, sheet_name)`: Clear sheet contents
  - Removes all data from sheet
  - Preserves sheet structure

- `create_sheet(spreadsheet_id, sheet_name)`: Create new spreadsheet
  - Creates spreadsheet if doesn't exist
  - Returns spreadsheet ID

**Features:**
- Automatic retry on API errors
- Rate limiting compliance
- Batch operations for efficiency

#### Authentication (auth.py)
**Supports two authentication methods:**

**1. OAuth2 (User Credentials)**
- For personal use
- Requires browser authentication (one-time)
- Credentials stored in `token.json`
- Best for: Development, personal projects

**Setup:**
```bash
# 1. Enable Google Sheets API in Google Cloud Console
# 2. Create OAuth2 credentials
# 3. Download credentials.json to project root
# 4. Run authentication flow (opens browser)
python -c "from turtle.google.auth import get_oauth_credentials; get_oauth_credentials()"
```

**2. Service Account (Application Credentials)**
- For automated/server use
- Requires service account JSON key
- No browser interaction needed
- Best for: Production, automated workflows

**Setup:**
```bash
# 1. Create service account in Google Cloud Console
# 2. Download JSON key file
# 3. Share target spreadsheet with service account email
# 4. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Configuration

**Environment Variables:**
```bash
# Service Account (recommended for automation)
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Target Spreadsheet
GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id"
```

**Or in code:**
```python
exporter = SignalExporter(
    credentials_path="credentials.json",  # OAuth2
    # OR
    credentials_path="service-account.json",  # Service Account
    spreadsheet_id="abc123xyz"
)
```

### Complete Usage Example

```python
from turtle.google import SignalExporter
from turtle.service import SignalService
from turtle.signal import DarvasBoxStrategy
from datetime import datetime

# Generate signals
signal_service = SignalService()
strategy = DarvasBoxStrategy()

signals = signal_service.generate_signals(
    strategy=strategy,
    start_date=datetime(2024, 6, 1),
    end_date=datetime(2024, 6, 30),
    tickers=None  # All tickers
)

# Export to Google Sheets
exporter = SignalExporter(
    credentials_path="service-account.json",
    spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
)

exporter.export_signals(
    signals=signals,
    sheet_name="June 2024 - Darvas Box"
)

print(f"Exported {len(signals)} signals to Google Sheets")
```

### Troubleshooting

**Problem**: `Authentication failed`
**Solutions:**
- OAuth2: Delete `token.json` and re-run authentication
- Service Account: Verify JSON key path in env var
- Check Google Sheets API is enabled in Cloud Console

**Problem**: `Permission denied`
**Solutions:**
- Service Account: Share spreadsheet with service account email
- OAuth2: Ensure user has edit access to spreadsheet
- Check scopes include `https://www.googleapis.com/auth/spreadsheets`

**Problem**: `Rate limit exceeded`
**Solutions:**
- Add delays between exports
- Use batch operations (handled automatically by client)
- Reduce signal export frequency

### Related Scripts
- `scripts/signal_runner.py --mode sheets`: Export signals to Google Sheets
- See: [Scripts Reference](#scripts-reference) for details

### Related Examples
- `examples/google_sheets_test.py` - Authentication and export test
- See: [Examples & Notebooks](#examples--notebooks) for details

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

## Examples & Notebooks

### Jupyter Notebooks

#### backtesting.ipynb
**Purpose**: Interactive single-strategy backtesting with visualizations

**Topics covered:**
- Strategy testing and parameter tuning
- Performance analysis with charts
- Comparing different exit strategies
- Visualizing equity curves and drawdowns

**Best for:**
- Learning strategy behavior
- Quick experimentation
- Parameter optimization
- Visual performance analysis

**How to run:**
```bash
uv run jupyter notebook examples/backtesting.ipynb
```

#### portfolio_backtesting.ipynb
**Purpose**: Portfolio-level backtesting with multiple positions

**Topics covered:**
- Portfolio construction with ranking strategies
- Multi-position management
- Performance metrics calculation
- Benchmark comparison

**Best for:**
- Multi-position strategy testing
- Capital allocation analysis
- Portfolio-level performance evaluation
- Ranking strategy comparison

**How to run:**
```bash
uv run jupyter notebook examples/portfolio_backtesting.ipynb
```

#### symbol_group.ipynb
**Purpose**: Managing custom symbol groups (watchlists)

**Topics covered:**
- Creating custom symbol groups
- Filtering symbols by criteria
- Group-based backtesting
- Universe management

**Best for:**
- Custom universe creation (e.g., NASDAQ-100, sector-specific)
- Symbol filtering and selection
- Focused strategy testing
- Watchlist management

**How to run:**
```bash
uv run jupyter notebook examples/symbol_group.ipynb
```

#### pandas.ipynb
**Purpose**: Data analysis and exploration

**Topics covered:**
- OHLCV data manipulation
- Technical indicators calculation
- Data quality checks
- Exploratory analysis

**Best for:**
- Understanding data structure
- Data quality validation
- Custom indicator development
- Exploratory data analysis

**How to run:**
```bash
uv run jupyter notebook examples/pandas.ipynb
```

### Python Examples

#### portfolio_backtest_example.py
**Purpose**: Template for programmatic portfolio backtesting

**Shows:**
- PortfolioService usage
- Parameter configuration
- Results processing
- Metrics extraction

**How to run:**
```bash
uv run python examples/portfolio_backtest_example.py
```

**Use cases:**
- Automated backtest pipelines
- Custom backtest workflows
- Integration with other tools
- Batch processing

#### portfolio_backtest_api_demo.py
**Purpose**: API-style portfolio backtesting demonstration

**Shows:**
- Service-based approach
- Custom portfolio parameters
- Metrics extraction
- Programmatic tearsheet generation

**How to run:**
```bash
uv run python examples/portfolio_backtest_api_demo.py
```

**Use cases:**
- API integration examples
- Automated reporting
- Service layer usage patterns

#### live_trading_example.py
**Purpose**: Complete live trading setup example

**Shows:**
- LiveTradingManager initialization
- Risk parameters configuration
- Signal processing workflow
- Position monitoring

**⚠️ WARNING**: Review and modify before using with real money. Always start with paper trading.

**How to run:**
```bash
# With paper trading (SAFE)
uv run python examples/live_trading_example.py
```

**Use cases:**
- Live trading setup reference
- Paper trading testing
- Understanding live trading workflow
- Risk management configuration

#### google_sheets_test.py
**Purpose**: Google Sheets integration test

**Shows:**
- Authentication setup (OAuth2 and Service Account)
- Signal export workflow
- Error handling
- API integration patterns

**How to run:**
```bash
# Ensure credentials are configured first
uv run python examples/google_sheets_test.py
```

**Prerequisites:**
- Google Sheets API enabled
- Credentials file (credentials.json or service-account.json)
- Spreadsheet ID configured

**Use cases:**
- Testing Google Sheets integration
- Authentication troubleshooting
- Signal export validation

### Running All Examples

**Start Jupyter:**
```bash
# Jupyter Notebook
uv run jupyter notebook examples/

# Or JupyterLab (recommended)
uv run jupyter lab examples/
```

**Run Python examples:**
```bash
# Portfolio backtest
uv run python examples/portfolio_backtest_example.py

# API demo
uv run python examples/portfolio_backtest_api_demo.py

# Live trading example (paper trading only!)
uv run python examples/live_trading_example.py

# Google Sheets test
uv run python examples/google_sheets_test.py
```

## Development Workflows

### Adding a New Trading Strategy

**Step-by-step guide:**

1. **Create strategy file**: `turtle/signal/my_strategy.py`

2. **Extend TradingStrategy base class:**
```python
from turtle.signal.base import TradingStrategy
from turtle.signal.models import Signal
import pandas as pd

class MyStrategy(TradingStrategy):
    def __init__(self, param1=10, param2=20):
        self.param1 = param1
        self.param2 = param2

    def generate_signals(
        self,
        ticker: str,
        bars_data: pd.DataFrame,
        **kwargs
    ) -> list[Signal]:
        """
        Generate trading signals for ticker.

        Args:
            ticker: Stock ticker symbol
            bars_data: OHLCV data with columns: date, open, high, low, close, volume

        Returns:
            List of Signal objects with entry dates and prices
        """
        signals = []

        # Your strategy logic here
        # Example: Simple moving average crossover
        bars_data['sma_short'] = bars_data['close'].rolling(self.param1).mean()
        bars_data['sma_long'] = bars_data['close'].rolling(self.param2).mean()

        # Generate signals when short SMA crosses above long SMA
        for i in range(1, len(bars_data)):
            if (bars_data['sma_short'].iloc[i] > bars_data['sma_long'].iloc[i] and
                bars_data['sma_short'].iloc[i-1] <= bars_data['sma_long'].iloc[i-1]):

                signal = Signal(
                    ticker=ticker,
                    date=bars_data['date'].iloc[i],
                    entry_price=bars_data['close'].iloc[i],
                    signal_type='BUY',
                    strategy_name='my_strategy'
                )
                signals.append(signal)

        return signals
```

3. **Add tests**: `tests/test_my_strategy.py`
```python
import pytest
from turtle.signal.my_strategy import MyStrategy
import pandas as pd

def test_my_strategy_generates_signals():
    strategy = MyStrategy(param1=10, param2=20)

    # Create test data
    bars_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100),
        'close': range(100, 200),  # Trending data
        # ... other OHLC columns
    })

    signals = strategy.generate_signals('TEST', bars_data)

    assert len(signals) > 0
    assert all(s.ticker == 'TEST' for s in signals)
```

4. **Register in SignalService**: Add to strategy mapping in `turtle/service/signal_service.py`

5. **Test with signal_runner.py**:
```bash
uv run python scripts/signal_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --strategy my_strategy --mode analyze
```

### Running Portfolio Backtests

**Complete workflow:**

**Step 1: Ensure data is up to date**
```bash
uv run python scripts/daily_eod_update.py --start-date 2024-01-01 --end-date 2024-12-31
```

**Step 2: Run portfolio backtest**
```bash
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --trading-strategy darvas_box \
  --exit-strategy profit_loss \
  --output-file results.html
```

**Step 3: Review results**
```bash
# Open HTML tearsheet in browser
open reports/results.html
# Or on Linux:
xdg-open reports/results.html
```

**Advanced workflow:**

1. **Test signal generation:**
```bash
uv run python scripts/signal_runner.py \
  --start-date 2024-01-01 --end-date 2024-01-31 \
  --strategy darvas_box --mode analyze
```

2. **Validate data quality:** Review signal statistics and counts

3. **Run backtest with ranking:**
```bash
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --ranking-strategy momentum \
  --min-signal-ranking 70
```

4. **Compare exit strategies:** Test multiple exit strategies
```bash
# Test with profit/loss exit
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --exit-strategy profit_loss \
  --output-file profit_loss.html

# Test with EMA exit
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --exit-strategy ema \
  --output-file ema.html
```

5. **Analyze metrics:** Review Sharpe ratio, max drawdown, win rate

6. **Iterate parameters:** Adjust min-signal-ranking, position sizes, etc.

### Setting Up Live Trading

**Safety-first workflow:**

**1. Verify Paper Trading Configuration**
```toml
# In config/settings.toml
[app.alpaca]
paper_trading = true  # MUST be true for testing
base_url = "https://paper-api.alpaca.markets"
```

**2. Configure Risk Parameters**
```bash
uv run python scripts/setup_live_trading.py \
  --strategy darvas_box \
  --max-position-size 5000 \
  --max-daily-loss 200 \
  --max-portfolio-exposure 0.8 \
  --paper-trading
```

**3. Monitor First Session**
- Watch logs: `tail -f logs/live_trading.log`
- Check positions: Via Alpaca web interface
- Verify orders: Confirm all orders are paper trading

**4. Run For Testing Period**
- Minimum 2 weeks paper trading
- Monitor daily performance
- Verify risk controls work
- Review all executed trades

**5. Live Trading Transition (Only After Success)**
- Change `paper_trading=false` in settings
- Start with minimal capital
- Set conservative risk limits
- Monitor continuously

**Emergency Procedures:**
- **Stop trading**: Ctrl+C in terminal running live trading
- **Cancel all orders**: Via Alpaca interface or API
- **Close all positions**: Manual intervention via broker
- **Review logs**: Check what happened before taking further action

## Troubleshooting

### Database Connection Issues

**Problem**: `psycopg.OperationalError: connection failed`

**Solutions:**
1. Verify PostgreSQL is running:
```bash
docker-compose ps
# Should show postgres container running
```

2. Check credentials in `config/settings.toml` or `.env`:
```bash
# Verify .env file exists and has correct values
cat .env | grep DB_
```

3. Verify database exists:
```bash
psql -U postgres -l
# Should list 'trading' database
```

4. Check firewall/port 5432 access:
```bash
telnet localhost 5432
# Or:
nc -zv localhost 5432
```

5. Test connection:
```python
from turtle.config.settings import Settings
settings = Settings.from_toml()
with settings.pool.connection() as conn:
    print("Connection successful!")
```

### Data Download Failures

**Problem**: API rate limiting or timeout errors

**Solutions:**
1. **EODHD API issues:**
   - Check API key in `.env` file (EODHD_API_KEY)
   - Verify API key is active at eodhd.com
   - Check rate limits (typically 20 requests/second)

2. **Add delays between requests:**
```bash
# Use ticker limit for testing
uv run python scripts/download_eodhd_data.py --ticker-limit 10
```

3. **Verify date ranges:**
```bash
# Ensure dates are valid and in YYYY-MM-DD format
uv run python scripts/download_eodhd_data.py \
  --start-date 2024-01-01 --end-date 2024-12-31
```

4. **Check API status:**
   - Visit EODHD status page
   - Check Alpaca status page for trading API
   - Review Yahoo Finance availability

5. **Network issues:**
```bash
# Test connectivity
curl -I https://eodhd.com/api
```

### Signal Generation Errors

**Problem**: No signals generated or unexpected results

**Solutions:**
1. **Verify data exists:**
```sql
-- Check bars_history table for date range
SELECT COUNT(*), MIN(date), MAX(date)
FROM turtle.bars_history
WHERE ticker = 'AAPL';
```

2. **Validate strategy parameters:**
```python
# Test strategy with known data
from turtle.signal import DarvasBoxStrategy
strategy = DarvasBoxStrategy()
# Verify parameters are reasonable
```

3. **Check ticker filters:**
   - Ensure tickers have sufficient history
   - Verify tickers are in database
   - Check for data quality issues

4. **Enable verbose logging:**
```bash
uv run python scripts/signal_runner.py \
  --start-date 2024-06-01 --end-date 2024-06-01 \
  --strategy darvas_box --verbose
```

5. **Test with known good ticker:**
```bash
uv run python scripts/signal_runner.py \
  --start-date 2024-06-01 --end-date 2024-06-01 \
  --tickers AAPL --strategy darvas_box --verbose
```

### Portfolio Backtest Errors

**Problem**: Position sizing or capital allocation issues

**Solutions:**
1. **Review capital constraints:**
```bash
# Check if position sizes are too large for capital
# initial_capital should be >= position_max_amount * max_positions
```

2. **Verify ranking threshold:**
```bash
# Lower min-signal-ranking if no signals selected
uv run python scripts/portfolio_runner.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --min-signal-ranking 50  # Lower threshold
```

3. **Check signal count:**
```bash
# Ensure signals exist for date range
uv run python scripts/signal_runner.py \
  --start-date 2024-01-01 --end-date 2024-01-31 \
  --strategy darvas_box --mode analyze
```

4. **Validate benchmark data:**
```sql
-- Ensure SPY/QQQ data available
SELECT COUNT(*) FROM turtle.bars_history
WHERE ticker IN ('SPY', 'QQQ')
AND date BETWEEN '2024-01-01' AND '2024-12-31';
```

5. **Adjust position parameters:**
```bash
# Use smaller position sizes for testing
uv run python scripts/portfolio_runner.py \
  --initial-capital 30000 \
  --position-min-amount 1000 \
  --position-max-amount 2000
```

### Live Trading Issues

**Problem**: Orders not executing or positions not tracking

**Solutions:**
1. **Verify market hours:**
   - Alpaca API only works during market hours for live trading
   - Paper trading works 24/7
   - Check current market status

2. **Check paper trading flag:**
```python
# Verify settings
from turtle.config.settings import Settings
settings = Settings.from_toml()
print(f"Paper trading: {settings.app.alpaca.paper_trading}")
# Should be True for testing
```

3. **Review risk checks:**
```bash
# Check logs for risk manager blocks
tail -f logs/risk_manager.log
# Look for rejection reasons
```

4. **Verify API credentials:**
   - Test connection with Alpaca dashboard
   - Verify API keys are correct
   - Check if keys are for paper or live trading

5. **Check logs:**
```bash
# Review live trading logs
tail -f logs/live_trading.log

# Check for errors
grep ERROR logs/live_trading.log
```

6. **Test with minimal setup:**
```python
# Minimal test
from alpaca.trading.client import TradingClient

client = TradingClient(api_key, secret_key, paper=True)
account = client.get_account()
print(f"Account: {account}")
```

### Google Sheets Export Failures

**Problem**: Authentication or permission errors

**Solutions:**
1. **OAuth2 authentication issues:**
```bash
# Delete token and re-authenticate
rm token.json
# Run authentication flow again
python -c "from turtle.google.auth import get_oauth_credentials; get_oauth_credentials()"
```

2. **Service Account issues:**
```bash
# Verify JSON key path in env vars
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should point to valid JSON file

# Check file exists and is readable
cat $GOOGLE_APPLICATION_CREDENTIALS
```

3. **Permission denied:**
   - Service Account: Share spreadsheet with service account email
   - OAuth2: Ensure user has edit access to spreadsheet
   - Check spreadsheet ID is correct

4. **API not enabled:**
   - Go to Google Cloud Console
   - Verify Google Sheets API is enabled
   - Check API quotas and limits

5. **Scope issues:**
```python
# Verify scopes include spreadsheets
# Should include: https://www.googleapis.com/auth/spreadsheets
```

### Performance Issues

**Problem**: Slow queries or high memory usage

**Solutions:**
1. **Database optimization:**
```sql
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_bars_ticker_date
ON turtle.bars_history(ticker, date);

-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM turtle.bars_history
WHERE ticker = 'AAPL' AND date BETWEEN '2024-01-01' AND '2024-12-31';
```

2. **Large datasets:**
```bash
# Use ticker limit for testing
uv run python scripts/portfolio_runner.py \
  --ticker-limit 100 \
  --start-date 2024-01-01 --end-date 2024-12-31
```

3. **Memory management:**
   - Process data in batches
   - Avoid loading all history at once
   - Use generators for large datasets

4. **Connection pool:**
```toml
# Adjust pool size in settings.toml
[database]
pool_size = 10  # Increase if needed
pool_timeout = 30
```

5. **Query optimization:**
   - Use appropriate indexes
   - Filter data at database level
   - Avoid SELECT * queries

### Migration Failures

**Problem**: Alembic migration errors

**Solutions:**
1. **Check current version:**
```bash
uv run alembic current
# Shows current migration revision
```

2. **Review migration history:**
```bash
uv run alembic history
# Shows all migrations and their status
```

3. **Rollback if needed:**
```bash
# Rollback one migration
uv run alembic downgrade -1

# Or rollback to specific revision
uv run alembic downgrade <revision>
```

4. **Manual fix:**
   - Edit migration file if needed
   - Test upgrade: `uv run alembic upgrade head`
   - Test downgrade: `uv run alembic downgrade -1`

5. **Database state mismatch:**
```sql
-- Check alembic version table
SELECT * FROM turtle.alembic_version;

-- Manually set version if needed (use with caution)
UPDATE turtle.alembic_version SET version_num = '<revision>';
```

6. **Fresh migration:**
```bash
# Create new migration
uv run alembic revision -m "fix_issue"
# Implement changes in new migration
```

## Linting
Use mypy and ruff tools configured in pyproject.toml 