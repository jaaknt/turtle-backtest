"""Tests for turtlex/repository/ingest/daily_bars.py DailyBarsRepository."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from turtlex.repository.ingest import DailyBarsRepository
from turtlex.schema import DailyBars


def _daily_bars(ticker: str = "AAPL.US", bar_date: date = date(2024, 1, 2)) -> DailyBars:
    return DailyBars(ticker=ticker, date=bar_date, open=100.0, high=105.0, low=99.0, close=103.0, adjusted_close=103.0, volume=1000000)


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
