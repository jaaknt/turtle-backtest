"""Tests for turtlex/repository/ingest/exchange.py ExchangeRepository."""

from unittest.mock import AsyncMock

import pytest

from turtlex.repository.ingest import ExchangeRepository
from turtlex.schema import Exchange


def _exchange(code: str = "NASDAQ") -> Exchange:
    return Exchange(Name="NASDAQ", Code=code, Country="USA", Currency="USD")


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
