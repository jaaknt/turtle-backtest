# Qullamaggie Research Prompts

Reusable prompts that drove the Qullamaggie v4 backtest research. Each prompt maps to a script in `scripts/` and (usually) a result doc in `docs/research/`. Grouped in pipeline order: validate the backtest first, study individual filters, then relax filters, rank, simulate the portfolio, and finally generate live signals.

Common references for most prompts: `docs/research/qullamaggie-backtest-v4.md` (methodology) and `docs/research/result-qullamaggie-backtest-v4.md` (baseline results).

**Standard algorithm set.** Unless a prompt says otherwise, "the algorithms" means `bk50d_s20_v2.0`, `bk50d_s16_v2.0` and `bk50d_s12_v2.0` — a 50-day breakout sitting more than 20% / 16% / 12% above the 50-day SMA, entered at the next trading day's split/dividend-adjusted open, held 366 calendar days, with the `QullamaggieRanking` gate `MIN_RANKING >= 40` applied. The naming convention is defined in `docs/research/qullamaggie-backtest-v4.md` (Step 1, "Algorithm naming"). Earlier runs used `_v1.3_roc100` labels and an s15/s17 pair instead of s16; where a **Note** records what a past run actually did, the original name is kept deliberately rather than rewritten.

## Index

| Prompt | Script | Results |
| -------- | -------- | --------- |
| [Validate & run backtest v4](#validate--run-backtest-v4) | `scripts/qullamaggie-backtest-v4.py` | `result-qullamaggie-backtest-v4.md`, `-2010-2015.md`, `-2016-2020.md` |
| [Long-term monthly analysis](#long-term-monthly-analysis) | `scripts/qullamaggie-longterm-monthly.py` | `result-qullamaggie-longterm-monthly.md` |
| [ROC 12m cohorts](#roc-12m-cohorts) | `scripts/qullamaggie-cohorts-roc.py` | `result-qullamaggie-cohorts-roc.md` |
| [ADR% cohorts](#adr-cohorts) | `scripts/qullamaggie-cohorts-adr.py` | `result-qullamaggie-cohorts-adr.md` |
| [ADR compression cohorts](#adr-compression-cohorts) | `scripts/qullamaggie-cohorts-adr-compression.py` | `result-qullamaggie-cohorts-adr-compression.md` |
| [RSI(14) cohorts](#rsi14-cohorts) | `scripts/qullamaggie-cohorts-rsi.py` | `result-qullamaggie-cohorts-rsi.md` |
| [Entry price cohorts](#entry-price-cohorts) | `scripts/qullamaggie-cohorts-price.py` | `result-qullamaggie-cohorts-price.md` |
| [Volume surge cohorts](#volume-surge-cohorts) | `scripts/qullamaggie-cohorts-vol-surge.py` | `result-qullamaggie-cohorts-vol-surge.md` |
| [Vol dry-up cohorts](#vol-dry-up-cohorts) | `scripts/qullamaggie-cohorts-vol-dry-up.py` | `result-qullamaggie-cohorts-vol-dry-up.md` |
| [Tight range cohorts](#tight-range-cohorts) | `scripts/qullamaggie-cohorts-tightrange.py` | `result-qullamaggie-cohorts-tightrange.md` |
| [pct-above-sma50 cohorts](#pct-above-sma50-cohorts) | `scripts/qullamaggie-cohorts-pct-above-sma50.py` | `result-qullamaggie-cohorts-pct-above-sma50.md` |
| [SMA(200) cohorts](#sma200-cohorts) | `scripts/qullamaggie-cohorts-sma200.py` | `result-qullamaggie-cohorts-sma200.md` |
| [Sector cohorts](#sector-cohorts) | `scripts/qullamaggie-cohorts-sector.py` | `result-qullamaggie-cohorts-sector.md` |
| [Ranking cohorts](#ranking-cohorts) | `scripts/qullamaggie-cohorts-ranking.py` | `result-qullamaggie-cohorts-ranking.md` |
| [Limit-order entry cohorts](#limit-order-entry-cohorts) | `scripts/qullamaggie-cohorts-limit-order.py` | `result-qullamaggie-cohorts-limit-order.md` |
| [Limit-order fill rate](#limit-order-fill-rate) | `scripts/qullamaggie-limit-fill-rate.py` | `result-qullamaggie-limit-fill-rate.md` |
| [Relaxation brainstorm (s15)](#relaxation-brainstorm-s15) | — | — |
| [Relaxation sweep (s20)](#relaxation-sweep-s20) | `scripts/qullamaggie-relax-sweep.py` | `result-qullamaggie-relax-sweep.md` |
| [Ranking algorithm proposal](#ranking-algorithm-proposal) | — | — |
| [Recalibrate ranking weights + validate](#recalibrate-ranking-weights--validate) | `scripts/qullamaggie-ranking-validation.py` | `result-qullamaggie-ranking-validation.md` |
| [Three-feature ranking weights](#three-feature-ranking-weights) | `scripts/qullamaggie-ranking-weights.py` | `result-qullamaggie-ranking-weights.md` |
| [Portfolio simulation](#portfolio-simulation) | `scripts/qullamaggie-portfolio-sim.py` | `result-qullamaggie-portfolio-v4.md`, `-2010-2015.md`, `-2016-2020.md` |
| [Exit strategy analyze](#exit-strategy-analyze) | `scripts/qullamaggie-exit-sweep.py` | `result-qullamaggie-exit-sweep.md` |
| [Signals: s12 with overlap & cohorts](#signals-s12-with-overlap--cohorts) | `scripts/qullamaggie-signals-v4.py` | screen |
| [Trades: s12 open-trade performance](#trades-s12-open-trade-performance) | `scripts/qullamaggie-trades-v4.py` | `result-qullamaggie-trades-v4.md` |
| [Maintenance: lint & tests](#maintenance-lint--tests) | — | — |

## Backtest foundation

### Validate & run backtest v4

**Goal:** Verify methodology doc and implementation agree, then produce the baseline results.

- Validate that `docs/research/qullamaggie-backtest-v4.md` and `scripts/qullamaggie-backtest-v4.py` are consistent.
- Run the backtest described in `docs/research/qullamaggie-backtest-v4.md`.
- **Results:** `docs/research/result-qullamaggie-backtest-v4.md` (2021-2026 baseline) and
  `docs/research/result-qullamaggie-backtest-v4-2010-2015.md` (2010-2015 period) and
  `docs/research/result-qullamaggie-backtest-v4-2016-2020.md` (2016-2020 period).
- **Scripts:**
  `uv run scripts/qullamaggie-backtest-v4.py --start-date 2010-01-01 --end-date 2015-12-31 --output docs/research/result-qullamaggie-backtest-v4-2010-2015.md`
  `uv run scripts/qullamaggie-backtest-v4.py --start-date 2016-01-01 --end-date 2020-12-31 --output docs/research/result-qullamaggie-backtest-v4-2016-2020.md`
  `uv run scripts/qullamaggie-backtest-v4.py --start-date 2021-01-01                       --output docs/research/result-qullamaggie-backtest-v4.md`

### Long-term monthly analysis

**Goal:** Analyze `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold, `MIN_RANKING >= 40`) over the long term; provide monthly Mean% and trade counts by year, plus general findings and pros/cons of the different algorithms.

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
   Year     N   Win%   Mean% QQQ%   SPY%   Med%  Sortino  CVaR95%
  ----------------------------------------------------------------
   2007    10   40.0   -4.45 +20.1  +10.1 -5.48   -0.093   -80.13
   2008    61   73.8  +20.26 +20.1  +10.1 +17.01   0.977   -33.40
   ...
  ```

- **Script:** `scripts/qullamaggie-longterm-monthly.py`
- **Results:** `docs/research/result-qullamaggie-longterm-monthly.md`
- **Note:** script must follow algorithm parameters in `docs/research/qullamaggie-backtest-v4.md`.
- **Note — the saved results predate the migration.** The script is on the shared signal layer (v2.0 labels,
  next-day adjusted-open entry, `MIN_RANKING >= 40`), but the committed doc is the 2026-07-22 run: four
  `_v1.3_roc100` sections (s12/s15/s17/s20), same-day close entry and no ranking gate. Its monthly grids are
  therefore pre-gate and not comparable with the current standard set until the script is re-run.

## Filter cohort studies

All cohort studies below share the same setup unless stated otherwise:

- **Algorithms:** `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold)
- **Ranking gate:** `MIN_RANKING >= 40`, **except** the four studies whose cohort variable is the
  `QullamaggieRanking` score or one of its three dimensions — ADR% (40 pts), pct-above-sma50 (35 pts), entry
  price (25 pts) and the ranking itself. Those run **ungated**, because a >=40 gate filters on the very variable
  being cohorted and empties the cohorts the study exists to measure (a gated ADR run collapsed `[0-1.0)` to
  N=1). Each of the four records the reason in its docstring; the ranking study additionally reports the `>=40`
  population as a reference row, so what the gate would keep can still be read off.
- **Period:** 2015-01-01 : 2026-06-26 — longer than the `backtest-v4` baseline window on purpose, so individual
  cohorts still carry enough trades to read
- **Output columns:** `Cohort  N  Med%  Mean%  Win%  Sortino  PF  CVaR95%`
- **Header:** `All filter conditions from algorithm`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`

### ROC 12m cohorts

**Goal:** How `roc_12m_cap` (`close / close[-252] − 1 < 100%`) affects performance.

- **Cohorts:** (<-20), [-20-0), [0-20), [20-40), [40-60), [60-80), [80-100), [100-120), [120-140), [140-160), (>160)
- **Filter under study is dropped:** the `roc_12m < 100%` cap is removed, otherwise every cohort from `[100-120)`
  up would be empty. It returns as the `<100% (cap)` reference row at the foot of each table.
- **Script:** `scripts/qullamaggie-cohorts-roc.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-roc.md`

### ADR% cohorts

**Goal:** How `adr_pct` (`mean((high_i − low_i)/low_i, i in last 20 days, shift-1)`) affects performance.

- **Cohorts:** [0-1.0), [1.0-2.0), [2.0-2.5), [2.5-3.0), [3.0-3.5), [3.5-4.0), [4.0-4.5), [4.5-5.0), [5.0-7.0), [7.0-8.0), (>8.0)
- **Filter under study is dropped:** the `adr_pct >= 3.0%` floor is removed, otherwise the four sub-3% cohorts
  would be empty. It returns as the `>=3% (min)` reference row at the foot of each table.
- **Script:** `scripts/qullamaggie-cohorts-adr.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-adr.md`
- **Note:** the script was recreated 2026-07-16 with the standardized v1.2 filters (vol_dry_up<90%, no tight_range); an earlier run with tr20 variants and vol_dry_up<80% had overwritten it with the ROC study, which now lives in `scripts/qullamaggie-cohorts-roc.py`.

### ADR compression cohorts

**Goal:** How ADR compression before the breakout affects results.

- **Metric:** `ADR%(N) = mean((high − low) / low)` over previous N days × 100 (exclude current day); `compression = ADR%(10) / ADR%(50)`
- **Cohorts:** (<0.5), [0.5-0.7), [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.3), (>1.3)
- **Filter under study is dropped:** the production `ADR_change < 90%` cap *is* a cap on this ratio, so it is
  removed, otherwise everything from `[0.9-1.0)` up would be empty. It returns as the `<0.9 (cap)` reference row
  at the foot of each table.
- **Script:** `scripts/qullamaggie-cohorts-adr-compression.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-adr-compression.md`

### RSI(14) cohorts

**Goal:** How `rsi_filter` (`RSI(14)` on the signal date) affects performance.

- **Cohorts:** [0-20), [20-40), [40-60), [40-50), [50-60), [60-70), [70-75), [75-80), [80-90), [90-100]
- **Filter under study is dropped:** the `RSI(14) < 70` cap is removed, otherwise the `[70-75)` through
  `[90-100]` cohorts would be empty. It returns as the `<70` reference row at the foot of each table.
- **Script:** `scripts/qullamaggie-cohorts-rsi.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-rsi.md`

### Entry price cohorts

**Goal:** How the close price on the signal date affects results.

- **Cohorts:** [0-5), [5-10), [10-20), [20-50), [50-100), [100-250), [250-700), [700-2000), (>2000)
- **Filter under study is dropped:** the `close > $5 & < $250` band is removed, otherwise `[0-5)` and everything
  from `[250-700)` up would be empty. It returns as the `$5-$250 (cap)` reference row at the foot of each table.
- **Script:** `scripts/qullamaggie-cohorts-price.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-price.md`

### Volume surge cohorts

**Goal:** How `vol_surge_ratio = volume / mean(volume[-51:-1])` affects results.

- **Cohorts:** (<0.7), [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.1), [1.1-1.2), [1.2-1.3), [1.3-1.4), [1.4-1.6), [1.6-2.0), [2.0-3.0), [3.0-4.0), [4.0-6.0), (>6.0)
- **Filter under study is dropped:** the `vol_surge < 2.0x` cap is removed, otherwise the `[2.0-3.0)` through
  `(>6.0)` cohorts would be empty. It returns as the `[1.00-2.00) cap` reference row at the foot of each table.
- **Script:** `scripts/qullamaggie-cohorts-vol-surge.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-vol-surge.md`

### Vol dry-up cohorts

**Goal:** How `vol_dry_up_ratio = avg_vol_10 / avg_vol_50` (both shift-1) affects results — the volume-side
twin of the ADR compression study. Below 1.0 the last 10 sessions were quieter than the last 50, the volume
contraction the setup looks for ahead of a breakout; above 1.0 volume is already expanding.

- **Cohorts:** (<0.5), [0.5-0.6), [0.6-0.7), [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.1), [1.1-1.25), [1.25-1.5), (>1.5)
- **Filter under study is dropped:** nothing is dropped any more — `vol_dry_up` was **retired from the
  strategy on 2026-08-01**, so like SMA(200) the cohorts just slice the existing signal population. The
  `<0.90 (cap)` reference row is kept so the retired cap stays measurable.
- **Script:** `scripts/qullamaggie-cohorts-vol-dry-up.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-vol-dry-up.md`
- **Note:** added 2026-08-01 — `vol_dry_up` was the last filter in the production chain with no cohort study
  of its own. Its first run is what retired it: the `<0.90 (cap)` slice scored *worse* than the full
  population on Mean% and Sortino at all three thresholds while dropping ~33% of signals. The filter was then
  removed from `QullamaggieStrategy`, `turtlex/research/qullamaggie.py`, `qullamaggie-backtest-v4.py` and
  every cohort script, and all of them were re-run.
- **Caveat:** the backtest-v4 re-run across all three windows shows the removal is **regime-dependent**, not a
  uniform gain — clearly better in 2021-2026, but Sortino falls in 2016-2020 at all three thresholds
  (s20 5.685 → 5.111) and is mixed in 2010-2015. The cohort study could not see this because it only spans
  2015-2026.

### Tight range cohorts

**Goal:** How `tight_range_ratio` (`(max(close[-11:-1]) − min(close[-11:-1])) / mean(close[-11:-1]) < Y`) affects results.

- **Algorithms:** `bk50d_s20_tr10_v2.0`, `bk50d_s20_tr20_v2.0`, `bk50d_s15_tr15_v2.0` (366d hold,
  `MIN_RANKING >= 40`) — the tight-range cap is the dimension under study, so the variants pair it with s20/s15
  rather than following the standard s20/s16/s12 set. With the cap removed the two s20 variants draw from the
  same candidate pool and differ only in their reference row (`<=0.10` vs `<=0.20`).
- **Cohorts:** (<0), [0.0-0.1), [0.1-0.15), [0.15-0.2), [0.2-0.25), [0.25-0.3), (>0.3)
- **Filter under study is dropped:** each variant's own `tight_range` cap is removed, otherwise the cohorts above
  it would be empty. It returns as a per-variant `<=0.10 (cap)` / `<=0.20 (cap)` / `<=0.15 (cap)` reference row
  at the foot of that variant's table.
- **Script:** `scripts/qullamaggie-cohorts-tightrange.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-tightrange.md`

### pct-above-sma50 cohorts

**Goal:** How `pct_above_sma50`: `close / mean(close[-51:-1]) − 1 > X` affects results.

- **Algorithms:** `bk50d_s<X>_v2.0` (366d hold, ungated) — X is the dimension under study here, so the standard s20/s16/s12 set does not apply; reference rows are printed for X = 12%/15%/17%/20%
- **Cohorts:** (<10), [10-12), [12-15), [15-17), [17-20), [20-30), (>30)
- **Filter under study is dropped:** the `pct_vs_sma50 > X` threshold is removed, otherwise the cohorts below X
  would be empty. Removing it also makes every X draw from one candidate pool, so there is a single table with
  one `>12% (s12)` / `>15% (s15)` / `>17% (s17)` / `>20% (s20)` reference row per threshold at its foot.
- **Script:** `scripts/qullamaggie-cohorts-pct-above-sma50.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-pct-above-sma50.md`

### SMA(200) cohorts

**Goal:** How `signal above sma(200)` (`SMA(200)` on the signal date) affects performance.

- **Cohorts:** (< -50%), [-50% : -20%), [-20% : 0%), [0% : 10%), [10% : 20%), [20% : 30%), [30% : 40%), [40% : 50%), [50% : 60%), [60% : 80%), [80% : 100%), (>100%)
- **Filter under study is dropped:** nothing is dropped — the strategy has no stock-level SMA(200) filter (only
  the SPY regime uses SMA200), so the full production chain runs and the cohorts just slice the existing signal
  population. `>=SMA200` and `<SMA200` reference rows split that population at zero.
- **Output:** setup is the same as for cohort analyze
- **Script:** `scripts/qullamaggie-cohorts-sma200.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-sma200.md`

### Sector cohorts

**Goal:** How company `sector` affects performance.

- **Cohorts:** different company sectors
- **Filter under study is dropped:** the Communication Services / Real Estate universe exclusion is removed,
  otherwise those two cohorts would be empty. It returns as the `excl Comm/RE (cap)` reference row at the foot
  of each table.
- **Script:** `scripts/qullamaggie-cohorts-sector.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-sector.md`

### Ranking cohorts

**Goal:** How Qullamagie ranking different deciles affects performance.

- **Cohorts:** two views of the same trades — fixed score bands `[0-20), [20-40), [40-50), [50-60), [60-70),
  [70-80), [80-90), [90-100]` (stable across runs, comparable with the ranking table in
  `scripts/qullamaggie-signals-v4.py`) and population deciles (which adapt to where the score mass sits).
  Both tables carry a `>=40 (gate)` reference row at the foot.
- **Filter under study is dropped:** no production *filter* is dropped, but the `MIN_RANKING >= 40` gate is not
  applied — the gate is the cohort variable, so applying it would empty every cohort below 40. It returns as the
  `>=40 (gate)` reference row, against an `ALL (ungated)` row.
- **Script:** `scripts/qullamaggie-cohorts-ranking.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-ranking.md`

## Entry-timing / limit-order studies

### Limit-order entry cohorts

**Goal:** How buying on the next day with a limit order (limit price = previous day closing price − X%) affects results.

- **Algorithms:** `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold, `MIN_RANKING >= 40`)
- **X%:** 0%, 1%, 2%, 3%, 4%, 5%; limit order is effective during the next 30 days.
- **Period:** 2015-01-01 : 2026-06-26
- **Output columns:** `Cohort  Fill%  N  Med%  Mean%  Win%  Sortino  PF` — `Fill%` is the share of the variant's
  signals that produced a trade, which the limit rows need (an unfilled order is not a loss, it is no trade) and
  the two baselines report too, so their N gaps stay readable.
- Additionally provide monthly Mean% and trade count by months/years for bk50d_s20 eod, bk50d_s16 eod, bk50d_s12 eod:

  ```text
   Year |    Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec |   Mean%    N
  ------------------------------------------------------------------------------------------------------------
   2010 |  +22.3|2   -4.5|1      ·      ·  +46.4|5      ·      ·  -31.4|2  -28.6|4  -39.1|2      ·      · |    -4.4|3   19
  ```

- **Script:** `scripts/qullamaggie-cohorts-limit-order.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-limit-order.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`
- **Note:** vol_dry_up<90%, no tight_range (standardized 2026-07-15); saved results were generated earlier with tr20 variants and vol_dry_up<80%.
- **Note — the script is migrated, the saved results are not.** The script now takes its signals from
  `turtlex/research/qullamaggie.py`, so all three variants are on the `_v2.0` labels with an s16 middle variant and
  the `MIN_RANKING >= 40` gate applied. Because the entry convention *is* the dimension under study, it reports two
  reference columns side by side: `next-open` (the canonical v2.0 entry) and `EOD` (signal-day close, the pre-v2.0
  convention kept for comparability with earlier runs and used by the monthly grids).
  `docs/research/result-qullamaggie-cohorts-limit-order.md` still carries the 2026-07-22 pre-migration run
  (`_v1.3_roc100`, s15, ungated, EOD only) — it needs a re-run before its numbers can be quoted against the v2.0 set.

### Limit-order fill rate

**Goal:** Calculate `bk50d_s12_v2.0` signals, then figure out the percentage of signals where the price drops X% during the next Y days so that a resting limit order would be filled.

- **Filters:** same as `scripts/qullamaggie-signals-v4.py` (RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, no tight_range, cooldown 30d, mcap>=1.5B excl Comm/RE), plus the standard `MIN_RANKING >= 40` gate
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
- **Note — the saved results predate the migration.** The script is on the shared signal layer (`bk50d_s12_v2.0`,
  `MIN_RANKING >= 40`), but the committed doc is the 2026-07-23 run, titled `bk50d_s12_v1.3_roc100` with no ranking
  gate in its config table. Fill rates from an ungated signal set are not the fill rates of the gated one — the
  gate removes the low-ADR, high-priced names whose pullback behaviour differs — so re-run before quoting them.

## Filter relaxation

### Relaxation brainstorm (s15)

**Goal:** Analyze `bk50d_s15_v1.3_roc100` 366d results in period 2001-01-01 : 2026-06-26.

- Propose 5 options how to achieve ~3 signals per month.
- Important: Med% and Sortino must stay on the same level.
- The main idea is to loosen currently applied filters — which filter conditions can be loosened with the least impact on Mean% and Sortino?

### Relaxation sweep (s20)

**Goal:** Increase signals per month (F/mo) for `bk50d_s20_v2.0` (366d hold) without degrading Sortino and Mean%.

- **Baseline** (2021-01-01 : 2026-07-05, unconstrained): N=243, F/mo=3.7, Win%=67.1, Mean%=+52.50, Med%=+22.32, Sortino=2.864, MaxDD%=39.71 — this was the prompt's *input* figure, taken from the then-current `backtest-v4` run; the study evaluates 2015-2026 and every variant is judged against the `baseline` row of its own table, not this line
- Propose 5 ideas how to loosen currently applied filters or expand the universe.
- Prefer relaxations where existing cohort studies show the excluded region performs at or above the included pool.
- For each idea run the modified variant (change ONE dimension at a time, all other filters unchanged) over 2015-01-01 : 2026-06-26, hold 366d, and report:

  ```text
  Variant                              N   F/mo   Win%    Mean%    Med%   Sortino      PF   MaxDD%
  ```

- Also run baseline + the best 2-3 ideas combined.
- **Fixed filters reference:** roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, mcap>=1.5B excl Comm/RE
- Important: Sortino and Mean% must stay on the same level as baseline; reject ideas that trade quality for count.
- Share your findings: which single relaxation has the best F/mo gain per unit of Sortino given up.
- **Script:** `scripts/qullamaggie-backtest-v4.py` (new: `scripts/qullamaggie-relax-sweep.py`)
- **Results:** `docs/research/result-qullamaggie-relax-sweep.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-cohorts-tightrange.md`, `docs/research/result-qullamaggie-cohorts-price.md`

## Ranking

### Ranking algorithm proposal

**Goal:** Propose a ranking algorithm for s15_tr15 trades that selects only the trades with the most potential based on technical data (higher ADR, (SMA10, SMA20), your own discoveries).

### Recalibrate ranking weights + validate

**Goal:** Check all cohort analyses in `docs/research/`, validate whether `turtlex/strategy/ranking/qullamaggie.py`'s band weights still match the current (v1.3, RSI<70) cohort data, and propose improvements to optimize Sortino and Mean%.

- Recalibrated all six dimensions' point tables using *reachable-only* cohort Sortino spreads (the bucket range a candidate can actually land in given that dimension's own entry filter) and added two new dimensions the ranking previously ignored: ROC252 and RSI(14) within the qualifying pool. New weight split: SMA50=50 (fixed by design), price=13, ADR=12, compression=12, ROC252=10, RSI=3.
- Built a genuine out-of-sample validation: a train/test split confirms the new scheme separates forward Sortino/Mean% better than the old 4-dimension bands, and a further 5-fold stability check across independent cutoffs (2019-2023) confirms the weight split is robust to being refit on shorter sub-periods (which is noisier and performs worse on average, not better).
- **Script:** `scripts/qullamaggie-ranking-validation.py` (new)
- **Results:** `docs/research/result-qullamaggie-ranking-validation.md`
- **References:** `turtlex/strategy/ranking/qullamaggie.py`, `docs/research/result-qullamaggie-cohorts-*.md`, `docs/research/result-qullamaggie-cohorts-ranking.md`

### Three-feature ranking weights

**Goal:** Propose weights for `turtlex/strategy/ranking/qullamaggie.py` assuming the ranking depends only on `adr_pct`, `pct_vs_sma50` and price; validate against the previous weighting by re-running the portfolio simulation, and check whether `MIN_RANKING=40` is still a reasonable gate.

- An ad-hoc per-trade scan (1685 bk50d_s12 signals, 2010-2020, 366d returns with each year's mean subtracted) found only three of the six dimensions kept the sign of their cross-sectional effect across both halves: ADR%(20) rho +0.121, %above-SMA50 +0.099, price -0.059. Compression/ROC252/RSI were 25-75% time effect and reversed sign. That scan is not committed — the weights it produced are.
- Kept the cohort band *shapes* and rescaled them to 40/35/25; coarser monotone bands fitted to the scan's own decile shape were tried and were worse.
- Validation deliberately avoids three traps: comparing schemes at a fixed gate (which compares selectivity, not skill — a score of 40 keeps 59% of signals under the old weights and 40% under the new), reading a result without a same-size random-subset null, and cutting top-K inside tie groups by date.
- Result: the new weights win at every selectivity at s12 and s16 and are mixed at s20. `MIN_RANKING=40` remains reasonable, and becomes a live filter at s20 where the old weights never dropped a single signal.
- **Script:** `scripts/qullamaggie-ranking-weights.py` (new)
- **Results:** `docs/research/result-qullamaggie-ranking-weights.md`
- **References:** `turtlex/strategy/ranking/qullamaggie.py`, `docs/research/result-qullamaggie-cohorts-*.md`, `docs/research/result-qullamaggie-ranking-validation.md`

## Portfolio simulation

### Portfolio simulation

**Goal:** Portfolio simulation over `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` signals.

- **Period:** 2021-01-01 : 2026-06-26
- **Algorithms:** `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold)
- **Ranking:** Calculate ranking (turtlex/strategy/ranking/qullamaggie.py) for all transactions, prefer signals with higher ranking.
Calculate results with applying filter `MIN_RANKING >= 40` and without applying it.
- **Initial portfolio:** $30,000
- **Position sizing:** invest {3%, 4%, 5%} of portfolio at a time per trade; if there is no liquidity, skip the trade.
- **Header:** a `## Configuration` table (`| Parameter | Value |`, the same shape the cohort studies
  use via `turtlex/common/report.py:config_table`) carrying every filter once at the top of the doc.
  Only `%abv_SMA50`, the swept dimension each algorithm is named for, stays on the per-algorithm
  heading — repeating the full filter list per section made three near-identical lines that could
  drift apart.
- **Output format:** **one table per algorithm**, carrying both ranking treatments. Each sizing
  appears twice on adjacent rows — gated then ungated — so the pair reads across rather than
  across two separate tables. Everything else (period, sizing, entry, exit) is identical between
  the two, so the difference isolates the gate. A `gate` column distinguishes the rows.

  ```text
  **Ranking gate:** `QullamaggieRanking >= 40` drops 184 signals (0 with no fillable next-day open);
  ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair
  reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

  size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
  -----------------------------------------------------------------------------------
  3%     R>=40        188,451  +39.87   -28.24   1.412    1.785    175    335   13.8%
  3%     ungated      151,102  +34.34   -27.66   1.242    1.625    184    510   11.6%
  4%     R>=40        206,548  +42.23   -28.01   1.508    1.769    135    375   11.3%
  4%     ungated      191,828  +40.32   -28.54   1.413    1.710    139    555    9.5%
  5%     R>=40        250,869  +47.37   -31.43   1.507    1.800    110    400    9.8%
  5%     ungated      169,102  +37.13   -29.20   1.272    1.609    114    580    9.7%
  ```

- The **monthly grid's** "top 5 by Final$" ranks across both treatments together, so each entry is
  labelled `s12 R>=40` or `s12 ungated`. The **ranking-decile** tables stay on the gated set only —
  they span `MIN_RANKING..100` by construction, and the ungated size-sweep table above is what
  answers whether the gate earns its keep.

- For the top 5 algorithms by `Final$`, print `monthly returns` and `trades count in particular month` by years (years are rows, months are columns):

  ```text
   Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
  -----------------------------------------------------------------------------------------------------------------------------------------------
   2010 |    -3.2|7    +3.8|1    +2.6|1    -0.4|2    -2.4|0    -3.9|0    +2.9|0    -3.1|4    +5.5|2    +1.0|2    -0.3|2    +8.3|6 |   +10.5    27
  ```

- Compare what the result would be if the whole amount were invested in SPY or QQQ on the first day of the period and sold on the last day of the period
- <!-- Provide a comparison with an alternative approach where a limit order is added to buy the stock 
    3% below closing price during the next 30 days (instead of buying on closing price). 
    - Provide comparison with an alternative holding lengths (90d, 120d, 180d, 240d, 360d) 
  - Provide all algorithms comparison with approach that instead of buying next day open price use limit order with values (close price, close price -1%, close price -3%, close price -5%)
  - Provide N CAGR%   MaxDD%  Calmar  Sortino for different ranking deciles grouped by algorithms
  -->
- Add your findings on how to improve the portfolio performance (Mean%, Sortino, Calmar).
- Run the same portfolio simulation for periods 2010 : 2015, 2016 : 2020 and results to @docs/research/result-qullamaggie-portfolio-v4-2010-2015.md and @docs/research/result-qullamaggie-portfolio-v4-2016-2020.md
- <!-- **Deferred/considered ideas** (commented out in the original prompt):
  - Prefer always bk50d_s20_tr10_v1.3_roc100 signals, but if there is liquidity use bk50d_s15_tr15_v1.3_roc100 signals to reduce uninvested amounts.
  - Implement rank-based funding to choose the trade if several trades are available on the same day.
  - Sell the position if the stock closes below the 200-day SMA for 3 consecutive trades.
  - Provide existing algorithms comparison with additional filter - sell stock if stock price is 5 days < 200SMA
  - Provide existing algorithms comparison with additional filter - sell stock if stock price has raised <5% during 120 days
  -->
- **Results:** `docs/research/result-qullamaggie-portfolio-v4.md` (2021-2026 baseline) and
  `docs/research/result-qullamaggie-portfolio-v4-2010-2015.md` (2010-2015 period) and
  `docs/research/result-qullamaggie-portfolio-v4-2016-2020.md` (2016-2020 period).
- **Scripts:**
  `uv run scripts/qullamaggie-portfolio-sim.py --start-date 2010-01-01 --end-date 2015-12-31 --output docs/research/result-qullamaggie-portfolio-v4-2010-2015.md`
  `uv run scripts/qullamaggie-portfolio-sim.py --start-date 2016-01-01 --end-date 2020-12-31 --output docs/research/result-qullamaggie-portfolio-v4-2016-2020.md`
  `uv run scripts/qullamaggie-portfolio-sim.py --start-date 2021-01-01 --end-date 2026-06-26 --output docs/research/result-qullamaggie-portfolio-v4.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `scripts/qullamaggie-backtest-v4.py`, `scripts/qullamaggie-exit-sweep.py`
- **Note — entry is the next-day open, and only that.** The limit-order entry comparison the script
  used to print (`close`, `close -1%`, `close -3%`, `close -5%`) was removed 2026-07-30 along with its
  `limit_fill` helper, per the commented-out bullet above. That dimension keeps its own two studies:
  [Limit-order entry cohorts](#limit-order-entry-cohorts) and [Limit-order fill rate](#limit-order-fill-rate).
  The `run_blend` function — an unreachable implementation of the deferred "fund s20 first, then s15
  with leftover liquidity" idea — was deleted in the same pass; nothing called it.

### Exit strategy analyze

**Goal:** Analyze different exit strategies to improve `scripts/qullamaggie-portfolio-sim.py` CAGR% and Sortino. Provide 5 ideas and validate them against the current 366d time-cap exit. To simplify testing use only `bk50d_s20_v2.0` / 366d / 3% of portfolio.

- **Period:** 2020-01-01 : 2026-06-26, initial $30,000, ranking gate >= 40
- **Baseline to beat:** Final $222,166, CAGR +36.17%, MaxDD -26.00%, Calmar 1.391, Sortino 1.334, 180 taken / 716 skipped
- **Pass bar (pre-registered):** CAGR **and** Sortino both above baseline, and MaxDD no more than 5pp worse
- **Ideas swept**, each with the 366d time cap still active underneath as a backstop:
  - `regime` — exit when SPY has closed below its 200d SMA for N consecutive days
  - `trail` — trail T% below the running peak close, armed only once the trade is up A%
  - `dead` — exit if the trade is not up at least R% after N trading bars
  - `trend` — exit after N consecutive closes below the position's own EMA20 / SMA50 / SMA200
  - `atr` — fixed stop at entry - k x ATR(14) measured at entry
- **Controls:** the four exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim` (`stop30`, `trail25`, `sma200x5`, `dead120` — `EXIT_MODES = ["time"]` never selects them)
- **Overfit guards:** baseline reconciliation against the committed portfolio-sim numbers; the full metric surface per idea rather than the winning cell alone (a real effect is a plateau, an artifact is a spike); per-year decomposition; stationary block bootstrap (1,000 resamples of 21-day blocks, paired on day indices)
- **Robustness matrix:** the winning rule re-run across `s20` / `s15` / `s12` x 2010-2015 / 2016-2020 / 2021-2026
- **Output format:**

  ```text
  variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip
  -------------------------------------------------------------------------------------------
  <+5% after 90 bars            299,845  +42.62   -24.04   1.773    1.555    246    650  PASS
  baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
  ```

- **Script:** `scripts/qullamaggie-exit-sweep.py` (new)
- **Results:** `docs/research/result-qullamaggie-exit-sweep.md`
- **References:** `turtlex/research/qullamaggie.py` (shared signal layer, parity-tested), `turtlex/backtest/metrics.py` (`compute_trade_metrics`), `docs/research/result-qullamaggie-portfolio-v4.md` (baseline), `docs/research/result-qullamaggie-portfolio-v4-2010-2015.md` and `-2016-2020.md` (cross-checks for the earlier matrix windows)
- **Note — the headline result is negative; keep the 366d time cap.** On the single 2020-2026 window `<+5% after 90 bars` looked decisive (CAGR +42.62%, Sortino 1.555, MaxDD -24.04%) and cleared every single-window guard: a bounded 90-150 bar plateau, better in 6 of 7 years, 91.8% / 94.1% bootstrap win rates. The robustness matrix then failed it in **7 of 9** config/period cells — every pass sits in 2021-2026, which overlaps the window it was fitted on. A follow-up run of the full 24-cell dead-money grid across all 9 cells (216 sims, run ad-hoc; not kept as a script) found **no** parameterisation passing more than 4 of 9, and 23 of 24 had a negative mean dCAGR. The passing region *moves* between eras — 2021-2026 favours short cutoffs, 2010-2015 long ones, 2016-2020 none at all — which is the signature of regime-specificity rather than mistuning. The single-window guards all agreed with each other because they were all measuring the same six years; they cannot detect that the window itself is the special case. `sma200 x 5d` and `arm +25% / trail 25%` also cleared the single-window bar and were never put through the matrix.
- **Note:** the study's own baseline reproduces the committed portfolio-sim figure exactly ($222,166 / +36.17% / -26.00%) despite generating signals through `turtlex/research/qullamaggie.py` rather than the sim's inline copy. For the matrix windows the harness reproduces `-2016-2020.md` to within 0.41pp CAGR. The `-2010-2015.md` gap this note used to describe (+8.48% vs +10.94%, attributed to the gate being absent from a 2026-07-21 run) is **gone**: all three portfolio docs were re-run 2026-07-29 with `min ranking: 40` in their headers, and `-2010-2015.md` now reports +8.48% at 3% sizing — the same figure as the harness.
- **Note:** exits fill at the day's adjusted close, so stop-based rules are measured optimistically; the universe filter uses *current* `company.market_cap >= $1.5B`, which inflates every absolute figure (baseline included) and worsens the further back the window sits.
- **Note — the saved results predate the `vol_dry_up` removal (2026-08-01).** The script takes its signals from
  `turtlex/research/qullamaggie.py`, which dropped the filter that day, so a re-run would draw from a larger
  signal population than the committed doc. The re-run was **deliberately skipped**: the study's conclusion is
  negative (keep the 366d time cap) and rests on the *shape* of the robustness matrix — a rule that passes only
  in the window it was fitted on — which a wider signal set does not plausibly reverse. Its absolute figures,
  including the `$222,166` baseline, are stale and should not be quoted against post-removal portfolio-sim runs.

## Live signal generation

### Signals: s12 with overlap & cohorts

**Goal:** Provide `bk50d_s12_v2.0` signals (`MIN_RANKING >= 40`) for period 2026-06-01 : today; mark signals that are also in `bk50d_s20_v2.0` and `bk50d_s16_v2.0`.

- **Output columns:**

  ```text
  Date │ Symbol │ Entry $ │ Curr Price │ 0.97*Entry Price │ Change % │ %abv SMA50 │ ADR% │ ADR_CHG │ RSI14 │ TR% │ ROC252% │ In s16? │ In s20? │ 0.97*Entry Price reached? │ Ranking │ Last date
  ```

  - `%abv SMA50`, `ADR%`, `RSI14`, `TR%`, `ROC252%` must be calculated on the **signal** date, since that is the bar every filter is evaluated on.
  - `Last date` = latest date when stock data is available in the `turtle.daily_bars` table.
  - `Ranking` - ranking calculated according to @turtlex/strategy/ranking/qullamaggie.py

- Report also the share of signals where the 0.97*Entry price was reached: `reached/total (Reached%)` in the summary line.
- Write also a separate table with aggregated results where `%abv SMA50` is in cohorts [12-15), [15-17.5), [17.5-20), (>20):

  ```text
  Cohort | N | Med% | Mean% | Win% | PF | Sortino | Max DD
  ```

- Write also a separate table with aggregated results where `Ranking` is in cohorts [0-20), [20-40), [40-60), [60-80), (>80):

  ```text
  Cohort | N | Med% | Mean% | Win% | PF | Sortino | Max DD
  ```

- Compare also mean(Mean%) with SPY.US and QQQ.US return for the whole period. Exclude LC.US and other suspicious data points.
- **Script:** `scripts/qullamaggie-signals-v4.py`
- **Output:** screen
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `scripts/qullamaggie-backtest-v4.py`
- **Note:** the script prints the full report — signal table, exclusions, both cohort tables and the benchmark comparison — to stdout. It used to also write `docs/research/result-qullamaggie-signals-v4.md`; that doc was deleted 2026-07-25 because the report is only meaningful for the day it is run.
- **Note:** the signal table is gated at `MIN_RANKING >= 40`, but both cohort tables are computed over the *ungated* s12 signals on purpose. Gating them would leave the `[0-20)` and `[20-40)` ranking buckets permanently empty and destroy the only thing those tables measure — whether the score separates outcomes at all. The summary line reports how many signals the gate dropped so the two views reconcile.

### Trades: s12 open-trade performance

**Goal:** Provide `bk50d_s12_v2.0` signals for period 2025-07-01 : today.

- **Output columns:**

  ```text
  Signal │ Entry │ Symbol │ Entry $ │ Curr Price │ Change % │ %abv SMA50 │ ADR% │ ADR_CHG │ RSI14 │ ROC252% │ Latest Data
  ```

  - `Signal` = the breakout bar; `Entry` = the next trading bar, which is where the position is opened.
  - `%abv SMA50`, `ADR%`, `ADR_CHG`, `RSI14`, `ROC252%` are calculated on the **signal** date, since every
    filter is evaluated on that bar.
  - `Entry $` = the entry bar's split/dividend-adjusted open (`open × adjusted_close / close`).
  - `Curr Price` = the symbol's latest available adjusted close; `Change %` marks the open position to it.
  - `Latest Data` = the symbol's latest *usable* bar in `turtle.daily_bars` (zero-volume and
    non-positive-close bars are dropped before indicators, so they cannot appear here).

- Provide mean trade performance and trade count if all trades are closed at the latest available adjusted close.
- **Script:** `scripts/qullamaggie-trades-v4.py`
- **Results:** `docs/research/result-qullamaggie-trades-v4.md`
- **References:** `turtlex/research/qullamaggie.py` (shared signal layer), `tests/research/test_qullamaggie_parity.py` (parity harness), `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-backtest-v4.md`
- **Note:** the signal layer is imported from `turtlex/research/qullamaggie.py`, which is parity-tested against
  `QullamaggieStrategy` — the strategy behind `backtest-runner --trading-strategy qullamaggie` — so this report and
  the runner agree on `(symbol, signal_date, entry_date, entry_price)`. The variant follows the strategy's
  `SMA_THRESH`, which moved 0.15 -> **0.12** on 2026-07-30 so this study reports the standard `s12` algorithm;
  indicators are split/dividend-adjusted and the `$5-$250` band stays on the raw close. `tight_range` is not
  part of the strategy, so the former informational `TR%` column is gone. Filters: RSI<70, ADR>=3.0%,
  ADR_change<90%, roc_12m<100%, vol_surge<2.0x, SPY>200d SMA, raw close>$5&<$250,
  avg_vol>=500K, >12% above the 50d SMA, cooldown 30d, mcap>=1.5B excl Comm/RE.

## Maintenance

### Maintenance: lint & tests

Run Ruff + mypy + pytest.

### Validate and run cohorts

- Verify that the cohort descriptions in `@docs/research/prompts.md` match the code in `@scripts/*.py`. If there are discrepancies, ask how to proceed.
- Verify that the cohort results are in sync with the cohort Python code in `@scripts/*.py`. If they are not, re-run the script.
- Validate the results in `@docs/research/result-qullamaggie-cohorts-*.md` and answer the following questions:
  - Are all filters in `@scripts/qullamaggie-backtest-v4.py` justified — does each one improve Mean% and/or Sortino? If any do not, surface those findings to the screen.
  - Is there a way to loosen the filters to generate more signals without degrading performance (Mean% and/or Sortino)? Surface those findings to the screen.

## Gap: five filters have no cohort study

`avg_vol >= 500K`, `market_cap >= 1.5B`, `SPY > 200d SMA`, and `cooldown 30d` are all unvalidated — no study varies them, so there's no evidence either way on whether they help.
