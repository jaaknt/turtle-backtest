#!/usr/bin/env python3
"""
Entry-price cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the close>$5&<$250 price bounds, so we can see
performance across the full entry-price range including sub-$5 and $250+ cohorts.

This study runs UNGATED, like the ADR% study. QullamaggieRanking scores the raw close as its
25-point dimension, so a >=44 gate filters on the very variable being cohorted and would thin
the expensive cohorts this study exists to measure.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

COHORTS: list[cohorts.Bucket] = [
    ("[0-5)      ", 0.0, 5.0),
    ("[5-10)     ", 5.0, 10.0),
    ("[10-20)    ", 10.0, 20.0),
    ("[20-50)    ", 20.0, 50.0),
    ("[50-100)   ", 50.0, 100.0),
    ("[100-250)  ", 100.0, 250.0),
    ("[250-700)  ", 250.0, 700.0),
    ("[700-2000) ", 700.0, 2000.0),
    ("[>2000]    ", 2000.0, float("inf")),
]


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by raw close; the reference row is what the $5-$250 band keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    references = [("$5-$250 (cap)", (pl.col("raw_close") > qm.MIN_PRICE) & (pl.col("raw_close") < qm.MAX_PRICE))]
    return cohorts.bucket_table(arm.label, trades, "raw_close", COHORTS, references, label_width=12)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie Entry-Price Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-price.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "raw close on the signal date, in dollars",
            "Filter under study": "**close > $5 & < $250 — removed; returns as the `$5-$250 (cap)` row**",
            "Ranking gate": "**not applied — price is the score's 25-point dimension and the cohort variable (ungated)**",
            "Price range": "**removed — this is the cohort variable**",
        }
    ),
    tables=tables,
    drop=("price",),
    gated=False,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
