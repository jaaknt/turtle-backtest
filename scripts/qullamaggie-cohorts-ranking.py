#!/usr/bin/env python3
"""
QullamaggieRanking cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

Cohorts every signal by the production ranking score from
`turtlex/strategy/ranking/qullamaggie.py` and reports forward 366d performance per cohort,
so the question "does the score this portfolio gates on actually separate outcomes, and is
MIN_RANKING >= 44 the right cut?" can be read off directly.

Runs UNGATED on purpose: the cohort variable *is* the ranking, so applying the >= 44 gate
would empty every cohort below it and destroy the only thing the study measures. The `>=44`
reference row at the foot of each table is what the gate would actually keep.

Two views of the same trades:
  - fixed score bands, which are stable across runs and comparable with the ranking cohort
    table in scripts/qullamaggie-signals-v4.py
  - population deciles, which adapt to where the score mass actually sits

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)

References: docs/research/qullamaggie-backtest-v4.md,
docs/research/result-qullamaggie-ranking-weights.md (where the 40/35/25 weights come from)
"""

from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

N_DECILES = 10

BANDS: list[cohorts.Bucket] = [
    ("[0-20)", 0.0, 20.0),
    ("[20-40)", 20.0, 40.0),
    ("[40-50)", 40.0, 50.0),
    ("[50-60)", 50.0, 60.0),
    ("[60-70)", 60.0, 70.0),
    ("[70-80)", 70.0, 80.0),
    ("[80-90)", 80.0, 90.0),
    ("[90-100]", 90.0, 100.0001),
]


def build_deciles(trades: pl.DataFrame) -> list[tuple[str, np.ndarray]]:
    """Group trades into population deciles by score, never splitting a tie group.

    QullamaggieRanking sums three band scores, so it takes only a few dozen distinct values
    and ties are large. Equal-N deciles would cut one score value across two rows and let the
    difference between them be read as an effect of the score, which it cannot be. Every trade
    sharing a score therefore lands in the same decile, which makes the rows uneven in size —
    so each row prints the score range it covers and its own N.

    Args:
        trades: Completed trades, each with `ranking` and `ret`

    Returns:
        (label, returns) per decile, ascending by score. Fewer than `N_DECILES` rows when
        the distinct scores present cannot be split that finely.
    """
    by_score: dict[int, list[float]] = defaultdict(list)
    for score, ret in zip(trades["ranking"].to_list(), trades["ret"].to_list(), strict=True):
        by_score[score].append(ret)

    target = trades.height / N_DECILES
    rows: list[tuple[str, np.ndarray]] = []
    lo: int | None = None
    bucket: list[float] = []
    seen = 0
    for score in sorted(by_score):
        if lo is None:
            lo = score
        bucket.extend(by_score[score])
        seen += len(by_score[score])
        if len(rows) < N_DECILES - 1 and seen >= target * (len(rows) + 1):
            rows.append((f"D{len(rows) + 1} [{lo}-{score}]", np.array(bucket)))
            lo, bucket = None, []
    if bucket and lo is not None:
        rows.append((f"D{len(rows) + 1} [{lo}-{max(by_score)}]", np.array(bucket)))
    return rows


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Two views of the same trades: fixed score bands, then tie-aware population deciles.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    everything = ("ALL (ungated)", cohorts.returns(trades))
    gate = (f">={qm.MIN_RANKING} (gate)", cohorts.returns(trades, pl.col("ranking") >= qm.MIN_RANKING))
    bands = cohorts.render_table(f"{arm.label} — fixed score bands", cohorts.bucket_groups(trades, "ranking", BANDS), [everything, gate])
    deciles = cohorts.render_table(f"{arm.label} — population deciles (D1 = lowest score)", build_deciles(trades), [everything])
    return bands + deciles


SPEC = cohorts.CohortSpec(
    title="Qullamaggie Ranking Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-ranking.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "QullamaggieRanking score — ADR%(20) 0-40 + %abv_sma50 0-35 + price 0-25",
            "Filter under study": "**none — no production filter is dropped, but the ranking gate below is the cohort variable**",
            "Ranking gate": f"**not applied — reported as the `>={qm.MIN_RANKING} (gate)` reference row against `ALL (ungated)`**",
        }
    ),
    tables=tables,
    gated=False,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
