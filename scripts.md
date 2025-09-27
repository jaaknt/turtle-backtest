# Scripts

This document describes the command-line scripts that provide convenient interfaces for common operations using the turtle backtest services.

## daily_eod_update.py

The `daily_eod_update.py` script provides a command-line interface for updating the database with stock market data. It supports multiple update modes for different types of data operations.

**Key Features:**
- Multiple update modes: bars (OHLCV data), symbols (symbol lists), companies (company data)
- Supports single date or date range updates for OHLCV data
- Built-in validation to ensure successful data retrieval
- Dry-run mode for testing without making changes
- Comprehensive logging with optional verbose output
- Trading day calculations (excludes weekends)
- Smart date validation based on mode requirements

**Update Modes:**
- `bars` (default) - Update OHLCV historical data for all symbols (requires dates)
- `symbols` - Download USA stocks symbol list from EODHD
- `companies` - Download company fundamental data from Yahoo Finance

**Usage:**
```bash
# Update OHLCV data for specific date (default mode)
uv run python scripts/daily_eod_update.py --start-date 2024-12-01

# Update OHLCV data for date range
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --end-date 2024-12-07

# Download symbol list from EODHD
uv run python scripts/daily_eod_update.py --mode symbols

# Download company data from Yahoo Finance
uv run python scripts/daily_eod_update.py --mode companies

# Dry run to preview updates without making changes
uv run python scripts/daily_eod_update.py --mode symbols --dry-run

# Enable detailed logging
uv run python scripts/daily_eod_update.py --start-date 2024-12-01 --verbose
```

**Options:**
- `--mode` - Update mode: bars, symbols, or companies (default: bars)
- `--start-date` - Start date in YYYY-MM-DD format (required for bars mode)
- `--end-date` - End date in YYYY-MM-DD format, defaults to start-date
- `--dry-run` - Show what would be updated without making changes
- `--verbose` - Enable detailed logging output

**Mode-Specific Behavior:**
- **bars mode**: Requires --start-date parameter, updates OHLCV historical data
- **symbols mode**: No date parameters needed, downloads symbol list from EODHD
- **companies mode**: No date parameters needed, downloads company data from Yahoo Finance

**Data Validation:**
- Mode-specific validation for each update type
- Verifies data was successfully retrieved for sample symbols
- Checks at least 80% success rate for validation to pass
- Provides detailed feedback on update success/failure

## strategy_performance.py

The `strategy_performance.py` script performs comprehensive strategy backtesting by analyzing historical signals and calculating performance metrics over specified holding periods.

**Key Features:**
- Comprehensive performance analysis with multiple metrics
- Benchmark comparison against market indices (QQQ, SPY)
- Multiple holding period analysis
- Flexible output formats (console, CSV, JSON)
- Support for custom symbol lists and limits
- Dry-run mode for testing configuration

**Usage:**
```bash
# Test Darvas Box strategy for January 2024
uv run python scripts/strategy_performance.py --strategy darvas_box --start-date 2024-01-01 --end-date 2024-01-31

# Test with custom holding period and limited symbols
uv run python scripts/strategy_performance.py --strategy mars --start-date 2024-01-01 --end-date 2024-03-31 --max-holding-period 2W --max-symbols 50

# Save results to CSV file
uv run python scripts/strategy_performance.py --strategy momentum --start-date 2024-01-01 --end-date 2024-02-29 --output csv --save results.csv

# Test specific symbols only
uv run python scripts/strategy_performance.py --strategy darvas_box --start-date 2024-01-01 --end-date 2024-01-31 --symbols "AAPL,MSFT,NVDA"
```

**Required Options:**
- `--strategy` - Strategy to test (darvas_box, mars, momentum)
- `--start-date` - Start date for signal generation (YYYY-MM-DD)
- `--end-date` - End date for signal generation (YYYY-MM-DD)

**Optional Parameters:**
- `--max-holding-period` - Maximum holding period (default: 1M, format: 3d, 1W, 2W, 1M)
- `--symbols` - Comma-separated list of specific symbols to test
- `--max-symbols` - Maximum number of symbols to test
- `--time-frame` - Time frame for analysis (DAY, WEEK, default: DAY)
- `--output` - Output format (console, csv, json, default: console)
- `--save` - Save results to specified filename
- `--verbose` - Enable detailed logging
- `--dry-run` - Show configuration without running test

**Performance Metrics:**
- Total and valid signal counts
- Average, best, and worst returns
- Win rates and success percentages
- Benchmark performance comparisons
- Period-based analysis results

## backtest.py

The `backtest.py` script provides comprehensive backtesting capabilities by combining signal generation with exit strategy analysis. It runs complete signal-to-exit backtests using configurable trading and exit strategies.

**Key Features:**
- Complete signal-to-exit backtesting workflow
- Multiple trading strategies (Darvas Box, Mars, Momentum)
- Multiple exit strategies (Buy and Hold, Profit/Loss, EMA, MACD, ATR)
- Configurable ranking strategies
- Flexible ticker selection and limiting
- Multiple analysis modes (list, signal, top)
- Comprehensive signal processing with benchmark comparisons

**Usage:**
```bash
# Basic backtest with Darvas Box strategy and EMA exit
uv run python scripts/backtest.py --start-date 2024-01-01 --end-date 2024-01-31 --trading-strategy darvas_box --exit-strategy ema

# Test specific tickers with ATR exit strategy
uv run python scripts/backtest.py --start-date 2024-01-01 --end-date 2024-01-31 --tickers AAPL MSFT NVDA --exit-strategy atr --verbose

# Mars strategy with profit/loss exits and limited ticker count
uv run python scripts/backtest.py --start-date 2024-02-01 --end-date 2024-02-29 --trading-strategy mars --exit-strategy profit_loss --max-tickers 50

# Top 20 signals mode with MACD exits
uv run python scripts/backtest.py --start-date 2024-01-15 --end-date 2024-01-15 --mode top --exit-strategy macd
```

**Required Options:**
- `--start-date` - Start date for analysis (YYYY-MM-DD format)
- `--end-date` - End date for analysis (YYYY-MM-DD format)

**Optional Parameters:**
- `--tickers` - Space-separated list of specific ticker symbols to test
- `--trading-strategy` - Signal generation strategy (default: darvas_box)
  - `darvas_box` - Darvas Box trend-following strategy
  - `mars` - Mars momentum strategy (@marsrides)
  - `momentum` - Traditional momentum strategy
- `--exit-strategy` - Exit timing strategy (default: buy_and_hold)
  - `buy_and_hold` - Hold until period end
  - `profit_loss` - Exit on profit target or stop loss
  - `ema` - Exit when price closes below EMA
  - `macd` - Exit on MACD bearish signals
  - `atr` - Volatility-based stop losses using ATR
- `--ranking-strategy` - Signal ranking method (default: momentum)
  - `momentum` - Momentum-based ranking
- `--max-tickers` - Maximum number of tickers to test (default: 10000)
- `--mode` - Analysis mode (default: list)
  - `list` - Get all tickers with signals in date range
  - `signal` - Check specific ticker signals
  - `top` - Get top 20 signals for the period
- `--verbose` - Enable detailed logging output

**Exit Strategy Details:**
- **Buy and Hold**: Simple hold until analysis period end
- **Profit/Loss**: Configurable profit targets and stop losses with early exit
- **EMA**: Technical analysis exit when price closes below exponential moving average
- **MACD**: Exit based on MACD indicator bearish crossovers
- **ATR**: Volatility-adjusted stop losses using Average True Range multipliers

**Output:**
- Signal processing results with entry/exit analysis
- Return calculations for individual positions
- Benchmark comparisons against QQQ and SPY indices
- Detailed logging of signal analysis workflow

## portfolio_runner.py

The `portfolio_runner.py` script provides sophisticated portfolio-level backtesting using the PortfolioService class. It simulates realistic trading with capital constraints, position sizing, and daily portfolio management across multiple strategies and time periods.

**Key Features:**
- **Realistic Portfolio Simulation**: Daily trading simulation with capital constraints and position overlap management
- **Multi-Strategy Support**: Configurable trading, exit, and ranking strategies
- **Risk Management**: Position sizing controls with minimum/maximum amounts
- **Performance Analytics**: Comprehensive tearsheet generation with HTML reports
- **Flexible Universe**: Support for specific tickers or full symbol database
- **Benchmark Analysis**: Automatic comparison against SPY, QQQ, or custom benchmarks
- **Signal Quality Control**: Ranking threshold filtering for high-quality entries only

**Strategy Options:**

**Trading Strategies:**
- `darvas_box` (default) - Darvas Box trend-following strategy
- `mars` - Mars momentum strategy (@marsrides)
- `momentum` - Traditional momentum strategy

**Exit Strategies:**
- `buy_and_hold` (default) - Hold until portfolio period end
- `profit_loss` - Exit on profit targets or stop losses
- `ema` - Exit when price closes below exponential moving average
- `macd` - Exit on MACD bearish signals
- `atr` - Volatility-based stop losses using Average True Range

**Ranking Strategies:**
- `momentum` (default) - Momentum-based signal ranking
- `volume_momentum` - Volume-weighted momentum ranking

**Usage:**
```bash
# Basic portfolio backtest with default settings
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31

# Advanced backtest with custom parameters
uv run python scripts/portfolio_runner.py \
    --start-date 2024-01-01 --end-date 2024-12-31 \
    --trading-strategy mars --exit-strategy profit_loss \
    --initial-capital 50000 --min-signal-ranking 80 \
    --output-file mars_strategy_results.html --verbose

# Test specific ticker universe
uv run python scripts/portfolio_runner.py \
    --start-date 2024-01-01 --end-date 2024-06-30 \
    --tickers AAPL MSFT GOOGL AMZN NVDA \
    --trading-strategy darvas_box --exit-strategy atr \
    --position-max-amount 5000 --verbose

# High-ranking signals only with custom benchmarks
uv run python scripts/portfolio_runner.py \
    --start-date 2024-01-01 --end-date 2024-12-31 \
    --min-signal-ranking 85 --max-tickers 500 \
    --benchmark-tickers SPY QQQ IWM \
    --output-file high_quality_signals.html
```

**Required Options:**
- `--start-date` - Start date for backtest (YYYY-MM-DD format)
- `--end-date` - End date for backtest (YYYY-MM-DD format)

**Strategy Configuration:**
- `--trading-strategy` - Trading strategy: darvas_box, mars, momentum (default: darvas_box)
- `--exit-strategy` - Exit strategy: buy_and_hold, profit_loss, ema, macd, atr (default: buy_and_hold)
- `--ranking-strategy` - Ranking strategy: momentum, volume_momentum (default: momentum)

**Portfolio Parameters:**
- `--initial-capital` - Starting capital amount (default: 30000.0)
- `--position-min-amount` - Minimum position size in dollars (default: 1500.0)
- `--position-max-amount` - Maximum position size in dollars (default: 3000.0)
- `--min-signal-ranking` - Minimum signal ranking threshold 1-100 (default: 70)

**Universe Selection:**
- `--max-tickers` - Maximum number of tickers from database (default: 10000)
- `--tickers` - Specific ticker symbols to test (space-separated list)
- `--benchmark-tickers` - Custom benchmark symbols (default: SPY QQQ)

**Output and Analysis:**
- `--output-file` - HTML tearsheet filename (saved in reports/ folder)
- `--verbose` - Enable detailed logging output

**Portfolio Management Process:**
1. **Daily Snapshots**: Records portfolio state each trading day
2. **Exit Processing**: Closes positions that reach scheduled exit dates
3. **Signal Generation**: Scans universe for new trading opportunities
4. **Quality Filtering**: Applies ranking threshold and avoids duplicate positions
5. **Position Sizing**: Calculates optimal position sizes within constraints
6. **Entry Execution**: Opens new positions with available capital
7. **Price Updates**: Marks existing positions to market daily

**Performance Analytics:**
- **Daily Portfolio Values**: Cash, positions, and total portfolio value tracking
- **Trade Analysis**: Individual trade performance with entry/exit details
- **Risk Metrics**: Drawdown analysis and risk-adjusted returns
- **Benchmark Comparison**: Performance vs. market indices
- **HTML Tearsheets**: Professional-quality performance reports with charts
- **Position Management**: Analysis of position sizing and capital utilization

**Advantages over Simple Backtesting:**
- **Capital Realism**: Cannot allocate more money than available
- **Position Overlap Control**: Prevents duplicate positions in same stock
- **Signal Quality Filter**: Only trades high-ranking signals above threshold
- **Risk Management**: Built-in position sizing and concentration limits
- **Performance Tracking**: Complete portfolio analytics and reporting
- **Market Simulation**: Realistic trading constraints and cash flow management

**Example Workflows:**

**Strategy Comparison:**
```bash
# Test different trading strategies with same exit logic
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --trading-strategy darvas_box --output-file darvas_results.html
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --trading-strategy mars --output-file mars_results.html
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --trading-strategy momentum --output-file momentum_results.html
```

**Exit Strategy Analysis:**
```bash
# Compare exit strategies with same trading approach
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --exit-strategy buy_and_hold --output-file bah_exits.html
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --exit-strategy atr --output-file atr_exits.html
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --exit-strategy ema --output-file ema_exits.html
```

**Risk Management Testing:**
```bash
# Test different position sizing and signal quality thresholds
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --min-signal-ranking 60 --position-max-amount 2000 --output-file conservative.html
uv run python scripts/portfolio_runner.py --start-date 2024-01-01 --end-date 2024-12-31 --min-signal-ranking 90 --position-max-amount 5000 --output-file aggressive.html
```