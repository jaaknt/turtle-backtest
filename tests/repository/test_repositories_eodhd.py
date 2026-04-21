"""Tests for turtle/repository/eodhd.py async repository classes."""

from datetime import date
from turtle.repository.eodhd import (
    CompanyRepository,
    DailyBarsRepository,
    ExchangeRepository,
    TickerQueryRepository,
    TickerRepository,
)
from turtle.schema import Company, DailyBars, Exchange, Ticker
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def session() -> AsyncMock:
    s = AsyncMock()
    s.execute = AsyncMock()
    s.commit = AsyncMock()
    return s


def _exchange(code: str = "NASDAQ") -> Exchange:
    return Exchange(Name="NASDAQ", Code=code, Country="USA", Currency="USD")


def _ticker(code: str = "AAPL") -> Ticker:
    return Ticker(Code=code, Name="Apple", Country="USA", Exchange="NASDAQ", Currency="USD", Type="Common Stock")


def _daily_bars(ticker: str = "AAPL.US", bar_date: date = date(2024, 1, 2)) -> DailyBars:
    return DailyBars(ticker=ticker, date=bar_date, open=100.0, high=105.0, low=99.0, close=103.0, adjusted_close=103.0, volume=1000000)


# ---------------------------------------------------------------------------
# ExchangeRepository
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_exchange_upsert_empty_list(session: AsyncMock) -> None:
    repo = ExchangeRepository(session)
    await repo.upsert([])
    session.execute.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.anyio
async def test_exchange_upsert_calls_execute_and_commit(session: AsyncMock) -> None:
    repo = ExchangeRepository(session)
    await repo.upsert([_exchange("NASDAQ"), _exchange("NYSE")])
    session.execute.assert_called_once()
    session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# TickerRepository
# ---------------------------------------------------------------------------


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
async def test_fetch_group_tickers_no_limit(session: AsyncMock) -> None:
    mock_rows = [MagicMock(code=f"TICK{i}.US") for i in range(5)]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    session.execute.return_value = mock_result

    repo = TickerRepository(session)
    result = await repo.fetch_group_tickers(country="USA", group_code="active", limit=None)

    assert result == mock_rows
    session.execute.assert_called_once()


@pytest.mark.anyio
async def test_fetch_group_tickers_with_limit(session: AsyncMock) -> None:
    mock_rows = [MagicMock(code=f"TICK{i}.US") for i in range(5)]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    session.execute.return_value = mock_result

    repo = TickerRepository(session)
    result = await repo.fetch_group_tickers(country="USA", group_code="active", limit=3)

    assert result == mock_rows[:3]


@pytest.mark.anyio
async def test_fetch_group_tickers_empty_group_code_raises(session: AsyncMock) -> None:
    repo = TickerRepository(session)
    with pytest.raises(ValueError, match="group_code must be a non-empty string"):
        await repo.fetch_group_tickers(country="USA", group_code="")


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


# ---------------------------------------------------------------------------
# DailyBarsRepository
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_daily_bars_upsert_empty_returns_zero(session: AsyncMock) -> None:
    repo = DailyBarsRepository(session)
    count = await repo.upsert_batch([])
    assert count == 0
    session.execute.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.anyio
async def test_daily_bars_upsert_valid_records(session: AsyncMock) -> None:
    repo = DailyBarsRepository(session)
    records = [_daily_bars(bar_date=date(2024, 1, 2)), _daily_bars(bar_date=date(2024, 1, 3))]
    count = await repo.upsert_batch(records)
    assert count == 2
    session.execute.assert_called_once()
    session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# CompanyRepository
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_company_upsert_empty_returns_zero(session: AsyncMock) -> None:
    repo = CompanyRepository(session)
    count = await repo.upsert_batch([])
    assert count == 0
    session.execute.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.anyio
async def test_company_upsert_calls_execute_and_commit(session: AsyncMock) -> None:
    repo = CompanyRepository(session)
    companies = [
        Company(
            symbol="AAPL",
            type="Common Stock",
            name="Apple",
            sector="Tech",
            industry="Software",
            averageVolume=50000000,
            fiftyDayAveragePrice=180.0,
            dividendYield=0.5,
            marketCap=3000000000000,
            pe=28.0,
            forwardPE=25.0,
        ),
        Company(
            symbol="MSFT",
            type="Common Stock",
            name="Microsoft",
            sector="Tech",
            industry="Software",
            averageVolume=30000000,
            fiftyDayAveragePrice=400.0,
            dividendYield=0.8,
            marketCap=3100000000000,
            pe=35.0,
            forwardPE=30.0,
        ),
    ]
    count = await repo.upsert_batch(companies)
    assert count == 2
    session.execute.assert_called_once()
    session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# TickerQueryRepository
# ---------------------------------------------------------------------------


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
