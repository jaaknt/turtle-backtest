# Qullamaggie Research Prompts

Reusable prompts that drove the Qullamaggie v4 backtest research. Each prompt maps to a script in `scripts/` and (usually) a result doc in `docs/research/`. Grouped in pipeline order: validate the backtest first, study individual filters, then relax filters, rank, simulate the portfolio, and finally generate live signals.

Common references for most prompts: `docs/research/qullamaggie-backtest-v4.md` (methodology) and `docs/research/result-qullamaggie-backtest-v4.md` (baseline results).

**Standard algorithm set.** Unless a prompt says otherwise, "the algorithms" means `bk50d_s20_v2.0`, `bk50d_s16_v2.0` and `bk50d_s12_v2.0` — a 50-day breakout sitting more than 20% / 16% / 12% above the 50-day SMA, entered at the next trading day's split/dividend-adjusted open, held 366 calendar days, with the `QullamaggieRanking` gate `MIN_RANKING >= 44` applied. The naming convention is defined in `docs/research/qullamaggie-backtest-v4.md` (Step 1, "Algorithm naming"). Earlier runs used `_v1.3_roc100` labels and an s15/s17 pair instead of s16; where a **Note** records what a past run actually did, the original name is kept deliberately rather than rewritten.

**The `avg_vol_20` floor moved 500K -> 100K on 2026-08-02**, in `QullamaggieStrategy`,
`turtlex/research/qullamaggie.py` and every `scripts/*.py` study. **Every committed result doc was
re-run on or after 2026-08-09** (pacing 08-20, the horizon study 08-29), and every one that prints a
`Min avg vol (20d)` row now reports `>= 100K`, so they are all on the wider floor and comparable with
each other and with backtest-v4. The rationale for the move is in
[Average volume cohorts](#average-volume-cohorts). Anything quoted from a doc predating that re-run is
on the 500K floor, which admitted roughly 40% fewer signals.

**The ranking gate moved 40 -> 44 on 2026-08-09**, after the bands were re-derived on the v2.0
cohorts; 44 is `portfolio-runner --min-signal-ranking`'s default and the value every `scripts/*.py`
study now uses, including the four that report it as a reference row rather than applying it. The
ranking studies (`-ranking-weights`, `-ranking-validation`, `-ranking-lab`) are the exception by
design: they sweep the gate instead of fixing it. `MIN_RANKING` is scheme-relative — it has to be
re-picked at matched selectivity whenever `QullamaggieRanking` changes — so a `>= 40` figure quoted
from an older run is not comparable with a `>= 44` one.

## Index

| Prompt | Script | Results |
| -------- | -------- | --------- |
| [Validate & run backtest v4](#validate--run-backtest-v4) | `scripts/qullamaggie-backtest-v4.py` | `result-qullamaggie-backtest-v4.md`, `-2010-2015.md`, `-2016-2020.md` |
| [Long-term monthly analysis](#long-term-monthly-analysis) | `scripts/qullamaggie-longterm-monthly.py` | `result-qullamaggie-longterm-monthly.md` |
| [Marginal monthly performance by signal year](#marginal-monthly-performance-by-signal-year) | `scripts/qullamaggie-horizon-monthly.py` | `result-qullamaggie-horizon-monthly.md` |
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
| [SPY SMA regime cohorts](#spy-sma-regime-cohorts) | `scripts/qullamaggie-cohorts-spy-sma.py` | `result-qullamaggie-cohorts-spy-sma.md` |
| [Sector cohorts](#sector-cohorts) | `scripts/qullamaggie-cohorts-sector.py` | `result-qullamaggie-cohorts-sector.md` |
| [Market cap cohorts](#market-cap-cohorts) | `scripts/qullamaggie-cohorts-market-cap.py` | `result-qullamaggie-cohorts-market-cap.md` |
| [Average volume cohorts](#average-volume-cohorts) | `scripts/qullamaggie-cohorts-avg-vol.py` | `result-qullamaggie-cohorts-avg-vol.md` |
| [Ranking cohorts](#ranking-cohorts) | `scripts/qullamaggie-cohorts-ranking.py` | `result-qullamaggie-cohorts-ranking.md` |
| [Limit-order entry cohorts](#limit-order-entry-cohorts) | `scripts/qullamaggie-cohorts-limit-order.py` | `result-qullamaggie-cohorts-limit-order.md` |
| [Limit-order fill rate](#limit-order-fill-rate) | `scripts/qullamaggie-limit-fill-rate.py` | `result-qullamaggie-limit-fill-rate.md` |
| [Relaxation brainstorm (s15)](#relaxation-brainstorm-s15) | — | — |
| [Relaxation sweep (s20)](#relaxation-sweep-s20) | `scripts/qullamaggie-relax-sweep.py` | `result-qullamaggie-relax-sweep.md` |
| [Ranking algorithm proposal](#ranking-algorithm-proposal) | — | — |
| [Recalibrate ranking weights + validate](#recalibrate-ranking-weights--validate) | `scripts/qullamaggie-ranking-validation.py` | `result-qullamaggie-ranking-validation.md` |
| [Three-feature ranking weights](#three-feature-ranking-weights) | `scripts/qullamaggie-ranking-weights.py` | `result-qullamaggie-ranking-weights.md` |
| [Ranking improvement loop](#ranking-improvement-loop) | `scripts/qullamaggie-ranking-lab.py` | `result-qullamaggie-ranking-lab.md` |
| [Portfolio pacing](#portfolio-pacing) | `scripts/qullamaggie-pacing.py` | `result-qullamaggie-pacing.md` |
| [Portfolio simulation](#portfolio-simulation) | `scripts/qullamaggie-portfolio-sim.py` | `result-qullamaggie-portfolio-v4.md`, `-2010-2015.md`, `-2016-2020.md` |
| [Exit strategy analyze](#exit-strategy-analyze) | `scripts/qullamaggie-exit-sweep.py` | `result-qullamaggie-exit-sweep.md` |
| [Signals: s12 with cohorts](#signals-s12-with-cohorts) | `scripts/qullamaggie-signals-v4.py` | screen |
| [Trades: s12 open-trade performance](#trades-s12-open-trade-performance) | `scripts/qullamaggie-trades-v4.py` | `result-qullamaggie-trades-v4.md` |
| [Maintenance: lint & tests](#maintenance-lint--tests) | — | — |
| [Validate and run cohorts](#validate-and-run-cohorts) | `scripts/qullamaggie-cohorts-*.py` | — |
| [Gap: what is still unvalidated](#gap-what-is-still-unvalidated) | — | — |

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

**Goal:** Analyze `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold, `MIN_RANKING >= 44`) over the long term; provide monthly Mean% and trade counts by year, plus general findings and pros/cons of the different algorithms.

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
- **Note:** the committed doc is the 2026-08-09 re-run — three `_v2.0` sections (s20/s16/s12), next-day
  adjusted-open entry and `QullamaggieRanking>=44` — so its monthly grids are on the current standard set.
  The 2026-07-22 version it replaced had four `_v1.3_roc100` sections (s12/s15/s17/s20), same-day close
  entry and no ranking gate; nothing quoted from that version is comparable with this one.

### Marginal monthly performance by signal year

**Goal:** Decompose the holding period. Every other study measures a signal at one horizon (366d), so
the repo can say what a signal is worth after a year but not *when* during that year the return is
earned, nor whether that shape changed across regimes. Report the return earned **during** each of the
18 months after entry, averaged by the year the signal was generated in.

- **Period:** 2015-01-01 : 2025-12-31 (signal dates)
- **Algorithm:** `bk50d_s12_v2.0` only (the live reference algorithm)
- **Ranking:** reported at **`MIN_RANKING >= 44` (live), `>= 60`, `>= 70`, `>= 80` and ungated** — the
  gated/ungated pairing the portfolio simulation uses, extended up a ladder of thresholds to show
  whether the ranking's edge keeps scaling with selectivity or flattens out, and where the signal
  count stops being able to fill a book. All come from one signal generation and differ only by the
  threshold applied to the score each signal already carries — same cooldown chain, same entries,
  same marks — so the differences isolate the gate. The gated sets are nested subsets of the ungated
  one. Thresholds live in the `GATES` list in the script; adding one is a one-line change.
- **Horizon:** marginal months 1-18, *not* the 366d fixed hold. `mark[0]` is the entry fill (next
  trading day's adjusted open), `mark[M]` is the adjusted close of the first bar on or after
  `entry_date + M` calendar months, and the cell is `mark[M] / mark[M-1] - 1`. Month 12 therefore
  lands within a day of the 366d exit — an ad-hoc check on the 2024 cohort measured it at +45.4%
  against the then-canonical +46.2%, corr 0.996, the gap being entry+365 vs entry+366. That check has
  not been repeated since; `result-qullamaggie-backtest-v4.md` now reports **+46.4%** (N=159) for the
  2024 s12 cohort against this study's 158.
- **Cohort:** per cell — every signal with a mark at both ends of that month. Cells rest on different
  signal sets as M grows, which is what `N@M18` in the gate comparison quantifies. Month 18 is only
  reachable for entries ~18 months before the last bar, so the final row's right-hand columns are a
  small early sub-cohort, not a better one.
- **Reading the axes:** the row is the signal's *birth year* and the column is its *age*, so calendar
  time drifts rightward along a row — a 2015-vintage M18 cell describes 2016-2017, not 2015.
- **Output format:** a `## Gate comparison` table first, then one Mean% matrix per treatment —
  `R>=44`, `R>=60`, `R>=70`, `R>=80`, then ungated — years as rows and month-since-entry as columns.
  No Win% matrix: the mean is what the study is for, and a per-month hit rate invited reading a
  50%-ish number as if it settled anything. No per-cell N matrices either — each year's count is
  already the Mean% grid's `Sig` column, and the totals plus month-18 attrition live in the
  comparison table, so five N grids were five copies of the same two facts.

  ```text
  | Gate | Signals | % of universe | N@M18 | M1–12 | M13–18 | Rebuy (M1) | Crossover | Thinnest years |
  | ungated        | 4808 | 100% | 4259 | +2.93% | +1.57% | +1.6% | M13 | 2018: 121, 2017: 161 |
  | `R>=44` (live) | 1894 |  39% | 1672 | +4.01% | +1.76% | +2.2% | M13 | 2018: 32, 2015: 45   |
  | …                                                                                          |
  ```

  `Rebuy (M1)` is what fresh capital earns in its first month, so `Crossover` — the first month
  falling below it — is the exit-timing read: hold while a month beats redeployment, stop when it
  does not. `N@M18` is how much of the sample still has eighteen months of forward data; it falls
  short of `Signals` because recent vintages run into the end of the data, not because those trades
  failed.

  ```text
  ──────────────────────────────────────────────────────────
  R>=44 — bk50d_s12_v2.0, QullamaggieRanking >= 44  (the live configuration)
  ──────────────────────────────────────────────────────────

  Mean% — return earned during month M

   Year |     M1     M2     M3   …    M17    M18 |    Sig
  ----------------------------------------------------------
   2015 |   +2.1   +1.4   -0.3   …   +0.9   +0.4 |     45
   …
  ----------------------------------------------------------
    All |   +1.9   +1.1   +0.4   …   +0.5   +0.3 |   1894

  ──────────────────────────────────────────────────────────
  R>=60 / R>=70 / R>=80 — … (stricter cuts)  ── same matrix each
  UNGATED — … (no ranking gate)              ── same matrix
  ──────────────────────────────────────────────────────────
  ```

- **Read the gate comparison before the grids.** A thin signal year (2018 has 32 at `R>=44`) falls to
  9 at `R>=60`, 4 at `R>=70` and 1 at `R>=80`, where a Mean% cell is one name's story rather than a
  cohort's. A rising Mean% beside a collapsing sample is selectivity eating its own evidence, not an
  improving edge — and a gate that leaves single-digit signals in a year cannot fill a 25-position
  book, whatever its per-signal mean says. The `Crossover` column is the tell: it holds at M13 for
  ungated / `R>=44` / `R>=60`, then jumps to M4 at `R>=70` and `R>=80`, which is the statistic
  disintegrating rather than a shorter optimal hold.
- **Cells below `MIN_CELL_N` (5) signals print `·` in the Mean% matrix**, the same floor the cohort
  studies apply (`if len(rets) < 5: return None`). Suppression is one-sided: the row's `Sig` column
  still reports the year's true count, so a `·` next to a non-zero `Sig` means the cell was withheld,
  while a whole row of `·` next to a small `Sig` means the year never cleared the floor at that gate.
- **Run:** needs the VPS — the local mirror starts 2021-08-19, and the script raises rather than
  returning empty years if a chunk comes back with no bars.

  ```bash
  ACTIVE_PROFILE=hetzner-db DB_APP_PASSWORD="$DB_CLAUDE_PASSWORD" \
    systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 \
    uv run scripts/qullamaggie-horizon-monthly.py
  ```

- **Note:** signal generation is chunked in 3-year slices with a 580-day forward pad. A single
  2013-2026 load is wider than the relax sweep's ~3.5 GB peak and does not fit the 4 GB cap; only the
  per-signal record list survives a chunk. Boundaries are safe for the 30-day cooldown because
  `qm.get_signals` runs its cooldown chain over the warmup rows too.
- **Note:** the `## Reading` section is emitted by the script, so a re-run regenerates the whole file —
  do not hand-write findings into it without adding it to `FINDINGS_DOCS` in `scripts/qullamaggie.sh`.
- **Caveat — the universe is survivor-only.** Every symbol in `turtle.daily_bars` still trades today
  (5,656 symbols, none ending before 2026), so companies delisted, acquired or wound up during the
  window never generate a signal; and the `market_cap >= 1.5B` filter reads the *current*
  `turtle.company` snapshot, admitting a 2015 signal only if that company is large today. Both bias
  the same way. This applies to **every** study in this file, not just this one, and it is why this
  study's near-zero count of early-ending series is not a measure of delisting risk. The shape across
  months is more trustworthy than the levels, and the early years are the most affected.
- **Script:** `scripts/qullamaggie-horizon-monthly.py`
- **Results:** `docs/research/result-qullamaggie-horizon-monthly.md`
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `docs/research/result-qullamaggie-longterm-monthly.md`

## Filter cohort studies

All cohort studies below share the same setup unless stated otherwise:

- **Algorithms:** `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold)
- **Ranking gate:** `MIN_RANKING >= 44`, **except** the four studies whose cohort variable is the
  `QullamaggieRanking` score or one of its three dimensions — ADR% (40 pts), pct-above-sma50 (35 pts), entry
  price (25 pts) and the ranking itself. Those run **ungated**, because a >=44 gate filters on the very variable
  being cohorted and empties the cohorts the study exists to measure (a gated ADR run collapsed `[0-1.0)` to
  N=1). Each of the four records the reason in its docstring; the ranking study additionally reports the `>=44`
  population as a reference row, so what the gate would keep can still be read off.
- **Period:** 2015-01-01 : 2026-06-26 — longer than the `backtest-v4` baseline window on purpose, so individual
  cohorts still carry enough trades to read
- **Output columns:** `Cohort  N  Med%  Mean%  Win%  Sortino  PF  CVaR95%`
- **Header:** a `## Configuration` table (`| Parameter | Value |`) carrying every filter once at the top of the
  doc, rendered by `turtlex/common/report.py:config_table`. Values that depart from this shared setup — a
  dropped filter, an ungated run, a non-standard algorithm set — are bolded by the caller.
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
  `MIN_RANKING >= 44`) — the tight-range cap is the dimension under study, so the variants pair it with s20/s15
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

### SPY SMA regime cohorts

**Goal:** How the market-regime filter `spy_close > mean(spy_close[-(N+1):-1])` affects results, sweeping the
lookback N. The production setting is N = 200.

- **Period:** Special periods as a regime filter's whole purpose is sitting out bear markets [2006 : 2010], [2018 : 2023]
- **Cohorts:** N = 150, 200, 250, 300, 350, plus `regime off`
- **This is a variant sweep, not a partition.** The cohort variable is a *parameter of the filter*, not a
  property of a signal, so the rows overlap: a signal clearing SMA150 usually clears SMA350 as well. Each row
  is the **whole** signal population under that regime setting, and the rows do **not** sum to `regime off`.
  Read a row as "what this algorithm would have produced with that lookback".
- **Filter under study is dropped:** `spy_above_200d` is removed and replaced by the swept variants. `SMA200 *`
  marks the production setting; `regime off` is the dropped-filter reference row at the foot of each table.
- **Ordering matters:** the regime gate runs *before* the 30-day cooldown, exactly as in production, so a
  different N also changes which triggers win the cooldown slot. Row counts are therefore not a clean subset
  relationship, and every variant regenerates signals rather than re-filtering a shared candidate set.
- **Script:** `scripts/qullamaggie-cohorts-spy-sma.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-spy-sma.md`
- **Note — period choice.** This study deliberately departs from the standard 2015-2026 cohort window: a regime
  filter can only pay for itself in a downturn, so both windows straddle one — 2006-2010 covers the 2008 crash,
  2018-2023 covers 2018 Q4, the 2020 Covid crash and 2022. Its numbers are therefore **not** comparable with the
  other cohort studies. Each window is loaded and simulated separately; a single 2006-2023 span would pull ~20
  years of the qualified universe and exhaust the memory cap.

### Sector cohorts

**Goal:** How company `sector` affects performance.

- **Cohorts:** different company sectors
- **Filter under study is dropped:** the Communication Services / Real Estate universe exclusion is removed,
  otherwise those two cohorts would be empty. It returns as the `excl Comm/RE (cap)` reference row at the foot
  of each table.
- **Script:** `scripts/qullamaggie-cohorts-sector.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-sector.md`

### Market cap cohorts

**Goal:** How company size relates to performance, including the three sub-floor bands the production universe
never sees.

- **Cohorts:** `(<300M)`, `[300M-1B)`, `[1B-1.5B)`, `[1.5-3B)`, `[3-10B)`, `[10-30B)`, `[30-100B)`, `(>100B)`
- **Filter under study is dropped:** the `market_cap >= 1.5B` universe floor is removed, otherwise the first
  three cohorts would be empty. It returns as the `>=1.5B (cap)` reference row at the foot of each table. The
  two bands straddling the floor (`[1B-1.5B)` and `[1.5-3B)`) are deliberately narrow so the floor itself can be
  read directly rather than inferred from a wide bucket. The top two bands are merged into `(>100B)` because
  only 37 qualified symbols exceed 300B.
- **⚠ Descriptive only — this cohort variable carries look-ahead.** `turtle.company.market_cap` is a single
  snapshot column with no history, so a 2015 trade is bucketed by its company's market cap **today**.
- **Memory — the universe is read in market-cap slabs.** Dropping the floor takes the read from 5.77M rows to
  11.75M, roughly double the widest existing study, which already peaks near the 4 GB cap. The script therefore
  loads `[0, 1.5B)` and `[1.5B, inf)` separately. `max_market_cap` on
  `DailyBarsQueryRepository.get_qualified_universe_bars_pl` exists for this.
- **Script:** `scripts/qullamaggie-cohorts-market-cap.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-market-cap.md`

### Average volume cohorts

**Goal:** How the liquidity floor `avg_vol_20 = mean(volume[-21:-1]) >= 100K` affects performance, including the
sub-floor band the production filter never lets through.

- **Cohorts:** `(<100K)`, `[100-250K)`, `[250-500K)`, `[500K-1M)`, `[1-2M)`, `[2-5M)`, `[5-10M)`, `(>10M)`
- **Filter under study is dropped:** the `avg_vol_20 >= 100K` floor is removed, otherwise the `(<100K)` cohort
  would be empty. It returns as the `>=100K (cap)` reference row at the foot of each table. The bands
  straddling the floor (`(<100K)` and `[100-250K)`) are deliberately narrow so the floor itself can be read
  directly rather than inferred from a wide bucket. The `[250-500K)` / `[500K-1M)` split is a leftover from
  the original 500K floor and is kept so the two runs stay comparable.
- **Note — this study is why the floor moved.** The first run (2026-08-02, at a 500K floor) found volume
  predicts nothing above 100K — `>=500K` scored the same as no floor at all while discarding 42% of signals —
  but `(<100K)` is genuinely bad: median +6.8% against ~+40% everywhere else, worst win rate, and a -86.6%
  CVaR95, i.e. a right-skewed pile of near-total losses carried by a few large winners. The floor moved to
  100K on 2026-08-02, the one boundary that separates something.
  `docs/research/result-qullamaggie-cohorts-avg-vol.md` was re-run on 2026-08-09 and now carries the
  `>=100K (cap)` reference row; the cohort rows themselves never moved, since the study drops the floor
  either way.
- **⚠ A sub-floor cohort scoring well is not automatically a relaxation.** Unlike ADR or RSI, this floor is
  partly a *tradability* constraint rather than a pure alpha filter: a 3-5% portfolio position in a thin name
  moves the price the backtest measures it at, so the returns get less attainable the lower the cohort sits.
  Any relaxation proposed off this study has to clear a fill-realism check, not just a Sortino comparison.
- **Note — the floor is denominated in shares, not dollars,** so it is not a constant liquidity bar across the
  `$5-$250` price band: a $200 name at 400K shares ($80M/day) is excluded while a $6 name at 600K shares
  ($3.6M/day) passes. If the cohorts show the floor is doing real work, the follow-up question is whether a
  dollar-volume floor would do it better.
- **Memory:** unchanged from the other cohort studies — the `market_cap >= 1.5B` universe floor still applies,
  so this is a standard single-load study, not a slabbed one.
- **Script:** `scripts/qullamaggie-cohorts-avg-vol.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-avg-vol.md`

### Ranking cohorts

**Goal:** How Qullamagie ranking different deciles affects performance.

- **Cohorts:** two views of the same trades — fixed score bands `[0-20), [20-40), [40-50), [50-60), [60-70),
  [70-80), [80-90), [90-100]` (stable across runs, comparable with the ranking table in
  `scripts/qullamaggie-signals-v4.py`) and population deciles (which adapt to where the score mass sits).
  Both tables carry a `>=44 (gate)` reference row at the foot.
- **Filter under study is dropped:** no production *filter* is dropped, but the `MIN_RANKING >= 44` gate is not
  applied — the gate is the cohort variable, so applying it would empty every cohort below 44. It returns as the
  `>=44 (gate)` reference row, against an `ALL (ungated)` row.
- **Script:** `scripts/qullamaggie-cohorts-ranking.py`
- **Results:** `docs/research/result-qullamaggie-cohorts-ranking.md`

## Entry-timing / limit-order studies

### Limit-order entry cohorts

**Goal:** How buying on the next day with a limit order (limit price = previous day closing price − X%) affects results.

- **Algorithms:** `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold, `MIN_RANKING >= 44`)
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
- **Note:** no tight_range and no vol_dry_up — the latter was retired from the strategy on 2026-08-01, so
  neither appears in the fixed-filter list any more.
- **Note:** the script takes its signals from `turtlex/research/qullamaggie.py`, so all three variants are on
  the `_v2.0` labels with an s16 middle variant and the `MIN_RANKING >= 44` gate applied. Because the entry
  convention *is* the dimension under study, it reports two reference columns side by side: `next-open` (the
  canonical v2.0 entry) and `EOD` (signal-day close, the pre-v2.0 convention kept for comparability with
  earlier runs and used by the monthly grids). `docs/research/result-qullamaggie-cohorts-limit-order.md` is
  the 2026-08-09 re-run and carries all of that; the 2026-07-22 version it replaced (`_v1.3_roc100`, s15,
  ungated, EOD only) is not comparable with it.

### Limit-order fill rate

**Goal:** Calculate `bk50d_s12_v2.0` signals, then figure out the percentage of signals where the price drops X% during the next Y days so that a resting limit order would be filled.

- **Filters:** same as `scripts/qullamaggie-signals-v4.py` (RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, SPY>200d SMA, close>$5&<$250, avg_vol>=100K, no tight_range, cooldown 30d, mcap>=1.5B excl Comm/RE), plus the standard `MIN_RANKING >= 44` gate
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
- **Note:** the committed doc is the 2026-08-09 re-run, titled `bk50d_s12_v2.0` with
  `QullamaggieRanking >= 44` in its config table, so its fill rates are the gated ones. The 2026-07-23 version
  it replaced was titled `bk50d_s12_v1.3_roc100` and had no gate; fill rates from an ungated signal set are not
  the fill rates of the gated one — the gate removes the low-ADR, high-priced names whose pullback behaviour
  differs — so nothing from that version is comparable.

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
- **Fixed filters reference:** roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=100K, cooldown 30d, mcap>=1.5B excl Comm/RE
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

**Goal:** Propose weights for `turtlex/strategy/ranking/qullamaggie.py` assuming the ranking depends only on `adr_pct`, `pct_vs_sma50` and price; validate against the previous weighting by re-running the portfolio simulation, and check whether the gate is still reasonable. **The gate was 40 when this study ran and is 44 now** — the script's `PROD_GATE` is 44 and its `GATES` sweep brackets it at 42/44/46, the range matching the old `>=40` selectivity under the new weights.

- An ad-hoc per-trade scan (1685 bk50d_s12 signals, 2010-2020, 366d returns with each year's mean subtracted) found only three of the six dimensions kept the sign of their cross-sectional effect across both halves: ADR%(20) rho +0.121, %above-SMA50 +0.099, price -0.059. Compression/ROC252/RSI were 25-75% time effect and reversed sign. That scan is not committed — the weights it produced are.
- Kept the cohort band *shapes* and rescaled them to 40/35/25; coarser monotone bands fitted to the scan's own decile shape were tried and were worse.
- Validation deliberately avoids three traps: comparing schemes at a fixed gate (which compares selectivity, not skill — a score of 40 keeps 59% of signals under the old weights and 40% under the new), reading a result without a same-size random-subset null, and cutting top-K inside tie groups by date.
- Result: the new weights win at every selectivity at s12 and s16 and are mixed at s20. The gate remains reasonable, and becomes a live filter at s20 where the old weights never dropped a single signal. Re-picking it at matched selectivity is what moved it from 40 to 44 on 2026-08-09.
- **Script:** `scripts/qullamaggie-ranking-weights.py` (new)
- **Results:** `docs/research/result-qullamaggie-ranking-weights.md`
- **References:** `turtlex/strategy/ranking/qullamaggie.py`, `docs/research/result-qullamaggie-cohorts-*.md`, `docs/research/result-qullamaggie-ranking-validation.md`

### Ranking improvement loop

**Goal:** raise the *held-out decile monotonicity* of `QullamaggieRanking` — the score should
order 366d outcomes, not merely separate them on average — without giving up
matched-selectivity portfolio performance.

The problem, from the committed evidence: `result-qullamaggie-cohorts-ranking.md` shows 8/9
non-decreasing Sortino decile steps at s12 but 6/9 at s16 and 5/9 at s20, and
`result-qullamaggie-ranking-validation.md` shows 5/9 for the production bands on the held-out
2021+ slice. The failure is concentrated out of sample and at the tighter entry filters.

**Invocation:** `/loop` (dynamic mode) with this prompt. One hypothesis per iteration.

**Per-iteration procedure:**

1. Read `docs/research/result-qullamaggie-ranking-lab.md` — the current baseline and every
   hypothesis already tried, accepted or rejected.
2. Pick the highest-value untried item from the backlog below, or a follow-up to whatever was
   accepted last. Prefer a hypothesis that attacks a *named* cause over one that tunes numbers.
3. Write `docs/research/ranking-lab/candidates/cNNN-<slug>.json` with a one-sentence falsifiable
   hypothesis in its `hypothesis` field — what should improve, and why that follows from the
   cause it attacks. Say what would make it wrong.
4. Stage B only: run `--screen <feature>` first. A feature that fails the screen may not enter
   a spec, however good it looks in aggregate.
5. Run `uv run scripts/qullamaggie-ranking-lab.py --eval <spec>` under the memory cap. This
   reads the parquet cache and needs no database; only `--build-cache` does, and that one
   needs `ACTIVE_PROFILE=hetzner-db` for history deeper than the local five-year mirror.
6. Read the verdict. The harness applies the acceptance rule and appends the ledger row itself
   — do not hand-edit the row or re-run until the number comes out right.
7. On ACCEPT: update the **Current baseline** line in the ledger, pass the new spec as
   `--baseline` from then on, and add follow-up hypotheses that build on what worked.
   On REJECT: say in one line *why the hypothesis was wrong*, not merely that it lost.

**Hard rules:**

- Never edit `turtlex/strategy/ranking/qullamaggie.py`, any `MIN_RANKING` constant, or any
  existing `result-*.md` from inside the loop. Promotion is a separate, user-approved step —
  it re-picks the gate at matched selectivity and stales ~15 committed result docs.
- Never compare two schemes at a fixed gate. A gate keeps a different fraction of signals under
  each scheme, so that compares selectivity, not skill. Always matched keep-%.
- Never touch entries on or after 2025-01-01. That slice is opened once, at promotion.
- Report every rejection. A backlog item that failed is the useful half of the record.
- A candidate that only wins in one sub-period has not won. This is the same standard that
  dropped compression/ROC252/RSI on 2026-07-29 — apply it to the incumbents too.

**Stop conditions:** 5 accepted baselines, or 3 consecutive rejections with the current stage's
backlog exhausted, or user interrupt.

#### Seeded hypothesis backlog

Stage A — the existing three features, no new data:

| # | Hypothesis | Cause it attacks |
| --- | --- | --- |
| A1 | Non-compensatory aggregation (`min`) | compensation |
| A2 | `sum_then_isotonic` — enforce train-monotonicity, test out of sample | direct |
| A3 | `linear_clip` ramps replacing coarse bands | tie clumping |
| A4 | `percentile_trailing` normalization of each feature | regime drift |
| A5 | Coordinate-descent weight re-fit on train folds (steps of 5, sum 100) | weights fitted on the full period |
| A6 | `grid2d` over ADR x SMA50-distance, replacing the two additive terms | interaction |
| A7 | Drop price entirely (rho was only -0.059, and floor-anchoring already cut its effective weight to ~20); test 50/50 | over-parameterization |

Stage B — new features, each screened first, then added at low weight:
`pct_off_52w_high`, `rs_63d`/`rs_126d` (relative strength, unlike the absolute `roc_252d` that
failed), `sma_stack`, `pct_vs_sma200` + `sma200_slope_20d`, `base_depth_50d` /
`days_since_50d_high`, `vol_dryup`, `breakout_vol_ratio` + `close_in_range` + `gap_pct`,
`breadth_sma50`, `adr_rel`.

- **Spec:** `docs/specs/qullamaggie-ranking-loop.md` (protocol, acceptance rule, promotion)
- **Script:** `scripts/qullamaggie-ranking-lab.py` (`--build-cache` once, then `--eval` / `--screen`)
- **Results:** `docs/research/result-qullamaggie-ranking-lab.md`
- **References:** `turtlex/strategy/ranking/qullamaggie.py`, `docs/research/result-qullamaggie-cohorts-ranking.md`, `docs/research/result-qullamaggie-ranking-validation.md`, `docs/research/result-qullamaggie-ranking-weights.md`

### Portfolio pacing

**Goal:** decide whether capping new positions per calendar month improves the live portfolio.

- **Motivation:** at $30,000 with 4% positions the book holds 25 names while s12 raises ~14 gated
  signals a month (1698 over the study's 2015-2024 window; ~36 a month before the gate) against the
  two or three the book can fund once it is full, so capacity can be consumed by a single month's
  signals — one entry vintage carrying the whole year, with nothing left for a better signal that
  appears later.
- **Answer: no.** The cap diversifies entry vintages exactly as intended (busiest-month share
  38.6% -> 8.9% at an 18-month horizon) and produces no gain in return, drawdown or start-date
  dispersion at any horizon tested. At 18 months it cuts dispersion and the mean in the same
  proportion — holding less exposure, not managing risk — and leaves the worst start date worse
  off. Adopt it as a preference if a concentrated vintage is uncomfortable to hold, not as an edge.
- Vintage concentration is a claim about **start-date dependence**, so a single backtest cannot
  test it: every horizon is replayed from quarterly start dates with fresh capital and the spread
  across them is reported alongside the average.
- The cap must not peek. `run_sim`'s `max_new_per_month` takes signals as they arrive within a
  month, best-scored first on any given day; picking "the best N of the month" would need the
  month in advance.
- Quarterly starts drawn from one ten-year window overlap heavily, so the dispersion columns rule
  out a large effect rather than resolving a small one.
- **Script:** `scripts/qullamaggie-pacing.py` (reads the ranking-lab cache; no database needed)
- **Results:** `docs/research/result-qullamaggie-pacing.md`
- **References:** `turtlex/research/portfolio_replay.py`, `docs/research/result-qullamaggie-ranking-lab.md`

## Portfolio simulation

### Portfolio simulation

**Goal:** Portfolio simulation over `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` signals.

- **Period:** 2021-01-01 : 2026-06-26
- **Algorithms:** `bk50d_s20_v2.0`, `bk50d_s16_v2.0`, `bk50d_s12_v2.0` (366d hold)
- **Ranking:** Calculate ranking (turtlex/strategy/ranking/qullamaggie.py) for all transactions, prefer signals with higher ranking.
Calculate results with applying filter `MIN_RANKING >= 44` and without applying it.
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
  **Ranking gate:** `QullamaggieRanking >= 44` drops 190 signals (0 with no fillable next-day open);
  ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair
  reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

  size   gate          Final$   CAGR%  MaxDD%   Calmar  Sortino  taken   skip  Uninv%
  -----------------------------------------------------------------------------------
  3%     R>=44        231,265  +45.20   -31.94   1.415    1.959    186    535    9.7%
  3%     ungated      202,291  +41.69   -28.99   1.438    1.838    192    719    9.0%
  4%     R>=44        166,413  +36.73   -27.47   1.337    1.621    142    579    9.0%
  4%     ungated      157,481  +35.36   -27.47   1.287    1.599    145    766    8.9%
  5%     R>=44        218,205  +43.66   -30.67   1.424    1.817    116    605    9.5%
  5%     ungated      235,503  +45.68   -30.67   1.489    1.887    117    794    9.3%
  ```

- List of Top 5 by Final$, List of Top 5 by Sortino

- List yearly results for these algorithms `s12 R>=44 3%`, `s12 R>=44 4%`, `s12 R>=44 5%` + Top 2 from Final$
  Yearly means portfolio result by end of the year (2021 : 2025) compared to previous year end

```text
  algo             year          Final$   CAGR%  MaxDD%   Calmar  Sortino  taken   skip  Uninv%
  ---------------------------------------------------------------------------------------------
  s12 R>=44 3%     2021         285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
                   2022         285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
                   2023         285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
                   2024         285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
                   2025         285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
  s12 R>=44 4%     2021         263,361  +48.68   -28.27   1.722    2.021    145    755    8.3%
  ...
```

- For the `s12 R>=44 3%`, `s12 R>=44 4%`, `s12 R>=44 5%` + Top 2 from Final$, print `monthly returns`
  and `trades count in particular month` by years (years are rows, months are columns):

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

### Exit strategy analyze

**Goal:** Analyze different exit strategies to improve `scripts/qullamaggie-portfolio-sim.py` CAGR% and Sortino. Provide 5 ideas and validate them against the current 366d time-cap exit. To simplify testing use only `bk50d_s12_v2.0` / 366d / 3% of portfolio.

- **Period:** 2021-01-01 : 2026-06-26, initial $30,000, ranking gate >= 44
- **Baseline to beat:** :

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
```

- **Pass bar (pre-registered):** CAGR **and** Sortino both above baseline, and MaxDD no more than 5pp worse
- **Ideas swept**, each with the 366d time cap still active underneath as a backstop:
  - `regime` — exit when SPY has closed below its 200d SMA for N consecutive days
  - `trail` — trail T% below the running peak close, armed only once the trade is up A%
  - `dead` — exit if the trade is not up at least R% after N trading bars
  - `trend` — exit after N consecutive closes below the position's own EMA20 / SMA50 / SMA200
  - `atr` — fixed stop at entry - k x ATR(14) measured at entry
- **Controls:** the four exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim` (`stop30`, `trail25`, `sma200x5`, `dead120` — `EXIT_MODES = ["time"]` never selects them)
- **Overfit guards:** baseline reconciliation against the committed portfolio-sim numbers; the full metric surface per idea rather than the winning cell alone (a real effect is a plateau, an artifact is a spike); per-year decomposition; stationary block bootstrap (1,000 resamples of 21-day blocks, paired on day indices)
- **Robustness matrix:** the best single-window rule re-run across 2010-2015 / 2016-2020 / 2021-2026 at s20 / s16 / s12
- **Output format:**

  ```text
  variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip
  -------------------------------------------------------------------------------------------
  <+10% after 120 bars          239,985  +46.18   -34.37   1.343    2.066    240    650  fail
  baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
  ```

- **Script:** `scripts/qullamaggie-exit-sweep.py` (new)
- **Results:** `docs/research/result-qullamaggie-exit-sweep.md`
- **References:** `turtlex/research/qullamaggie.py` (shared signal layer, parity-tested), `turtlex/backtest/metrics.py` (`compute_trade_metrics`), `docs/research/result-qullamaggie-portfolio-v4.md` (baseline), `docs/research/result-qullamaggie-portfolio-v4-2010-2015.md` and `-2016-2020.md` (cross-checks for the earlier matrix windows)
- **Note — the headline result is negative; keep the 366d time cap.** On the committed 2026-08-09 re-run
  **no variant of any idea cleared the pass bar** — 0 of 8 `regime`, 0 of 12 `trail`, 0 of 24 `dead`, 0 of 9
  `trend`, 0 of 5 `atr`, against a baseline of +50.84% CAGR / 2.168 Sortino / -27.91% MaxDD. The best variant
  per idea loses 4.65 to 14.25pp of CAGR. The robustness matrix, still run on `<+5% after 90 bars` (the rule
  that had looked decisive on the pre-removal signal set), now passes **1 of 9** config/period cells — and the
  one pass is *2010-2015 s12*, not the 2021-2026 window it was fitted on, which is regime-specificity rather
  than a surviving edge. The bootstrap agrees: every finalist wins on 7-28% of resampled CAGR paths.
- **Note — the earlier, pre-`vol_dry_up`-removal run reached the same conclusion by a longer route,** and the
  reasoning is worth keeping because it is the general trap. On that signal set `<+5% after 90 bars` cleared
  every single-window guard (a bounded 90-150 bar plateau, better in 6 of 7 years, 91.8% / 94.1% bootstrap win
  rates) and was killed only by the matrix. A follow-up run of the full 24-cell dead-money grid across all 9
  cells (216 sims, run ad-hoc against that signal set; not kept as a script) found **no** parameterisation
  passing more than 4 of 9, and 23 of 24 had a negative mean dCAGR. The passing region *moves* between eras —
  2021-2026 favoured short cutoffs, 2010-2015 long ones, 2016-2020 none at all. The single-window guards all
  agreed with each other because they were all measuring the same six years; they cannot detect that the window
  itself is the special case.
- **Note:** the study's own baseline reconciles with the committed portfolio-sim figure to 0.04pp CAGR
  ($285,404 / +50.88% / -28.01% committed against $284,922 / +50.84% / -27.91% for the harness) despite
  generating signals through `turtlex/research/qullamaggie.py` rather than the sim's inline copy — the harness
  runs its cooldown chain through the warmup window, the sim starts it at the evaluation start, so a small
  divergence is expected and a large one would invalidate every comparison in the doc.
- **Note:** exits fill at the day's adjusted close, so stop-based rules are measured optimistically; the universe filter uses *current* `company.market_cap >= $1.5B`, which inflates every absolute figure (baseline included) and worsens the further back the window sits.

## Live signal generation

### Signals: s12 with cohorts

**Goal:** Provide `bk50d_s12_v2.0` signals (`MIN_RANKING >= 44`) for period 2026-06-01 : today.

- **Output columns:**

  ```text
  Date │ Symbol │ Sector │ %abv SMA50 │ ADR% │ ADR_CHG │ VOL_DRY │ RSI14 │ TR% │ ROC252% │ Last date │ Ranking │ Entry $ │ Curr Price │ Change %
  ```

  - `Ranking`, `Entry $`, `Curr Price` and `Change %` sit at the end on purpose: they are what the eye
    lands on, so they read off the right edge rather than from between `Sector` and the indicator block.
  - `%abv SMA50`, `ADR%`, `ADR_CHG`, `VOL_DRY`, `RSI14`, `TR%`, `ROC252%` must be calculated on the **signal** date, since that is the bar every filter is evaluated on.
  - `Sector` = `turtle.company.sector`. The signal universe excludes Communication Services and Real
    Estate, so neither ever appears here — the current-investments table below reads the same column
    but over whatever is actually held, so both sectors can show up there.
  - `VOL_DRY` = `mean(volume[-11:-1]) / mean(volume[-51:-1])`, both shift-1 — the old `vol_dry_up < 0.90`
    filter, **retired 2026-08-01** (see [Vol dry-up cohorts](#vol-dry-up-cohorts)). Shown for information
    only, like `TR%`; values at or above 0.90 now appear where they previously could not.
  - `Last date` = latest date when stock data is available in the `turtle.daily_bars` table.
  - `Ranking` - ranking calculated according to @turtlex/strategy/ranking/qullamaggie.py

- Write also a separate table with aggregated results where `%abv SMA50` is in cohorts [12-15), [15-17.5), [17.5-20), (>20):

  ```text
  Cohort | N | Med% | Mean% | Win% | PF | Sortino | Max DD
  ```

- Write also a separate table with aggregated results where `Ranking` is in cohorts [0-20), [20-40), [40-60), [60-80), (>80):

  ```text
  Cohort | N | Med% | Mean% | Win% | PF | Sortino | Max DD
  ```

- Write current investments value, source table is `turtle.lightyear_transaction` + add Curr Price and Change% from `turtle.daily_bars`,
  exclude shares where `Shares` <= 0
  - `Entry date` - First buy date from `turtle.lightyear_transaction`
  - `Signal date` - Closest date before `Entry date` when a signal was generated: the newest
    `bk50d_s12_v2.0` signal — **ungated**, no `QullamaggieRanking` filter — sitting **strictly**
    before the buy and no more than 50 calendar days earlier, so a stale trigger cannot attach
    itself to an unrelated buy. The window is deliberately wider than the 30-day cooldown — a buy
    placed weeks after the breakout still finds its trigger — so unlike a cooldown-width window it
    can hold two signals, and the newest one wins. `--` when no such signal exists: either the
    newest one falls outside the 50-day window, or the symbol never signalled at all.
  - `Days` - calendar days held, `Last date` − `Entry date`. The operands are this way round so a
    holding period reads positive; `Last date` is the symbol's latest usable bar — the same one
    `Curr Price` comes from — and is not shown as a column of its own.
  - `Ranking` - `QullamaggieRanking` scored on the `Signal date`. Ungated like the signal it comes
    from, so a score below the 44 the signal table gates on is printed as it stands and a buy made
    off a weak signal stays visible; `--` exactly when `Signal date` is `--`, since there is no bar
    to score the ranking on.
  - `Avg Price` - quantity-weighted average ticker price over the **buys** in
    `turtle.lightyear_transaction`. Sells reduce `Shares` but never move the cost basis, so `PL` is
    purely unrealized — the realized gain on shares already sold is not shown. It is the per-share
    `price`; the statement's `fee` and `tax` columns are deliberately not folded in, so `PL` reads
    slightly better than the realised result.
  - `Shares` - total number shares `turtle.lightyear_transaction` calculated over same ticker buys and sells
  - `Curr Price` - the symbol's latest **raw** close in `turtle.daily_bars`; the statement records the
    actual fill price, so only the unadjusted series is comparable with `Avg Price`
  - `Change %` - `(Curr Price / Avg Price − 1) × 100`
  - `PL` - `(Curr Price − Avg Price) × Shares` Profit/Loss of current investment, in dollars
  - A `TOTAL` row closes the table with portfolio cost, value, change and PL — the "value" this bullet asks for

  ```text
  Symbol │ Sector │ Signal date │ Entry date │ Days │ Ranking │ Avg Price │ Shares │ Curr Price │ Change % │ PL
  ```

- Compare also mean(Mean%) with SPY.US and QQQ.US return for the whole period. Exclude LC.US and other suspicious data points.
- **Script:** `scripts/qullamaggie-signals-v4.py`
- **Output:** screen
- **References:** `docs/research/qullamaggie-backtest-v4.md`, `scripts/qullamaggie-backtest-v4.py`
- **Note:** the script prints the full report — signal table, exclusions, both cohort tables, current investments and the benchmark comparison — to stdout. It used to also write `docs/research/result-qullamaggie-signals-v4.md`; that doc was deleted 2026-07-25 because the report is only meaningful for the day it is run.
- **Note:** the signal table is gated at `MIN_RANKING >= 44`, but both cohort tables are computed over the *ungated* s12 signals on purpose. Gating them would leave the `[0-20)` and `[20-40)` ranking buckets permanently empty and destroy the only thing those tables measure — whether the score separates outcomes at all. The summary line reports how many signals the gate dropped so the two views reconcile.

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
  avg_vol>=100K, >12% above the 50d SMA, cooldown 30d, mcap>=1.5B excl Comm/RE.

## Maintenance

### Maintenance: lint & tests

Run Ruff + mypy + pytest.

### Validate and run cohorts

- Verify that the cohort descriptions in `@docs/research/prompts.md` match the code in `@scripts/*.py`. If there are discrepancies, ask how to proceed.
- Verify that the cohort results are in sync with the cohort Python code in `@scripts/*.py`. If they are not, re-run the script.
- Validate the results in `@docs/research/result-qullamaggie-cohorts-*.md` and answer the following questions:
  - Are all filters in `@scripts/qullamaggie-backtest-v4.py` justified — does each one improve Mean% and/or Sortino? If any do not, surface those findings to the screen.
  - Is there a way to loosen the filters to generate more signals without degrading performance (Mean% and/or Sortino)? Surface those findings to the screen.

## Gap: what is still unvalidated

`cooldown 30d` is the last filter with no **cohort** study, but it is not unmeasured: the relaxation sweep runs a
`cd15` variant (30 -> 15 days) and `docs/research/result-qullamaggie-relax-sweep.md` reports it as mildly
favourable — N 1541 -> 1658, F/mo 11.2 -> 12.1, Mean% +57.76 -> +58.08, Sortino 3.454 -> 3.471 — and it survives
into two of the three combos. What is missing is a cohort study sweeping the window properly (15/30/45/60), so
the shape of the tradeoff past 15 days is unknown.

`market_cap >= 1.5B` now has a study but is **not** validated by it: the cohort variable carries look-ahead (see
[Market cap cohorts](#market-cap-cohorts)), so the study describes which of today's size classes the good trades
came from and cannot say whether the floor helps. That needs a point-in-time cap the schema does not carry.

`avg_vol >= 100K` and `SPY > 200d SMA` are covered — see [Average volume cohorts](#average-volume-cohorts) and
[SPY SMA regime cohorts](#spy-sma-regime-cohorts).
