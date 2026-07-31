from datetime import date
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from turtlex.common.enums import TimeFrameUnit
from turtlex.repository.query.daily_bars import LOAD_BATCH_ROWS, DailyBarsQueryRepository


@pytest.fixture
def mock_engine() -> MagicMock:
    return MagicMock()


def _make_repo(mock_engine: MagicMock) -> DailyBarsQueryRepository:
    return DailyBarsQueryRepository(engine=mock_engine)


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


# --- get_bars_pl ---


def test_get_bars_pl_returns_polars_dataframe(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=_sample_pl_df()):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pl.DataFrame)
    assert result.columns == ["date", "open", "high", "low", "close", "adjusted_close", "volume"]
    assert len(result) == 2
    assert result["close"].to_list() == [102.0, 108.0]


def test_get_bars_pl_returns_empty_dataframe_when_no_data(mock_engine: MagicMock) -> None:
    empty_df = pl.DataFrame({"date": [], "open": [], "high": [], "low": [], "close": [], "adjusted_close": [], "volume": []})

    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=empty_df):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 2), date(2024, 1, 3))

    assert isinstance(result, pl.DataFrame)
    assert result.is_empty()


def test_get_bars_pl_passes_correct_date_range(mock_engine: MagicMock) -> None:
    """Verify the SQL statement filters on the expected date boundaries."""
    captured: list[object] = []

    def capture(query: object, connection: object, **kwargs: object) -> pl.DataFrame:
        captured.append(query)
        return pl.DataFrame()

    with patch("turtlex.repository.query.daily_bars.pl.read_database", side_effect=capture):
        _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 12, 31))

    assert len(captured) == 1
    compiled = str(captured[0].compile(compile_kwargs={"literal_binds": True}))
    assert "2024-01-01" in compiled
    assert "2024-12-31" in compiled
    assert "AAPL" in compiled


def test_get_bars_pl_uses_engine_connection(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=pl.DataFrame()):
        _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 1, 31))

    mock_engine.connect.assert_called_once()


def test_get_bars_pl_day_returns_daily_data(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=_sample_pl_df()):
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
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=two_weeks):
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
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=empty):
        result = _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 1, 31), TimeFrameUnit.WEEK)

    assert result.is_empty()


def test_get_bars_pl_raises_for_unsupported_time_frame_unit(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=_sample_pl_df()):
        with pytest.raises(ValueError, match="Unsupported time_frame_unit"):
            _make_repo(mock_engine).get_bars_pl("AAPL", date(2024, 1, 1), date(2024, 1, 31), "month")  # type: ignore[arg-type]


# --- get_qualified_universe_bars_pl ---


def _sample_universe_pl_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "symbol": ["AAPL.US", "AAPL.US", "MSFT.US"],
            "date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 2)],
            "open": [100.0, 102.0, 300.0],
            "high": [105.0, 110.0, 310.0],
            "low": [95.0, 100.0, 295.0],
            "close": [102.0, 108.0, 305.0],
            "adjusted_close": [51.0, 54.0, 305.0],
            "volume": [1_000_000, 1_200_000, 900_000],
        }
    )


def test_get_qualified_universe_bars_pl_returns_multi_symbol_frame(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=iter([_sample_universe_pl_df()])):
        result = _make_repo(mock_engine).get_qualified_universe_bars_pl(date(2024, 1, 2), date(2024, 1, 3))

    assert result.shape == (3, 8)
    assert result["symbol"].unique().sort().to_list() == ["AAPL.US", "MSFT.US"]
    # Returned as stored: adjusted_close is not folded into close by the repository.
    assert result["close"][0] == 102.0
    assert result["adjusted_close"][0] == 51.0


def test_get_qualified_universe_bars_pl_applies_default_filters(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=iter([_sample_universe_pl_df()])) as read_database:
        _make_repo(mock_engine).get_qualified_universe_bars_pl(date(2024, 1, 2), date(2024, 1, 3))

    sql = str(read_database.call_args.kwargs["query"])
    assert "market_cap" in sql
    assert "sector" in sql
    assert "country" in sql
    assert "type" in sql


def test_get_qualified_universe_bars_pl_honours_overrides(mock_engine: MagicMock) -> None:
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=iter([_sample_universe_pl_df()])) as read_database:
        _make_repo(mock_engine).get_qualified_universe_bars_pl(
            date(2024, 1, 2), date(2024, 1, 3), min_market_cap=5_000_000_000, excluded_sectors=["Energy"]
        )

    params = read_database.call_args.kwargs["query"].compile().params
    assert 5_000_000_000 in params.values()
    assert "Energy" in [v for value in params.values() for v in (value if isinstance(value, tuple | list) else [value])]


def test_get_qualified_universe_bars_pl_returns_empty_frame(mock_engine: MagicMock) -> None:
    """No batches at all — an empty result set must not blow up in pl.concat."""
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=iter([])):
        result = _make_repo(mock_engine).get_qualified_universe_bars_pl(date(2024, 1, 2), date(2024, 1, 3))

    assert result.is_empty()


def test_get_qualified_universe_bars_pl_concatenates_batches(mock_engine: MagicMock) -> None:
    """The server-side cursor yields several batches; all rows must survive the concat."""
    df = _sample_universe_pl_df()
    batches = iter([df[:2], df[2:]])

    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=batches) as read_database:
        result = _make_repo(mock_engine).get_qualified_universe_bars_pl(date(2024, 1, 2), date(2024, 1, 3))

    assert result.shape == (3, 8)
    assert result["symbol"].to_list() == ["AAPL.US", "AAPL.US", "MSFT.US"]
    assert read_database.call_args.kwargs["iter_batches"] is True


def test_get_qualified_universe_bars_pl_streams_results(mock_engine: MagicMock) -> None:
    """A buffered read materialises ~7M Python row tuples and has OOM-killed the host."""
    with patch("turtlex.repository.query.daily_bars.pl.read_database", return_value=iter([_sample_universe_pl_df()])):
        _make_repo(mock_engine).get_qualified_universe_bars_pl(date(2024, 1, 2), date(2024, 1, 3))

    mock_engine.connect.return_value.execution_options.assert_called_once_with(stream_results=True, max_row_buffer=LOAD_BATCH_ROWS)
