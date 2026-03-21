from datetime import date
from turtle.repositories.analytics import OhlcvAnalyticsRepository
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture
def mock_engine() -> MagicMock:
    return MagicMock()


def _make_repo(mock_engine: MagicMock) -> OhlcvAnalyticsRepository:
    return OhlcvAnalyticsRepository(engine=mock_engine)


def test_get_bars_returns_dataframe(mock_engine: MagicMock) -> None:
    expected_df = pd.DataFrame(
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

    with patch("turtle.repositories.analytics.pd.read_sql", return_value=expected_df):
        repo = _make_repo(mock_engine)
        result = repo.get_bars("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["open", "high", "low", "close", "adjusted_close", "volume"]
    assert len(result) == 2
    assert result["close"].tolist() == [102.0, 108.0]


def test_get_bars_returns_empty_dataframe_when_no_data(mock_engine: MagicMock) -> None:
    empty_df = pd.DataFrame(
        columns=["open", "high", "low", "close", "adjusted_close", "volume"]
    )

    with patch("turtle.repositories.analytics.pd.read_sql", return_value=empty_df):
        repo = _make_repo(mock_engine)
        result = repo.get_bars("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_get_bars_passes_correct_date_range(mock_engine: MagicMock) -> None:
    """Verify the SQL statement filters on the expected date boundaries."""
    captured: list[object] = []

    def capture_read_sql(stmt: object, conn: object, **kwargs: object) -> pd.DataFrame:
        captured.append(stmt)
        return pd.DataFrame(columns=["open", "high", "low", "close", "adjusted_close", "volume"])

    with patch("turtle.repositories.analytics.pd.read_sql", side_effect=capture_read_sql):
        repo = _make_repo(mock_engine)
        repo.get_bars("AAPL", date(2024, 1, 1), date(2024, 12, 31))

    assert len(captured) == 1
    compiled = str(captured[0].compile(compile_kwargs={"literal_binds": True}))
    assert "2024-01-01" in compiled
    assert "2024-12-31" in compiled
    assert "AAPL" in compiled


def test_get_bars_uses_engine_connection(mock_engine: MagicMock) -> None:
    with patch("turtle.repositories.analytics.pd.read_sql", return_value=pd.DataFrame()):
        repo = _make_repo(mock_engine)
        repo.get_bars("AAPL", date(2024, 1, 1), date(2024, 1, 31))

    mock_engine.connect.assert_called_once()
