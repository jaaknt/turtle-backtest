# Scripts

This document describes the command-line scripts that provide convenient interfaces for common operations using the turtle backtest services.

All strategy name → class mappings used by `--trading-strategy`, `--exit-strategy`, and `--ranking-strategy` flags are defined in `turtlex/strategy/factory.py`. Add new strategies there to make them available across all scripts.

Every console script records its invocation in `turtle.job_runs` — arguments, duration, exit code and error, plus the resolved strategy parameters for the three analysis runners — when `[job_runs] enabled` is set in the resolved configuration — off in the base file, switched on by the `hetzner` profile that the VPS runs under. See [specs/run_jobs.md](specs/run_jobs.md).

Return/risk statistics come from `turtlex/backtest/metrics.py`, which owns the canonical definitions. It covers two sampling regimes, and they must not be mixed:

- **Trade series** — `compute_trade_metrics` (Win%, PF, Sortino, Med%, Mean%, CVaR, mean per-trade MaxDD), annualized by the mean holding period.
- **Daily equity-curve series** — `compute_daily_sortino`, annualized by `sqrt(252)`.

In both, Sortino's downside deviation is the RMS of `min(r, 0)` over **all N** observations, and the ratio — not its inputs — is annualized. Every `scripts/qullamaggie-*.py` study, plus `backtest-runner` and `portfolio-runner`, now goes through one of the two, so Sortino columns are directly comparable within each regime. They are *not* comparable across regimes: a daily-series Sortino and a trade-series Sortino answer different questions.

Until 2026-08-01 most studies divided instead by the RMS of the losers only — a different statistic, smaller in the denominator and so **larger** in the ratio by exactly `sqrt(N / n_losers)`. Because that factor depends on each series' own win rate it reordered cohorts rather than merely rescaling them (17 of 255 pairwise comparisons flipped on migration), which is why every affected result doc was regenerated. **Result docs published before 2026-08-01 are not comparable with the current ones.**

`tests/scripts/test_metric_conventions.py` enforces this: a study that reports a Sortino must import one of the two helpers, and must not also hand-roll an RMS itself. The second rule exists because an import-only check let `exit-sweep` keep a private losers-only daily Sortino alongside the imported trade helper.

For a daily series, `quantstats.stats.sortino` uses the same all-N denominator and agrees with `compute_daily_sortino` by construction; the helper exists because quantstats needs a pandas Series with a datetime index, and pandas is confined to `turtlex/portfolio/analytics.py`.

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
- `--trading-strategy` — `darvas_box`, `mars`, `momentum`, `qullamaggie` (default: `qullamaggie`)
- `--ranking-strategy` — `momentum`, `volume_momentum`, `breakout_quality`, `qullamaggie` (default: `qullamaggie`)
- `--trading-param KEY=VALUE` — Override a trading-strategy constructor parameter, e.g. `--trading-param sma_thresh=0.20` (repeatable)
- `--max-tickers` — Maximum symbols to scan (default: 10000)
- `--verbose` — Enable detailed logging

**Output:**

One fixed-width row per signal, sorted by date then ticker. The column layout matches the
signal table of `scripts/qullamaggie-signals-v4.py`, so the two read the same way — but the row
sets differ: that script also gates at `ranking >= 44` and drops signals whose raw close moved
more than 50% in a day, so its table is a subset of this one.

```text
Date       │ Symbol │ Sector                 │ %abv SMA50 │   ADR% │ ADR_CHG │ VOL_DRY │  RSI14 │    TR% │  ROC252% │   Last date │ Ranking │  Entry $ │ Curr Price │  Change %
2026-06-01 │ FA.US  │ Industrials            │     +30.8% │   5.4% │    0.83 │    0.62 │   50.5 │   7.4% │    +0.2% │  2026-08-21 │      75 │    17.07 │      20.90 │    +22.4%
```

The seven indicator columns carry the value each column holds on the signal-date row (most are
computed from prior-day data — see `QullamaggieStrategy.calculate_indicators_pl`). `Entry $` is
that day's raw close and `Curr Price` the raw close of the last bar in the window, so `Change %`
is mark-to-window-end, not a realised return, and it is **not** adjusted for splits or dividends
between the two dates. `Sector` comes from `turtle.company`. Every signal is listed — unlike
`portfolio-runner` there is no `--min-signal-ranking` gate here.

Only `qullamaggie` fills these columns. `darvas_box`, `mars` and `momentum` emit a bare signal,
so for them `Last date`, `Entry $`, `Curr Price` and `Change %` render `--` as well; only `Date`,
`Symbol`, `Sector` and `Ranking` populate.

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
- `--trading-strategy` - Signal generation strategy (default: qullamaggie)
  - `darvas_box` - Darvas Box trend-following strategy
  - `mars` - Mars momentum strategy (@marsrides)
  - `momentum` - Traditional momentum strategy
  - `qullamaggie` (default) - Qullamaggie-style 50-day-high breakout strategy
- `--exit-strategy` - Exit timing strategy (default: buy_and_hold)
  - `buy_and_hold` - Hold for a fixed number of calendar days (default 30)
  - `profit_loss` - Exit on profit target or stop loss
  - `ema` - Exit when price closes below EMA
  - `macd` - Exit on MACD bearish signals
  - `atr` - Volatility-based stop losses using ATR
  - `trailing_percentage_loss` - Trailing stop set as a fixed percentage below the running max close
- `--exit-param KEY=VALUE` - Override an exit-strategy parameter, e.g. `--exit-param profit_target=15` (repeatable)
- `--ranking-strategy` - Signal ranking method (default: qullamaggie)
  - `momentum` - Momentum-based ranking
  - `volume_momentum` - Volume-weighted momentum ranking
  - `breakout_quality` - Breakout event strength ranking
  - `qullamaggie` (default) - Cohort-derived Sortino ranking for Qullamaggie breakouts
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

- `darvas_box` - Darvas Box trend-following strategy
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

- `momentum` - Momentum-based signal ranking
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

- `--trading-strategy` - Trading strategy: darvas_box, mars, momentum, qullamaggie (default: qullamaggie)
- `--exit-strategy` - Exit strategy: buy_and_hold, profit_loss, ema, macd, atr, trailing_percentage_loss (default: buy_and_hold)
- `--exit-param KEY=VALUE` - Override an exit-strategy parameter, e.g. `--exit-param holding_days=365` (repeatable)
- `--ranking-strategy` - Ranking strategy: momentum, volume_momentum, breakout_quality, qullamaggie (default: qullamaggie)
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

## lightyear-import

The `lightyear-import` console script parses every `*.csv` account statement in a drop folder and stores the real Buy/Sell executions in `turtle.lightyear_transaction`, giving the repo a durable ledger of what is actually held. Files are left in place. Only rows whose `Type` is `Buy` or `Sell`, whose `CCY` is `USD`, and whose `TICKER.US` code is a member of the named `turtle.ticker_group` are imported — the currency rule is what keeps a EUR sale of an Amsterdam listing from being recorded as a sale of the same-named US ADR. `Dividend` and `Conversion` rows are parsed and skipped.

The `reference` column is the unique key and inserts use `ON CONFLICT DO NOTHING`, so re-importing overlapping statements never double-counts. A second run over an unchanged folder reports 0 inserted.

The ticker group is a hand-maintained watchlist; nothing in this codebase writes it. Seed it with SQL before the first run, or every row is silently dropped:

```sql
INSERT INTO turtle.ticker_group (code, ticker_code)
VALUES ('lightyear', 'DUOL.US'), ('lightyear', 'PRGS.US')
ON CONFLICT DO NOTHING;
```

An empty group aborts the run with an error rather than reporting a misleading "0 inserted". A *single* symbol missing from the group is named in a `WARNING` — check that warning before concluding the parser dropped something.

A damaged statement fails in isolation: the file is named with its offending row, **nothing from that file is stored** (the insert happens once, after the whole file parses), and the remaining files still import. The run exits `1` so the failure cannot pass unnoticed, but the summary for the healthy files is printed first. Malformed headers, truncated rows, unparseable dates and non-numeric amounts are all caught this way; a UTF-8 BOM is tolerated.

**Usage:**

```bash
# Download the statement from Lightyear, drop it in, then:
mkdir -p data/lightyear
uv run lightyear-import

# Scan a different folder against a different watchlist
uv run lightyear-import --folder /path/to/statements --ticker-group lightyear
```

**Options:**

- `--folder PATH` — Folder to scan for `*.csv` statements (default: `data/lightyear`)
- `--ticker-group CODE` — `turtle.ticker_group` code listing held symbols (default: `lightyear`)
- `--verbose` — Enable detailed logging

`data/lightyear/` is gitignored: statements are personal financial records. `docs/specs/lightyear-example.csv` is an anonymised fixture of the format.
