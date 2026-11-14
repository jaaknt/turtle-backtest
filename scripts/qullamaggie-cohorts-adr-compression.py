#!/usr/bin/env python3
"""
ADR compression cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All standard bk50d filters (no tight_range) apply as-is EXCEPT the production
ADR_change < 90% cap, which is a cap on this very metric — it is removed so the
cohorts above 0.9 exist at all, and reported instead as the `<0.9 (cap)` row.

ADR%(N)     = mean((high[-i] - low[-i]) / low[-i] for i in 1..N) * 100  (shift-1, no look-ahead)
compression = ADR%(10) / ADR%(50), supplied by qm.add_indicators as `adr_pct_change`

compression < 1 means the last 10 days have been quieter than the last 50 (volatility
contraction ahead of the breakout); > 1 means recent volatility is expanding.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

COHORTS: list[cohorts.Bucket] = [
    ("[<0.5)    ", float("-inf"), 0.5),
    ("[0.5-0.7) ", 0.5, 0.7),
    ("[0.7-0.8) ", 0.7, 0.8),
    ("[0.8-0.9) ", 0.8, 0.9),
    ("[0.9-1.0) ", 0.9, 1.0),
    ("[1.0-1.3) ", 1.0, 1.3),
    ("[>1.3)    ", 1.3, float("inf")),
]


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by ADR compression; the reference row is what the ADR_change < 90% cap keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    references = [(f"<{qm.ADR_CHANGE_CAP:g} (cap)", pl.col("adr_pct_change") < qm.ADR_CHANGE_CAP)]
    return cohorts.bucket_table(arm.label, trades, "adr_pct_change", COHORTS, references, label_width=12)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie ADR Compression Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-adr-compression.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "compression = ADR%(10) / ADR%(50) (`adr_pct_change`), on the signal date",
            "Filter under study": "**ADR_change < 90% — removed; returns as the `<0.9 (cap)` row**",
            "Fixed filters": "RSI<70, ADR>=3.0%, roc_12m<100%, vol_surge<2.0x (no tight_range)",
        }
    ),
    tables=tables,
    drop=("adr_change",),
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
