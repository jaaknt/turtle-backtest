# US Stock Screening — Predictive Signal Discovery

## Objective

Using the `turtle.daily_bars`, `turtle.company` and `turtle.ticker` PostgreSQL tables, identify which combination of **price action and volume metrics** best predicts top-quartile returns over a **12-month** holding period. The main metric to optimize is the per-trade Sortino ratio, annualized. Each signal trigger produces one trade return observation, regardless of how many signals fire on the same day. Returns are not aggregated by date. `annualization_factor = 365 / holding calendar days`

---

## Data Scope

- Universe: US common stocks (`turtle.ticker` where `country = 'USA'` and `type = 'Common Stock'`)
- Minimum filters: `close > 5` and `close < 250` and `mean(volume[-21:-1]) >= 100_000`, all evaluated on the signal date
- Market cap is ≥ 1.5B (`turtle.company` where `market_cap >= 1500000000` and `company.ticker_code = ticker.code`)
- Evaluation period (baseline): **2021-2025**. Signals fire through the end of the window, but a trade
  needs 366 calendar days of forward data to reach its exit — so signals from roughly the last twelve
  months produce no completed trade and are skipped. The reported period is therefore the range that
  actually yields trades, not the range scanned.
- Historical range: `turtle.daily_bars` from 730 calendar days before the evaluation window (burn-in,
  indicators only) forward to **2026-06-30**. Signals stop at the window end, but exits may reach
  into that forward data, so a trade entered late in the window can still complete its 366-day hold.
  The forward load is capped at the later of what the last entry could need — so a 2010-2015 run
  pulls ~7 years of bars, not ~18 — and entries whose exit would fall past 2026-06-30 are skipped.
  For the 2021-2025 baseline that means entries through roughly 2025-06 complete; later ones do not.
- Exclude tickers with fewer than 300 trading days of history
- Exclude tickers in sectors: Communication Services, Real Estate (`turtle.company` where `company.sector not in ('Communication Services', 'Real Estate')` and `company.ticker_code = ticker.code`)

---

## Step 1 — Candidate Entry Signals

For each trading day, compute the following metrics per ticker. Actual entry signal is triggered if all conditions are met:

**Price momentum conditions:**

- `breakout_N_days`: `close > max(close[-(N+1):-1])` — exceeds prior N trading days' high (sweep N ∈ {50})
- `pct_above_sma50`: `close / mean(close[-51:-1]) − 1 >= X` (sweep X ∈ {12%, 16%, 20%}) — inclusive, so a
  signal sitting exactly on the threshold is kept, matching the `>=` convention the other thresholds use
<!--  
- `tight_range`: `(max(close[-11:-1]) − min(close[-11:-1])) / mean(close[-11:-1]) < 30%` 
-->

**Volatility quality filter (fixed, not swept):**

- `adr_pct`: `mean((high_i − low_i)/low_i, i in last 20 days, shift-1) >= 3.0%` — average daily range as a percent of price over the prior 20 trading days >= 3.0%
- `adr_pct_change`: `adr_pct(10 days) / adr_pct(50 days) < 0.9` - average daily range of 10 days divided by average daily range of 50 days < 0.9
- `rsi_filter`: `RSI(14) < 70` — 14-period RSI computed on prior closes (shift-1 convention, no look-ahead). Excludes already-overbought entries (fixed, not swept)
- `roc_12m_cap`: `close / close[-252] − 1 < 100%` — 12-month return of stock. Excludes stocks that have already more than doubled in the past year, filtering out overextended breakouts that are likely in a late stage of their move.

**Volume signals:**

- `vol_surge`: `volume < 2.0 × mean(volume[-51:-1])` — breakout volume must stay below 2.0× the 50-day average.
<!--
- `vol_dry_up`: `mean(volume[-11:-1]) < 0.90 × mean(volume[-51:-1])` — base volume must be below 90% of the 50-day average, confirming the consolidation happened on declining volume before the breakout surge (fixed, not swept)
-->
<!--
**Trend alignment filter (fixed, not swept):**
- `sma_alignment`: `SMA(close, 10) > SMA(close, 20) > SMA(close, 50)` — all computed on prior closes (shift-1 convention, no look-ahead). Confirms the stock is in a short-term uptrend at all timeframes before the breakout.
-->

**Market regime filter (fixed, not swept):**

- `spy_above_200d`: SPY closing price on the signal date is above its 200-day SMA. Computed as `spy_close > mean(spy_close[-201:-1])` using `daily_bars` where `ticker_code = 'SPY.US'`. Skip any entry signal on dates where this condition is false.

**Entering condition:**

- `qullamaggie_style`: `spy_above_200d` AND `adr_pct` AND `adr_pct_change` AND `rsi_filter` AND `roc_12m_cap` AND `breakout_N_days(N)` AND `pct_above_sma50(X)` AND `vol_surge`

**Algorithm naming:**

Each swept entry signal is named `bk{N}d_s{X}_v{version}` — the breakout window, the
`pct_above_sma50` threshold as a whole percent, and the `version` of the algorthm. With N = 50 and
`version` = 2.0, the three algorithms in this study are:

| Name | Breakout | `pct_above_sma50` | `version` |
|---|---|---|---|
| `bk50d_s20_v2.0` | 50d high | >= 20% | 2.0 |
| `bk50d_s16_v2.0` | 50d high | >= 16% | 2.0 |
| `bk50d_s12_v2.0` | 50d high | >= 12% | 2.0 |

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

---

## Step 3 — Evaluation Methodology

- **Burn-in period**: the 730 calendar days before the evaluation window. Used only for indicator warm-up; no signals are evaluated in it. The 30-day cooldown chain does run across it, so a trigger just before the window opens correctly suppresses an early in-window one.
- **Evaluation period**: the window itself. All entry signals and forward returns computed here.

Three windows are run, each written to its own result file:

| Window | Result file |
|---|---|
| 2021-01-01 – 2025-12-31 (baseline) | `docs/research/result-qullamaggie-backtest-v4.md` |
| 2010-01-01 – 2015-12-31 | `docs/research/result-qullamaggie-backtest-v4-2010-2015.md` |
| 2016-01-01 – 2020-12-31 | `docs/research/result-qullamaggie-backtest-v4-2016-2020.md` |

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
- **Mean return** (reported as `Mean%`): the **annualized** mean return — a CAGR-style annualization of
  the arithmetic per-trade mean. With a single 366d hold it is near-identical to the raw mean; the
  annualized form is the one reported so figures stay comparable with studies run at other holding
  periods, and the raw mean is not reported separately
  - `mean = (1 / N) × Σ rᵢ`, then `Mean% = (1 + mean)^(annualization_factor) − 1`
- **Sortino ratio**: annualized per-trade Sortino (MAR = 0%):
  - `downside_dev = sqrt(mean(min(rᵢ, 0)²))`  — RMS of negative returns (positives count as 0)
  - `sortino = mean(R) × sqrt(annualization_factor) / downside_dev`
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

---

## Step 6 — Output Format

Report **one ranking table** carrying both ranking treatments, distinguished by a `Gate` column. Each
algorithm appears twice on adjacent rows, so the pair reads across rather than across two separate
tables:

1. **`R>=40`** — a trade is taken only if its `QullamaggieRanking` score is ≥ R.
2. **`ungated`** — every entry signal that meets the entering condition is taken as a trade.

Output order: algorithm (bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0) and then Gated (ungated, R >= 40)

```text
Entry Signal     | Gate    | N    | Win% | Mean Ret | Median Ret | Profit Factor | Sortino | CVaR(95%) | Freq/mo |
-----------------|---------|------|------|----------|------------|---------------|---------|-----------|---------|
bk50d_s20_v2.0   | ungated |  520 |  65% |  +56.2%  |   +26.4%   |     7.1       |   2.94  |   -60.1%  |   7.8   |
bk50d_s20_v2.0   | R>=40   |  379 |  65% |  +58.5%  |   +27.8%   |     6.9       |   2.85  |   -64.2%  |   5.7   |
bk50d_s16_v2.0   | ungated | ...
```

### Monthly Mean% / N grid

Below the ranking table, report one monthly grid — **`bk50d_s12_v2.0 R>=40` only**, the reference
algorithm. A grid per combination would be six tables, and the other five are read off the ranking
table instead.

Rows are the entry year, columns the entry month. Each cell is `Mean%|N`: the mean 366-day return of
the trades *entered* in that calendar month, and how many there were. `·` marks a month with no
entries. The right-hand pair is the year's own aggregate across all its months — computed from that
year's trades, not as the mean of the twelve cells, so months with different trade counts are weighted
correctly.

**Pad the two halves of a cell independently**: the mean right-aligned in 6 characters, then `|`,
then the count left-aligned in 3. Right-aligning the joined `Mean%|N` string instead lets the `|`
drift with each cell's width, so the means no longer line up down a column and the grid cannot be
scanned vertically — which is the only reason to lay it out as a grid. The month name is
right-aligned over the mean field, and `·` sits in the same column, so an empty month reads as a gap
in the numbers rather than a shifted cell.

```text
 Year |    Jan        Feb        Mar        Apr   ...        Dec     |   Mean%     N
-------------------------------------------------------------------------------------
 2021 |  +67.7|39   +51.0|26    -4.1|2    +11.8|5 ...          ·     |  +55.4%    98
 2022 |  +14.1|2    +42.7|7     -3.7|21   +20.3|10...   +14.6|39     |  +13.0%    79
```

### History of changes

Every new run adds a row per window to this table if the outcome is different. The row is always
the reference algorithm — `bk50d_s12_v2.0` gated at `R>=40`, period 2021-2025 — read straight off that window's
result file.

This is a hand-maintained log, not script output: the script must not write into this file
Every new run should print latest run output to screen where it can be copy-pasted

```text
Execution              N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo  Comment
2026-08-02 17:37:48  531   63.8   +51.23   +23.11   5.95    2.466   -63.78    9.0  avg_vol >= 500K
2026-08-02 18:14:46  676   63.8   +53.12   +22.21   6.02    2.519   -64.97   11.5  avg_vol >= 100K; pct_vs_sma50 >= X (was >)
```

---

## Constraints & Caveats

- **Survivorship bias**: only use tickers present in the DB at the *entry* date, not just tickers that survived to today (market cap is exception as it changes slowly in time)
- **Look-ahead bias**: all signals must be computable from data available on the signal date only; the entry price is the *next* day's open, which is deliberately not knowable when the signal fires

## Implementation

- create/overwrite script scripts/qullamaggie-backtest-v4.py
- the evaluation window and output path are CLI arguments (`--start-date`, `--end-date`, `--output`), defaulting to the baseline window and `docs/research/result-qullamaggie-backtest-v4.md`; run it once per window in the Step 3 table, overwriting existing result files
- always update ## Configuration values to reflect latest setup
- add your findings and ideas how to improve the algorithm to end of each result file, each improvement on a separate line in the list
