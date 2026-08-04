"""Tests for TickerQueryRepository sync ticker list reads."""

from unittest.mock import MagicMock

from turtlex.repository.query.ticker import TickerQueryRepository


def _make_engine_mock(rows: list[MagicMock]) -> MagicMock:
    mock_result = MagicMock()
    mock_result.fetchall.return_value = rows
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn
    return mock_engine


def test_ticker_query_get_symbol_list_returns_codes() -> None:
    rows = [MagicMock(code=c) for c in ["AAPL.US", "AMZN.US", "TSLA.US"]]
    engine = _make_engine_mock(rows)
    repo = TickerQueryRepository(engine)
    result = repo.get_symbol_list("USA")
    assert result == ["AAPL.US", "AMZN.US", "TSLA.US"]


def test_ticker_query_get_symbol_list_empty() -> None:
    engine = _make_engine_mock([])
    repo = TickerQueryRepository(engine)
    result = repo.get_symbol_list("USA")
    assert result == []


def test_ticker_query_get_symbol_list_min_code_filter() -> None:
    rows = [MagicMock(code=c) for c in ["AAPL.US", "AMZN.US", "GOOGL.US", "MSFT.US", "TSLA.US"]]
    engine = _make_engine_mock(rows)
    repo = TickerQueryRepository(engine)
    assert repo.get_symbol_list("USA", min_code="MSFT.US") == ["MSFT.US", "TSLA.US"]
    assert repo.get_symbol_list("USA", min_code="Z") == []
    assert repo.get_symbol_list("USA", min_code="") == ["AAPL.US", "AMZN.US", "GOOGL.US", "MSFT.US", "TSLA.US"]


def test_ticker_query_get_symbol_list_limit() -> None:
    rows = [MagicMock(code=c) for c in ["AAPL.US", "AMZN.US", "TSLA.US"]]
    engine = _make_engine_mock(rows)
    repo = TickerQueryRepository(engine)
    assert repo.get_symbol_list("USA", limit=2) == ["AAPL.US", "AMZN.US"]
    assert repo.get_symbol_list("USA", limit=None) == ["AAPL.US", "AMZN.US", "TSLA.US"]


def test_ticker_query_get_qullamaggie_qualified_symbols_returns_codes() -> None:
    rows = [MagicMock(code=c) for c in ["AAPL.US", "NVDA.US"]]
    engine = _make_engine_mock(rows)
    repo = TickerQueryRepository(engine)
    assert repo.get_qullamaggie_qualified_symbols() == ["AAPL.US", "NVDA.US"]


def test_ticker_query_get_qullamaggie_qualified_symbols_limit() -> None:
    rows = [MagicMock(code=c) for c in ["AAPL.US", "AMZN.US", "NVDA.US"]]
    engine = _make_engine_mock(rows)
    repo = TickerQueryRepository(engine)
    assert repo.get_qullamaggie_qualified_symbols(limit=2) == ["AAPL.US", "AMZN.US"]


def test_ticker_query_get_group_ticker_codes_returns_set() -> None:
    rows = [MagicMock(ticker_code=c) for c in ["DUOL.US", "PRGS.US", "GENI.US"]]
    engine = _make_engine_mock(rows)
    repo = TickerQueryRepository(engine)
    assert repo.get_group_ticker_codes("lightyear") == {"DUOL.US", "PRGS.US", "GENI.US"}


def test_ticker_query_get_group_ticker_codes_unknown_group_is_empty() -> None:
    engine = _make_engine_mock([])
    repo = TickerQueryRepository(engine)
    assert repo.get_group_ticker_codes("nope") == set()


def test_ticker_query_get_group_ticker_codes_does_not_join_ticker_table() -> None:
    engine = _make_engine_mock([])
    repo = TickerQueryRepository(engine)
    repo.get_group_ticker_codes("lightyear")

    sql = str(engine.connect.return_value.execute.call_args.args[0])
    assert "turtle.ticker_group" in sql
    assert "JOIN" not in sql.upper()
