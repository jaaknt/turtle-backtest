#!/usr/bin/env python3
"""
pct_above_sma50 cohort analysis for bk50d_<X>_v2.0 (366d hold).

All strategy filters applied EXCEPT the pct_vs_sma50 >= X threshold itself, so
we can see performance across the full distance-above-SMA50 range. Removing
that filter makes the s12/s15/s17/s20 variants draw from the same candidate
pool, so there is a single cohort table with one reference row per current
threshold cap. pct_above_sma50 = close / mean(close[-51:-1]) - 1

This study runs UNGATED, like the ADR% and entry-price studies. QullamaggieRanking scores
pct_vs_sma50 as its 35-point dimension and awards 0 below 10%, so a >=44 gate filters on the
very variable being cohorted and would empty the low cohorts this study exists to measure.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts

# Current threshold caps shown as reference rows
SMA_THRESHS = [0.12, 0.15, 0.17, 0.20]

COHORTS: list[cohorts.Bucket] = [
    ("(<10)    ", float("-inf"), 0.10),
    ("[10-12)  ", 0.10, 0.12),
    ("[12-15)  ", 0.12, 0.15),
    ("[15-17)  ", 0.15, 0.17),
    ("[17-20)  ", 0.17, 0.20),
    ("[20-30)  ", 0.20, 0.30),
    ("(>30)    ", 0.30, float("inf")),
]


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by distance above SMA50, with one reference row per production threshold.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    references = [(f">={int(t * 100)}% (s{int(t * 100)})", pl.col("pct_vs_sma50") >= t) for t in SMA_THRESHS]
    return cohorts.bucket_table(arm.label, trades, "pct_vs_sma50", COHORTS, references, label_width=10)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie pct_above_sma50 Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-pct-above-sma50.md",
    config_rows=cohorts.config_rows(
        {
            "Cohorts": "**`bk50d_s<X>_v2.0` (366d) — one shared pool; reference rows for X = 12% / 15% / 17% / 20%**",
            "Cohort variable": "pct_vs_sma50 = close / mean(close[-51:-1]) - 1",
            "Filter under study": "**pct_vs_sma50 >= X — removed; returns as one reference row per X**",
            "Ranking gate": "**not applied — %abv_sma50 is the score's 35-point dimension and the cohort variable (ungated)**",
        }
    ),
    tables=tables,
    # With the threshold dropped every variant draws from one pool, so there is a single arm.
    arms=[cohorts.Arm("bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)", 0.0)],
    drop=("sma_dist",),
    gated=False,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
