# US Stock Screening — Predictive Signal Discovery

## Objective

Using the `turtle.daily_bars`, `turtle.company` and `turtle.ticker` PostgreSQL tables, identify which combination of **price action and volume metrics** best predicts top-quartile returns over a **1-month** and **3-month** holding period. Backtest findings using a **rolling out-of-sample window** to avoid look-ahead bias. The main metric to optimize is annulized Sortino ratio
using equal-weights. annualization_factor = 252 / holding_days

---

## Data Scope

- Universe: US common stocks (`turtle.ticker` where `country = 'USA'` and `type = 'Common Stock'`)
- Minimum filters: price ≥ $5 at entry, 20-day avg volume ≥ 300k shares (liquidity screen)
- Market cap is > 2B (`turtle.company` where `market_cap >= 2000000000` and `company.ticker_code = ticker.code`)
- Historical range: use all available data in `turtle.daily_bars`
- Exclude tickers with fewer than 300 trading days of history
- Exclude tickers in sectors: Communication Services, Real Estate (`turtle.company` where `company.sector not in ('Communication Services', 'Real Estate')` and `company.ticker_code = ticker.code`) 

---

## Step 1 — Candidate Entry Signals

For each trading day, compute the following metrics per ticker and flag as potential signal flags. Actual entry signal is triggered if all conditions are met:

**Price momentum conditions:**
- `rising_price`: Closing price at entry > SMA(10, close), SMA(20, close). This is fixed condition
- `breakout_N_week`: close price crosses above N-week high (sweep N ∈ {10, 20, 50})
- `pct_above_sma50`: price is X% above 50-day SMA (sweep X ∈ {10%, 15%, 20%})
- `tight_base`: 10-day close std dev / mean < X (low-volatility consolidation before breakout) sweep X ∈ {5%, 10%} tight_base should be computed over days
  [-11, -1] (excluding today)

**Volume signals:**
- `vol_surge`: today's volume > N × 50-day avg volume (sweep N ∈ {1.2, 1.3, 1.4}). 50-day avg volume = rolling mean of volume over [-50, -1]

**Entering condition:**
- `qullamaggie_style`: `rising_price` AND `breakout_N_week(N)` AND `pct_above_sma50(X)` AND `tight_base(X)` AND `vol_surge(N)`

---

## Step 2 — Exit Criteria

Test these exit rules against `qullamaggie_style`.

| Exit Rule | Parameters to sweep |
|-----------|---------------------|
| Time-based | Hold exactly 21 days (1M) or 63 days (3M) |
Skip any entry where 21 or 63 forward bars are not available in the DB.
---

## Step 3 — Rolling Window Backtest Methodology

Use a **walk-forward** approach to avoid curve-fitting:

History constraint - assume that data starts Jan-2020

```
Window size:   12 months in-sample  →  3 months out-of-sample
Roll by:       3 months each iteration
Example:
  Window 1:  Train Jan–Dec 2020, Test Jan–Mar 2021
  Window 2:  Train Apr 2020–Mar 2021, Test Apr–Jun 2021
  ...continue to present
```

For each window:
1. Compute all entry signals on every trading day in the in-sample period
2. Record forward returns at 1M and 3M for every triggered signal
3. Rank signal combinations by Sortino ratio, exclude combinations where fewer than 10 trades have negative returns before computing Sortino.
4. Record out-of-sample performance without re-fitting, discard combinations with fewer than 30 total OOS trades before
  ranking.

---

## Step 4 — Performance Metrics

For each (entry signal, exit rule, window) combination, report:

- **Win rate**: % of trades with positive return
- **Median return**: at 1M and 3M
- **Top-quartile threshold**: what return does the top 25% achieve?
- **Sortino ratio**: annualized Sortino ratio 
- **Max drawdown**: mean of largest peak-to-trough within holding period
- **Signal frequency**: how many triggers per day on average (avoid rare signals)
- **Profit factor**: gross wins / gross losses
- **Calmar ratio**: annualized return (CAGR) ÷ maximum drawdown

---

## Step 5 — Output Format

Rank all (entry signal × exit rule) combinations by **out-of-sample Sortino ratio**:

```
Rank | Entry Signal       | Exit Rule          | Win% | Median return | Sortino | Freq/mo
-----|--------------------|--------------------|------|-----------|-----------|--------|--------
  1  | breakout_N_week+... | exit_63d          |  62% |    +8.3%      |  1.82  |   43
  2  | ...
```

Flag the **top 10 combinations** with the best out-of-sample consistency (in-sample vs out-of-sample Sortino ratio degradation < 30%), exclude out-of-sample Sortino < 0.
Exclude combinations where fewer than 10 trades have negative returns before computing Sortino.
---

## Constraints & Caveats

- **Survivorship bias**: only use tickers present in the DB at the *entry* date, not just tickers that survived to today (market cap is exception as it changes slowly in time)
- **Look-ahead bias**: all signals must be computable from data available on the entry date only 
- **Multiple triggers**: if the same ticker re-triggers within 30 days, skip (avoid counting the same move twice)

## Implementation
- create/overwrite script scripts/qullamaggie-backtest-v2.py
- save research results in file research/result-qullamaggie-backtest-v2.md overwriting existing file if file exists

