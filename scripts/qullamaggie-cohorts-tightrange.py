#!/usr/bin/env python3
"""
Tight-range cohort analysis for bk50d_s20_tr10, bk50d_s20_tr20, bk50d_s15_tr15 (366d hold).

All strategy filters applied EXCEPT the tight_range cap, so we can see
performance across the full tight_range_ratio range.
tight_range_ratio = (max(close[-11:-1]) - min(close[-11:-1])) / mean(close[-11:-1])

Note: s20_tr10 and s20_tr20 share the same pct_above_sma50 threshold (20%) and
differ only in their tight_range cap. With that cap removed, both draw from the
same underlying candidate pool — only their "current filter" reference row
differs (<=0.10 vs <=0.20).

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts

# Each variant: (pct_above_sma50 threshold, tight_range cap reported as its reference row).
VARIANTS = {
    "bk50d_s20_tr10_v2.0": (0.20, 0.10),
    "bk50d_s20_tr20_v2.0": (0.20, 0.20),
    "bk50d_s15_tr15_v2.0": (0.15, 0.15),
}
ARMS = [cohorts.Arm(label, sma_thresh) for label, (sma_thresh, _cap) in VARIANTS.items()]

COHORTS: list[cohorts.Bucket] = [
    ("[<0)      ", float("-inf"), 0.0),
    ("[0.0-0.1) ", 0.0, 0.10),
    ("[0.1-0.15)", 0.10, 0.15),
    ("[0.15-0.2)", 0.15, 0.20),
    ("[0.2-0.25)", 0.20, 0.25),
    ("[0.25-0.3)", 0.25, 0.30),
    ("[>0.3)    ", 0.30, float("inf")),
]


def add_study_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Add this study's cohort variable on top of qm.add_indicators.

    `tight_range_ratio` is the prior 10 closes' range over their mean, all on the shift-1
    adjusted close (the shared layer drops its internal shifted column, so it is rebuilt here).
    """
    df = df.sort(["symbol", "date"])
    df = df.with_columns(pl.col("adj_close").shift(1).over("symbol").alias("_c1"))
    df = df.with_columns(
        [
            pl.col("_c1").rolling_max(10, min_samples=10).over("symbol").alias("_tr_max"),
            pl.col("_c1").rolling_min(10, min_samples=10).over("symbol").alias("_tr_min"),
            pl.col("_c1").rolling_mean(10, min_samples=10).over("symbol").alias("_tr_mean"),
        ]
    )
    df = df.with_columns(((pl.col("_tr_max") - pl.col("_tr_min")) / pl.col("_tr_mean")).alias("tight_range_ratio"))
    return df.drop(["_c1", "_tr_max", "_tr_min", "_tr_mean"])


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by tight-range ratio; the reference row is what this variant's cap keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    _sma_thresh, cap = VARIANTS[arm.label]
    heading = f"{arm.label}  (current tr cap: <={cap:.2f})"
    references = [(f"<={cap:.2f} (cap)", pl.col("tight_range_ratio") <= cap)]
    return cohorts.bucket_table(heading, trades, "tight_range_ratio", COHORTS, references, label_width=12)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie Tight-Range Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-tightrange.md",
    config_rows=cohorts.config_rows(
        {
            "Cohorts": "**bk50d_s20_tr10_v2.0, bk50d_s20_tr20_v2.0, bk50d_s15_tr15_v2.0 (366d)**",
            "Cohort variable": "tight_range_ratio = (max - min) / mean of the previous 10 closes",
            "Filter under study": "**each variant's tight_range cap — removed; returns as its `<=0.10` / `<=0.20` / `<=0.15 (cap)` row**",
            "Fixed filters": "RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x",
        }
    )
    + [
        (
            "Note",
            "s20_tr10 and s20_tr20 share pct_above_sma50=20%, so with the cap removed they draw from the same "
            "candidate pool — only the reference row differs",
        )
    ],
    tables=tables,
    arms=ARMS,
    require=("tight_range_ratio",),
    add_indicators=add_study_indicators,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
