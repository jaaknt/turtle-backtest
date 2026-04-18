# Services

This document describes the core service classes that provide the business logic layer for the turtle backtest library. These services orchestrate data management, signal generation, backtesting, and portfolio management operations.

## EodhdService

The `EodhdService` is responsible for data ingestion from the EODHD API. It downloads and stores exchange reference data, US ticker lists, historical OHLCV prices, and company fundamentals into PostgreSQL. All operations are async and use concurrent batch requests.

**Key Features:**
- Downloads exchange reference data from EODHD
- Downloads US ticker list for NYSE and NASDAQ
- Fetches historical OHLCV data with configurable date ranges
- Downloads company fundamental data
- Configurable batch sizes and rate-limit delays

**Primary Methods:**
- `download_exchanges()` — Fetches and upserts exchange reference data
- `download_us_tickers()` — Downloads US ticker list into `turtle.ticker`
- `download_historical_data(ticker_limit, start_date, end_date)` — Downloads OHLCV history into `turtle.daily_bars`
- `download_company_data(ticker_limit)` — Downloads company fundamentals into `turtle.company`

**Usage:**
```python
import asyncio
service = EodhdService(settings)
asyncio.run(service.download_exchanges())
asyncio.run(service.download_us_tickers())
asyncio.run(service.download_historical_data(start_date="2024-01-01", end_date="2024-12-31"))
```

## SignalService

The `SignalService` provides a clean interface for executing trading strategies against historical market data. It acts as a wrapper around trading strategy implementations.

**Key Features:**
- Executes any TradingStrategy implementation on US stock symbols
- Integrates with data repositories for market data access
- Supports configurable time frame units and warmup periods

**Constructor Parameters:**
- `engine` - SQLAlchemy `Engine` instance
- `trading_strategy` - TradingStrategy instance to execute
- `market_ticker` - Market index ticker for regime filter (e.g. `"SPY"`)
- `time_frame_unit` - Time frame for analysis (default: DAY)
- `warmup_period` - Historical data warmup period in days (default: 730)

**Primary Methods:**
- `get_signals(ticker, start_date, end_date)` - Gets list of Signal objects for ticker over date range

**Usage:**
```python
from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
from turtle.repository.analytics import OhlcvAnalyticsRepository

bars_history = OhlcvAnalyticsRepository(engine)
strategy = DarvasBoxStrategy(bars_history, time_frame_unit=TimeFrameUnit.DAY)
signal_service = SignalService(engine, strategy, market_ticker="SPY")

# Get signals for specific ticker
signals = signal_service.get_signals("AAPL", start_date, end_date)
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
- `symbol_repo` - TickerQueryRepository instance for fetching the symbol universe

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
from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
from turtle.strategy.exit.atr import ATRExitStrategy
from turtle.repository.analytics import OhlcvAnalyticsRepository

bars_history = OhlcvAnalyticsRepository(engine)
strategy = DarvasBoxStrategy(bars_history)
signal_service = SignalService(engine, strategy, market_ticker="SPY")
exit_strategy = ATRExitStrategy(bars_history, atr_multiplier=2.0)
signal_processor = SignalProcessor(30, bars_history, exit_strategy, ["QQQ", "SPY"])
symbol_repo = TickerQueryRepository(engine)

# Run backtest
backtest_service = BacktestService(signal_service, signal_processor, symbol_repo)
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
from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
from turtle.strategy.exit.atr import ATRExitStrategy

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

### EodhdService
**Use when:** You need to download and manage market data
- Initial database setup with exchange, ticker, and company data
- Bulk or incremental OHLCV historical data downloads
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

1. **Data Setup**: Use `EodhdService` (via `scripts/download_eodhd_data.py`) to populate your database with market data
2. **Strategy Development**: Use `SignalService` to test and refine signal generation logic
3. **Strategy Validation**: Use `BacktestService` to test complete strategies with exit logic
4. **Portfolio Testing**: Use `PortfolioService` for realistic portfolio-level backtesting

## Strategy Instantiation

When instantiating strategies from CLI string names (e.g. `--trading-strategy darvas_box`), use the factory functions in `turtle/strategy/factory.py` — they own the canonical name → class mapping:

```python
from turtle.strategy.factory import get_trading_strategy, get_exit_strategy, get_ranking_strategy

ranking_strategy = get_ranking_strategy("momentum")
exit_strategy = get_exit_strategy("atr", bars_history)
trading_strategy = get_trading_strategy("darvas_box", ranking_strategy, bars_history)
```

For programmatic use where the concrete class is already known, instantiate the strategy directly.

## Integration Examples

**Simple Signal Analysis:**
```python
# Test signals for specific stocks
signal_service = SignalService(engine, darvas_strategy, market_ticker="SPY")
signals = signal_service.get_signals("AAPL", start_date, end_date)
```

**Complete Strategy Backtesting:**
```python
# Test strategy with exits and benchmarks
backtest_service = BacktestService(signal_service, signal_processor, symbol_repo)
results = backtest_service.run(start_date, end_date, symbol_list)
```

**Portfolio-Level Analysis:**
```python
# Realistic portfolio simulation with capital management
portfolio_service = PortfolioService(strategy, exit_strategy, bars_history, ...)
portfolio_service.run_backtest(start_date, end_date, universe, "tearsheet.html")
```