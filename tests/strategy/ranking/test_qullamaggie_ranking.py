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
    roc_252d: float | None = -0.30,
    rsi14: float | None = 45.0,
) -> dict:
    return {
        "date": row_date,
        "close": close,
        "adr_pct": adr_pct,
        "adr_pct_change": adr_pct_change,
        "pct_vs_sma50": pct_vs_sma50,
        "roc_252d": roc_252d,
        "rsi14": rsi14,
    }


class TestQullamaggieRanking:
    """Test cases for QullamaggieRanking."""

    def setup_method(self) -> None:
        self.strategy = QullamaggieRanking()

    def test_best_cohorts_score_100(self) -> None:
        """A row in the best band of every dimension scores the full 100."""
        df = _df([_row(close=7.5, adr_pct=0.09, adr_pct_change=0.6, pct_vs_sma50=0.35, roc_252d=-0.30, rsi14=45.0)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_worst_cohorts_score_0(self) -> None:
        """A row in the worst band of every dimension scores 0."""
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05, roc_252d=1.1, rsi14=80.0)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 0

    @pytest.mark.parametrize(
        ("adr_pct", "expected"),
        [(0.034, 0), (0.035, 0), (0.04, 3), (0.045, 4), (0.05, 8), (0.08, 12)],
    )
    def test_adr_band_edges(self, adr_pct: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=adr_pct, adr_pct_change=1.1, pct_vs_sma50=0.05, roc_252d=1.1, rsi14=80.0)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("adr_pct_change", "expected"),
        [(0.69, 12), (0.7, 0), (0.8, 1), (0.9, 0)],
    )
    def test_compression_band_edges(self, adr_pct_change: float, expected: int) -> None:
        df = _df(
            [_row(close=300.0, adr_pct=0.015, adr_pct_change=adr_pct_change, pct_vs_sma50=0.05, roc_252d=1.1, rsi14=80.0)]
        )
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("pct_vs_sma50", "expected"),
        [(0.05, 0), (0.10, 12), (0.12, 22), (0.15, 31), (0.17, 17), (0.20, 44), (0.30, 50)],
    )
    def test_pct_sma50_band_edges(self, pct_vs_sma50: float, expected: int) -> None:
        df = _df(
            [_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=pct_vs_sma50, roc_252d=1.1, rsi14=80.0)]
        )
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("close", "expected"),
        [(9.0, 13), (10.0, 4), (20.0, 1), (50.0, 1), (100.0, 0), (250.0, 0)],
    )
    def test_price_band_edges(self, close: float, expected: int) -> None:
        df = _df([_row(close=close, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05, roc_252d=1.1, rsi14=80.0)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("roc_252d", "expected"),
        [(-0.25, 10), (-0.20, 6), (0.0, 5), (0.20, 8), (0.40, 10), (0.60, 5), (0.80, 0), (1.00, 0)],
    )
    def test_roc252_band_edges(self, roc_252d: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05, roc_252d=roc_252d, rsi14=80.0)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    @pytest.mark.parametrize(
        ("rsi14", "expected"),
        [(45.0, 3), (50.0, 2), (60.0, 0), (70.0, 0)],
    )
    def test_rsi_band_edges(self, rsi14: float, expected: int) -> None:
        df = _df([_row(close=300.0, adr_pct=0.015, adr_pct_change=1.1, pct_vs_sma50=0.05, roc_252d=1.1, rsi14=rsi14)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == expected

    def test_null_values_score_component_zero(self) -> None:
        """Null indicator values drop only that component, no exception."""
        df = _df([_row(close=7.5, adr_pct=None, adr_pct_change=None, pct_vs_sma50=None, roc_252d=None, rsi14=None)])
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 13  # price component only

    def test_missing_columns_score_zero(self) -> None:
        """A df without the Qullamaggie indicator columns scores price only."""
        df = pl.DataFrame({"date": [date(2024, 6, 3)], "close": [7.5]})
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 13

    def test_rows_after_signal_date_are_ignored(self) -> None:
        """Only the last row at/before the signal date is scored."""
        df = _df(
            [
                _row(
                    row_date=date(2024, 6, 3),
                    close=7.5,
                    adr_pct=0.09,
                    adr_pct_change=0.6,
                    pct_vs_sma50=0.35,
                    roc_252d=-0.30,
                    rsi14=45.0,
                ),
                _row(
                    row_date=date(2024, 6, 4),
                    close=300.0,
                    adr_pct=0.015,
                    adr_pct_change=1.1,
                    pct_vs_sma50=0.05,
                    roc_252d=1.1,
                    rsi14=80.0,
                ),
            ]
        )
        assert self.strategy.ranking(df, date(2024, 6, 3)) == 100

    def test_empty_filtered_df_returns_zero(self) -> None:
        """A signal date before all rows yields 0."""
        df = _df([_row(row_date=date(2024, 6, 3))])
        assert self.strategy.ranking(df, date(2024, 6, 1)) == 0
