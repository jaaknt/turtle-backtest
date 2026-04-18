import asyncio
import logging
from datetime import datetime
from turtle.client.eodhd import EodhdApiClient
from turtle.config.settings import Settings
from turtle.repository.eodhd import CompanyRepository, DailyBarsRepository, ExchangeRepository, TickerRepository
from turtle.schema import Company, DailyBars

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)

DATE_FROM = "2000-01-01"
DATE_TO = datetime.now().strftime("%Y-%m-%d")
API_BATCH_SIZE = 10
DB_BATCH_SIZE = 1000
BATCH_DELAY_SECONDS = 2.0


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

    async def download_exchanges(self) -> None:
        """Downloads exchange data from EODHD and stores it in the database."""
        logger.info("Starting EODHD exchange data download...")
        try:
            exchanges = await self.api_client.get_exchanges()
            logger.info(f"Fetched {len(exchanges)} exchanges from EODHD.")
            async with self.AsyncSessionLocal() as session:
                repo = ExchangeRepository(session)
                await repo.upsert(exchanges)
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
            tickers = await self.api_client.get_tickers_for_exchange("US")
            logger.info(f"Fetched {len(tickers)} tickers from EODHD for US exchange.")
            async with self.AsyncSessionLocal() as session:
                repo = TickerRepository(session)
                total = await repo.upsert(tickers, batch_size=batch_size)
            logger.info(f"Successfully stored/updated {total} US tickers in the database.")
        except Exception as e:
            logger.error(f"Error downloading or storing US tickers: {e}", exc_info=True)
            raise

    async def download_historical_data(
        self, ticker_limit: int | None = None, start_date: str | None = None, end_date: str | None = None
    ) -> None:
        """
        Downloads historical EOD data for filtered US stocks and stores it in the database.

        Args:
            ticker_limit: Optional limit on number of tickers to process.
            start_date: Optional start date (YYYY-MM-DD). Defaults to DATE_FROM.
            end_date: Optional end date (YYYY-MM-DD). Defaults to today.
        """
        from_date = start_date or DATE_FROM
        to_date = end_date or DATE_TO

        logger.info("Starting EODHD historical data download for US stocks...")
        logger.info(f"Date range: {from_date} to {to_date}")
        total_records_inserted = 0
        total_stocks_processed = 0
        total_stocks_failed = 0

        try:
            async with self.AsyncSessionLocal() as session:
                ticker_repo = TickerRepository(session)
                us_stocks = await ticker_repo.fetch_group_tickers(country="USA", group_code="active", limit=ticker_limit)
                if ticker_limit is not None:
                    logger.info(f"Limiting to first {ticker_limit} tickers for testing.")

                logger.info(f"Found {len(us_stocks)} US stocks matching criteria for historical data download.")
                num_batches = (len(us_stocks) + API_BATCH_SIZE - 1) // API_BATCH_SIZE
                bars_repo = DailyBarsRepository(session)

                for i in range(0, len(us_stocks), API_BATCH_SIZE):
                    batch = us_stocks[i : i + API_BATCH_SIZE]
                    batch_num = i // API_BATCH_SIZE + 1

                    tasks = [
                        self.api_client.get_eod_historical_data(
                            ticker=f"{row.code}",
                            from_date=from_date,
                            to_date=to_date,
                        )
                        for row in batch
                    ]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    batch_price_records: list[DailyBars] = []
                    for idx, result in enumerate(batch_results):
                        eodhd_ticker = f"{batch[idx].code}"
                        if isinstance(result, Exception):
                            logger.error(f"Error fetching historical data for {eodhd_ticker}: {type(result).__name__}: {result}")
                            total_stocks_failed += 1
                        elif isinstance(result, list):
                            batch_price_records.extend(result)
                            total_stocks_processed += 1

                    if batch_price_records:
                        for j in range(0, len(batch_price_records), DB_BATCH_SIZE):
                            db_batch = batch_price_records[j : j + DB_BATCH_SIZE]
                            total_records_inserted += await bars_repo.upsert_batch(db_batch)

                    logger.info(
                        f"Batch {batch_num}/{num_batches}: Processed {len(batch)} stocks, "
                        f"collected {len(batch_price_records)} records. "
                        f"Total: {total_stocks_processed} stocks, {total_records_inserted} records inserted."
                    )

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

    async def download_company_data(self, ticker_limit: int | None = None) -> None:
        """
        Downloads company data for US stocks and stores it in the database.

        Args:
            ticker_limit: Optional limit on number of tickers to process.
        """
        logger.info("Starting EODHD company data download for US stocks...")
        total_records_inserted = 0
        total_tickers_processed = 0
        total_tickers_failed = 0

        try:
            async with self.AsyncSessionLocal() as session:
                ticker_repo = TickerRepository(session)
                us_stocks = await ticker_repo.fetch_tickers(country="USA", limit=ticker_limit)
                if ticker_limit is not None:
                    logger.info(f"Limiting to first {ticker_limit} tickers for testing.")

                logger.info(f"Found {len(us_stocks)} US stocks matching criteria for company data download.")
                num_batches = (len(us_stocks) + API_BATCH_SIZE - 1) // API_BATCH_SIZE
                company_repo = CompanyRepository(session)

                for i in range(0, len(us_stocks), API_BATCH_SIZE):
                    batch = us_stocks[i : i + API_BATCH_SIZE]
                    batch_num = i // API_BATCH_SIZE + 1

                    tasks = [self.api_client.get_us_quote_delayed(ticker=f"{row.code}") for row in batch]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    companies_to_insert: list[Company] = []
                    for idx, result in enumerate(batch_results):
                        eodhd_ticker = f"{batch[idx].code}"
                        if isinstance(result, Exception):
                            logger.error(f"Error fetching company data for {eodhd_ticker}: {type(result).__name__}: {result}")
                            total_tickers_failed += 1
                        elif isinstance(result, Company):
                            has_data = any(
                                [
                                    result.type,
                                    result.name,
                                    result.sector,
                                    result.industry,
                                    result.average_volume,
                                    result.fifty_day_average_price,
                                    result.market_cap,
                                ]
                            )
                            if not has_data:
                                logger.warning(f"Skipping {eodhd_ticker} - API returned empty data (all fields are None)")
                                total_tickers_failed += 1
                                continue

                            companies_to_insert.append(result)
                            total_tickers_processed += 1

                    inserted = await company_repo.upsert_batch(companies_to_insert)
                    total_records_inserted += inserted

                    logger.info(
                        f"Batch {batch_num}/{num_batches}: Processed {len(batch)} tickers, "
                        f"inserted {inserted} records. "
                        f"Total: {total_tickers_processed} tickers, {total_records_inserted} records inserted."
                    )

                    if i + API_BATCH_SIZE < len(us_stocks):
                        await asyncio.sleep(BATCH_DELAY_SECONDS)

            logger.info(
                f"Company data download completed. "
                f"Successfully processed: {total_tickers_processed} tickers, "
                f"Failed: {total_tickers_failed} tickers, "
                f"Total records inserted/updated: {total_records_inserted}"
            )
        except Exception as e:
            logger.error(f"Error downloading or storing company data: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the underlying resources."""
        await self.engine.dispose()
        await self.api_client.close()
