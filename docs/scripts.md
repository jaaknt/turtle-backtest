# Scripts

This document describes the command-line scripts that provide convenient interfaces for common operations using the turtle backtest services.

All strategy name → class mappings used by `--trading-strategy`, `--exit-strategy`, and `--ranking-strategy` flags are defined in `turtlex/strategy/factory.py`. Add new strategies there to make them available across all scripts.

Trade statistics (Win%, PF, Sortino, Med%, Mean%, CVaR, mean per-trade MaxDD) come from `turtlex/backtest/metrics.py`, which owns the canonical definitions — notably Sortino's downside deviation as the RMS of `min(r, 0)` over **all N** trades, annualized as a ratio. `backtest-runner`, `portfolio-runner`, `scripts/qullamaggie-backtest-v4.py`, `scripts/qullamaggie-cohorts-adr.py` and `scripts/qullamaggie-signals-v4.py` use it. The remaining `scripts/qullamaggie-*.py` studies still carry their own copies, several of which divide by the RMS of the losers only — a different statistic, larger by `sqrt(N / n_losers)` — so their Sortino columns are not comparable with the ones above. Each result doc states the convention its own run used.

## download-eodhd-data

The `download-eodhd-data` console script downloads bulk data from the EODHD API and stores it in the database. It covers four datasets: exchanges, US ticker lists, company fundamentals, and full historical price data. Use this for initial database population or large historical backfills.

**Key Features:**

- Selective dataset download via `--data` flag
- Concurrent API requests with configurable batch sizes and rate-limit delays
- Upsert semantics — safe to re-run without duplicating data
- `--ticker-limit` flag for testing with a small subset
- Custom date range support for historical price downloads

**Datasets:**

- `exchange` — Exchange reference data (name, country, currency)
- `us_ticker` — Full US ticker list for NYSE and NASDAQ (stored in `turtle.ticker`)
- `company` — Extended fundamentals per ticker: sector, industry, market cap, P/E, volume (stored in `turtle.company`)
- `history` — Full OHLCV price history per ticker (stored in `turtle.daily_bars`)

**Usage:**

```bash
# Download exchange reference data
uv run download-eodhd-data --data exchange

# Download only US ticker list
uv run download-eodhd-data --data us_ticker

# Download company fundamentals, limited to 10 tickers (for testing)
uv run download-eodhd-data --data company --ticker-limit 10

# Download historical price data for a specific date range
uv run download-eodhd-data --data history --start-date 2024-01-01 --end-date 2024-12-31

# Test historical download with 10 tickers
uv run download-eodhd-data --data history --ticker-limit 10 --start-date 2024-06-01 --end-date 2024-06-30
```

**Options:**

- `--data` — Dataset to download: `exchange`, `us_ticker`, `company`, `history` (required)
- `--ticker-limit` — Limit processing to first N tickers (useful for testing)
- `--start-date` — Start date for historical data in `YYYY-MM-DD` format (default: `2000-01-01`)
- `--end-date` — End date for historical data in `YYYY-MM-DD` format (default: `2025-12-30`)
- `--verbose` — Enable detailed logging

**Recommended first-run order:**

```bash
# 1. Populate exchange reference data
uv run download-eodhd-data --data exchange

# 2. Download US ticker list
uv run download-eodhd-data --data us_ticker

# 3. Download company fundamentals
uv run download-eodhd-data --data company

# 4. Download full price history (long-running — thousands of tickers)
uv run download-eodhd-data --data history --start-date 2020-01-01 --end-date 2024-12-31
```

**Notes:**

- Requires `EODHD_API_KEY` environment variable
- Historical download is rate-limited (configurable batch size and delay)

## signal-runner

The `signal-runner` console script scans the strategy's ticker universe and lists all signals in a date range. Architecture and flow diagrams are in [signal_runner.md](signal_runner.md).

**Usage:**

```bash
# Scan all symbols for signals on a given day
uv run signal-runner --start-date 2024-06-01 --end-date 2024-06-01

# Limit the universe scan size
uv run signal-runner --start-date 2024-06-01 --end-date 2024-06-01 --max-tickers 500

# Use a different strategy
uv run signal-runner --start-date 2024-06-01 --end-date 2024-06-01 --trading-strategy mars
```

**Options:**

- `--start-date` / `--end-date` — Date range (required)
- `--trading-strategy` — `darvas_box`, `mars`, `momentum`, `qullamaggie` (default: `darvas_box`)
- `--ranking-strategy` — `momentum`, `volume_momentum`, `breakout_quality`, `qullamaggie` (default: `momentum`)
- `--trading-param KEY=VALUE` — Override a trading-strategy constructor parameter, e.g. `--trading-param sma_thresh=0.20` (repeatable)
- `--max-tickers` — Maximum symbols to scan (default: 10000)
- `--verbose` — Enable detailed logging

## backtest-runner

The `backtest-runner` console script provides comprehensive backtesting capabilities by combining signal generation with exit strategy analysis. It runs complete signal-to-exit backtests using configurable trading and exit strategies.

**Key Features:**

- Complete signal-to-exit backtesting workflow
- Multiple trading strategies (Darvas Box, Mars, Momentum, Qullamaggie)
- Multiple exit strategies (Buy and Hold, Profit/Loss, EMA, MACD, ATR, Trailing Percentage Loss)
- Configurable ranking strategies
- Flexible ticker selection and limiting
- Multiple analysis modes (list, signal, top)
- Comprehensive signal processing with benchmark comparisons

**Usage:**

```bash
# Basic backtest with Darvas Box strategy and EMA exit
uv run backtest-runner --start-date 2024-01-01 --end-date 2024-01-31 --trading-strategy darvas_box --exit-strategy ema

# Test specific tickers with ATR exit strategy
uv run backtest-runner --start-date 2024-01-01 --end-date 2024-01-31 --tickers AAPL MSFT NVDA --exit-strategy atr --verbose

# Mars strategy with profit/loss exits and limited ticker count
uv run backtest-runner --start-date 2024-02-01 --end-date 2024-02-29 --trading-strategy mars --exit-strategy profit_loss --max-tickers 50

# Top 20 signals mode with MACD exits
uv run backtest-runner --start-date 2024-01-15 --end-date 2024-01-15 --mode top --exit-strategy macd
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
  - `qullamaggie` - Qullamaggie-style 50-day-high breakout strategy
- `--exit-strategy` - Exit timing strategy (default: buy_and_hold)
  - `buy_and_hold` - Hold for a fixed number of calendar days (default 30)
  - `profit_loss` - Exit on profit target or stop loss
  - `ema` - Exit when price closes below EMA
  - `macd` - Exit on MACD bearish signals
  - `atr` - Volatility-based stop losses using ATR
  - `trailing_percentage_loss` - Trailing stop set as a fixed percentage below the running max close
- `--exit-param KEY=VALUE` - Override an exit-strategy parameter, e.g. `--exit-param profit_target=15` (repeatable)
- `--ranking-strategy` - Signal ranking method (default: momentum)
  - `momentum` - Momentum-based ranking
  - `volume_momentum` - Volume-weighted momentum ranking
  - `breakout_quality` - Breakout event strength ranking
  - `qullamaggie` - Cohort-derived Sortino ranking for Qullamaggie breakouts
- `--trading-param KEY=VALUE` - Override a trading-strategy constructor parameter, e.g. `--trading-param sma_thresh=0.20` (repeatable)
- `--max-tickers` - Maximum number of tickers to test (default: 10000)
- `--mode` - Analysis mode (default: list)
  - `list` - Get all tickers with signals in date range
  - `signal` - Check specific ticker signals
  - `top` - Get top 20 signals for the period
- `--verbose` - Enable detailed logging output

**Exit Strategy Details:**

- **Buy and Hold**: Hold for a fixed holding period (default 30 calendar days), selling at the first bar on/after the cutoff
- **Profit/Loss**: Configurable profit targets and stop losses with early exit
- **EMA**: Technical analysis exit when price closes below exponential moving average
- **MACD**: Exit based on MACD indicator bearish crossovers
- **ATR**: Volatility-adjusted stop losses using Average True Range multipliers
- **Trailing Percentage Loss**: Trailing stop set as a fixed percentage below the running maximum close price; stop only moves up, never down

**Output:**

- Signal processing results with entry/exit analysis
- Return calculations for individual positions
- Benchmark comparisons against QQQ and SPY indices
- Detailed logging of signal analysis workflow

## portfolio-runner

The `portfolio-runner` console script provides sophisticated portfolio-level backtesting using the PortfolioService class. It simulates realistic trading with capital constraints, position sizing, and daily portfolio management across multiple strategies and time periods.

**Key Features:**

- **Realistic Portfolio Simulation**: Daily trading simulation with capital constraints and position overlap management
- **Multi-Strategy Support**: Configurable trading, exit, and ranking strategies
- **Risk Management**: Position sizing as a configurable fraction of portfolio value
- **Performance Analytics**: Comprehensive tearsheet generation with HTML reports
- **Flexible Universe**: Support for specific tickers or full symbol database
- **Benchmark Analysis**: Automatic comparison against SPY, QQQ, or custom benchmarks
- **Signal Quality Control**: Ranking threshold filtering for high-quality entries only

**Strategy Options:**

**Trading Strategies:**

- `darvas_box` (default) - Darvas Box trend-following strategy
- `mars` - Mars momentum strategy (@marsrides)
- `momentum` - Traditional momentum strategy
- `qullamaggie` - Qullamaggie-style 50-day-high breakout strategy

**Exit Strategies:**

- `buy_and_hold` (default) - Hold for a fixed number of calendar days (default 30)
- `profit_loss` - Exit on profit targets or stop losses
- `ema` - Exit when price closes below exponential moving average
- `macd` - Exit on MACD bearish signals
- `atr` - Volatility-based stop losses using Average True Range
- `trailing_percentage_loss` - Trailing stop set as a fixed percentage below the running max close

**Ranking Strategies:**

- `momentum` (default) - Momentum-based signal ranking
- `volume_momentum` - Volume-weighted momentum ranking
- `breakout_quality` - Breakout event strength ranking
- `qullamaggie` - Cohort-derived Sortino ranking for Qullamaggie breakouts

**Usage:**

```bash
# Basic portfolio backtest with default settings
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31

# Advanced backtest with custom parameters
uv run portfolio-runner \
    --start-date 2024-01-01 --end-date 2024-12-31 \
    --trading-strategy mars --exit-strategy profit_loss \
    --initial-capital 50000 --min-signal-ranking 80 \
    --output-file mars_strategy_results.html --verbose

# Test specific ticker universe
uv run portfolio-runner \
    --start-date 2024-01-01 --end-date 2024-06-30 \
    --tickers AAPL MSFT GOOGL AMZN NVDA \
    --trading-strategy darvas_box --exit-strategy atr \
    --position-size-pct 0.05 --verbose

# High-ranking signals only, compared against a custom benchmark
uv run portfolio-runner \
    --start-date 2024-01-01 --end-date 2024-12-31 \
    --min-signal-ranking 85 --max-tickers 500 \
    --benchmark-ticker SPY.US \
    --output-file high_quality_signals.html
```

**Required Options:**

- `--start-date` - Start date for backtest (YYYY-MM-DD format)
- `--end-date` - End date for backtest (YYYY-MM-DD format)

**Strategy Configuration:**

- `--trading-strategy` - Trading strategy: darvas_box, mars, momentum, qullamaggie (default: darvas_box)
- `--exit-strategy` - Exit strategy: buy_and_hold, profit_loss, ema, macd, atr, trailing_percentage_loss (default: buy_and_hold)
- `--exit-param KEY=VALUE` - Override an exit-strategy parameter, e.g. `--exit-param holding_days=365` (repeatable)
- `--ranking-strategy` - Ranking strategy: momentum, volume_momentum, breakout_quality, qullamaggie (default: momentum)
- `--trading-param KEY=VALUE` - Override a trading-strategy constructor parameter, e.g. `--trading-param sma_thresh=0.20` (repeatable)

**Portfolio Parameters:**

- `--initial-capital` - Starting capital amount (default: 30000.0)
- `--position-size-pct` - Fraction of portfolio value per position, compounding as the portfolio grows (default: 0.04 = 4%)
- `--min-signal-ranking` - Minimum signal ranking threshold 1-100 (default: 40)

**Universe Selection:**

- `--max-tickers` - Maximum number of tickers from database (default: 10000)
- `--tickers` - Specific ticker symbols to test (space-separated list)
- `--benchmark-ticker` - Symbol the tearsheet compares the portfolio against, in database convention with the `.US` suffix; quantstats takes exactly one (default: `QQQ.US`)

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
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --trading-strategy darvas_box --output-file darvas_results.html
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --trading-strategy mars --output-file mars_results.html
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --trading-strategy momentum --output-file momentum_results.html
```

**Exit Strategy Analysis:**

```bash
# Compare exit strategies with same trading approach
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --exit-strategy buy_and_hold --output-file bah_exits.html
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --exit-strategy atr --output-file atr_exits.html
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --exit-strategy ema --output-file ema_exits.html
```

**Risk Management Testing:**

```bash
# Test different position sizing and signal quality thresholds
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --min-signal-ranking 60 --position-size-pct 0.02 --output-file conservative.html
uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31 --min-signal-ranking 90 --position-size-pct 0.08 --output-file aggressive.html
```

## snapshot-company

The `snapshot-company` console script copies the current `turtle.company` rows into `turtle.company_history`, stamping them with `snapshot_date` set to the last day of the previous month. Intended to run on the 1st of each month via `deploy/snapshot_company.timer`. The operation is idempotent — running it twice for the same month skips the second write.

**Usage:**

```bash
# Take this month's snapshot
uv run snapshot-company
```

**Options:**

- `--verbose` — Enable detailed logging
