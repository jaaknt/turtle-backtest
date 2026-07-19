import logging
import math
from datetime import date

import polars as pl

from turtlex.strategy.ranking.base import RankingStrategy

# Band tables mimic the bk50d_s15_v1.2_roc100 cohort tables in
# docs/research/result-qullamaggie-cohorts-*.md (run 2026-07-16): each bucket's
# points are that cohort's Sortino linearly rescaled to 0-<weight> within its
# dimension (min Sortino -> 0, max -> weight). Distance above SMA50 carries a
# fixed weight of 50 by design; the remaining 50 points are split across
# price/ADR/compression proportionally to each dimension's Sortino spread
# within its filter-surviving domain (21/15/14, total 100). Entries are
# (upper_bound, points), first match wins; values >= the last bound score
# the trailing constant.

# ADR%(20) as a fraction — result-qullamaggie-cohorts-adr.md (higher is better, weight 15)
_ADR_BANDS = [(0.02, 0), (0.025, 2), (0.03, 3), (0.035, 4), (0.04, 4), (0.045, 8), (0.05, 9), (0.08, 13)]
_ADR_TOP = 15
# ADR compression ADR10/ADR50 — result-qullamaggie-cohorts-adr-compression.md (lower is better, weight 14)
_COMPRESSION_BANDS = [(0.7, 14), (0.8, 4), (0.9, 4), (1.0, 2)]
_COMPRESSION_TOP = 0
# Distance above SMA50 as a fraction — result-qullamaggie-cohorts-pct-above-sma50.md (higher is better, weight 50)
_PCT_SMA50_BANDS = [(0.10, 0), (0.12, 12), (0.15, 22), (0.17, 31), (0.20, 17), (0.30, 44)]
_PCT_SMA50_TOP = 50
# Raw close price in dollars — result-qullamaggie-cohorts-price.md (lower is better, weight 21)
_PRICE_BANDS = [(5.0, 19), (10.0, 21), (20.0, 11), (50.0, 9), (100.0, 9), (250.0, 6)]
_PRICE_TOP = 0

logger = logging.getLogger(__name__)


class QullamaggieRanking(RankingStrategy):
    """
    Cohort-derived ranking for Qullamaggie-style breakout signals.

    Scores each signal by the four entry-time parameters with the strongest
    positive Sortino gradients in the cohort research
    (docs/research/result-qullamaggie-cohorts-*.md, bk50d_s15_v1.2_roc100).
    Distance above SMA50 carries half the weight by design; the rest is split
    proportionally to each dimension's Sortino spread within its
    filter-surviving cohort domain:

    - Distance above SMA50 (0-50 pts): further above the 50-day SMA outperforms
    - Entry price         (0-21 pts): cheaper entries carry higher Sortino
    - ADR%(20)            (0-15 pts): higher daily range -> higher Sortino
    - ADR compression     (0-14 pts): ADR10/ADR50 < 0.7 is the strongest cohort

    Total: 0-100. Expects the shift-1 indicator columns produced by
    ``QullamaggieStrategy.calculate_indicators_pl`` (``adr_pct``,
    ``adr_pct_change``, ``pct_vs_sma50``); a missing column or null value
    scores that component 0, so the ranking degrades gracefully with other
    trading strategies.

    Note: per docs/research/result-qullamaggie-cohort-ranking.md, composite
    cohort scores separate *filtered* signals only weakly — this ranking
    orders surviving signals and is not a substitute for the entry filters.
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
                adr_pct_change, pct_vs_sma50.
            date: The signal date.

        Returns:
            int: Score in range 0-100.
        """
        filtered_pl_df = df.filter(pl.col("date") <= date)
        if filtered_pl_df.is_empty():
            return 0

        row = filtered_pl_df.row(-1, named=True)

        adr_pts = self._band_score(row.get("adr_pct"), _ADR_BANDS, _ADR_TOP)
        compression_pts = self._band_score(row.get("adr_pct_change"), _COMPRESSION_BANDS, _COMPRESSION_TOP)
        pct_sma50_pts = self._band_score(row.get("pct_vs_sma50"), _PCT_SMA50_BANDS, _PCT_SMA50_TOP)
        price_pts = self._band_score(row.get("close"), _PRICE_BANDS, _PRICE_TOP)

        score = adr_pts + compression_pts + pct_sma50_pts + price_pts
        logger.debug(
            f"QullamaggieRanking date={date} adr={adr_pts} compression={compression_pts} "
            f"pct_sma50={pct_sma50_pts} price={price_pts} total={score}"
        )
        return score
