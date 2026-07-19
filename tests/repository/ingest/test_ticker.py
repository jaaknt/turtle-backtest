"""Tests for turtlex/repository/ingest/ticker.py TickerRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from turtlex.repository.ingest import TickerRepository
from turtlex.schema import Ticker


def _ticker(code: str = "AAPL") -> Ticker:
    return Ticker(Code=code, Name="Apple", Country="USA", Exchange="NASDAQ", Currency="USD", Type="Common Stock")


@pytest.mark.anyio
async def test_ticker_upsert_returns_total_count(session: AsyncMock) -> None:
    repo = TickerRepository(session)
    tickers = [_ticker("AAPL"), _ticker("MSFT"), _ticker("GOOG")]
    total = await repo.upsert(tickers, batch_size=2)
    assert total == 3
    assert session.execute.call_count == 2  # two batches: [0:2] and [2:3]
    session.commit.assert_called_once()


@pytest.mark.anyio
async def test_ticker_upsert_appends_us_suffix(session: AsyncMock) -> None:
    """Verifies the INSERT values use `code + '.US'` for the ticker code column."""
    captured: list = []

    async def capture_stmt(stmt):  # type: ignore[no-untyped-def]
        captured.append(stmt)

    session.execute.side_effect = capture_stmt

    repo = TickerRepository(session)
    await repo.upsert([_ticker("AAPL")])

    # The statement carries compiled values; inspect via the INSERT clause
    stmt = captured[0]
    # pg_insert statement stores values in .statement.parameters or directly
    # We verify by inspecting the compile-level parameters on the insert
    compiled = stmt.compile(compile_kwargs={"literal_binds": True})
    sql = str(compiled)
    assert "AAPL.US" in sql
    assert "AAPL" in sql


@pytest.mark.anyio
async def test_fetch_us_downloadable_tickers(session: AsyncMock) -> None:
    mock_rows = [MagicMock(code=f"TICK{i}.US") for i in range(5)]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    session.execute.return_value = mock_result

    repo = TickerRepository(session)
    result = await repo.fetch_us_downloadable_tickers()

    assert result == mock_rows
    session.execute.assert_called_once()


@pytest.mark.anyio
async def test_fetch_tickers_no_limit(session: AsyncMock) -> None:
    mock_rows = [MagicMock(exchange_code=f"TICK{i}") for i in range(5)]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    session.execute.return_value = mock_result

    repo = TickerRepository(session)
    result = await repo.fetch_tickers(country="USA", limit=None)

    assert result == mock_rows
    session.execute.assert_called_once()


@pytest.mark.anyio
async def test_fetch_tickers_with_limit(session: AsyncMock) -> None:
    mock_rows = [MagicMock(exchange_code=f"TICK{i}") for i in range(5)]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    session.execute.return_value = mock_result

    repo = TickerRepository(session)
    result = await repo.fetch_tickers(country="USA", limit=2)

    assert result == mock_rows[:2]
