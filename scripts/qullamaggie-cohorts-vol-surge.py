#!/usr/bin/env python3
"""
Vol-surge cohort analysis for bk50d_s20_v2.0 and bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the vol_surge_max cap, so we can see
performance across the full vol_surge_ratio range including >2x bands.
vol_surge_ratio = volume / avg_vol_50

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

COHORTS: list[cohorts.Bucket] = [
    ("[<0.70)    ", 0.00, 0.70),
    ("[0.70-0.80)", 0.70, 0.80),
    ("[0.80-0.90)", 0.80, 0.90),
    ("[0.90-1.00)", 0.90, 1.00),
    ("[1.00-1.10)", 1.00, 1.10),
    ("[1.10-1.20)", 1.10, 1.20),
    ("[1.20-1.30)", 1.20, 1.30),
    ("[1.30-1.40)", 1.30, 1.40),
    ("[1.40-1.60)", 1.40, 1.60),
    ("[1.60-2.00)", 1.60, 2.00),
    ("[2.00-3.00)", 2.00, 3.00),
    ("[3.00-4.00)", 3.00, 4.00),
    ("[4.00-6.00)", 4.00, 6.00),
    ("[6.00+    )", 6.00, float("inf")),
]


def add_study_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Add this study's cohort variable on top of qm.add_indicators.

    `vol_surge_ratio` is the breakout bar's own volume over the prior 50-day average, so it
    reads current `volume` against the shift-1 `avg_vol_50` the shared layer already computed.
    """
    return df.with_columns((pl.col("volume").cast(pl.Float64) / pl.col("avg_vol_50")).alias("vol_surge_ratio"))


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by volume surge; the reference row is the [1.0, 2.0) band the live filter sits in.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    vsr = pl.col("vol_surge_ratio")
    return cohorts.bucket_table(arm.label, trades, vsr, COHORTS, [("[1.00-2.00) cap", (vsr >= 1.0) & (vsr < qm.VOL_SURGE_MAX))])


SPEC = cohorts.CohortSpec(
    title="Qullamaggie Vol-Surge Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-vol-surge.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "vol_surge_ratio = volume / mean(volume[-51:-1])",
            "Filter under study": "**vol_surge < 2.0x — removed; returns as the `[1.00-2.00) cap` row**",
            "Fixed filters": "RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100% (no tight_range)",
        }
    ),
    tables=tables,
    drop=("vol_surge",),
    add_indicators=add_study_indicators,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
