# US Stock Screening — Predictive Signal Discovery

## Objective

Using the `turtle.daily_bars`, `turtle.company` and `turtle.ticker` PostgreSQL tables, identify which combination of **price action and volume metrics** best predicts top-quartile returns over a **1-month** and **3-month** holding period. The main metric to optimize is the per-trade Sortino ratio, annualized. Each signal trigger produces one trade return observation, regardless of how many signals fire on the same day. Returns are not aggregated by date. `annualization_factor = 252 / holding_days`

---

## Data Scope

- Universe: US common stocks (`turtle.ticker` where `country = 'USA'` and `type = 'Common Stock'`)
- Minimum filters: `close >= 10` and `mean(volume[-21:-1]) >= 500_000` at entry
- Market cap is > 1.5B (`turtle.company` where `market_cap >= 1500000000` and `company.ticker_code = ticker.code`)
- Historical range: Jan 2020 onward in `turtle.daily_bars`
- Exclude tickers with fewer than 300 trading days of history
- Exclude tickers in sectors: Communication Services, Real Estate (`turtle.company` where `company.sector not in ('Communication Services', 'Real Estate')` and `company.ticker_code = ticker.code`)

---

## Step 1 — Candidate Entry Signals

For each trading day, compute the following metrics per ticker. Actual entry signal is triggered if all conditions are met:

**Price momentum conditions:**
- `breakout_N_days`: `close > max(close[-(N+1):-1])` — exceeds prior N trading days' high (sweep N ∈ {50})
- `pct_above_sma50`: `close / mean(close[-51:-1]) − 1 > X` (sweep X ∈ {15%, 20%, 25%})
- `tight_range`: `(max(close[-11:-1]) − min(close[-11:-1])) / mean(close[-11:-1]) < Y` (10 trading days ending yesterday, sweep Y ∈ {10%, 15%, 20%})

**Volatility quality filter (fixed, not swept):**
- `adr_pct`: `mean(high[-(21+1):-1] − low[-(21+1):-1]) / mean(close[-(21+1):-1]) >= 2.5%` — average daily range as a percent of price over the prior 20 trading days. Requires `high` and `low` columns from `daily_bars`.
- `rsi_filter`: `RSI(14) < 72` — 14-period RSI computed on prior closes (shift-1 convention, no look-ahead). Excludes already-overbought entries (fixed, not swept)
- `roc_12m_cap`: `close[-1] / close[-253] − 1 < 100%` — 12-month return computed on prior closes (shift-1, no look-ahead). Excludes stocks that have already more than doubled in the past year, filtering out overextended breakouts that are likely in a late stage of their move. 

**Volume signals:**
- `vol_surge`: `1.0 × mean(volume[-51:-1]) < volume < 2.0 × mean(volume[-51:-1])` — breakout volume must exceed 1.0× the 50-day average but stay below 2.0×. The upper cap removes panic/news-driven spikes: VolX Q4 (>2.0×) has 46.7–54.5% win rate vs 65%+ for Q1–Q3 across backtests (fixed, not swept)
- `vol_dry_up`: `mean(volume[-11:-1]) < 0.80 × mean(volume[-51:-1])` — base volume must be below 80% of the 50-day average, confirming the consolidation happened on declining volume before the breakout surge (fixed, not swept)

<!--
**Trend alignment filter (fixed, not swept):**
- `sma_alignment`: `SMA(close, 10) > SMA(close, 20) > SMA(close, 50)` — all computed on prior closes (shift-1 convention, no look-ahead). Confirms the stock is in a short-term uptrend at all timeframes before the breakout.
-->

**Market regime filter (fixed, not swept):**
- `spy_above_200d`: SPY closing price on the entry date is above its 200-day SMA. Computed as `spy_close > mean(spy_close[-201:-1])` using `daily_bars` where `ticker_code = 'SPY.US'`. Skip any entry signal on dates where this condition is false.

**Entering condition:**
- `qullamaggie_style`: `spy_above_200d` AND `adr_pct` AND `rsi_filter` AND `roc_12m_cap` AND `breakout_N_days(N)` AND `pct_above_sma50(X)` AND `tight_range(Y)` AND `vol_surge(Z)` AND `vol_dry_up`

---

## Step 2 — Exit Criteria

| Exit Rule | Parameters to sweep |
|-----------|---------------------|
| Time-based | Hold exactly 184 calendar days (6M), 366 calendar days (12M) |

Skip any entry where 366 calendar days are not available in the DB.

---

## Step 3 — Evaluation Methodology

- **Burn-in period**: Jan 2020 – Dec 2020. Used only for indicator warm-up; no signals evaluated.
- **Evaluation period**: Jan 2021 – present. All entry signals and forward returns computed here.

Trade return formula: `return = close[entry_date + holding_days] / close[entry_date] − 1`

Exclusions applied to all combinations before reporting:
- Exclude combinations with fewer than 30 total trades
- Exclude combinations where fewer than 10 trades have negative returns (Sortino denominator unreliable)

**Multiple triggers**: if the same ticker re-triggers within 30 calendar days of the first trigger's entry date, skip all subsequent triggers in that window.

---

## Step 4 — Performance Metrics

For each (entry signal × exit rule) combination, report the metrics below.

Notation: let `r₁, …, r_N` be the `N` per-trade returns for the combination, and
`percentile(·, p)` the p-th percentile of that set. `annualization_factor = 252 / holding_days`.

- **Win rate**: % of trades with positive return
  - `win_rate = count(rᵢ > 0) / N`
- **Median return**: middle return when all trades are sorted
  - `median = percentile({rᵢ}, 50)`
- **Mean return**: arithmetic average return per trade
  - `mean = (1 / N) × Σ rᵢ`
- **Top-quartile threshold**: what return does the top 25% achieve?
  - `Q75 = percentile({rᵢ}, 75)`
- **Sortino ratio**: annualized per-trade Sortino (MAR = 0%):
  - `downside_dev = sqrt(mean(min(rᵢ, 0)²))`  — RMS of negative returns (positives count as 0)
  - `sortino = mean(R) × sqrt(annualization_factor) / downside_dev`
- **Max drawdown**: mean over trades of each trade's peak-to-trough decline (closing price)
  - per trade: `mdd = max over t∈[entry, exit] of (1 − closeₜ / max(close[entry..t]))`
  - report `mean(mddᵢ)`
- **Signal frequency**: how many triggers per month on average
  - `freq_per_month = N / months_in_eval_period`
- **Profit factor**: gross wins / gross losses
  - `PF = Σ(rᵢ | rᵢ > 0) / |Σ(rᵢ | rᵢ < 0)|`
- **CVaR(95%)**: mean return of the worst 5th percentile of trades (Expected Shortfall)
  - `k = max(1, floor(0.05 × N))`
  - `CVaR = mean of the k smallest rᵢ`

---

## Step 5 — Output Format

Rank all (entry signal × exit rule) combinations by **Sortino ratio** on the full evaluation period. Exclude any combination where overall Sortino ≤ 0.

**Year-by-year consistency flag**: for each complete calendar year in the evaluation period, compute the annual Sortino ratio. A combination is flagged ✓ consistent if:
- Sortino > 0 in ≥ 70% of complete calendar years, AND
- At least 3 complete calendar years have ≥ 10 negative-return trades (enough to compute a valid annual Sortino)

The `Yrs+` column shows `positive_sortino_years / total_valid_years` (e.g. `4/5`).

```
Rank | Entry Signal        | Exit  | Win% | Mean Ret |Median Ret | Profit Factor |Sortino | CVaR(95%) | Freq/mo | Yrs+ | Consistent
-----|---------------------|-------|------|----------|-----------|---------------|--------|-----------|---------|------|-----------
  1  | breakout_100d+...   | 63d   |  62% |   +8.3%  | +10.3%    |    1.2        |    1.82|     -6.1% |      43 | 4/5  | ✓
  2  | ...
```

---

## Constraints & Caveats

- **Survivorship bias**: only use tickers present in the DB at the *entry* date, not just tickers that survived to today (market cap is exception as it changes slowly in time)
- **Look-ahead bias**: all signals must be computable from data available on the entry date only

## Implementation
- create/overwrite script scripts/qullamaggie-backtest-v3.py
- save research results in file docs/research/result-qullamaggie-backtest-v3.md overwriting existing file if file exists
- add your findings and ideas how to improve the algorithm to end of docs/research/result-qullamaggie-backtest-v3.md file 
