import logging
import math
from datetime import date

import polars as pl

from turtlex.strategy.ranking.base import RankingStrategy

# Band tables mimic the bk50d_s15_v1.3_roc100 cohort tables in
# docs/research/result-qullamaggie-cohorts-*.md (run 2026-07-22, RSI<70): each bucket's
# points are that cohort's Sortino linearly rescaled to 0-<weight> within its dimension
# (worst reachable value -> 0, best reachable value -> weight). "Reachable" means the
# cohort buckets a real candidate can actually land in given that dimension's own entry
# filter (e.g. adr_pct_change < 0.90 makes the >=0.90 buckets structurally impossible) --
# both the weight-spread calculation and the point rescale use reachable buckets only, so
# a dimension whose entry filter already excludes its most extreme values (e.g. RSI, ROC252)
# correctly gets a smaller ranking weight than one with a wide open reachable range.
# Distance above SMA50 carries a fixed weight of 50 by design (Qullamaggie's own emphasis
# on this metric); the remaining 50 points are split across the other five dimensions
# proportionally to each one's reachable-domain Sortino spread (13/12/12/10/3, total 50).
# Entries are (upper_bound, points), first match wins; values >= the last bound score the
# trailing constant (0 for dimensions with an entry-filter ceiling -- that region is
# unreachable in practice; ADR has no ceiling, so its constant is a genuine unbounded top tier).

# ADR%(20) as a fraction — result-qullamaggie-cohorts-adr.md (higher is better, weight 12)
_ADR_BANDS = [(0.035, 0), (0.04, 0), (0.045, 3), (0.05, 4), (0.08, 8)]
_ADR_TOP = 12
# ADR compression ADR10/ADR50 — result-qullamaggie-cohorts-adr-compression.md (lower is better, weight 12)
_COMPRESSION_BANDS = [(0.7, 12), (0.8, 0), (0.9, 1)]
_COMPRESSION_TOP = 0
# Distance above SMA50 as a fraction — result-qullamaggie-cohorts-pct-above-sma50.md (higher is better, weight 50)
_PCT_SMA50_BANDS = [(0.10, 0), (0.12, 12), (0.15, 22), (0.17, 31), (0.20, 17), (0.30, 44)]
_PCT_SMA50_TOP = 50
# Raw close price in dollars — result-qullamaggie-cohorts-price.md (lower is better, weight 13)
_PRICE_BANDS = [(10.0, 13), (20.0, 4), (50.0, 1), (100.0, 1), (250.0, 0)]
_PRICE_TOP = 0
# 12-month ROC as a fraction — result-qullamaggie-cohorts-roc.md (non-monotonic: best near
# <-20% and 40-60%, worst approaching the 100% entry-filter cap; weight 10)
_ROC252_BANDS = [(-0.20, 10), (0.0, 6), (0.20, 5), (0.40, 8), (0.60, 10), (0.80, 5), (1.00, 0)]
_ROC252_TOP = 0
# RSI(14) — result-qullamaggie-cohorts-rsi.md, fine partition (lower is better within the
# qualifying <70 pool; weight 3)
_RSI_BANDS = [(50.0, 3), (60.0, 2), (70.0, 0)]
_RSI_TOP = 0

logger = logging.getLogger(__name__)


class QullamaggieRanking(RankingStrategy):
    """
    Cohort-derived ranking for Qullamaggie-style breakout signals.

    Scores each signal by six entry-time parameters against Sortino gradients in the
    cohort research (docs/research/result-qullamaggie-cohorts-*.md, bk50d_s15_v1.3_roc100,
    2026-07-22 run). Distance above SMA50 carries half the weight by design; the rest is
    split proportionally to each dimension's Sortino spread within its *reachable* cohort
    domain (the bucket range a candidate can actually land in given that dimension's own
    entry filter):

    - Distance above SMA50 (0-50 pts): further above the 50-day SMA outperforms
    - Entry price         (0-13 pts): cheaper entries carry higher Sortino
    - ADR%(20)            (0-12 pts): higher daily range -> higher Sortino
    - ADR compression     (0-12 pts): ADR10/ADR50 < 0.7 is the strongest cohort
    - 12-month ROC        (0-10 pts): non-monotonic -- best near <-20% and 40-60%, worst
      approaching the 100% entry-filter cap
    - RSI(14)             (0-3 pts): lower RSI within the qualifying <70 pool outperforms

    Total: 0-100. Expects the shift-1 indicator columns produced by
    ``QullamaggieStrategy.calculate_indicators_pl`` (``adr_pct``, ``adr_pct_change``,
    ``pct_vs_sma50``, ``roc_252d``, ``rsi14``); a missing column or null value scores that
    component 0, so the ranking degrades gracefully with other trading strategies.

    Note: per docs/research/result-qullamaggie-cohort-ranking.md, a differently-constructed
    composite (walk-forward log-odds P(success)) separates *filtered* signals only weakly
    out-of-sample. docs/research/result-qullamaggie-ranking-validation.md walk-forward
    validates this exact weighted-points scheme (train/test split) -- see that doc before
    assuming these weights hold up out-of-sample; this ranking orders surviving signals and
    is not a substitute for the entry filters.
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
                adr_pct_change, pct_vs_sma50, roc_252d, rsi14.
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
        roc_pts = self._band_score(row.get("roc_252d"), _ROC252_BANDS, _ROC252_TOP)
        rsi_pts = self._band_score(row.get("rsi14"), _RSI_BANDS, _RSI_TOP)

        score = adr_pts + compression_pts + pct_sma50_pts + price_pts + roc_pts + rsi_pts
        logger.debug(
            f"QullamaggieRanking date={date} adr={adr_pts} compression={compression_pts} "
            f"pct_sma50={pct_sma50_pts} price={price_pts} roc={roc_pts} rsi={rsi_pts} total={score}"
        )
        return score
