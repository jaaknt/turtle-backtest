"""Tests for turtlex/repository/ingest/company.py CompanyRepository."""

from unittest.mock import AsyncMock

import pytest

from turtlex.repository.ingest import CompanyRepository
from turtlex.schema import Company


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
