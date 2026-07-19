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
    adr_pct_change: float | None = 0.6,
    roc_252d: float | None = 0.5,
) -> dict:
    return {"date": row_date, "close": close, "adr_pct": adr_pct, "adr_pct_change": adr_pct_change, "roc_252d": roc_252d}


class TestQullamaggieRanking:
    """Test cases for QullamaggieRanking."""

    def setup_method(self) -> None:
        self.strategy = QullamaggieRanking()

    def test_best_cohorts_score_100(self) -> None:
        """A row in the best band of every dimension scores the full 100."""
        df = _df([_row(close=7.5, adr_pct=0.09, adr_pct_change=0.6, roc_252d=0.5)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_worst_cohorts_score_0(self) -> None:
        """A row in the worst band of every dimension scores 0."""
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, roc_252d=0.9)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    @pytest.mark.parametrize(
        ("adr_pct", "expected"),
        [(0.019, 0), (0.02, 3), (0.025, 5), (0.03, 7), (0.035, 7), (0.04, 13), (0.045, 15), (0.05, 21), (0.08, 25)],
    )
    def test_adr_band_edges(self, adr_pct: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=adr_pct, adr_pct_change=1.1, roc_252d=0.9)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("adr_pct_change", "expected"),
        [(0.69, 25), (0.7, 8), (0.8, 8), (0.9, 4), (1.0, 0)],
    )
    def test_compression_band_edges(self, adr_pct_change: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=adr_pct_change, roc_252d=0.9)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("roc_252d", "expected"),
        [(-0.3, 22), (-0.1, 17), (0.1, 13), (0.3, 18), (0.5, 25), (0.7, 4), (0.85, 0)],
    )
    def test_roc_band_edges(self, roc_252d: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, roc_252d=roc_252d)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("close", "expected"),
        [(4.0, 22), (5.0, 25), (10.0, 13), (20.0, 11), (50.0, 10), (100.0, 7), (250.0, 0)],
    )
    def test_price_band_edges(self, close: float, expected: int) -> None:
        df = _df([_row(close=close, adr_pct=0.015, adr_pct_change=1.1, roc_252d=0.9)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    def test_null_values_score_component_zero(self) -> None:
        """Null indicator values drop only that component, no exception."""
        df = _df([_row(close=7.5, adr_pct=None, adr_pct_change=None, roc_252d=None)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 25  # price component only

    def test_missing_columns_score_zero(self) -> None:
        """A df without the Qullamaggie indicator columns scores price only."""
        df = pl.DataFrame({"date": [date(2024, 6, 3)], "close": [7.5]})
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 25

    def test_rows_after_signal_date_are_ignored(self) -> None:
        """Only the last row at/before the signal date is scored."""
        df = _df(
            [
                _row(row_date=date(2024, 6, 3), close=7.5, adr_pct=0.09, adr_pct_change=0.6, roc_252d=0.5),
                _row(row_date=date(2024, 6, 4), close=300.0, adr_pct=0.015, adr_pct_change=1.1, roc_252d=0.9),
            ]
        )
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_empty_filtered_df_returns_zero(self) -> None:
        """A signal date before all rows yields 0."""
        df = _df([_row(row_date=date(2024, 6, 3))])
        assert self.strategy.ranking(df, date(2024, 6, 1)) == 0
