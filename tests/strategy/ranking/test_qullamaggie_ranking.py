"""Tests for QullamaggieRanking cohort-derived scoring."""

from datetime import date

import polars as pl
import pytest

from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking


def _df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows)


def _row(
    row_date: date = date(2024, 6, 3),
    close: float | None = 7.5,
    adr_pct: float | None = 0.09,
    pct_vs_sma50: float | None = 0.35,
) -> dict:
    return {
        "date": row_date,
        "close": close,
        "adr_pct": adr_pct,
        "pct_vs_sma50": pct_vs_sma50,
    }


class TestQullamaggieRanking:
    """Test cases for QullamaggieRanking."""

    def setup_method(self) -> None:
        self.strategy = QullamaggieRanking()

    def test_best_cohorts_score_100(self) -> None:
        """A row in the best band of every dimension scores the full 100."""
        df = _df([_row(close=7.5, adr_pct=0.09, pct_vs_sma50=0.35)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_worst_cohorts_score_0(self) -> None:
        """A row in the worst band of every dimension scores 0."""
        df = _df([_row(close=300.0, adr_pct=0.015, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    @pytest.mark.parametrize(
        ("adr_pct", "expected"),
        [(0.034, 0), (0.035, 0), (0.04, 10), (0.045, 13), (0.05, 27), (0.08, 40)],
    )
    def test_adr_band_edges(self, adr_pct: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=adr_pct, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("pct_vs_sma50", "expected"),
        [(0.05, 0), (0.10, 8), (0.12, 15), (0.15, 22), (0.17, 12), (0.20, 31), (0.30, 35)],
    )
    def test_pct_sma50_band_edges(self, pct_vs_sma50: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, pct_vs_sma50=pct_vs_sma50)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("close", "expected"),
        [(9.0, 25), (10.0, 8), (20.0, 2), (50.0, 2), (100.0, 0), (250.0, 0)],
    )
    def test_price_band_edges(self, close: float, expected: int) -> None:
        df = _df([_row(close=close, adr_pct=0.015, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize("dropped", ["adr_pct_change", "roc_252d", "rsi14"])
    def test_dropped_dimensions_do_not_score(self, dropped: str) -> None:
        """ADR compression, 12-month ROC and RSI(14) no longer contribute any points."""
        best = {"adr_pct_change": 0.6, "roc_252d": -0.30, "rsi14": 45.0}[dropped]
        df = _df([{**_row(close=300.0, adr_pct=0.015, pct_vs_sma50=0.05), dropped: best}])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    def test_dropped_dimensions_cannot_push_past_100(self) -> None:
        """Re-adding a dimension would break the 0-100 contract; pin the ceiling from above."""
        best_dropped = {"adr_pct_change": 0.6, "roc_252d": -0.30, "rsi14": 45.0}
        df = _df([{**_row(close=7.5, adr_pct=0.09, pct_vs_sma50=0.35), **best_dropped}])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_values_score_component_zero(self, bad: float) -> None:
        """Non-finite metrics score 0, not the top band.

        Without the isfinite guard these fall through every `value < upper` comparison and
        collect the trailing constant — adr_pct=nan would score the full 40 and sail through
        the default min_ranking gate on garbage.
        """
        df = _df([_row(close=300.0, adr_pct=bad, pct_vs_sma50=bad)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    def test_null_values_score_component_zero(self) -> None:
        """Null indicator values drop only that component, no exception."""
        df = _df([_row(close=7.5, adr_pct=None, pct_vs_sma50=None)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 25  # price component only

    def test_all_null_scores_zero(self) -> None:
        """With every scored column null there is nothing left to earn points on."""
        df = _df([_row(close=None, adr_pct=None, pct_vs_sma50=None)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    def test_missing_columns_score_price_only(self) -> None:
        """A df without the Qullamaggie indicator columns scores price only.

        This is the cross-strategy pairing: darvas_box/mars/momentum compute neither
        adr_pct nor pct_vs_sma50, so every signal caps at 25 — below the default
        min_ranking of 40, which means no trades at all rather than a degraded ranking.
        """
        df = pl.DataFrame({"date": [date(2024, 6, 3)], "close": [7.5]})
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 25

    def test_single_dimension_cannot_clear_the_default_gate_alone(self) -> None:
        """Characterise which dimensions clear min_ranking=40 unaided — this inverted in 2026-07.

        Under the previous 50/13/12 weighting a best-band pct_vs_sma50 scored 50 and cleared
        the gate on its own while a best-band adr_pct (12) could not. At 40/35/25 it is the
        other way round. Anyone re-weighting again should see this move.
        """
        best_sma50_only = _row(close=300.0, adr_pct=0.015, pct_vs_sma50=0.35)
        best_adr_only = _row(close=300.0, adr_pct=0.09, pct_vs_sma50=0.05)
        assert self.strategy.ranking(_df([best_sma50_only]), date(2024, 6, 3)) == 35
        assert self.strategy.ranking(_df([best_adr_only]), date(2024, 6, 3)) == 40

    def test_rows_after_signal_date_are_ignored(self) -> None:
        """Only the last row at/before the signal date is scored."""
        df = _df(
            [
                _row(row_date=date(2024, 6, 3), close=7.5, adr_pct=0.09, pct_vs_sma50=0.35),
                _row(row_date=date(2024, 6, 4), close=300.0, adr_pct=0.015, pct_vs_sma50=0.05),
            ]
        )
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_empty_filtered_df_returns_zero(self) -> None:
        """A signal date before all rows yields 0."""
        df = _df([_row(row_date=date(2024, 6, 3))])
        assert self.strategy.ranking(df, date(2024, 6, 1)) == 0
