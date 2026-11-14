#!/usr/bin/env python3
"""
Average-volume cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

Drops the production `avg_vol_20 >= 100K` liquidity floor and buckets every signal by that
same 20-day average volume, so the sub-floor cohort exists at all. `>=100K (cap)` is the
reference row: the slice the live filter keeps. The floor was 500K when this study first ran,
and this study is why it moved — the committed result doc still shows the 500K reference row.

avg_vol_20 = mean(volume[-21:-1]) — raw share volume, shift-1, exactly what the filter reads.

Two things this study can and cannot say. The floor is partly a *tradability* constraint rather
than a pure alpha filter: a sub-floor cohort scoring well does not mean those signals are
takeable at portfolio size, because a 3-5% position in a thin name moves the price it is
measured at. And the floor is denominated in **shares, not dollars**, so it is not a constant
liquidity bar across the $5-$250 price band — a $200 name at 400K shares ($80M/day) is excluded
while a $6 name at 600K shares ($3.6M/day) passes.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

_K = 1_000
_M = 1_000_000

COHORTS: list[cohorts.Bucket] = [
    ("(<100K)    ", 0, 100 * _K),
    ("[100-250K) ", 100 * _K, 250 * _K),
    ("[250-500K) ", 250 * _K, 500 * _K),
    ("[500K-1M)  ", 500 * _K, 1 * _M),
    ("[1-2M)     ", 1 * _M, 2 * _M),
    ("[2-5M)     ", 2 * _M, 5 * _M),
    ("[5-10M)    ", 5 * _M, 10 * _M),
    ("(>10M)     ", 10 * _M, float("inf")),
]


PREAMBLE = (
    "> **⚠ A sub-floor cohort scoring well is not automatically a relaxation.** The `avg_vol_20 >= 100K` "
    "floor is partly a *tradability* constraint rather than a pure alpha filter: a 3-5% portfolio "
    "position in a thin name moves the price the backtest measures it at, so these returns are less "
    "attainable the lower the cohort sits. The floor is also denominated in **shares, not dollars**, so "
    "it is not a constant liquidity bar across the $5-$250 price band — a $200 name at 400K shares "
    "($80M/day) is excluded while a $6 name at 600K shares ($3.6M/day) passes.\n\n"
)


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by 20-day average volume; the reference row is what the liquidity floor keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    references = [(f">={qm.MIN_AVG_VOL // 1000}K (cap)", pl.col("avg_vol_20") >= qm.MIN_AVG_VOL)]
    return cohorts.bucket_table(arm.label, trades, "avg_vol_20", COHORTS, references, label_width=12)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie Average-Volume Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-avg-vol.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "avg_vol_20 = mean(volume[-21:-1]) — raw shares, shift-1",
            "Filter under study": (
                f"**`avg_vol_20 >= {qm.MIN_AVG_VOL // 1000}K` — removed, otherwise the sub-floor cohort would be "
                f"empty; returns as the `>={qm.MIN_AVG_VOL // 1000}K (cap)` row**"
            ),
            "⚠ Tradability": (
                "**this floor is partly a fill constraint, not pure alpha — a sub-floor cohort scoring well is "
                "not necessarily takeable at 3-5% position size. It is also denominated in shares, not dollars**"
            ),
            "Min avg vol (20d)": None,
        }
    ),
    tables=tables,
    drop=("avg_vol",),
    require=("avg_vol_20",),
    preamble=PREAMBLE,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
