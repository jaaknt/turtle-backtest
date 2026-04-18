from datetime import date, datetime
from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository
from unittest.mock import MagicMock, patch

import pandas as pd
import polars as pl
import pytest


@pytest.fixture
def mock_engine() -> MagicMock:
    return MagicMock()


def _make_repo(mock_engine: MagicMock) -> OhlcvAnalyticsRepository:
    return OhlcvAnalyticsRepository(engine=mock_engine)


def _sample_pd_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [100.0, 102.0],
            "high": [105.0, 110.0],
            "low": [95.0, 100.0],
            "close": [102.0, 108.0],
            "adjusted_close": [102.0, 108.0],
            "volume": [1_000_000, 1_200_000],
        },
        index=pd.Index([date(2024, 1, 2), date(2024, 1, 3)], name="date"),
    )


def _sample_pl_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date": [date(2024, 1, 2), date(2024, 1, 3)],
            "open": [100.0, 102.0],
            "high": [105.0, 110.0],
            "low": [95.0, 100.0],
            "close": [102.0, 108.0],
            "adjusted_close": [102.0, 108.0],
            "volume": [1_000_000, 1_200_000],
        }
    )


# --- get_bars_pd ---


def test_get_bars_pd_returns_dataframe(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pd.read_sql", return_value=_sample_pd_df()):
        result = _make_repo(mock_engine).get_bars_pd("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["open", "high", "low", "close", "adjusted_close", "volume"]
    assert len(result) == 2
    assert result["close"].tolist() == [102.0, 108.0]


def test_get_bars_pd_returns_empty_dataframe_when_no_data(mock_engine: MagicMock) -> None:
    empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "adjusted_close", "volume"])

    with patch("turtle.repository.analytics.pd.read_sql", return_value=empty_df):
        result = _make_repo(mock_engine).get_bars_pd("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_get_bars_pd_passes_correct_date_range(mock_engine: MagicMock) -> None:
    captured: list[object] = []

    def capture(stmt: object, conn: object, **kwargs: object) -> pd.DataFrame:
        captured.append(stmt)
        return pd.DataFrame(columns=["open", "high", "low", "close", "adjusted_close", "volume"])

    with patch("turtle.repository.analytics.pd.read_sql", side_effect=capture):
        _make_repo(mock_engine).get_bars_pd("AAPL", date(2024, 1, 1), date(2024, 12, 31))

    assert len(captured) == 1
    compiled = str(captured[0].compile(compile_kwargs={"literal_binds": True}))
    assert "2024-01-01" in compiled
    assert "2024-12-31" in compiled
    assert "AAPL" in compiled


def test_get_bars_pd_uses_engine_connection(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pd.read_sql", return_value=pd.DataFrame()):
        _make_repo(mock_engine).get_bars_pd("AAPL", date(2024, 1, 1), date(2024, 1, 31))

    mock_engine.connect.assert_called_once()


# --- get_bars_pl ---


def test_get_bars_pl_returns_polars_dataframe(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pl.read_database", return_value=_sample_pl_df()):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pl.DataFrame)
    assert result.columns == ["date", "open", "high", "low", "close", "adjusted_close", "volume"]
    assert len(result) == 2
    assert result["close"].to_list() == [102.0, 108.0]


def test_get_bars_pl_returns_empty_dataframe_when_no_data(mock_engine: MagicMock) -> None:
    empty_df = pl.DataFrame({"date": [], "open": [], "high": [], "low": [], "close": [], "adjusted_close": [], "volume": []})

    with patch("turtle.repository.analytics.pl.read_database", return_value=empty_df):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pl.DataFrame)
    assert result.is_empty()


def test_get_bars_pl_passes_correct_date_range(mock_engine: MagicMock) -> None:
    """Verify the SQL statement filters on the expected date boundaries."""
    captured: list[object] = []

    def capture(query: object, connection: object, **kwargs: object) -> pl.DataFrame:
        captured.append(query)
        return pl.DataFrame()

    with patch("turtle.repository.analytics.pl.read_database", side_effect=capture):
        _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 12, 31))

    assert len(captured) == 1
    compiled = str(captured[0].compile(compile_kwargs={"literal_binds": True}))
    assert "2024-01-01" in compiled
    assert "2024-12-31" in compiled
    assert "AAPL" in compiled


def test_get_bars_pl_uses_engine_connection(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pl.read_database", return_value=pl.DataFrame()):
        _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 1, 31))

    mock_engine.connect.assert_called_once()


def test_get_bars_pl_day_returns_daily_data(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pl.read_database", return_value=_sample_pl_df()):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 2), date(2024, 1, 3), TimeFrameUnit.DAY)

    assert len(result) == 2
    assert result["close"].to_list() == [102.0, 108.0]


def test_get_bars_pl_week_resamples(mock_engine: MagicMock) -> None:
    # Two weeks of data: Mon 2024-01-08 and Mon 2024-01-15
    two_weeks = pl.DataFrame(
        {
            "date": [date(2024, 1, 8), date(2024, 1, 9), date(2024, 1, 15), date(2024, 1, 16)],
            "open": [100.0, 101.0, 110.0, 111.0],
            "high": [105.0, 106.0, 115.0, 116.0],
            "low": [99.0, 100.0, 109.0, 110.0],
            "close": [103.0, 104.0, 113.0, 114.0],
            "adjusted_close": [103.0, 104.0, 113.0, 114.0],
            "volume": [1_000_000, 1_100_000, 1_200_000, 1_300_000],
        }
    )
    with patch("turtle.repository.analytics.pl.read_database", return_value=two_weeks):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 8), date(2024, 1, 16), TimeFrameUnit.WEEK)

    assert len(result) == 2
    # Week 1 aggregation
    assert result["open"][0] == 100.0
    assert result["high"][0] == 106.0
    assert result["low"][0] == 99.0
    assert result["close"][0] == 104.0
    assert result["volume"][0] == 2_100_000
    # Week 2 aggregation
    assert result["open"][1] == 110.0
    assert result["high"][1] == 116.0
    assert result["volume"][1] == 2_500_000


def test_get_bars_pl_week_returns_empty_for_empty_input(mock_engine: MagicMock) -> None:
    empty = pl.DataFrame({"date": [], "open": [], "high": [], "low": [], "close": [], "adjusted_close": [], "volume": []})
    with patch("turtle.repository.analytics.pl.read_database", return_value=empty):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 1, 31), TimeFrameUnit.WEEK)

    assert result.is_empty()


def test_get_bars_pl_raises_for_unsupported_time_frame_unit(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pl.read_database", return_value=_sample_pl_df()):
        with pytest.raises(ValueError, match="Unsupported time_frame_unit"):
            _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 1, 31), "month")  # type: ignore[arg-type]


# --- get_ticker_history ---


def test_get_ticker_history_day_returns_dataframe(mock_engine: MagicMock) -> None:
    with patch("turtle.repository.analytics.pd.read_sql", return_value=_sample_pd_df()):
        result = _make_repo(mock_engine).get_ticker_history("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["open", "high", "low", "close", "adjusted_close", "volume"]
    assert len(result) == 2


def test_get_ticker_history_accepts_datetime_inputs(mock_engine: MagicMock) -> None:
    """datetime inputs must be coerced to date before reaching the SQL statement."""
    captured: list[object] = []

    def capture(stmt: object, conn: object, **kwargs: object) -> pd.DataFrame:
        captured.append(stmt)
        return _sample_pd_df()

    with patch("turtle.repository.analytics.pd.read_sql", side_effect=capture):
        _make_repo(mock_engine).get_ticker_history(
            "AAPL",
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 3, 0, 0, 0),
        )

    compiled = str(captured[0].compile(compile_kwargs={"literal_binds": True}))
    assert "2024-01-02" in compiled
    assert "2024-01-03" in compiled


def test_get_ticker_history_week_resamples(mock_engine: MagicMock) -> None:
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [110.0, 111.0, 112.0, 113.0, 114.0],
            "low": [90.0, 91.0, 92.0, 93.0, 94.0],
            "close": [105.0, 106.0, 107.0, 108.0, 109.0],
            "adjusted_close": [105.0, 106.0, 107.0, 108.0, 109.0],
            "volume": [1_000, 1_100, 1_200, 1_300, 1_400],
        },
        index=pd.to_datetime(["2024-01-08", "2024-01-09", "2024-01-10", "2024-01-15", "2024-01-16"]),
    )
    with patch("turtle.repository.analytics.pd.read_sql", return_value=df):
        result = _make_repo(mock_engine).get_ticker_history("AAPL", date(2024, 1, 8), date(2024, 1, 16), TimeFrameUnit.WEEK)

    assert len(result) == 2  # two calendar weeks
    assert result["open"].iloc[0] == 100.0  # first of week
    assert result["high"].iloc[0] == 112.0  # max of week
    assert result["low"].iloc[0] == 90.0  # min of week
    assert result["close"].iloc[0] == 107.0  # last of week
    assert result["volume"].iloc[0] == 3_300  # sum of week


def test_get_ticker_history_returns_empty_when_no_data(mock_engine: MagicMock) -> None:
    empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "adjusted_close", "volume"])
    with patch("turtle.repository.analytics.pd.read_sql", return_value=empty_df):
        result = _make_repo(mock_engine).get_ticker_history("AAPL", date(2024, 1, 1), date(2024, 1, 31))

    assert result.empty


def test_get_ticker_history_raises_for_unsupported_time_frame_unit(mock_engine: MagicMock) -> None:
    unknown_unit = MagicMock(spec=TimeFrameUnit)  # simulates a future enum member
    with patch("turtle.repository.analytics.pd.read_sql", return_value=_sample_pd_df()):
        with pytest.raises(ValueError, match="Unsupported time_frame_unit"):
            _make_repo(mock_engine).get_ticker_history("AAPL", date(2024, 1, 1), date(2024, 1, 31), unknown_unit)  # type: ignore[arg-type]
