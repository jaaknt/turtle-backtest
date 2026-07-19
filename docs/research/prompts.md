# Qullamaggie Research Prompts

Reusable prompts that drove the Qullamaggie v4 backtest research. Each prompt maps to a script in `scripts/` and (usually) a result doc in `docs/research/`. Grouped in pipeline order: validate the backtest first, study individual filters, then relax filters, rank, simulate the portfolio, and finally generate live signals.

Common references for most prompts: `docs/research/qullamaggie-backtest-v4.md` (methodology) and `docs/research/result-qullamaggie-backtest-v4.md` (baseline results).

## Index

| Prompt | Script | Results |
| -------- | -------- | --------- |
| [Validate & run backtest v4](#validate--run-backtest-v4) | `scripts/qullamaggie-backtest-v4.py` | `result-qullamaggie-backtest-v4.md` |
| [Long-term monthly analysis](#long-term-monthly-analysis) | `scripts/qullamaggie-longterm-monthly.py` | `result-qullamaggie-longterm-monthly.md` |
| [ROC 12m cohorts](#roc-12m-cohorts) | `scripts/qullamaggie-cohorts-roc.py` | `result-qullamaggie-cohorts-roc.md` |
| [ADR% cohorts](#adr-cohorts) | `scripts/qullamaggie-cohorts-adr.py` | `result-qullamaggie-cohorts-adr.md` |
| [ADR compression cohorts](#adr-compression-cohorts) | `scripts/qullamaggie-cohorts-adr-compression.py` | `result-qullamaggie-cohorts-adr-compression.md` |
| [RSI(14) cohorts](#rsi14-cohorts) | `scripts/qullamaggie-cohorts-rsi.py` | `result-qullamaggie-cohorts-rsi.md` |
| [Entry price cohorts](#entry-price-cohorts) | `scripts/qullamaggie-cohorts-price.py` | `result-qullamaggie-cohorts-price.md` |
| [Volume surge cohorts](#volume-surge-cohorts) | `scripts/qullamaggie-cohorts-volsurge.py` | `result-qullamaggie-cohorts-volsurge.md` |
| [Tight range cohorts](#tight-range-cohorts) | `scripts/qullamaggie-cohorts-tightrange.py` | `result-qullamaggie-cohorts-tightrange.md` |
| [Limit-order entry cohorts](#limit-order-entry-cohorts) | `scripts/qullamaggie-cohorts-limit-order.py` | `result-qullamaggie-cohorts-limit-order.md` |
| [Limit-order fill rate](#limit-order-fill-rate) | `scripts/qullamaggie-limit-fill-rate.py` | `result-qullamaggie-limit-fill-rate.md` |
| [Relaxation brainstorm (s15)](#relaxation-brainstorm-s15) | — | — |
| [Relaxation sweep (s20)](#relaxation-sweep-s20) | `scripts/qullamaggie-relax-sweep.py` | `result-qullamaggie-relax-sweep.md` |
| [Ranking algorithm proposal](#ranking-algorithm-proposal) | — | `result-qullamaggie-ranking.md` |
| [Dynamic cohort ranking (s15)](#dynamic-cohort-ranking-s15) | `scripts/qullamaggie-cohort-ranking.py` | `result-qullamaggie-cohort-ranking.md` |
| [Portfolio simulation](#portfolio-simulation) | `scripts/qullamaggie-portfolio-sim.py` | `result-qullamaggie-portfolio-v4.md` |
| [Signals: s12 with overlap & cohorts](#signals-s12-with-overlap--cohorts) | `scripts/qullamaggie-signals-v4.py` | screen |
| [Trades: s20 open-trade performance](#trades-s20-open-trade-performance) | `scripts/qullamaggie-trades-v4.py` | `result-qullamaggie-trades-v4.md` |
| [Maintenance: lint & tests](#maintenance-lint--tests) | — | — |

## Backtest foundation

### Validate & run backtest v4

**Goal:** Verify methodology doc and implementation agree, then produce the baseline results.

- Validate that `docs/research/qullamaggie-backtest-v4.md` and `scripts/qullamaggie-backtest-v4.py` are consistent.
- Run the backtest described in `docs/research/qullamaggie-backtest-v4.md`.

### Long-term monthly analysis

**Goal:** Analyze `bk50d_s12_v1.2_roc100-366d`, `bk50d_s15_v1.2_roc100-366d`, `bk50d_s17_v1.2_roc100-366d`, `bk50d_s20_v1.2_roc100-366d` over the long term; provide monthly Mean% and trade counts by year, plus general findings and pros/cons of the different algorithms.

- **Period:** 2007-01-01 : 2026-06-26
- **Output format** (monthly matrix, years as rows):

  ```text
   Year |    Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec |   Mean%    N
  ------------------------------------------------------------------------------------------------------------
   2007 |  +22.3   -4.5      ·      ·  +46.4      ·      ·  -31.4  -28.6  -39.1      ·      · |    -4.4   10
   2008 |      ·      ·      ·      ·      ·  +24.8  +19.7   +9.3  +32.2  +37.2   +1.7  +23.5 |   +20.3   61
   ...
  ```

- **Output format** (yearly summary):

  ```text
   Year     N   Win%   Mean%    Med%  Sortino  CVaR95%
  ----------------------------------------------------
   2007    10   40.0   -4.45   -5.48   -0.093   -80.13
   2008    61   73.8  +20.26  +17.01    0.977   -33.40
   ...
  ```

- **Script:** `scripts/qullamaggie-longterm-monthly.py`
- **Results:** `docs/research/result-qullamaggie-longterm-monthly.md`
- **Note:** script uses ADR>=2.5% (looser than the v4 canonical 3.0%); no tight_range.

## Filter cohort studies

All cohort studies below share the same setup unless stated otherwise:

- **Algorithms:** `bk50d_s20_v1.2_roc100-366d`, `bk50d_s15_v1.2_roc100-366d`, `bk50d_s12_v1.2_roc100-366d`
- **Period:** 2015-01-01 : 2026-06-26
- **Output columns:** `Cohort  N  Med%  Mean%  Win%  Sortino  PF`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`

### ROC 12m cohorts

**Goal:** How `roc_12m_cap` (`close / close[-252] − 1 < 100%`) affects performance.

- **Cohorts:** (<-20), [-20-0), [0-20), [20-40), [40-60), [60-80), [80-100), [100-120), [120-140), [140-160), (>160)
- **Script:** `scripts/qullamaggie-cohorts-roc.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-roc.md`

### ADR% cohorts

**Goal:** How `adr_pct` (`mean((high_i − low_i)/low_i, i in last 20 days, shift-1)`) affects performance.

- **Cohorts:** [0-1.0), [1.0-2.0), [2.0-2.5), [2.5-3.0), [3.0-3.5), [3.5-4.0), [4.0-4.5), [4.5-5.0), [5.0-7.0), (>8.0)
- **Script:** `scripts/qullamaggie-cohorts-adr.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-adr.md`
- **Note:** the script was recreated 2026-07-16 with the standardized v1.2 filters (vol_dry_up<90%, no tight_range); an earlier run with tr20 variants and vol_dry_up<80% had overwritten it with the ROC study, which now lives in `scripts/qullamaggie-cohorts-roc.py`.

### ADR compression cohorts

**Goal:** How ADR compression before the breakout affects results.

- **Metric:** `ADR%(N) = mean((high − low) / low)` over previous N days × 100 (exclude current day); `compression = ADR%(10) / ADR%(50)`
- **Cohorts:** (<0.5), [0.5-0.7), [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.3), (>1.3)
- **Script:** `scripts/qullamaggie-cohorts-adr-compression.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-adr-compression.md`

### RSI(14) cohorts

**Goal:** How `rsi_filter` (`RSI(14)` on entry) affects performance.

- **Cohorts:** [0-20), [20-40), [40-60), [40-50), [50-60), [60-70), [70-75), [75-80), [80-90), [90-100]
- **Script:** `scripts/qullamaggie-cohorts-rsi.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-rsi.md`

### Entry price cohorts

**Goal:** How the close price on entry affects results.

- **Cohorts:** [0-5), [5-10), [10-20), [20-50), [50-100), [100-250), [250-700), [700-2000), (>2000)
- **Script:** `scripts/qullamaggie-cohorts-price.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-price.md`

### Volume surge cohorts

**Goal:** How `vol_surge_ratio = volume / mean(volume[-51:-1])` affects results.

- **Cohorts:** (<0.7), [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.1), [1.1-1.2), [1.2-1.3), [1.3-1.4), [1.4-1.6), [1.6-2.0), [2.0-3.0), [3.0-4.0), [4.0-6.0), (>6.0)
- **Script:** `scripts/qullamaggie-cohorts-volsurge.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-volsurge.md`

### Tight range cohorts

**Goal:** How `tight_range2` (`(max(close[-11:-1]) − min(close[-11:-1])) / mean(close[-11:-1]) < Y`) affects results.

- **Algorithms:** `bk50d_s12_v1.2_roc100-366d`, `bk50d_s15_v1.2_roc100-366d`, `bk50d_s17_v1.2_roc100-366d`, `bk50d_s20_v1.2_roc100-366d`
- **Cohorts:** (<0), [0.0-0.1), [0.1-0.15), [0.15-0.2), [0.2-0.25), [0.25-0.3), (>0.3)
- **Script:** `scripts/qullamaggie-cohorts-tightrange.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-tightrange.md`
- **Note:** implemented as s20_tr10, s20_tr20, s15_tr15 variants (not s12/s17).

### SMA(200) analyze

**Goal:** How `signal above sma(200)` (`SMA(200)` on entry) affects performance.

- **Output:** setup is the same as for cohort analyze
- **Script:** `scripts/qullamaggie-sma200.py`updat
- **Results:** `docs/research/result-qullamaggie-sma200.md`

### Sector analyze

**Goal:** How company `sector` affects performance.

- **Cohorts:** different company sectors
- **Script:** `scripts/qullamaggie-cohorts-sector.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-sector.md`

## Entry-timing / limit-order studies

### Limit-order entry cohorts

**Goal:** How buying on the next day with a limit order (limit price = previous day closing price − X%) affects results.

- **Algorithms:** `bk50d_s20_v1.2_roc100-366d`, `bk50d_s15_v1.2_roc100-366d`, `bk50d_s12_v1.2_roc100-366d`
- **X%:** 0%, 1%, 2%, 3%, 4%, 5%; limit order is effective during the next 30 days.
- **Period:** 2010-01-01 : 2026-06-26
- **Output columns:** `Cohort  N  Med%  Mean%  Win%  Sortino  PF`
- Additionally provide monthly Mean% and trade count by months/years for bk50d_s20 eod, bk50d_s15 eod, bk50d_s12 eod:

  ```text
   Year |    Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec |   Mean%    N
  ------------------------------------------------------------------------------------------------------------
   2010 |  +22.3|2   -4.5|1      ·      ·  +46.4|5      ·      ·  -31.4|2  -28.6|4  -39.1|2      ·      · |    -4.4|3   19
  ```

- **Script:** `scripts/qullamaggie-cohorts-limit-order.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-limit-order.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`
- **Note:** vol_dry_up<90%, no tight_range (standardized 2026-07-15); saved results were generated earlier with tr20 variants and vol_dry_up<80%.

### Limit-order fill rate

**Goal:** Calculate `bk50d_s12_v1.2_roc100` signals, then figure out the percentage of signals where the price drops X% during the next Y days so that a resting limit order would be filled.

- **Filters:** same as `scripts/qullamaggie-signals-v4.py` (RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, no tight_range, cooldown 30d, mcap>=1.5B excl Comm/RE)
- **Limit order price:** signal-day close × (1 − X%), X = 0%, 1%, 2%, 3%, 4%, 5%
- **Window:** order effective for Y calendar days after the signal day, Y = 30, 60, 90
- **Fill rule:** order is eligible from the day after the signal; fills on the first trading day whose low <= limit price, else expires unfilled (adjusted prices, same convention as `scripts/qullamaggie-cohorts-limit-order.py`)
- **Period:** 2010-06-01 : today
- **Output format:**

  ```text
    X%  |        Y=30d         |        Y=60d         |        Y=90d
        |  Fill%   MedD  MeanD |  Fill%   MedD  MeanD |  Fill%   MedD  MeanD
  ```

  MedD/MeanD = median/mean trading days from signal to fill, filled orders only. Report also total signal count N and n_filled per cell.

- **Script:** `scripts/qullamaggie-limit-fill-rate.py` (created new)
- **Results:** `docs/research/result-qullamaggie-limit-fill-rate.md`
- **References:** `scripts/qullamaggie-signals-v4.py`, `scripts/qullamaggie-cohorts-limit-order.py`, `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`

## Filter relaxation

### Relaxation brainstorm (s15)

**Goal:** Analyze `bk50d_s15_v1.2_roc100` 366d results in period 2001-01-01 : 2026-06-26.

- Propose 5 options how to achieve ~3 signals per month.
- Important: Med% and Sortino must stay on the same level.
- The main idea is to loosen currently applied filters — which filter conditions can be loosened with the least impact on Mean% and Sortino?

### Relaxation sweep (s20)

**Goal:** Increase signals per month (F/mo) for `bk50d_s20_v1.2_roc100-366d` without degrading Sortino and Mean%.

- **Baseline** (2021-01-01 : 2026-07-05, unconstrained): N=243, F/mo=3.7, Win%=67.1, Mean%=+52.50, Med%=+22.32, Sortino=2.864, MaxDD%=39.71
- Propose 5 ideas how to loosen currently applied filters or expand the universe.
- Prefer relaxations where existing cohort studies show the excluded region performs at or above the included pool.
- For each idea run the modified variant (change ONE dimension at a time, all other filters unchanged) over 2015-01-01 : 2026-06-26, hold 366d, and report:

  ```text
  Variant                              N   F/mo   Win%    Mean%    Med%   Sortino      PF   MaxDD%
  ```

- Also run baseline + the best 2-3 ideas combined.
- **Fixed filters reference:** vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, mcap>=1.5B excl Comm/RE
- Important: Sortino and Mean% must stay on the same level as baseline; reject ideas that trade quality for count.
- Share your findings: which single relaxation has the best F/mo gain per unit of Sortino given up.
- **Script:** `scripts/qullamaggie-backtest-v4.py` (new: `scripts/qullamaggie-relax-sweep.py`)
- **Results:** `docs/research/result-qullamaggie-relax-sweep.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-cohorts-tightrange.md`, `docs/research/result-qullamaggie-cohorts-price.md`

## Ranking

### Ranking algorithm proposal

**Goal:** Propose a ranking algorithm for s15_tr15 trades that selects only the trades with the most potential based on technical data (higher ADR, (SMA10, SMA20), your own discoveries).

### Dynamic cohort ranking (s15)

**Goal:** Build a dynamic ranking score for `bk50d_s15_v1.2_roc100` signals that estimates the probability the signal will succeed (trade return > 0 at the 366d exit), derived from the per-dimension cohort statistics of the existing cohort studies.

- **Dimensions** (all computed on the entry date, definitions identical to the cohort scripts): `adr_pct` (ADR% cohorts), `adr_pct_change` = ADR%(10)/ADR%(50) (compression cohorts), `rsi14` (RSI cohorts), entry close price (price cohorts), `vol_surge_ratio` (volsurge cohorts), `roc_252d` (ROC cohorts). Reuse each study's cohort boundaries.
- **Per-dimension probability:** the Win% of the signal's cohort, computed **walk-forward** — from s15 trades whose 366d hold completed before the signal date (expanding window; no look-ahead). Shrink small cohorts toward the running pool win rate: `p̂ = (wins + k·p₀) / (n + k)` with `k = 20`.
- **Composite score:** average the per-dimension log-odds and convert back: `P = σ( mean_d( ln(p̂_d / (1 − p̂_d)) ) )`. Report the score as a probability in [0, 1].
- **Warm-up:** scoring starts once ≥ 300 completed trades exist (~2017); earlier signals are excluded from validation.
- **Validation:** rank all scored signals by P and split into deciles; report per decile:

  ```text
  Decile   PredP%      N     Med%    Mean%    Win%   Sortino      PF
  ```

  - `PredP%` = mean predicted probability in the decile; compare with realized Win% (calibration).
  - Check the Win%/Mean%/Sortino gradient is monotonic from D1 (lowest score) to D10 (highest).

- **Period:** 2015-01-01 : 2026-06-26, hold 366d, all standardized v1.2 filters (vol_dry_up<90%, no tight_range).
- **Script:** `scripts/qullamaggie-cohort-ranking.py` (create new; reuse the shared harness of the cohort scripts)
- **Results:** `docs/research/result-qullamaggie-cohort-ranking.md`
- **Note:** implementation adds a second, regime-neutral decile table (score minus running pool log-odds) because the raw walk-forward P proved anti-calibrated — dominated by pool-win-rate time drift; see Findings in the result doc. RSI uses the fine partition ([40-50), [50-60)) so bins are disjoint; values in cohort gaps (e.g. ADR [7-8)) fall back to the pool win rate via n=0 shrinkage.
- **Important files:** `scripts/qullamaggie-cohorts-adr.py`, `scripts/qullamaggie-cohorts-roc.py`, `docs/research/result-qullamaggie-cohorts-adr.md`, `docs/research/result-qullamaggie-cohorts-adr-compression.md`, `docs/research/result-qullamaggie-cohorts-rsi.md`, `docs/research/result-qullamaggie-cohorts-price.md`, `docs/research/result-qullamaggie-cohorts-volsurge.md`, `docs/research/result-qullamaggie-cohorts-roc.md`, `docs/research/qullamaggie-backtest-v4.md`

## Portfolio simulation

**Goal:** Portfolio simulation over `bk50d_s20_v1.2_roc100-366d`, `bk50d_s15_v1.2_roc100-366d`, `bk50d_s12_v1.2_roc100-366d` signals.

- **Period:** 2020-01-01 : 2026-06-26
- **Initial portfolio:** $30,000
- **Position sizing:** invest {3%, 4%, 5%, 6%, 7%, 8%} of portfolio at a time per trade; if there is no liquidity, skip the trade.
- **Output format:**

  ```text
  size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
  --------------------------------------------------------------------------
  3%         145,397  +20.44   -30.34   0.674    0.885    261    977   14.4%
  4%         162,566  +22.04   -29.08   0.758    0.938    198   1040   13.5%
  5%         187,419  +24.10   -28.07   0.859    0.977    160   1078   11.8%
  ```

- For the top 5 algorithms by `Calmar` and by `Final$`, print `monthly returns` and `trades count in particular month` by years (years are rows, months are columns):

  ```text
   Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
  -----------------------------------------------------------------------------------------------------------------------------------------------
   2010 |    -3.2|7    +3.8|1    +2.6|1    -0.4|2    -2.4|0    -3.9|0    +2.9|0    -3.1|4    +5.5|2    +1.0|2    -0.3|2    +8.3|6 |   +10.5    27
  ```

- Provide a comparison with an alternative approach where a limit order is added to buy the stock 3% below closing price during the next 30 days (instead of buying on closing price).
- Add your findings on how to improve the portfolio performance (Mean%, Sortino, Calmar).
- **Deferred/considered ideas** (commented out in the original prompt):
  - Prefer always bk50d_s20_tr10_v1.2_roc100 signals, but if there is liquidity use bk50d_s15_tr15_v1.2_roc100 signals to reduce uninvested amounts.
  - Implement rank-based funding to choose the trade if several trades are available on the same day.
  - Sell the position if the stock closes below the 200-day SMA for 3 consecutive trades.
- **Script:** `scripts/qullamaggie-portfolio-sim.py`
- **Results:** `docs/research/result-qullamaggie-portfolio-v4.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`

## Live signal generation

### Signals: s12 with overlap & cohorts

**Goal:** Provide `bk50d_s12_v1.2_roc100` signals for period 2026-06-01 : today; mark signals that are also in `bk50d_s20_v1.2_roc100` and `bk50d_s15_v1.2_roc100`.

- **Output columns:**

  ```text
  Date │ Symbol │ Entry $ │ Curr Price │ 0.97*Entry Price │ Change % │ %abv SMA50 │ ADR% │ ADR_CHG │ RSI14 │ TR% │ ROC252% │ In s15? │ In s20? │ 0.97*Entry Price reached? │ Last date
  ```

  - `%abv SMA50`, `ADR%`, `RSI14`, `TR%`, `ROC252%` must be calculated on the entry date.
  - `Last date` = latest date when stock data is available in the `turtle.daily_bars` table.

- Report also the share of signals where the 0.97*Entry price was reached: `reached/total (Reached%)` in the summary line.
- Write also a separate table with aggregated results where `%abv SMA50` is in cohorts [12-15), [15-17.5), [17.5-20), (>20):

  ```text
  Cohort | N | Med% | Mean% | Win% | PF | Sortino | Max DD
  ```

- Compare also mean(Mean%) with SPY.US and QQQ.US return for the whole period. Exclude LC.US and other suspicious data points.
- **Script:** `scripts/qullamaggie-signals-v4.py`
- **Output:** screen
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `scripts/qullamaggie-backtest-v4.py`

### Trades: s20 open-trade performance

**Goal:** Provide `bk50d_s20_v1.2_roc100` signals for period 2025-07-01 : today.

- **Output columns:**

  ```text
  Date │ Symbol │ Entry $ │ Curr Price │ Change in % │ %abv SMA50 │ ADR% │ ADR_CHANGE │ RSI14 │ TR% │ ROC252%
  ```

  - `%abv SMA50`, `ADR%`, `RSI14`, `TR%`, `ROC252%` must be calculated on the entry date.
  - Add also the latest date when stock data is available.

- Provide mean trade performance and trade count if all trades are closed on the last date.
- **Script:** `scripts/qullamaggie-trades-v4.py`
- **Results:** `docs/research/result-qullamaggie-trades-v4.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`
- **Note:** implemented as bk50d_s20_v1.2_roc100 (vol_dry_up<90%, no tight_range — TR% shown for information only).

## Maintenance

### Maintenance: lint & tests

Run Ruff + mypy + pytest.
