#!/usr/bin/env python3
"""
RSI(14) cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the RSI filter (< 70), so we can see
performance across the full RSI(14) range including the 70-100 band.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

COHORTS: list[cohorts.Bucket] = [
    ("[0-20)    ", 0.0, 20.0),
    ("[20-40)   ", 20.0, 40.0),
    ("[40-60)   ", 40.0, 60.0),
    ("[40-50)   ", 40.0, 50.0),
    ("[50-60)   ", 50.0, 60.0),
    ("[60-70)   ", 60.0, 70.0),
    ("[70-75)   ", 70.0, 75.0),
    ("[75-80)   ", 75.0, 80.0),
    ("[80-90)   ", 80.0, 90.0),
    ("[90-100]  ", 90.0, 100.0001),
]


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by RSI(14); the reference row is what the RSI < 70 filter keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    return cohorts.bucket_table(arm.label, trades, "rsi14", COHORTS, [(f"<{int(qm.RSI_CAP)}", pl.col("rsi14") < qm.RSI_CAP)])


SPEC = cohorts.CohortSpec(
    title="Qullamaggie RSI(14) Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-rsi.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "RSI(14) on the signal date",
            "Filter under study": f"**RSI < {int(qm.RSI_CAP)} — removed; returns as the `<{int(qm.RSI_CAP)}` row**",
            "Fixed filters": "ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range)",
        }
    ),
    tables=tables,
    drop=("rsi",),
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
