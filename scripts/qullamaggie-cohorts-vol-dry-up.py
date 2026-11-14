#!/usr/bin/env python3
"""
Vol-dry-up cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied — since 2026-08-01 the strategy has no vol_dry_up cap, so like the
SMA(200) study the cohorts simply slice the existing signal population.
vol_dry_up_ratio = avg_vol_10 / avg_vol_50, both on the shift-1 volume series.

Below 1.0 the last 10 sessions have been quieter than the last 50 — the volume contraction
Qullamaggie looks for ahead of a breakout; above 1.0 recent volume is already expanding.
This is the volume-side twin of the ADR compression study.

This study is what retired the filter: the `<0.90 (cap)` slice the old cap kept scored *worse*
than the full population on Mean% and Sortino at all three thresholds while dropping ~33% of
signals. That row is kept as a reference so the retired cap stays measurable.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts

VOL_DRY_UP = 0.90

COHORTS: list[cohorts.Bucket] = [
    ("[<0.50)    ", 0.00, 0.50),
    ("[0.50-0.60)", 0.50, 0.60),
    ("[0.60-0.70)", 0.60, 0.70),
    ("[0.70-0.80)", 0.70, 0.80),
    ("[0.80-0.90)", 0.80, 0.90),
    ("[0.90-1.00)", 0.90, 1.00),
    ("[1.00-1.10)", 1.00, 1.10),
    ("[1.10-1.25)", 1.10, 1.25),
    ("[1.25-1.50)", 1.25, 1.50),
    ("[1.50+    )", 1.50, float("inf")),
]


def add_study_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Add this study's cohort variable on top of qm.add_indicators.

    Both averages are already shift-1 in the shared layer, so the ratio carries no
    look-ahead: it is the 10-day volume average over the 50-day average as of the bar
    before the breakout.
    """
    return df.with_columns((pl.col("avg_vol_10") / pl.col("avg_vol_50")).alias("vol_dry_up_ratio"))


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by volume dry-up; the reference row is what the retired < 0.90 filter kept.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    references = [(f"<{VOL_DRY_UP:.2f} (cap)", pl.col("vol_dry_up_ratio") < VOL_DRY_UP)]
    return cohorts.bucket_table(arm.label, trades, "vol_dry_up_ratio", COHORTS, references)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie Vol-Dry-Up Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-vol-dry-up.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "vol_dry_up_ratio = avg_vol_10 / avg_vol_50, on the signal date",
            "Filter under study": "**none — vol_dry_up was retired 2026-08-01; `<0.90 (cap)` shows what it used to keep**",
        }
    ),
    tables=tables,
    require=("vol_dry_up_ratio",),
    add_indicators=add_study_indicators,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
