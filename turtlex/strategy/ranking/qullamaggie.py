import logging
import math
from datetime import date

import polars as pl

from turtlex.strategy.ranking.base import RankingStrategy

# Band shapes come from the bk50d_s12_v2.0 column of the cohort tables in
# docs/research/result-qullamaggie-cohorts-{adr,pct-above-sma50,price}.md (run 2026-08-02):
# each bucket's points are that cohort's Sortino linearly rescaled within its dimension, one
# band per cohort bucket. s12 is the reference algorithm and the widest pool; the bands were
# previously fitted to an s15_v1.3_roc100 run that no longer exists as a standard variant.
#
# The rescale has two anchors, and they are deliberately asymmetric:
#
#   ceiling = the best bucket a signal can REACH given that dimension's own entry filter
#             -> scores the full weight. Price anchors on [5-10), not the better [0-5),
#             because close > $5 is an entry filter: anchoring on an unreachable bucket
#             would mean the dimension could never award its weight.
#   floor   = the worst bucket OBSERVED anywhere in the table, including buckets the entry
#             filter excludes -> scores 0.
#
# The floor anchor changed on 2026-08-07. It used to be the worst *reachable* bucket, which
# meant the weakest qualifying cohort in every dimension scored exactly 0. That was not a
# rounding artifact: under the previous ADR bands both [3.0-3.5) and [3.5-4.0) scored 0, so
# 2213 of the 4459 qualifying s12 signals -- 49.6% of the pool -- scored zero on the largest
# dimension, despite [3.0-3.5) posting a +19.41% median and a 66.6% win rate. Anchoring the
# floor outside the filter puts every reachable bucket strictly inside the range instead.
#
# The cost is that effective weights no longer equal nominal ones. Reachable spread is now
# ADR 4->40 (36 points), SMA50 7->35 (28) and price 9->25 (16), i.e. an effective 45/35/20
# against the nominal 40/35/25 -- price is the dimension that loses. That is inherent: the old
# rule forced spread to equal weight precisely by zeroing the weakest cohort. A real s12 signal
# now scores at least 20 (4 + 7 + 9); 0 is reachable only from values below the entry filters
# or from missing columns, which is what keeps the cross-strategy warning below true.
#
# Any change here moves the score distribution, so MIN_RANKING / --min-signal-ranking is
# scheme-relative and has to be re-picked at matched selectivity rather than carried over.
#
# The *weights* no longer come from those cohort Sortino spreads. They were derived on
# 2026-07-29 from an ad-hoc per-trade scan -- 1685 bk50d_s12 signals over 2010-2020, scored
# on 366d returns with each calendar year's mean return subtracted, to strip out the time
# effect and leave only cross-sectional separation. That scan is NOT committed: no script in
# scripts/ reproduces the rho values quoted below, so treat them as the recorded rationale
# for the split, not as a reproducible result. Only three of the six dimensions carried an
# effect that kept its sign across both halves of that period: ADR%(20) (rho +0.121),
# distance above SMA50 (+0.099) and price (-0.059). ADR compression, 12-month ROC and
# RSI(14) were 25-75% time effect and reversed sign between halves, so they are gone --
# restoring them at low weight as tie-breakers was tested in the same scan and recovered
# nothing. Coarser monotone bands fitted to that scan's decile shape were also tried and were
# worse than the cohort curves below, so the shapes are kept as-is and only rescaled.
#
# What IS committed is the out-of-sample check: docs/research/result-qullamaggie-ranking-weights.md
# (regenerate with scripts/qullamaggie-ranking-weights.py) replays 2021-2026 at matched
# selectivity. Read the CAGR figures there rather than copying them here -- they move slightly
# on every regeneration, so any number transcribed into this comment is wrong by the next run.
# The direction is stable: 40/35/25 beats the old weights at every selectivity at s12 and s16,
# and is mixed at s20 -- CAGR within noise, but Sortino and MaxDD worse at the tightest
# selectivity, because at that threshold the entry filter has already made all but the top two
# SMA50 bands reachable.
#
# The split is roughly proportional to the demeaned effect sizes above, rounded, and blended
# with those features' decile-spread ranking -- which is why price gets 25 rather than the ~21
# that strict rho-proportionality would give.
#
# Caveat worth carrying: the gain is concentrated in 2023-2026, better in 8 of the 9
# sub-period cells. In 2021-2023 the new weights are *behind* the old ones in 7 of 9, by up to
# 9pp. That is the same "works in one half only" pattern used to disqualify the three dropped
# dimensions, so the standard is not being applied evenly here -- the re-weighting was kept
# because the full-period result is strong and consistent across configs, not because it
# passed the sub-period test.
#
# Entries are (upper_bound, points), first match wins; values >= the last bound score the
# trailing constant (0 for dimensions with an entry-filter ceiling -- that region is
# unreachable in practice; ADR has no ceiling, so its constant is a genuine unbounded top tier).

# ADR%(20) as a fraction — result-qullamaggie-cohorts-adr.md (higher is better, weight 40).
# Everything below the adr_pct >= 3.0% entry filter collapses to one 0 band rather than
# carrying the table's [2.0-2.5) 1.384 > [2.5-3.0) 1.342 inversion, which no signal can reach.
_ADR_BANDS = [(0.03, 0), (0.035, 4), (0.04, 9), (0.045, 12), (0.05, 15), (0.07, 19), (0.08, 33)]
_ADR_TOP = 40
# Distance above SMA50 as a fraction — result-qullamaggie-cohorts-pct-above-sma50.md (higher is better, weight 35)
_PCT_SMA50_BANDS = [(0.10, 0), (0.12, 2), (0.15, 7), (0.17, 11), (0.20, 13), (0.30, 21)]
_PCT_SMA50_TOP = 35
# Raw close price in dollars — result-qullamaggie-cohorts-price.md (lower is better, weight 25)
_PRICE_BANDS = [(10.0, 25), (20.0, 21), (50.0, 14), (100.0, 10), (250.0, 9)]
_PRICE_TOP = 0

logger = logging.getLogger(__name__)


class QullamaggieRanking(RankingStrategy):
    """
    Cohort-derived ranking for Qullamaggie-style breakout signals.

    Scores each signal by three entry-time parameters against Sortino gradients in the
    cohort research (docs/research/result-qullamaggie-cohorts-*.md, bk50d_s12_v2.0,
    2026-08-02 run), weighted by the size of each one's year-demeaned cross-sectional
    effect on 366d outcomes (docs/research/result-qullamaggie-ranking-weights.md):

    - ADR%(20)            (0-40 pts): higher daily range -> higher Sortino
    - Distance above SMA50 (0-35 pts): higher is better, monotonically. The 2026-07-22
      calibration had a dip at the 17-20% band; that was an artifact of the superseded run
      and is not present in the v2.0 cohort curve
    - Entry price         (0-25 pts): cheaper entries carry higher Sortino

    Total: 0-100, but a signal that passed the entry filters scores at least 20 -- see the
    anchor note above the band constants. Expects the shift-1 indicator columns produced by
    ``QullamaggieStrategy.calculate_indicators_pl`` (``adr_pct``, ``pct_vs_sma50``); a
    missing column or null value scores that component 0.

    That fallback is not as graceful as it looks, and the 2026-07-29 re-weighting made it
    worse: pair this ranking with a strategy that does not compute these columns (darvas_box,
    mars, momentum compute neither) and every signal scores price only -- at most 25, below
    the default ``--min-signal-ranking 44``, so the backtest silently takes no trades. A
    missing ``adr_pct`` alone now costs 40 points rather than the 12 it cost before. Pair
    this ranking with QullamaggieStrategy, or lower the gate deliberately.

    Note: docs/research/result-qullamaggie-cohorts-ranking.md cohorts signals by this score
    and finds it separates 366d outcomes monotonically, with the default >=44 gate lifting
    both pool Sortino and median return -- but far less so at s20, where the entry filter has
    already made the low bands unreachable. docs/research/result-qullamaggie-ranking-validation.md
    walk-forward validates the earlier six-dimension weighting (train/test split); the weights
    here replace it and are validated instead in result-qullamaggie-ranking-weights.md. Read
    those before assuming these weights hold up out-of-sample; this ranking orders surviving
    signals and is not a substitute for the entry filters.
    """

    @staticmethod
    def _band_score(value: float | None, bands: list[tuple[float, int]], top_points: int) -> int:
        """Return the points of the first band whose upper bound exceeds value.

        Args:
            value: Metric value to score; None or non-finite scores 0
            bands: (upper_bound, points) pairs in ascending bound order
            top_points: Points for values at or above the last upper bound
        """
        if value is None or not math.isfinite(value):
            return 0
        for upper, points in bands:
            if value < upper:
                return points
        return top_points

    def ranking(self, df: pl.DataFrame, date: date) -> int:
        """
        Calculate the cohort-mimicking ranking score (0-100).

        Args:
            df: DataFrame with OHLCV and Qullamaggie indicator columns up to
                and including the signal date. Used columns: close, adr_pct,
                pct_vs_sma50.
            date: The signal date.

        Returns:
            int: Score in range 0-100.
        """
        filtered_pl_df = df.filter(pl.col("date") <= date)
        if filtered_pl_df.is_empty():
            return 0

        row = filtered_pl_df.row(-1, named=True)

        adr_pts = self._band_score(row.get("adr_pct"), _ADR_BANDS, _ADR_TOP)
        pct_sma50_pts = self._band_score(row.get("pct_vs_sma50"), _PCT_SMA50_BANDS, _PCT_SMA50_TOP)
        price_pts = self._band_score(row.get("close"), _PRICE_BANDS, _PRICE_TOP)

        score = adr_pts + pct_sma50_pts + price_pts
        logger.debug(f"QullamaggieRanking date={date} adr={adr_pts} pct_sma50={pct_sma50_pts} price={price_pts} total={score}")
        return score
