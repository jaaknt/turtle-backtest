# Qullamaggie Ranking Improvement Loop

## Context

`QullamaggieRanking` (`turtlex/strategy/ranking/qullamaggie.py`) sums three piecewise-constant
band scores — ADR%(20) 0-40, distance above SMA50 0-35, raw close price 0-25 — and the portfolio
gates on `MIN_RANKING >= 44`. The score separates outcomes on average but **does not order them
monotonically**, and the committed evidence says so:

| Slice | Sortino monotone decile steps |
| --- | --- |
| `result-qullamaggie-cohorts-ranking.md`, s12 population deciles | 8/9 |
| same doc, s16 | 6/9 |
| same doc, s20 | 5/9 |
| `result-qullamaggie-ranking-validation.md`, production bands, held-out 2021+ | **5/9** Sortino, 6/9 Mean% |

So the failure is concentrated exactly where it matters: out-of-sample, and at the tighter
entry filters. Three structural causes are visible in the current design:

1. **Compensation.** The score is additive, so 40 ADR points fully offset a bottom-band SMA50
   distance. Signals with identical scores are not comparable populations, which is enough on its
   own to invert deciles.
2. **Tie clumping.** Coarse bands leave huge groups on one score — s12 decile D1 is 702 signals
   spanning scores [20-25]. A decile boundary that falls inside a tie group is arbitrary.
3. **Absolute, not regime-relative.** An ADR of 5% meant something different in 2017 than in 2021,
   but scores the same points.

The goal is a repeatable loop that proposes one hypothesis at a time, judges it under a fixed
protocol that cannot be gamed by selectivity, and only then replaces the baseline. Improving
the ranking by hand-fitting to the full period is what produced the current non-monotonic scheme
(`result-qullamaggie-ranking-weights.md` notes the 40/35/25 split was kept despite failing the
same sub-period test used to disqualify three other dimensions) — the protocol exists to stop
that repeating.

**Chosen scope** (confirmed with the user): prompt + lab harness; `/loop` dynamic mode with a
bounded budget; monotonicity gate with portfolio confirmation; hypothesis space = recalibrating
the existing three features **and** screening new technical features. Fitted models (GBM /
logistic) are out of scope. Fundamentals are out of scope — `turtle.company_history` holds only
three snapshots (2026-05-30 … 2026-07-30), so any fundamental feature carries look-ahead over a
2015-2026 backtest.

---

## Deliverables

| File | Role |
| --- | --- |
| `turtlex/research/ranking_lab.py` | **new** — spec model, feature transforms, aggregations, PAVA isotonic, Spearman, decile/fold protocol |
| `turtlex/research/portfolio_replay.py` | **new** — `Market`, `run_sim`, `top_k` for the confirmation replay |
| `scripts/qullamaggie-ranking-lab.py` | **new** — CLI: `--build-cache`, `--eval SPEC`, `--screen FEATURE` |
| `tests/research/test_ranking_lab.py` | **new** — parity + unit tests |
| `docs/research/ranking-lab/candidates/*.json` | **new** — one file per hypothesis (the committed record) |
| `docs/research/result-qullamaggie-ranking-lab.md` | **new** — append-only ledger of every iteration |
| `docs/research/prompts.md` | **edit** — add `### Ranking improvement loop` under `## Ranking` + index row |
| `config/settings-hetzner-db.toml` | **new** — read the VPS Postgres over Tailscale for the deep history the cache needs |
| `.gitignore` | **edit** — one line for `.cache/ranking-lab/` |

Nothing under `turtlex/strategy/ranking/`, no `MIN_RANKING` constant, and no existing
`result-*.md` is touched by the loop. Promotion is a separate, user-approved step (below).

---

## 1. Signal cache — make each iteration cheap

`scripts/qullamaggie-ranking-lab.py --build-cache` runs **once** (re-run only when data changes):

- Loads bars **2010-01-01 … 2026-06-26** in 3-year chunks, each fetched with the standard
  730-day warmup, so peak memory stays at today's levels rather than scaling with the window.
  The 30-day cooldown chain in `qm.get_signals` already runs over the warmup rows, so chunk
  boundaries do not create phantom signals.
- Per chunk: `qm.load_bars` → `qm.add_indicators` → `add_lab_features` (new, below) →
  `qm.get_signals(sma_thresh=…)` for 0.12/0.16/0.20 → `qm.resolve_entries`.
- Computes each signal's fixed **366-calendar-day** forward return on `adj_close` from the
  entry bar, mirroring `run_trades` in `scripts/qullamaggie-cohorts-ranking.py` — entry at the
  next day's adjusted open, exit at the adjusted close 366 days on — plus a
  `ret_demeaned` column (entry-year mean subtracted) — the year-demeaning that the 2026-07-29
  scan used and that the loop's rank metric needs.
- Writes to `.cache/ranking-lab/`: `signals-s12.parquet`, `-s16`, `-s20`, and `prices.parquet`
  (`symbol, date, adj_close` restricted to symbols that ever signal). Gitignored, regenerable.

The local Docker Postgres is a five-year mirror (`scripts/update-local-db.sh`), so the build
must read the VPS through the `hetzner-db` profile — added for this, and the one profile that
names a database rather than a machine. Run it under the standard cap (CLAUDE.md "Running
Research Studies"):

```bash
ACTIVE_PROFILE=hetzner-db \
  systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 \
  uv run scripts/qullamaggie-ranking-lab.py --build-cache
```

`--eval` and `--screen` read the parquet cache and touch no database, so they run unqualified.

After this, `--eval` scores ~10.9k rows across the three configs and finishes in seconds. That is what makes a loop viable.

### `add_lab_features` — candidate feature columns

Added in `turtlex/research/ranking_lab.py`, computed on shift-1 values exactly like
`qm.add_indicators`, so nothing leaks. All derive from `daily_bars` only:

`pct_off_52w_high`, `rs_63d` / `rs_126d` (return minus SPY's over the same window),
`sma_stack` (ordinal 0-4 over close > SMA10 > SMA20 > SMA50 > SMA200), `pct_vs_sma200`,
`sma200_slope_20d`, `base_depth_50d` (the prior 50-day range as a fraction of its high — a normalized range, not a
drawdown, since the low need not follow the high),
`days_since_50d_high`, `vol_dryup` (`avg_vol_10 / avg_vol_50`), `breakout_vol_ratio`
(`volume / avg_vol_50`), `close_in_range` ((close−low)/(high−low) on the signal bar),
`gap_pct`, `adr_rel` (ADR ÷ cross-sectional median ADR that day), and `breadth_sma50`
(fraction of the qualified universe above its own SMA50 on the signal date).

---

## 2. Candidate spec — hypotheses are data, not code

One JSON file per hypothesis under `docs/research/ranking-lab/candidates/`, committed. This is
the record of what was tried, and it is what `--eval` consumes:

```json
{
  "id": "c003-noncompensatory",
  "hypothesis": "Weighted min instead of sum: a signal weak on any dimension cannot buy a high score with the others, so equal scores describe comparable populations.",
  "parent": "c000-production",
  "aggregate": "min",
  "terms": [
    {"feature": "adr_pct",      "transform": "bands", "bands": [[0.03,0],[0.035,4],[0.04,9],[0.045,12],[0.05,15],[0.07,19],[0.08,33]], "top": 40},
    {"feature": "pct_vs_sma50", "transform": "percentile_trailing", "window_days": 252, "direction": "higher", "weight": 35},
    {"feature": "raw_close",    "transform": "linear_clip", "lo": 10.0, "hi": 250.0, "direction": "lower", "weight": 25}
  ]
}
```

**Transforms** (closed set — keep it small):

- `bands` — the existing `(upper_bound, points)` form, first match wins. Ships as-is to production.
- `linear_clip` — monotone ramp between `lo`/`hi`, clipped, scaled to `weight`. Removes tie clumping.
- `percentile_trailing` — percentile rank within the trailing `window_days` of *raised signals*
  (causal, regime-relative), scaled to `weight`.
- `grid2d` — a 2-D band table over two features, for the one interaction hypothesis.

**Aggregations**: `sum` (today's behaviour), `min` (non-compensatory), `sum_then_isotonic`
(sum, then remap through a PAVA isotonic fit of raw-sum → mean `ret_demeaned`, **fit on the
training fold only**, rescaled to 0-100).

`c000-production.json` reproduces the shipped bands exactly and is the seed baseline.

---

## 3. Evaluation protocol — the fixed judge

`--eval docs/research/ranking-lab/candidates/cNNN-*.json` runs this and nothing else. It is
fixed so candidates are comparable across iterations.

**Folds.** Walk-forward: cutoffs 2019-01-01 … 2024-01-01 (yearly). Train = entries before the
cutoff, test = entries in `[cutoff, cutoff+2y)`. Any fitted piece (isotonic, coordinate-descent
weights) sees the train side only. **Entries on/after 2025-01-01 are a frozen holdout, never
evaluated inside the loop** — it is opened once, at promotion.

**Per fold × config (s12/s16/s20), on the test side:**

- Held-out decile table via `compute_trade_metrics` from `turtlex/backtest/metrics.py`
  (`min_losers=5`) — reuse it, do not recompute Sortino locally (`tests/scripts/test_metric_conventions.py`
  enforces this).
- `mono_sortino` / `mono_mean` — non-decreasing steps out of 9.
- `spearman` — rank correlation between score and `ret_demeaned` (Pearson on average ranks;
  no scipy in this project, and none is being added).
- `spread` — D10 − D1 Sortino; `top_decile_sortino`.

**Portfolio confirmation** — only for candidates that pass the monotonicity gate, since it is the
expensive half. Reuses the replay from `turtlex/research/portfolio_replay.py`: matched
selectivity at keep 35/25/15%, ties broken at random over 10 redraws, against 30 random
same-size subsets, split at the window midpoint (2020-01-01). This mirrors `scripts/qullamaggie-ranking-weights.py`
and measures around the same three traps its docstring names.

> Note: `qullamaggie-ranking-weights.py` keeps its own copy of `Market`/`run_sim`/`top_k`. The
> new module is used by the lab only; the weights script is a frozen record generator and is
> deliberately left untouched. De-duplicating it is a separate, optional follow-up.

### Acceptance rule

A candidate becomes the new baseline only if **all** hold:

1. Fold-mean `mono_sortino` ≥ baseline's, **and** fold-mean `spearman` ≥ baseline + `margin`.
2. No config collapses: in each of s12/s16/s20, `mono_sortino` ≥ baseline − 1 step and
   `spread` ≥ baseline `spread` − 0.35 (an absolute give-back; a proportional one inverts when
   the baseline spread is negative, which individual folds are).
3. Portfolio confirm at keep 25%: mean CAGR ≥ baseline − 1.0pp **and** beats its random null in
   ≥ 27/30 draws, **in both sub-periods**. A gate that cannot be measured — a nan on either
   side — counts as a failure, never as a pass.
4. Simplicity tiebreak: within noise, fewer terms/features wins (CLAUDE.md §2).

`margin = 0.01 + 0.002 · log2(max(1, n_tested/10))` — a multiple-testing budget that rises with
the number of hypotheses the ledger has already recorded, so iteration 40 has to clear a higher
bar than iteration 4. Rejections are logged with the reason; they are the useful half of the record.

### New-feature screening gate

Before a Stage-B feature may appear in a candidate, `--screen FEATURE` must show its
year-demeaned Spearman rho **keeps its sign in both halves of the training period and in all
but one of the fold-training slices** (5 of 6, at the current fold count). This is the standard that dropped compression/ROC252/RSI on
2026-07-29; the docs record that it was then *not* applied to the surviving three. Applying it
evenly is the point.

### Ledger

`--eval` writes one row between the `<!-- lab:ledger:start -->` / `<!-- lab:ledger:end -->`
markers in `docs/research/result-qullamaggie-ranking-lab.md` and touches nothing outside them, so
hand-written analysis survives. The row is keyed on the candidate id: re-running a spec replaces
its row rather than adding a second one, so `n_tested` counts hypotheses rather than invocations
— a `--no-portfolio` preview or a re-measurement after a harness fix must not raise the margin
for every later candidate. (The known
`qullamaggie-portfolio-sim.py` behaviour of clobbering hand-written `## Findings` is exactly
what this avoids.)

---

## 4. The prompt — `### Ranking improvement loop` in `docs/research/prompts.md`

Added under `## Ranking`, with a row in the index table. Content:

- **Goal:** raise held-out decile monotonicity of `QullamaggieRanking` without giving up
  matched-selectivity portfolio performance. Baseline to beat: the table in the Context section above.
- **Invocation:** `/loop` (dynamic mode) with the prompt text; one hypothesis per iteration.
- **Per-iteration procedure:** read the ledger → pick the highest-value untried backlog item →
  write `cNNN-*.json` with a one-sentence falsifiable hypothesis → (Stage B only) `--screen` the
  feature first → `--eval` → apply the acceptance rule → append verdict → if accepted, set the
  new baseline id at the top of the ledger and add follow-up hypotheses that build on it.
- **Hard rules:** never edit `turtlex/strategy/ranking/qullamaggie.py`, `MIN_RANKING`, or any
  existing `result-*.md` from inside the loop; never compare at a fixed gate (always matched
  keep-%); never touch the ≥2025 holdout; report every rejection.
- **Stop conditions:** 5 accepted baselines, or 3 consecutive rejections with the current stage's
  backlog exhausted, or user interrupt.

### Seeded hypothesis backlog (ordered by expected value)

#### Stage A — existing three features, no new data

| # | Hypothesis | Attacks |
| --- | --- | --- |
| A1 | Non-compensatory aggregation (`min`) | compensation |
| A2 | `sum_then_isotonic` — enforce train-monotonicity, test OOS | direct |
| A3 | `linear_clip` ramps replacing coarse bands | tie clumping |
| A4 | `percentile_trailing` normalization of each feature | regime drift |
| A5 | Coordinate-descent weight re-fit on train folds (steps of 5, sum 100), objective = fold-mean Spearman | weight fit on full period |
| A6 | `grid2d` over ADR × SMA50-distance, replacing the two additive terms | interaction |
| A7 | Drop price entirely (rho was only −0.059, and floor-anchoring already cut its effective weight to ~20); test 50/50 | over-parameterization |

#### Stage B — new features, each screened first, then added at low weight

`pct_off_52w_high` · `rs_63d`/`rs_126d` (relative strength, unlike the absolute `roc_252d` that
failed) · `sma_stack` · `pct_vs_sma200` + `sma200_slope_20d` · `base_depth_50d` /
`days_since_50d_high` · `vol_dryup` · `breakout_vol_ratio` + `close_in_range` + `gap_pct` ·
`breadth_sma50` · `adr_rel`.

---

## 5. Promotion (separate, user-approved — not part of the loop)

When the user accepts a baseline for production, and only then:

1. Open the ≥2025 frozen holdout once and report it. A candidate that fails here is dropped.
2. Distil the winning spec into band constants in `turtlex/strategy/ranking/qullamaggie.py`,
   keeping the pure-Python int 0-100 contract of `RankingStrategy.ranking`.
3. **Re-pick `MIN_RANKING` at matched selectivity** — it is scheme-relative, as the module
   docstring says. It is duplicated across ~20 files (`scripts/qullamaggie-cohorts-*.py`,
   `-exit-sweep.py`, `-signals-v4.py`, `-limit-*.py`, `CLAUDE.md`).
4. Re-run the dependent studies; ~15 committed result docs go stale at once.

Steps 2-4 are a large, doc-invalidating cascade. Keeping them out of the loop is deliberate.

---

## Verification

1. `uv run pytest tests/research/test_ranking_lab.py` — the anchor test is **parity**:
   `c000-production.json` must reproduce `QullamaggieRanking.ranking` scores exactly on every
   cached signal. Plus unit tests for PAVA (output is non-decreasing; already-monotone input is
   unchanged), Spearman against hand-computed values, and each transform's monotonicity.
2. `uv run pytest` and `uv run mypy` (no args — `files` in `pyproject.toml` covers `turtlex` and
   `scripts`), per CLAUDE.md §6.
3. `--build-cache` under the 4G cap; confirm signal counts match the committed docs — s12 should
   raise ~4.5k signals over 2015-2026, matching `result-qullamaggie-cohorts-ranking.md`'s
   `ALL (ungated) 4542`. A mismatch means the cache diverged from `turtlex/research/qullamaggie.py`.
4. `--eval c000-production.json` — its decile monotonicity must land on the numbers in the
   Context table above. This is the calibration check that the judge itself is right; if it
   disagrees with the committed docs, fix the harness before running any hypothesis.
5. Dry-run one full loop iteration (A1) manually end to end, confirm the ledger row appends and
   nothing outside the markers changed, before handing the loop to `/loop`.
