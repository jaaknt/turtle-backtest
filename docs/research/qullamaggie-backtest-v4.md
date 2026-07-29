# US Stock Screening — Predictive Signal Discovery

## Objective

Using the `turtle.daily_bars`, `turtle.company` and `turtle.ticker` PostgreSQL tables, identify which combination of **price action and volume metrics** best predicts top-quartile returns over a **12-month** holding period. The main metric to optimize is the per-trade Sortino ratio, annualized. Each signal trigger produces one trade return observation, regardless of how many signals fire on the same day. Returns are not aggregated by date. `annualization_factor = 365 / holding calendar days`

---

## Data Scope

- Universe: US common stocks (`turtle.ticker` where `country = 'USA'` and `type = 'Common Stock'`)
- Minimum filters: `close > 5` and `close < 250` and `mean(volume[-21:-1]) >= 500_000`, all evaluated on the signal date
- Market cap is ≥ 1.5B (`turtle.company` where `market_cap >= 1500000000` and `company.ticker_code = ticker.code`)
- Historical range: Jan 2020 onward in `turtle.daily_bars`
- Exclude tickers with fewer than 300 trading days of history
- Exclude tickers in sectors: Communication Services, Real Estate (`turtle.company` where `company.sector not in ('Communication Services', 'Real Estate')` and `company.ticker_code = ticker.code`)

---

## Step 1 — Candidate Entry Signals

For each trading day, compute the following metrics per ticker. Actual entry signal is triggered if all conditions are met:

**Price momentum conditions:**

- `breakout_N_days`: `close > max(close[-(N+1):-1])` — exceeds prior N trading days' high (sweep N ∈ {50})
- `pct_above_sma50`: `close / mean(close[-51:-1]) − 1 > X` (sweep X ∈ {12%, 16%, 20%})
<!--  
- `tight_range`: `(max(close[-11:-1]) − min(close[-11:-1])) / mean(close[-11:-1]) < 30%` 
-->

**Volatility quality filter (fixed, not swept):**

- `adr_pct`: `mean((high_i − low_i)/low_i, i in last 20 days, shift-1) >= 3.0%` — average daily range as a percent of price over the prior 20 trading days > 3.0%
- `adr_pct_change`: `adr_pct(10 days) / adr_pct(50 days) < 0.9` - average daily range of 10 days divided by average daily range of 50 days < 0.9
- `rsi_filter`: `RSI(14) < 70` — 14-period RSI computed on prior closes (shift-1 convention, no look-ahead). Excludes already-overbought entries (fixed, not swept)
- `roc_12m_cap`: `close / close[-252] − 1 < 100%` — 12-month return of stock. Excludes stocks that have already more than doubled in the past year, filtering out overextended breakouts that are likely in a late stage of their move.

**Volume signals:**

- `vol_surge`: `volume < 2.0 × mean(volume[-51:-1])` — breakout volume must stay below 2.0× the 50-day average.
- `vol_dry_up`: `mean(volume[-11:-1]) < 0.90 × mean(volume[-51:-1])` — base volume must be below 90% of the 50-day average, confirming the consolidation happened on declining volume before the breakout surge (fixed, not swept)

<!--
**Trend alignment filter (fixed, not swept):**
- `sma_alignment`: `SMA(close, 10) > SMA(close, 20) > SMA(close, 50)` — all computed on prior closes (shift-1 convention, no look-ahead). Confirms the stock is in a short-term uptrend at all timeframes before the breakout.
-->

**Market regime filter (fixed, not swept):**

- `spy_above_200d`: SPY closing price on the signal date is above its 200-day SMA. Computed as `spy_close > mean(spy_close[-201:-1])` using `daily_bars` where `ticker_code = 'SPY.US'`. Skip any entry signal on dates where this condition is false.

**Entering condition:**

- `qullamaggie_style`: `spy_above_200d` AND `adr_pct` AND `adr_pct_change` AND `rsi_filter` AND `roc_12m_cap` AND `breakout_N_days(N)` AND `pct_above_sma50(X)` AND `vol_surge` AND `vol_dry_up`

**Algorithm naming:**

Each swept entry signal is named `bk{N}d_s{X}_v{version}` — the breakout window, the
`pct_above_sma50` threshold as a whole percent, and the `version` of the algorthm. With N = 50 and
`version` = 2.0, the three algorithms in this study are:

| Name | Breakout | `pct_above_sma50` | `version` |
|---|---|---|---|
| `bk50d_s20_v2.0` | 50d high | > 20% | 2.0 |
| `bk50d_s16_v2.0` | 50d high | > 16% | 2.0 |
| `bk50d_s12_v2.0` | 50d high | > 12% | 2.0 |

Every other filter is fixed across all three, so none of them is encoded in the name — read the
Configuration table in the result file for those. Ranking-gated variants append the gate, e.g.
`bk50d_s20_v2.0 R≥45`.

**Entry timing — buy the next day's open:**

The **signal date** is the day the entering condition becomes true, evaluated on that day's close and
its shift-1 indicators. The **entry date** is the next trading day, and the position is filled at that
bar's **split/dividend-adjusted open** (`open × adjusted_close/close`). Signal date and entry date are
distinct throughout the rest of this document.

- The entry bar is the first bar strictly after the signal date. Skip the signal if no such bar appears within 7 calendar days, or if that bar's adjusted open is not positive. This matches `SignalProcessor.calculate_entry_data` and `resolve_entries` in `turtlex/research/qullamaggie.py`, so the study fills the same way the production path does.
- Every filter in Step 1 and the ranking score in Step 5 are computed from signal-date data only. The entry price is therefore never an input to the decision to trade — it is the consequence of a decision already made at the prior close.

---

## Step 2 — Exit Criteria

| Exit Rule | Parameters to sweep |
|-----------|---------------------|
| Time-based | Hold exactly 366 calendar days (12M) from the **entry** date |

Skip any signal where 366 calendar days past its entry date are not available in the DB.

---

## Step 3 — Evaluation Methodology

- **Burn-in period**: Jan 2020 – Dec 2020. Used only for indicator warm-up; no signals evaluated.
- **Evaluation period**: Jan 2021 – present. All entry signals and forward returns computed here.

Trade return formula: `return = close[entry_date + holding_days] / open[entry_date] − 1` — bought at the
entry bar's adjusted open, sold at the close of the first trading day at or after `entry_date + holding_days`.

Exclusions applied to all combinations before reporting:

- Exclude combinations with fewer than 30 total trades
- Exclude combinations where fewer than 10 trades have negative returns (Sortino denominator unreliable)

**Multiple triggers**: if the same ticker re-triggers within 30 calendar days of the first trigger's signal date, skip all subsequent triggers in that window.

---

## Step 4 — Performance Metrics

For each (entry signal × exit rule) combination, report the metrics below.

Notation: let `r₁, …, r_N` be the `N` per-trade returns for the combination, and
`percentile(·, p)` the p-th percentile of that set. `annualization_factor = 365 / holding_days`.

- **Win rate**: % of trades with positive return
  - `win_rate = count(rᵢ > 0) / N`
- **Median return**: middle return when all trades are sorted
  - `median = percentile({rᵢ}, 50)`
- **Mean return**: arithmetic average return per trade
  - `mean = (1 / N) × Σ rᵢ`
- **Annualized mean return**: CAGR-style annualization of the mean return. With a single 366d hold this is near-identical to the mean return; it is kept so figures stay comparable with studies run at other holding periods
  - `ann_mean = (1 + mean)^(annualization_factor) − 1`
- **Top-quartile threshold**: what return does the top 25% achieve?
  - `Q75 = percentile({rᵢ}, 75)`
- **Sortino ratio**: annualized per-trade Sortino (MAR = 0%):
  - `downside_dev = sqrt(mean(min(rᵢ, 0)²))`  — RMS of negative returns (positives count as 0)
  - `sortino = mean(R) × sqrt(annualization_factor) / downside_dev`
- **Max drawdown**: mean over trades of each trade's peak-to-trough decline, along the price path `[open[entry], close[entry], close[entry+1], …, close[exit]]` (the entry open is the first point, since that is where the position begins)
  - per trade: `mdd = max over t of (1 − priceₜ / max(price[..t]))`
  - report `mean(mddᵢ)`
- **Signal frequency**: how many triggers per month on average
  - `freq_per_month = N / months_in_eval_period`
- **Profit factor**: gross wins / gross losses
  - `PF = Σ(rᵢ | rᵢ > 0) / |Σ(rᵢ | rᵢ < 0)|`
- **CVaR(95%)**: mean return of the worst 5th percentile of trades (Expected Shortfall)
  - `k = max(1, floor(0.05 × N))`
  - `CVaR = mean of the k smallest rᵢ`

---

## Step 5 — Signal Ranking

Every signal that passes the entering condition is scored 0–100 by `QullamaggieRanking`
(`turtlex/strategy/ranking/qullamaggie.py`) — the same class the live `portfolio-runner` gates on via
`--min-signal-ranking`. Do not reimplement the bands here; call the production class so the study and
the live path cannot drift apart.

The score sums three independent dimensions, each a first-match-wins band lookup (`value < upper_bound`
→ that band's points; values at or above the last bound score the trailing constant):

| Dimension | Column | Weight | Bands (`upper_bound` → points) | ≥ last bound |
|---|---|---|---|---|
| ADR%(20) — higher is better | `adr_pct` | 40 | 0.035→0, 0.04→0, 0.045→10, 0.05→13, 0.08→27 | 40 |
| Distance above SMA50 — higher is better, non-monotonic | `pct_vs_sma50` | 35 | 0.10→0, 0.12→8, 0.15→15, 0.17→22, 0.20→12, 0.30→31 | 35 |
| Entry price — lower is better | raw `close` | 25 | 10→25, 20→8, 50→2, 100→2, 250→0 | 0 |

Scoring inputs must match the production pairing exactly:

- `adr_pct` and `pct_vs_sma50` are the shift-1 indicators already computed for the entry filter (derived from the split/dividend-adjusted close), so the ranking introduces no look-ahead.
- The price band scores the **raw (unadjusted) close** — `QullamaggieStrategy` keeps `close` raw and its adjusted series in `adj_close`, and `QullamaggieRanking` reads `close`. Scoring an adjusted price against dollar-denominated bands would put a stock in the wrong band whenever a split happened after the entry date.

Note the interaction between the ranking and the entry filter: `pct_above_sma50(X)` makes the lower
SMA50 bands unreachable, so the minimum achievable score rises with X (at X = 20% the SMA50 dimension
alone contributes ≥ 31). The `adr_pct ≥ 3.0%` filter does **not** rescue the ADR dimension — a signal
with ADR in 3.0–4.0% scores 0 on the highest-weighted dimension. The gate is therefore far more
selective at low X than at high X, and that must be read alongside the tables rather than assumed away.

---

## Step 6 — Output Format

Rank all (entry signal × exit rule) combinations by **Sortino ratio** on the full evaluation period. Exclude any combination where overall Sortino ≤ 0.

Report two ranking tables, same columns and ranking rule, side by side:

1. **No ranking condition** — every entry signal that meets the entering condition is taken as a trade.
2. **Ranking R ≥ {40%, 45%, 50%}** — same signals, but a trade is taken only if its `QullamaggieRanking` score is ≥ R. Report the mean and median score of the accepted trades, and how many signals the gate rejected.

**Year-by-year consistency flag**: for each complete calendar year in the evaluation period, compute the annual Sortino ratio. A combination is flagged ✓ consistent if:

- Sortino > 0 in ≥ 70% of complete calendar years, AND
- At least 3 complete calendar years have ≥ 10 negative-return trades (enough to compute a valid annual Sortino)

The `Yrs+` column shows `positive_sortino_years / total_valid_years` (e.g. `4/5`).

```text
Rank | Entry Signal        | Exit  | Win% | Mean Ret | AnnMean Ret |Median Ret | Profit Factor |Sortino | CVaR(95%) | Freq/mo | Yrs+ | Consistent
-----|---------------------|-------|------|----------|-------------|-----------|---------------|--------|-----------|---------|------|-----------
  1  | breakout_100d+...   | 63d   |  62% |   +8.3%  |    +54.1%   | +10.3%    |    1.2        |    1.82|     -6.1% |      43 | 4/5  | ✓
  2  | ...
```

---

## Constraints & Caveats

- **Survivorship bias**: only use tickers present in the DB at the *entry* date, not just tickers that survived to today (market cap is exception as it changes slowly in time)
- **Look-ahead bias**: all signals must be computable from data available on the signal date only; the entry price is the *next* day's open, which is deliberately not knowable when the signal fires

## Implementation

- create/overwrite script scripts/qullamaggie-backtest-v4.py
- save research results in file docs/research/result-qullamaggie-backtest-v4.md overwriting existing file if file exists
- always update ## Configuration values to reflect latest setup
- add your findings and ideas how to improve the algorithm to end of docs/research/result-qullamaggie-backtest-v4.md file each improvement on separate line in the list
