import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import and_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from turtle.clients.eodhd import EodhdApiClient
from turtle.config.settings import Settings
from turtle.data.models import Exchange, PriceHistory, Ticker
from turtle.data.tables import exchange_table, price_history_table, ticker_table

logger = logging.getLogger(__name__)

# Constants for historical data download
US_EXCHANGES = ["NASDAQ", "NYSE", "NYSE ARCA", "NYSE MKT"]
COMMON_STOCK_TYPE = "Common Stock"
DATE_FROM = "2000-01-01"
DATE_TO = "2025-12-30"
API_BATCH_SIZE = 50  # Number of concurrent API requests per batch
DB_BATCH_SIZE = 1000  # Number of records to insert per database batch
BATCH_DELAY_SECONDS = 1.0  # Delay between API batches to respect rate limits


class EodhdService:
    """
    Service for downloading and storing EODHD data into the PostgreSQL database.
    """

    def __init__(self, config: Settings):
        self.config = config
        self.api_client = EodhdApiClient(config.app)
        self.engine = create_async_engine(config.database.sqlalchemy_url)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    async def _get_db_session(self) -> AsyncGenerator[AsyncSession]:
        """Helper to get an async database session."""
        async with self.AsyncSessionLocal() as session:
            yield session

    async def download_exchanges(self) -> None:
        """
        Downloads exchange data from EODHD and stores it in the database.
        """
        logger.info("Starting EODHD exchange data download...")
        try:
            exchanges: list[Exchange] = await self.api_client.get_exchanges()
            logger.info(f"Fetched {len(exchanges)} exchanges from EODHD.")

            async with self.AsyncSessionLocal() as session:
                values = [
                    {
                        "code": ex.code,
                        "name": ex.name,
                        "country": ex.country,
                        "currency": ex.currency,
                        "country_iso3": ex.country_iso3,
                    }
                    for ex in exchanges
                ]

                stmt = pg_insert(exchange_table).values(values)

                on_conflict_stmt = stmt.on_conflict_do_update(
                    index_elements=[exchange_table.c.code],
                    set_={
                        "name": stmt.excluded.name,
                        "country": stmt.excluded.country,
                        "currency": stmt.excluded.currency,
                        "country_iso3": stmt.excluded.country_iso3,
                    },
                )
                await session.execute(on_conflict_stmt)
                await session.commit()
                logger.info(f"Successfully stored/updated {len(exchanges)} exchanges in the database.")
        except Exception as e:
            logger.error(f"Error downloading or storing exchanges: {e}", exc_info=True)
            raise

    async def download_us_tickers(self, batch_size: int = 1000) -> None:
        """
        Downloads ticker data for the 'US' exchange from EODHD and stores it in the database.

        Args:
            batch_size: Number of rows to insert per batch (default: 1000)
        """
        logger.info("Starting EODHD US ticker data download...")
        try:
            tickers: list[Ticker] = await self.api_client.get_tickers_for_exchange("US")
            logger.info(f"Fetched {len(tickers)} tickers from EODHD for US exchange.")

            async with self.AsyncSessionLocal() as session:
                total_processed = 0

                # Process tickers in batches
                for i in range(0, len(tickers), batch_size):
                    batch = tickers[i : i + batch_size]
                    values = [
                        {
                            "code": t.code,
                            "name": t.name,
                            "country": t.country,
                            "exchange": t.exchange,
                            "currency": t.currency,
                            "type": t.type,
                            "isin": t.isin,
                        }
                        for t in batch
                    ]

                    stmt = pg_insert(ticker_table).values(values)
                    on_conflict_stmt = stmt.on_conflict_do_update(
                        index_elements=[ticker_table.c.code, ticker_table.c.exchange],
                        set_={
                            "name": stmt.excluded.name,
                            "country": stmt.excluded.country,
                            "currency": stmt.excluded.currency,
                            "type": stmt.excluded.type,
                            "isin": stmt.excluded.isin,
                        },
                    )
                    await session.execute(on_conflict_stmt)
                    total_processed += len(batch)
                    logger.info(f"Processed batch {i // batch_size + 1}: {total_processed}/{len(tickers)} tickers")

                await session.commit()
                logger.info(f"Successfully stored/updated {total_processed} US tickers in the database.")
        except Exception as e:
            logger.error(f"Error downloading or storing US tickers: {e}", exc_info=True)
            raise

    async def _insert_price_history_batch(self, session: AsyncSession, price_records: list[PriceHistory]) -> int:
        """
        Helper method to insert a batch of price history records into the database.

        Args:
            session: Database session
            price_records: List of PriceHistory records to insert

        Returns:
            Number of records inserted/updated
        """
        if not price_records:
            return 0

        values_to_insert = []
        for record in price_records:
            # Convert date string to datetime object
            try:
                record_date = datetime.fromisoformat(record.date)
            except ValueError as e:
                logger.warning(f"Invalid date format for {record.ticker}: {record.date}, skipping. Error: {e}")
                continue

            values_to_insert.append(
                {
                    "symbol": record.ticker,
                    "time": record_date,
                    "open": record.open,
                    "high": record.high,
                    "low": record.low,
                    "close": record.close,
                    "adjusted_close": record.adjusted_close,
                    "volume": record.volume,
                    "source": text("'eodhd'::turtle.data_source_type"),  # Cast to enum type
                }
            )

        if not values_to_insert:
            return 0

        stmt = pg_insert(price_history_table).values(values_to_insert)

        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[price_history_table.c.symbol, price_history_table.c.time],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "adjusted_close": stmt.excluded.adjusted_close,
                "volume": stmt.excluded.volume,
                "source": text("'eodhd'::turtle.data_source_type"),  # Cast to enum type
            },
        )
        await session.execute(on_conflict_stmt)
        await session.commit()

        return len(values_to_insert)

    async def download_historical_data(
        self, ticker_limit: int | None = None, start_date: str | None = None, end_date: str | None = None
    ) -> None:
        """
        Downloads historical EOD data for filtered US stocks and stores it in the database.
        Uses batch processing for both API calls and database inserts to manage memory efficiently.

        Args:
            ticker_limit: Optional limit on number of tickers to process. Useful for testing.
                         If None, processes all tickers. Default: None.
            start_date: Optional start date for historical data (format: YYYY-MM-DD).
                       If None, uses DATE_FROM constant. Default: None.
            end_date: Optional end date for historical data (format: YYYY-MM-DD).
                     If None, uses DATE_TO constant. Default: None.
        """
        # Use provided dates or fall back to defaults
        from_date = start_date or DATE_FROM
        to_date = end_date or DATE_TO

        logger.info("Starting EODHD historical data download for US stocks...")
        logger.info(f"Date range: {from_date} to {to_date}")
        total_records_inserted = 0
        total_stocks_processed = 0
        total_stocks_failed = 0

        try:
            async with self.AsyncSessionLocal() as session:
                # Fetch tickers to process - Filter: USA, specific exchanges, Common Stock type
                stmt = select(ticker_table.c.code, ticker_table.c.exchange).where(
                    and_(
                        ticker_table.c.country == "USA", ticker_table.c.exchange.in_(US_EXCHANGES), ticker_table.c.type == COMMON_STOCK_TYPE
                    )
                )
                result = await session.execute(stmt)
                us_stocks = result.fetchall()  # List of (code, exchange) tuples

                # Apply limit if specified (for testing)
                if ticker_limit is not None:
                    us_stocks = us_stocks[:ticker_limit]
                    logger.info(f"Limiting to first {ticker_limit} tickers for testing.")

                logger.info(f"Found {len(us_stocks)} US stocks matching criteria for historical data download.")

                # Process in batches to manage API rate limits and memory
                num_batches = (len(us_stocks) + API_BATCH_SIZE - 1) // API_BATCH_SIZE

                for i in range(0, len(us_stocks), API_BATCH_SIZE):
                    batch = us_stocks[i : i + API_BATCH_SIZE]
                    batch_num = i // API_BATCH_SIZE + 1

                    # Create concurrent API requests for this batch
                    # Note: EODHD API always uses "US" exchange code for all US stocks
                    tasks = []
                    for stock_code, _stock_exchange in batch:
                        tasks.append(
                            self.api_client.get_eod_historical_data(
                                ticker=stock_code,
                                exchange="US",  # EODHD API uses "US" for all US exchanges
                                from_date=from_date,
                                to_date=to_date,
                            )
                        )

                    # Execute API calls concurrently
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Process results and collect price history records
                    batch_price_records: list[PriceHistory] = []
                    for idx in range(len(batch_results)):
                        result = batch_results[idx]  # type: ignore[assignment]
                        stock_code, stock_exchange = batch[idx]
                        if isinstance(result, Exception):
                            logger.error(
                                f"Error fetching historical data for {stock_code}.US (exchange: {stock_exchange}): "
                                f"{type(result).__name__}: {result}"
                            )
                            total_stocks_failed += 1
                        elif isinstance(result, list):
                            batch_price_records.extend(result)
                            total_stocks_processed += 1

                    # Insert collected records into database in smaller batches
                    if batch_price_records:
                        for j in range(0, len(batch_price_records), DB_BATCH_SIZE):
                            db_batch = batch_price_records[j : j + DB_BATCH_SIZE]
                            records_inserted = await self._insert_price_history_batch(session, db_batch)
                            total_records_inserted += records_inserted

                    logger.info(
                        f"Batch {batch_num}/{num_batches}: Processed {len(batch)} stocks, "
                        f"collected {len(batch_price_records)} records. "
                        f"Total: {total_stocks_processed} stocks, {total_records_inserted} records inserted."
                    )

                    # Rate limiting: Add delay between API batches (except for the last batch)
                    if i + API_BATCH_SIZE < len(us_stocks):
                        await asyncio.sleep(BATCH_DELAY_SECONDS)

                logger.info(
                    f"Historical data download completed. "
                    f"Successfully processed: {total_stocks_processed} stocks, "
                    f"Failed: {total_stocks_failed} stocks, "
                    f"Total records inserted/updated: {total_records_inserted}"
                )

        except Exception as e:
            logger.error(f"Error downloading or storing historical data: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the underlying resources."""
        await self.engine.dispose()
        await self.api_client.close()
