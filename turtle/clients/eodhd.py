import logging
from typing import Any


import httpx
from httpx import AsyncClient, URL
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from turtle.config.model import AppConfig
from turtle.data.models import Exchange, PriceHistory, Ticker, TickerExtended

logger = logging.getLogger(__name__)


class EodhdApiClient:
    """EODHD API client for fetching financial data."""

    BASE_URL = "https://eodhd.com/api/"

    def __init__(self, config: AppConfig):
        self.api_key = config.eodhd["api_key"]
        if self.api_key == "**REPLACE_ME**":
            logger.error("EODHD API key is not configured. Please update config/settings.toml")
            raise ValueError("EODHD API key is not configured")
        self._client = AsyncClient(base_url=self.BASE_URL)

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def _get(self, path: str, params: dict | None = None) -> Any:
        """
        Helper method to make authenticated GET requests to the EODHD API with retry logic.
        """
        if params is None:
            params = {}
        params["api_token"] = self.api_key
        params["fmt"] = "json"

        url = URL(path, params=params)
        logger.debug(f"Fetching data from EODHD: {url}")

        response = await self._client.get(url)
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        return response.json()

    async def get_exchanges(self) -> list[Exchange]:
        """
        Fetches the list of all available exchanges.
        """
        response_data = await self._get("exchanges-list")
        if isinstance(response_data, list):
            return [Exchange(**data) for data in response_data]
        raise TypeError("Unexpected response format from EODHD API for exchanges")

    async def get_tickers_for_exchange(self, exchange_code: str) -> list[Ticker]:
        """
        Fetches the list of all available tickers for a given exchange.
        """
        response_data = await self._get(f"exchange-symbol-list/{exchange_code}")
        if isinstance(response_data, list):
            return [Ticker(**data) for data in response_data]
        raise TypeError("Unexpected response format from EODHD API for tickers")

    async def get_eod_historical_data(
        self, ticker: str, from_date: str, to_date: str
    ) -> list[PriceHistory]:
        """
        Fetches End-of-Day historical price data for a given ticker with exchange suffix (e.g., "AAPL.US").

        Args:
            ticker: Ticker symbol with exchange suffix (e.g., "AAPL.US")
            from_date: Start date for historical data
            to_date: End date for historical data
        """
        path = f"eod/{ticker}"
        params = {"from": from_date, "to": to_date, "period": "d", "order": "a"}
        response_data = await self._get(path, params=params)
        if isinstance(response_data, list):
            # EODHD API response contains `date`, which conflicts with Pydantic's `date` type
            # We explicitly pass ticker here to the PriceHistory model.
            return [PriceHistory(ticker=ticker, **data) for data in response_data]
        raise TypeError("Unexpected response format from EODHD API for historical data")


    async def get_us_quote_delayed(self, ticker: str) -> TickerExtended:
        """
        Fetches extended quote data for a US ticker from the delayed quotes API.

        Args:
            ticker: Ticker symbol with exchange suffix (e.g., "AAPL.US")

        Returns:
            TickerExtended object with extended ticker information
        """
        params = {"s": ticker}
        response_data = await self._get("us-quote-delayed", params=params)
        if isinstance(response_data, dict):
            # Debug: Log full API response to understand format
            logger.debug(f"=== EODHD API Response for {ticker} ===")
            logger.debug(f"Response keys: {list(response_data.keys())}")
            logger.debug(f"Full response data: {response_data}")

            # Extract nested data - the actual ticker data is inside data[ticker]
            if 'data' not in response_data:
                raise TypeError(f"Expected 'data' key in API response, got: {response_data.keys()}")

            # Check if data is empty or ticker is not in data
            if not response_data['data'] or ticker not in response_data['data']:
                logger.warning(f"No data available for {ticker} in API response")
                raise TypeError(f"No data found for {ticker} in API response")

            ticker_data = response_data['data'][ticker]
            logger.debug(f"Extracted ticker data keys: {list(ticker_data.keys())}")

            # Add symbol to ticker data (redundant but ensures consistency)
            ticker_data["symbol"] = ticker

            # Create TickerExtended object
            ticker_extended = TickerExtended(**ticker_data)

            # Debug: Log the parsed object to see what values were extracted
            logger.debug(f"Parsed TickerExtended object:")
            logger.debug(f"  symbol: {ticker_extended.symbol}")
            logger.debug(f"  type: {ticker_extended.type}")
            logger.debug(f"  name: {ticker_extended.name}")
            logger.debug(f"  sector: {ticker_extended.sector}")
            logger.debug(f"  industry: {ticker_extended.industry}")
            logger.debug(f"  average_volume: {ticker_extended.average_volume}")
            logger.debug(f"  fifty_day_average_price: {ticker_extended.fifty_day_average_price}")
            logger.debug(f"  dividend_yield: {ticker_extended.dividend_yield}")
            logger.debug(f"  market_cap: {ticker_extended.market_cap}")
            logger.debug(f"  pe: {ticker_extended.pe}")
            logger.debug(f"  forward_pe: {ticker_extended.forward_pe}")
            logger.debug("=" * 50)

            return ticker_extended
        raise TypeError("Unexpected response format from EODHD API for US quote delayed")

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        await self._client.aclose()
