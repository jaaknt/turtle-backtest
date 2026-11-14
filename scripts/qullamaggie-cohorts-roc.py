#!/usr/bin/env python3
"""
ROC252 cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the roc_12m_cap < 100% cap, so we can see
performance across the full 12-month-ROC range including >100% cohorts.
roc_252d = close / close[-252] - 1

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

COHORTS: list[cohorts.Bucket] = [
    ("<-20%    ", float("-inf"), -0.20),
    ("-20-0%   ", -0.20, 0.00),
    ("0-20%    ", 0.00, 0.20),
    ("20-40%   ", 0.20, 0.40),
    ("40-60%   ", 0.40, 0.60),
    ("60-80%   ", 0.60, 0.80),
    ("80-100%  ", 0.80, 1.00),
    ("100-120% ", 1.00, 1.20),
    ("120-140% ", 1.20, 1.40),
    ("140-160% ", 1.40, 1.60),
    (">160%    ", 1.60, float("inf")),
]


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by 12-month ROC; the reference row is what the roc_12m < 100% cap keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    return cohorts.bucket_table(arm.label, trades, "roc_252d", COHORTS, [("<100% (cap)", pl.col("roc_252d") < qm.ROC_CAP)], label_width=10)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie ROC252 Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-roc.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "roc_252d = close / close[-252] - 1, on the signal date",
            "Filter under study": "**roc_12m < 100% — removed; returns as the `<100% (cap)` row**",
            "Fixed filters": "RSI<70, ADR>=3.0%, ADR_change<90%, vol_surge<2.0x (no tight_range)",
        }
    ),
    tables=tables,
    drop=("roc",),
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
