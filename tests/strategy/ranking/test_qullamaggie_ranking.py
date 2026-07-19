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
    pct_vs_sma50: float | None = 0.35,
) -> dict:
    return {"date": row_date, "close": close, "adr_pct": adr_pct, "adr_pct_change": adr_pct_change, "pct_vs_sma50": pct_vs_sma50}


class TestQullamaggieRanking:
    """Test cases for QullamaggieRanking."""

    def setup_method(self) -> None:
        self.strategy = QullamaggieRanking()

    def test_best_cohorts_score_100(self) -> None:
        """A row in the best band of every dimension scores the full 100."""
        df = _df([_row(close=7.5, adr_pct=0.09, adr_pct_change=0.6, pct_vs_sma50=0.35)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_worst_cohorts_score_0(self) -> None:
        """A row in the worst band of every dimension scores 0."""
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    @pytest.mark.parametrize(
        ("adr_pct", "expected"),
        [(0.019, 0), (0.02, 3), (0.025, 4), (0.03, 6), (0.035, 7), (0.04, 12), (0.045, 14), (0.05, 19), (0.08, 23)],
    )
    def test_adr_band_edges(self, adr_pct: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=adr_pct, adr_pct_change=1.1, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("adr_pct_change", "expected"),
        [(0.69, 22), (0.7, 7), (0.8, 7), (0.9, 4), (1.0, 0)],
    )
    def test_compression_band_edges(self, adr_pct_change: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=adr_pct_change, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("pct_vs_sma50", "expected"),
        [(0.05, 0), (0.10, 6), (0.12, 10), (0.15, 14), (0.17, 8), (0.20, 20), (0.30, 23)],
    )
    def test_pct_sma50_band_edges(self, pct_vs_sma50: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=pct_vs_sma50)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("close", "expected"),
        [(4.0, 28), (5.0, 32), (10.0, 16), (20.0, 14), (50.0, 13), (100.0, 10), (250.0, 0)],
    )
    def test_price_band_edges(self, close: float, expected: int) -> None:
        df = _df([_row(close=close, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    def test_null_values_score_component_zero(self) -> None:
        """Null indicator values drop only that component, no exception."""
        df = _df([_row(close=7.5, adr_pct=None, adr_pct_change=None, pct_vs_sma50=None)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 32  # price component only

    def test_missing_columns_score_zero(self) -> None:
        """A df without the Qullamaggie indicator columns scores price only."""
        df = pl.DataFrame({"date": [date(2024, 6, 3)], "close": [7.5]})
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 32

    def test_rows_after_signal_date_are_ignored(self) -> None:
        """Only the last row at/before the signal date is scored."""
        df = _df(
            [
                _row(row_date=date(2024, 6, 3), close=7.5, adr_pct=0.09, adr_pct_change=0.6, pct_vs_sma50=0.35),
                _row(row_date=date(2024, 6, 4), close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05),
            ]
        )
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_empty_filtered_df_returns_zero(self) -> None:
        """A signal date before all rows yields 0."""
        df = _df([_row(row_date=date(2024, 6, 3))])
        assert self.strategy.ranking(df, date(2024, 6, 1)) == 0
