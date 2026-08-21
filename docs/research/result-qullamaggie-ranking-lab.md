# Ranking Lab — hypothesis ledger

Record of every ranking hypothesis the improvement loop has tested. Written by
`scripts/qullamaggie-ranking-lab.py --eval`, which touches nothing outside the
`lab:ledger:start` / `lab:ledger:end` markers — the Findings section at the foot of this file
survives a re-run. One row per candidate: a re-run of a spec that already has a row overwrites
that row in place, keeping its number, because the row count is the multiple-testing counter
behind `required_margin` and a duplicate would charge every later candidate a margin no new
hypothesis earned.

The protocol, the acceptance rule and the loop are defined in
[docs/specs/qullamaggie-ranking-loop.md](../specs/qullamaggie-ranking-loop.md). Read that before
reading a verdict here: none of these numbers mean anything without the matched-selectivity and
random-null controls the protocol imposes.

**Current baseline:** `c000-production` — the shipped `QullamaggieRanking` 40/35/25 bands.

Measured on the 2026-08-20 cache (bars 2010-2026 from the VPS; 5389 s12 signals cached, 5150 of
them entered before the 2025-01-01 holdout boundary):

```text
config    folds  mono_sortino  mono_mean   spearman   spread  topD_sortino
--------------------------------------------------------------------------
s12           6         0.581      0.669    +0.1304    3.318         4.404
s16           6         0.613      0.719    +0.1298    3.459         5.311
s20           6         0.536      0.609    +0.1488    3.461         5.696
--------------------------------------------------------------------------
ALL          18         0.577               +0.1364    3.410
```

That `0.577` is the problem in one number: on held-out slices only about 5.2 of 9 decile steps
are non-decreasing, against 7.6/9 for the same score in-sample. The gap, not the level, is what
the loop is trying to close.

## What the columns mean

| Column | Meaning |
| --- | --- |
| `mono` | Fold-mean fraction of non-decreasing Sortino decile steps on held-out slices, all configs. Higher is better; this is the metric the loop exists to raise. |
| `rho` | Fold-mean Spearman correlation between score and year-demeaned 366d return. |
| `spread` | Fold-mean D10 − D1 Sortino. A scheme can be monotone and useless if this is flat. |
| `CAGR%` | Portfolio replay at keep 25%, s12, 2015-01-01 … 2024-12-31. Only run for candidates that clear the monotonicity gates. |

Baseline reference, from the committed cohort and validation studies rather than from this
harness — the numbers `c000-production` has to reproduce before any verdict below is
trustworthy:

| Slice | Sortino monotone decile steps |
| --- | --- |
| `result-qullamaggie-cohorts-ranking.md`, s12 population deciles | 8/9 |
| same doc, s16 | 6/9 |
| same doc, s20 | 5/9 |
| `result-qullamaggie-ranking-validation.md`, production bands, held-out 2021+ | 5/9 |

Reproduced by this harness on its own cache: s12 7.6/9, s16 6.2/9, s20 6.1/9. Note this is a
**different population** from the committed docs — `_full_period_reference` excludes the holdout,
so it scores 4269 s12 signals entered 2015-01-01..2024-12-31, against the docs' 4542 over
2015-2026. On the docs' own window this cache holds 4508, ~0.8% short, because the qualified
universe is defined by a *current* `market_cap` snapshot that has moved since 2026-08-09.

Read the step counts, not the populations: s12 and s16 land on the committed figures and s20
comes out about one step higher, because this harness breaks decile ties at random over ten
redraws while the committed studies cut tie groups by row order. At s20 the coarse bands leave
large tie blocks, so part of that doc's 5/9 is tie-cut noise rather than genuine
non-monotonicity.

## Ledger

**Two acceptance rules appear in the Reason column.** Rows 1-7 were judged while the per-config
spread gate was proportional (`< 90% of baseline`); rows 8-9 were judged under the absolute
`MAX_SPREAD_GIVEBACK = 0.35` give-back the spec now defines, adopted because a proportional rule
inverts against a negative baseline spread — `0.9 * -2.0 = -1.8` demands the candidate *beat*
-2.0, and individual folds do go negative. No verdict moves: each of rows 1-7 also failed
monotonicity or the rho margin. But the bounds quoted inside those rows' spread reasons are the
retired ones, so read them against the rule of their own row, not against rows 8-9.

<!-- lab:ledger:start -->

| # | Candidate | Hypothesis | mono | rho | spread | CAGR% | Verdict | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `c001-noncompensatory` | Replacing the additive sum with a non-compensatory minimum makes equal scores describe comparable populations, so deciles stop inverting. | 0.557 | +0.1118 | 2.586 | — | **REJECT** | mono_sortino 0.557 < baseline 0.577; spearman +0.1118 < baseline +0.1364 + margin 0.0100; s12: spread 2.592 < 90% of baseline 3.318; s16: spread 2.463 < 90% of baseline 3.459; s20: spread 2.726 < 90% of baseline 3.461 |
| 2 | `c003-linear-ramps` | Replacing the coarse bands with monotone linear ramps over the same reachable ranges removes the tie clumping that makes decile boundaries arbitrary — 702 s12 signals share scores [20-25] today — so held-out monotonicity should rise without changing what the score measures. | 0.616 | +0.1294 | 3.637 | — | **REJECT** | spearman +0.1294 < baseline +0.1364 + margin 0.0100 |
| 3 | `c007-drop-price` | Price carried the weakest demeaned effect of the three (rho -0.059) and floor-anchoring already cut its effective weight to about 20, so dropping it entirely and splitting 50/50 between ADR and SMA50 distance should lose nothing and remove a dimension that mostly adds noise to the score. | 0.570 | +0.1063 | 3.062 | — | **REJECT** | mono_sortino 0.570 < baseline 0.577; spearman +0.1063 < baseline +0.1364 + margin 0.0100; s12: spread 2.884 < 90% of baseline 3.318; s16: spread 2.960 < 90% of baseline 3.459 |
| 4 | `c005-sma-only` | A weight search over the 2010-2018 training slice puts all 100 points on SMA50 distance and none on ADR or price (train rho +0.0545 vs +0.0203 for 40/35/25), so if that corner solution is real rather than a fit artifact, SMA50 distance alone should order held-out outcomes better than the production blend. | 0.567 | +0.0978 | 2.249 | — | **REJECT** | mono_sortino 0.567 < baseline 0.577; spearman +0.0978 < baseline +0.1364 + margin 0.0100; s12: spread 2.573 < 90% of baseline 3.318; s16: spread 2.833 < 90% of baseline 3.459; s20: spread 1.341 < 90% of baseline 3.461 |
| 5 | `c006-grid2d` | ADR and SMA50 distance interact rather than add — a 3x3 cell table fitted on 2010-2018 shows the payoff concentrated where both are high — so replacing the two additive terms with a joint grid should order better than summing them independently. | 0.544 | +0.1170 | 1.508 | — | **REJECT** | mono_sortino 0.544 < baseline 0.577; spearman +0.1170 < baseline +0.1364 + margin 0.0100; s12: spread 2.969 < 90% of baseline 3.318; s16: spread 1.888 < 90% of baseline 3.459; s20: spread -0.700 < 90% of baseline 3.461 |
| 6 | `c008-ramps-basedepth` | Combining the two best findings so far — continuous ramps, which lifted held-out monotonicity from 0.577 to 0.616, and base_depth_50d, the only new feature with a sign-stable effect near the incumbents' size (rho +0.0937) — should beat the baseline on monotonicity and recover the rank correlation that ramps alone gave up. | 0.579 | +0.1322 | 3.868 | — | **REJECT** | spearman +0.1322 < baseline +0.1364 + margin 0.0100 |
| 7 | `c009-bands-basedepth` | Adding base_depth_50d to the production bands at the same 15 points c008 gives it, keeping the band transform, isolates the new feature's contribution from the ramp change — so the pair of runs says whether the gain comes from the feature, the transform, or only their combination. | 0.596 | +0.1375 | 3.731 | — | **REJECT** | spearman +0.1375 < baseline +0.1364 + margin 0.0100 |
| 8 | `c002-isotonic` | Remapping the production sum through an isotonic fit of raw-score to year-demeaned return, fitted on each fold's training slice, makes the score monotone in outcome by construction on train; if that survives out of sample the non-monotonicity was a calibration problem, not an information problem. | 0.580 | +0.1200 | 2.586 | — | **REJECT** | spearman (margin 0.0100) 0.1200 < 0.1464; s12: spread 2.5837 < 2.9682; s16: spread 2.4383 < 3.1093; s20: spread 2.7647 < 3.1109 |
| 9 | `c004-percentile` | Scoring each dimension by its percentile among the trailing 252 days of raised signals makes the score regime-relative — a 5% ADR meant something different in 2017 than in 2021 but scores the same points today — which should help most on the held-out folds where the regime differs from training. | 0.593 | +0.1352 | 2.481 | — | **REJECT** | spearman (margin 0.0100) 0.1352 < 0.1464; s12: spread 2.5745 < 2.9682; s16: spread 2.2572 < 3.1093; s20: spread averaged over 4 candidate folds vs 5 baseline folds — not comparable; s20: spread 2.6763 < 3.1109 |
<!-- lab:ledger:end -->

## Findings

Ten iterations, nine candidates evaluated plus one feature-screening pass. **Nothing was
accepted.** That is the headline, and the rejections are consistent enough to say why.

### The result that reframes the problem

`c009-bands-basedepth` produced the best held-out monotonicity of the run (0.596 against the
baseline's 0.577) and the second-best spread (3.731 against 3.410) — and the **worst** portfolio
performance of the three schemes taken to a replay:

```text
keep 25%, s12, 2015-01-01..2024-12-31     CAGR%   Sortino   MaxDD%   pre-split  post-split
------------------------------------------------------------------------------------------
c000-production (baseline)               +30.60     1.561   -44.09      +16.28      +44.45
c003-linear-ramps                        +30.67     1.550   -45.06      +16.47      +45.46
c009-bands-basedepth                     +27.32     1.434   -39.92      +19.17      +38.94
```

Better decile ordering cost 3.3pp of CAGR, and not as a one-period artifact — the post-split
half is 5.5pp worse. The reason is structural: decile monotonicity is mostly a statement about
ordering the *middle and bottom* of the distribution, and a portfolio gated at `>= 44` or
filled top-down never trades those signals. **Monotonicity and portfolio return are different
objectives here, and this run shows they can move in opposite directions.**

All three schemes beat their same-size random null 30/30 at every selectivity, so the ranking
carries real skill. It is the *marginal changes* to it that do not pay.

> Provenance: `--eval` runs the portfolio replay only for candidates that clear the monotonicity
> gates, which is why every ledger row's CAGR column reads "—". The table above was produced by
> invoking `portfolio_confirm` directly on the two rejected candidates. Reproduce it that way,
> not by re-running `--eval`.

### What each rejection established

- **A1 `min` (non-compensatory).** Fixing compensation by taking the weakest dimension discards
  the other two: spread fell uniformly across all three configs (3.41 -> 2.59) and rho lost a
  quarter of its value. Compensation is real but second-order next to throwing away evidence.
- **A2 isotonic.** Buys a hair of monotonicity (0.577 -> 0.580, the only candidate to clear the
  baseline there) and pays for it heavily in discrimination: rho +0.1364 -> +0.1200 and spread
  3.410 -> 2.586. Pooling a locally non-monotone run of scores into one value does remove that
  inversion, but it also makes those signals indistinguishable, and the lost ordering costs more
  than the recovered monotonicity is worth.

  **This row was re-measured on 2026-08-20 after a review found `isotonic_apply` interpolating
  between knots instead of stepping** — which re-separated every pooled block and made the
  calibration a rank-preserving identity, so the first run scored the baseline by construction
  and tested nothing. The corrected result is the one above. Note the conclusion survived the
  bug while the reasoning did not: isotonic is not "incapable by construction" (a step function
  is only *weakly* monotone, and its ties genuinely move deciles) — it simply loses more than it
  gains.
- **A3 continuous ramps.** The one structural change that helps: monotonicity 0.577 -> 0.616,
  spread 3.410 -> 3.637, and portfolio-neutral (+30.67 vs +30.60 CAGR). It fails only the rho
  margin, by 0.007. Removing tie clumping is a genuine, if modest, improvement.
- **A4 trailing percentile.** Regime-relative scoring collapsed spread (3.41 -> 2.48). Mapping
  each feature to a uniform distribution destroys the information in *how far* past the
  threshold a value sits, which is most of what these features carry. Also re-measured on
  2026-08-20: the original run ranked each signal against its own same-day peers, making the
  score depend on the ticker's alphabetical position.
- **A5 SMA50-only.** A weight search on 2010-2018 put all 100 points on SMA50 distance
  (train rho +0.0545 vs +0.0203 for 40/35/25). Out of sample it collapsed to rho +0.0978 and
  spread 2.249 — a textbook corner solution that did not generalize.
- **A6 ADR x SMA50 grid.** Worst result of the run: s20 spread went **negative** (-0.700), the
  top decile scoring below the bottom. A 64-signal corner cell took 75 of the 75 points and
  inverted the ranking. Interaction fitting needs more data than this universe has.
- **A7 drop price.** Price's weak standalone effect (rho -0.059) understated it: removing it
  cost rho +0.1364 -> +0.1063. The three dimensions are complementary, not redundant.

### Feature screen — 4 of 14 passed

`base_depth_50d` (rho +0.0937), `breadth_sma50` (+0.0623), `rs_63d` (-0.0469) and `vol_dryup`
(-0.0111) kept their sign across both training halves and all but one fold. The other ten
failed, including every trend-quality feature tried — `sma_stack`, `pct_vs_sma200`,
`sma200_slope_20d`, `pct_off_52w_high` — which is consistent with those being time effects
rather than cross-sectional ones.

`base_depth_50d` is the only one near the incumbents in size, and its sign is the interesting
part: a **deeper** 50-day base predicts a better outcome (Q5 mean demeaned return +0.079 vs Q1
-0.045). It is worth study in its own right, but as the c009 replay shows, adding it to the
ranking is not how to capture it.

### Standing recommendation

Do not change the shipped weights or bands on this evidence. The 40/35/25 scheme sits at a local
optimum that nine directed attempts could not beat on the objective that matters. If a change is
made at all, A3's continuous ramps are the only candidate that improves ordering at no portfolio
cost — a low-risk swap, but one whose benefit is measured in decile statistics rather than
return.

## Conclusion

Twelve things were tested against the shipped configuration: nine candidate ranking schemes, a
`MIN_RANKING` gate sweep on two windows, and a portfolio intake cap. **None of them beat what is
already running.**

| Question | Answer |
| --- | --- |
| Change the 40/35/25 weights or bands? | No — 9 candidates, 0 accepted |
| Move `MIN_RANKING` off 44? | No — 2015-2024 favoured 55, the 2025+ holdout favoured 44, and 55 splits its sub-periods |
| Cap new positions per month? | No — it diversifies entry vintages as designed (top-month share 38.6% -> 8.9%) but produces no gain in return, drawdown or dispersion |

Given that changing the weights or the gate stales ~15 committed result docs and touches ~20
files, "no change" is the actionable result, not a null one.

### Two findings worth carrying forward

**Monotonicity and portfolio return are different objectives, and can move in opposite
directions.** `c009` posted the best held-out decile monotonicity of the run and the worst
portfolio CAGR (-3.3pp). A gated, top-down-filled portfolio only ever trades the top two or
three deciles, so ordering the middle of the distribution correctly buys nothing. Any future
work on this ranking should optimize top-K lift, not full-range monotonicity.

**The score has a dead zone exactly where the gate sits.** An isotonic fit refit on all six
folds puts scores 32-48 in a single flat block every time: within that range a higher score does
not predict a better outcome, and `MIN_RANKING = 44` is in the middle of it. Moving the gate to
the block edge did not exploit this, so it stands as a property of the score rather than an
opportunity — but it means the difference between a 44 and a 47 is noise, and no future scheme
should be judged on distinctions inside that band.

### State of the evidence

The 2025+ holdout has now been opened, on the gate question. It is no longer clean for judging a
future scheme change; that would need a new frozen slice.

Rows 8 and 9 (`c002-isotonic`, `c004-percentile`) were re-measured on 2026-08-20 after a review
found two defects in the harness — an isotonic map that interpolated instead of stepping, and a
trailing percentile that ranked signals against same-day peers. Their original rows were removed
rather than kept, because they recorded measurements the harness could not actually make. Both
verdicts are unchanged; the numbers are not.

The intake-cap test is reproducible: `scripts/qullamaggie-pacing.py`, results in
`docs/research/result-qullamaggie-pacing.md`. It reads the same ranking-lab cache, so its signal
set is identical to the one every candidate above was judged on.
