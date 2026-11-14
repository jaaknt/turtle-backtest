#!/usr/bin/env python3
"""
ADR% cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

All strategy filters applied EXCEPT the adr_pct >= 3.0% floor, so we can see
performance across the full ADR% range including the sub-3% cohorts.
adr_pct = mean((high_i - low_i) / low_i, i in last 20 days, shift-1)

Bars, indicators and entry resolution come from turtlex.research.qullamaggie, which is
parity-tested against QullamaggieStrategy. That gives this study split/dividend-adjusted
prices (the local copy this replaced used raw closes, so a split showed as a fake ~90%
one-day move) and next-trading-day open entries. The ADR floor is dropped by name through
`qm.get_signals`'s `drop`, so the rest of the production filter chain is the shared one.

This study runs UNGATED, unlike the other cohort studies. QullamaggieRanking scores adr_pct as
its 40-point dimension, so a >=44 gate filters on the very variable being cohorted: a gated run
collapsed [0-1.0) to N=1 and wiped out the sub-3% comparison this study exists to make.

Period: 2015-01-01 - 2026-06-26  (warmup handled by qm.load_bars)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

COHORTS: list[cohorts.Bucket] = [
    ("[0-1.0)  ", 0.000, 0.010),
    ("[1.0-2.0)", 0.010, 0.020),
    ("[2.0-2.5)", 0.020, 0.025),
    ("[2.5-3.0)", 0.025, 0.030),
    ("[3.0-3.5)", 0.030, 0.035),
    ("[3.5-4.0)", 0.035, 0.040),
    ("[4.0-4.5)", 0.040, 0.045),
    ("[4.5-5.0)", 0.045, 0.050),
    ("[5.0-7.0)", 0.050, 0.070),
    ("[7.0-8.0)", 0.070, 0.080),
    ("(>8.0)   ", 0.080, float("inf")),
]


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by ADR%(20); the reference row is what the ADR >= 3% floor keeps.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    return cohorts.bucket_table(arm.label, trades, "adr_pct", COHORTS, [(">=3% (min)", pl.col("adr_pct") >= qm.ADR_MIN)], label_width=10)


SPEC = cohorts.CohortSpec(
    title="Qullamaggie ADR% Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-adr.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "adr_pct = mean((high - low) / low) over the previous 20 days (shift-1)",
            "Filter under study": "**ADR >= 3.0% — removed; returns as the `>=3% (min)` row**",
            "Fixed filters": "RSI<70, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range)",
            "Ranking gate": "**not applied — ADR%(20) is the score's 40-point dimension and the cohort variable (ungated)**",
        }
    ),
    tables=tables,
    drop=("adr_min",),
    require=("adr_pct",),
    gated=False,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
