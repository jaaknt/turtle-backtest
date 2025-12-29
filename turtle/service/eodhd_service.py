import logging
from collections.abc import AsyncGenerator

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from turtle.clients.eodhd import EodhdApiClient
from turtle.config.settings import Settings
from turtle.data.models import Exchange, Ticker
from turtle.data.tables import exchange_table, ticker_table

logger = logging.getLogger(__name__)


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
                    batch = tickers[i:i + batch_size]
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
        finally:
            await self.api_client.close()

    async def close(self) -> None:
        """Close the underlying resources."""
        await self.engine.dispose()
        await self.api_client.close()
