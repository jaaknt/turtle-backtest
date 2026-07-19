"""Tests for EodhdApiClient response parsing."""

from turtle.client.eodhd import EodhdApiClient
from turtle.config.model import AppConfig
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _make_client() -> EodhdApiClient:
    return EodhdApiClient(AppConfig(name="test", debug=False, eodhd={"api_key": "test-key"}))


def _ticker_record(code: str, name: str | None) -> dict:
    return {"Code": code, "Name": name, "Country": "USA", "Exchange": "NASDAQ", "Currency": "USD", "Type": "Common Stock"}


@pytest.mark.anyio
async def test_get_tickers_skips_invalid_records() -> None:
    client = _make_client()
    client._get = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            _ticker_record("AAPL", "Apple Inc"),
            _ticker_record("BAD", None),  # null Name — must be skipped, not raise
            _ticker_record("MSFT", "Microsoft Corp"),
        ]
    )
    tickers = await client.get_tickers_for_exchange("US")
    assert [t.code for t in tickers] == ["AAPL", "MSFT"]


@pytest.mark.anyio
async def test_get_tickers_non_list_response_raises() -> None:
    client = _make_client()
    client._get = AsyncMock(return_value={"error": "unexpected"})  # type: ignore[method-assign]
    with pytest.raises(TypeError):
        await client.get_tickers_for_exchange("US")
