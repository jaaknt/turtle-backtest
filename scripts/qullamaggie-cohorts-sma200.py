#!/usr/bin/env python3
"""
SMA(200) cohort analysis for bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d hold).

Cohort variable: pct_vs_sma200 = close / SMA200 − 1 on the signal date, where SMA200 is the
mean of the previous 200 closes (shift-1, same convention as sma50). The baseline strategy
has no stock-level SMA(200) filter (only the SPY regime uses SMA200), so ALL v2.0 filters
are applied unchanged and the cohorts just slice the existing signal population.

Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)
"""

from pathlib import Path

import polars as pl

from turtlex.research import cohorts

COHORTS: list[cohorts.Bucket] = [
    ("(<-50%)   ", float("-inf"), -50.0),
    ("[-50:-20) ", -50.0, -20.0),
    ("[-20:0)   ", -20.0, 0.0),
    ("[0:10)    ", 0.0, 10.0),
    ("[10:20)   ", 10.0, 20.0),
    ("[20:30)   ", 20.0, 30.0),
    ("[30:40)   ", 30.0, 40.0),
    ("[40:50)   ", 40.0, 50.0),
    ("[50:60)   ", 50.0, 60.0),
    ("[60:80)   ", 60.0, 80.0),
    ("[80:100)  ", 80.0, 100.0),
    ("(>100%)   ", 100.0, float("inf")),
]


def add_study_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Add this study's cohort variable on top of qm.add_indicators.

    `sma200` is the 200-day mean of the shift-1 adjusted close (the shared layer drops its
    internal shifted column, so it is rebuilt here); `pct_vs_sma200` compares the breakout
    bar's adjusted close against it.
    """
    df = df.sort(["symbol", "date"])
    df = df.with_columns(pl.col("adj_close").shift(1).over("symbol").alias("_c1"))
    df = df.with_columns(pl.col("_c1").rolling_mean(200, min_samples=200).over("symbol").alias("sma200"))
    df = df.with_columns(((pl.col("adj_close") / pl.col("sma200")) - 1.0).alias("pct_vs_sma200"))
    return df.drop("_c1")


def tables(arm: cohorts.Arm, trades: pl.DataFrame) -> list[str]:
    """Bucket by distance from SMA200 in percent, with above/below summary rows.

    Args:
        arm: The algorithm variant being tabulated
        trades: Its completed trades, from `cohorts.cohort_trades`
    """
    pct = pl.col("pct_vs_sma200") * 100
    return cohorts.bucket_table(arm.label, trades, pct, COHORTS, [(">=SMA200", pct >= 0), ("<SMA200", pct < 0)])


SPEC = cohorts.CohortSpec(
    title="Qullamaggie SMA(200) Cohort Analysis",
    result_path=Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-sma200.md",
    config_rows=cohorts.config_rows(
        {
            "Cohort variable": "pct_vs_sma200 = close / SMA200(prev 200 closes) - 1 on the signal date, in %",
            "Filter under study": (
                "**none — the baseline has no stock-level SMA(200) filter, so the cohorts just slice the existing signal population**"
            ),
        }
    ),
    tables=tables,
    require=("sma200",),
    add_indicators=add_study_indicators,
)


if __name__ == "__main__":
    cohorts.run_cohort_study(SPEC)
