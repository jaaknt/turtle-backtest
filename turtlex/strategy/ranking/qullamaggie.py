import logging
import math
from datetime import date

import polars as pl

from turtlex.strategy.ranking.base import RankingStrategy

# Band shapes still come from the bk50d_s15_v1.3_roc100 cohort tables in
# docs/research/result-qullamaggie-cohorts-*.md (run 2026-07-22, RSI<70): each bucket's
# points are that cohort's Sortino linearly rescaled to 0-<weight> within its dimension
# (worst reachable value -> 0, best reachable value -> weight). "Reachable" means the
# cohort buckets a real candidate can actually land in given that dimension's own entry
# filter -- a dimension whose filter already excludes its most extreme values gets a
# narrower reachable range and, historically, a smaller weight.
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

# ADR%(20) as a fraction — result-qullamaggie-cohorts-adr.md (higher is better, weight 40)
_ADR_BANDS = [(0.035, 0), (0.04, 0), (0.045, 10), (0.05, 13), (0.08, 27)]
_ADR_TOP = 40
# Distance above SMA50 as a fraction — result-qullamaggie-cohorts-pct-above-sma50.md (higher is better, weight 35)
_PCT_SMA50_BANDS = [(0.10, 0), (0.12, 8), (0.15, 15), (0.17, 22), (0.20, 12), (0.30, 31)]
_PCT_SMA50_TOP = 35
# Raw close price in dollars — result-qullamaggie-cohorts-price.md (lower is better, weight 25)
_PRICE_BANDS = [(10.0, 25), (20.0, 8), (50.0, 2), (100.0, 2), (250.0, 0)]
_PRICE_TOP = 0

logger = logging.getLogger(__name__)


class QullamaggieRanking(RankingStrategy):
    """
    Cohort-derived ranking for Qullamaggie-style breakout signals.

    Scores each signal by three entry-time parameters against Sortino gradients in the
    cohort research (docs/research/result-qullamaggie-cohorts-*.md, bk50d_s15_v1.3_roc100,
    2026-07-22 run), weighted by the size of each one's year-demeaned cross-sectional
    effect on 366d outcomes (docs/research/result-qullamaggie-ranking-weights.md):

    - ADR%(20)            (0-40 pts): higher daily range -> higher Sortino
    - Distance above SMA50 (0-35 pts): higher is better overall, but not monotonically --
      the 17-20% band scores 12, below the 22 of the 15-17% band, a dip inherited from the
      cohort Sortino curve
    - Entry price         (0-25 pts): cheaper entries carry higher Sortino

    Total: 0-100. Expects the shift-1 indicator columns produced by
    ``QullamaggieStrategy.calculate_indicators_pl`` (``adr_pct``, ``pct_vs_sma50``); a
    missing column or null value scores that component 0.

    That fallback is not as graceful as it looks, and the 2026-07-29 re-weighting made it
    worse: pair this ranking with a strategy that does not compute these columns (darvas_box,
    mars, momentum compute neither) and every signal scores price only -- at most 25, below
    the default ``--min-signal-ranking 40``, so the backtest silently takes no trades. A
    missing ``adr_pct`` alone now costs 40 points rather than the 12 it cost before. Pair
    this ranking with QullamaggieStrategy, or lower the gate deliberately.

    Note: per docs/research/result-qullamaggie-cohort-ranking.md, a differently-constructed
    composite (walk-forward log-odds P(success)) separates *filtered* signals only weakly
    out-of-sample. docs/research/result-qullamaggie-ranking-validation.md walk-forward
    validates the earlier six-dimension weighting (train/test split); the weights here
    replace it and are validated instead in result-qullamaggie-ranking-weights.md. Read
    either doc before assuming these weights hold up out-of-sample; this ranking orders
    surviving signals and is not a substitute for the entry filters.
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
