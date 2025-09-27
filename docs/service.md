# Services

This document describes the core service classes that provide the business logic layer for the turtle backtest library. These services orchestrate data management, signal generation, backtesting, and portfolio management operations.

## DataUpdateService

The `DataUpdateService` is responsible for data ingestion and management operations. It handles downloading and storing market data from multiple external APIs into the PostgreSQL database.

**Key Features:**
- Downloads symbol lists from EODHD API for US markets
- Retrieves company fundamental data from Yahoo Finance
- Fetches historical OHLCV (Open, High, Low, Close, Volume) data from Alpaca API
- Manages database connections using connection pooling
- Supports configurable time frame units (DAY, WEEK, MONTH)

**Primary Methods:**
- `update_symbol_list()` - Downloads and stores US stock symbols
- `update_company_list()` - Retrieves company information for all symbols
- `update_bars_history(start_date, end_date)` - Downloads historical price data for date range
- `get_company_list(symbol_list)` - Returns company data as DataFrame
- `get_symbol_group_list(symbol_group)` - Retrieves custom symbol groupings

**Usage:**
```python
data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
data_updater.update_symbol_list()
data_updater.update_company_list()
data_updater.update_bars_history(start_date, end_date)
```

## SignalService

The `SignalService` provides a clean interface for executing trading strategies against historical market data. It acts as a wrapper around trading strategy implementations and provides symbol management capabilities.

**Key Features:**
- Executes any TradingStrategy implementation on US stock symbols
- Provides symbol list filtering and management
- Integrates with data repositories for market data access
- Supports configurable time frame units and warmup periods
- Retrieves company information for analysis

**Constructor Parameters:**
- `pool` - Database connection pool
- `app_config` - Application configuration with API keys
- `trading_strategy` - TradingStrategy instance to execute
- `time_frame_unit` - Time frame for analysis (default: DAY)
- `warmup_period` - Historical data warmup period in days (default: 730)

**Primary Methods:**
- `get_signals(ticker, start_date, end_date)` - Gets list of Signal objects for ticker over date range
- `get_symbol_list(symbol_filter, max_symbols)` - Returns filtered list of stock symbols
- `get_company_list(symbol_names)` - Retrieves company data as DataFrame for provided symbols

**Usage:**
```python
from turtle.signal.darvas_box import DarvasBoxStrategy

# Initialize with specific strategy
strategy = DarvasBoxStrategy(bars_history, time_frame_unit=TimeFrameUnit.DAY)
signal_service = SignalService(pool, app_config, strategy)

# Get signals for specific ticker
signals = signal_service.get_signals("AAPL", start_date, end_date)

# Get symbol universe for analysis
symbols = signal_service.get_symbol_list("USA", max_symbols=1000)
```

## BacktestService

The `BacktestService` orchestrates complete signal-to-exit backtesting by combining signal generation with exit strategy processing. It runs comprehensive backtests across multiple symbols and provides detailed performance analysis.

**Key Features:**
- Complete signal-to-exit backtesting workflow
- Processes signals from any TradingStrategy through any ExitStrategy
- Comprehensive performance metrics and analysis
- Benchmark comparison with market indices (QQQ, SPY)
- Ranking-based performance analysis in 20-percentile buckets
- Top performer identification and reporting
- Handles large symbol universes efficiently

**Constructor Parameters:**
- `signal_service` - SignalService instance for signal generation
- `signal_processor` - SignalProcessor instance for converting signals to trade results

**Primary Methods:**
- `run(start_date, end_date, tickers)` - Execute backtest and return FutureTrade results

**Performance Analysis:**
- Average returns vs. benchmark performance (QQQ, SPY)
- Win rates and trade statistics
- Ranking bucket analysis (1-20, 21-40, 41-60, 61-80, 81-100 percentiles)
- Top 5 performing trades with detailed metrics
- Average holding period calculations

**Usage:**
```python
from turtle.signal.darvas_box import DarvasBoxStrategy
from turtle.exit.atr import ATRExitStrategy

# Initialize components
strategy = DarvasBoxStrategy(bars_history)
signal_service = SignalService(pool, app_config, strategy)
exit_strategy = ATRExitStrategy(bars_history, atr_multiplier=2.0)
signal_processor = SignalProcessor(30, bars_history, exit_strategy, ["QQQ", "SPY"])

# Run backtest
backtest_service = BacktestService(signal_service, signal_processor)
results = backtest_service.run(start_date, end_date, ["AAPL", "MSFT", "NVDA"])

# Results contain FutureTrade objects with entry/exit details and performance metrics
```

## PortfolioService

The `PortfolioService` is the most sophisticated backtesting engine that simulates realistic portfolio management with daily signal generation, position sizing, risk management, and comprehensive performance tracking. It manages a portfolio of stocks with fixed capital allocation and realistic trading constraints.

**Key Features:**
- **Daily Portfolio Simulation**: Processes each trading day individually with realistic market constraints
- **Dynamic Position Management**: Opens and closes positions based on signal generation and exit strategies
- **Risk Management**: Configurable position sizing with minimum/maximum position amounts
- **Capital Management**: Tracks available cash and prevents over-allocation
- **Performance Analytics**: Comprehensive tearsheet generation with detailed metrics
- **Signal Ranking**: Only considers high-quality signals above minimum ranking threshold
- **Realistic Trading**: Accounts for position overlap, cash constraints, and holding periods

**Constructor Parameters:**
- `trading_strategy` - Strategy for generating trading signals
- `exit_strategy` - Strategy for determining when to exit positions
- `bars_history` - Data repository for historical price data
- `start_date` - Portfolio backtest start date
- `end_date` - Portfolio backtest end date
- `initial_capital` - Starting capital amount (default: $30,000)
- `position_min_amount` - Minimum dollar amount per position (default: $1,500)
- `position_max_amount` - Maximum dollar amount per position (default: $3,000)
- `min_signal_ranking` - Minimum signal ranking to consider (default: 70)
- `time_frame_unit` - Time frame for analysis (default: DAY)

**Core Components:**
- **PortfolioManager**: Handles position tracking, cash management, and daily snapshots
- **PortfolioSignalSelector**: Filters and ranks signals for entry consideration
- **PortfolioAnalytics**: Generates comprehensive performance reports and tearsheets
- **SignalProcessor**: Calculates complete trade lifecycle including exits

**Primary Methods:**
- `run_backtest(start_date, end_date, universe, output_file)` - Execute complete portfolio backtest

**Daily Trading Process:**
1. **Record Daily Snapshot**: Capture portfolio state for the trading day
2. **Process Exits**: Close positions that have reached their scheduled exit dates
3. **Generate Entry Signals**: Scan universe for new trading opportunities
4. **Filter Signals**: Apply ranking threshold and avoid duplicate positions
5. **Process Entries**: Open new positions with calculated position sizes
6. **Update Prices**: Mark-to-market existing positions with current prices

**Performance Analytics:**
- Daily portfolio value tracking with cash and position values
- Trade-by-trade analysis with entry/exit details
- Risk metrics and drawdown analysis
- Benchmark comparisons against market indices
- HTML tearsheet generation with comprehensive visualizations
- Position sizing effectiveness analysis

**Usage:**
```python
from turtle.signal.darvas_box import DarvasBoxStrategy
from turtle.exit.atr import ATRExitStrategy

# Initialize strategy components
strategy = DarvasBoxStrategy(bars_history, time_frame_unit=TimeFrameUnit.DAY)
exit_strategy = ATRExitStrategy(bars_history, atr_multiplier=2.5)

# Create portfolio service
portfolio_service = PortfolioService(
    trading_strategy=strategy,
    exit_strategy=exit_strategy,
    bars_history=bars_history,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 6, 30),
    initial_capital=50000.0,
    position_min_amount=2000.0,
    position_max_amount=4000.0,
    min_signal_ranking=75
)

# Run comprehensive backtest
symbol_universe = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]  # Or larger universe
portfolio_service.run_backtest(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 6, 30),
    universe=symbol_universe,
    output_file="portfolio_tearsheet.html"
)
```

**Advantages over Simple Backtesting:**
- **Realistic Capital Constraints**: Cannot allocate more capital than available
- **Position Overlap Management**: Prevents duplicate positions in same stock
- **Dynamic Universe**: Can handle large symbol universes with selective entry
- **Risk Management**: Built-in position sizing and concentration limits
- **Performance Tracking**: Daily portfolio valuation and comprehensive analytics
- **Signal Quality Control**: Only acts on high-ranking signals above threshold

## ~~StrategyPerformanceService~~ (Removed)

~~The `StrategyPerformanceService` orchestrated comprehensive strategy backtesting and performance analysis across multiple symbols and time periods. This service has been removed as part of codebase simplification.~~

**Previously Available Features:**
- ~~Comprehensive backtesting framework with multiple holding periods~~
- ~~Statistical performance analysis including win rates, average returns, and risk metrics~~
- ~~Benchmark comparison against market indices (QQQ, SPY)~~
- ~~Support for multiple exit strategies (EMA-based, profit/loss targets)~~
- ~~Flexible output formats (console, CSV, JSON)~~

**Note:** For strategy testing and backtesting, use the individual strategy classes directly with the `SignalService` and manual analysis tools.

## Service Selection Guide

Choose the appropriate service based on your analysis needs:

### DataUpdateService
**Use when:** You need to download and manage market data
- Initial database setup with symbol lists and company data
- Daily/periodic OHLCV data updates
- Building and maintaining your market data foundation

### SignalService
**Use when:** You need basic signal generation and analysis
- Testing strategy logic on individual symbols
- Generating signals for specific time periods
- Building custom analysis tools that need signal data

### BacktestService
**Use when:** You need comprehensive signal-to-exit analysis
- Testing complete trading strategies with exit logic
- Analyzing performance across multiple symbols
- Comparing different exit strategies
- Getting detailed trade-by-trade results with benchmark comparisons

### PortfolioService
**Use when:** You need realistic portfolio-level backtesting
- Simulating actual trading with capital constraints
- Managing multiple positions simultaneously
- Testing position sizing and risk management
- Generating professional tearsheets for strategy presentation
- Understanding real-world trading limitations and cash flow

## Typical Workflow

1. **Data Setup**: Use `DataUpdateService` to populate your database with market data
2. **Strategy Development**: Use `SignalService` to test and refine signal generation logic
3. **Strategy Validation**: Use `BacktestService` to test complete strategies with exit logic
4. **Portfolio Testing**: Use `PortfolioService` for realistic portfolio-level backtesting

## Integration Examples

**Simple Signal Analysis:**
```python
# Test signals for specific stocks
signal_service = SignalService(pool, config, darvas_strategy)
signals = signal_service.get_signals("AAPL", start_date, end_date)
```

**Complete Strategy Backtesting:**
```python
# Test strategy with exits and benchmarks
backtest_service = BacktestService(signal_service, signal_processor)
results = backtest_service.run(start_date, end_date, symbol_list)
```

**Portfolio-Level Analysis:**
```python
# Realistic portfolio simulation with capital management
portfolio_service = PortfolioService(strategy, exit_strategy, bars_history, ...)
portfolio_service.run_backtest(start_date, end_date, universe, "tearsheet.html")
```