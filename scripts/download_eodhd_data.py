import argparse
import asyncio
import logging
import re
import sys
from pathlib import Path

# Add project root to path to import turtle modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtle.config.settings import Settings
from turtle.services.eodhd_service import EodhdService

logger = logging.getLogger(__name__)


class _ApiTokenFilter(logging.Filter):
    """Redact api_token query parameter from httpx request log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = str(record.msg)
        if "api_token=" in record.msg:
            record.msg = re.sub(r"api_token=[^&\s\"]+", "api_token=***", record.msg)
        return True


async def main(
    data: str,
    ticker_limit: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> None:
    """
    Main function to download EODHD data.

    Args:
        data: Which dataset to download - exchange, us_ticker, company, or history.
        ticker_limit: Optional limit on number of tickers to download data for.
                     If None, downloads all tickers. Useful for testing.
        start_date: Optional start date for historical data (format: YYYY-MM-DD).
                   If None, uses default from service configuration.
        end_date: Optional end date for historical data (format: YYYY-MM-DD).
                 If None, uses default from service configuration.
    """
    # Force logging to stdout for this script
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="[%(levelname)s|%(module)s|%(funcName)s] %(message)s")
    # Obfuscate api_token in httpx request logs
    logging.getLogger("httpx").addFilter(_ApiTokenFilter())
    logger.info("Starting EODHD data download script.")
    logger.info(f"Dataset to download: {data}")
    if ticker_limit is not None:
        logger.info(f"Running in TEST MODE - limiting to {ticker_limit} tickers")
    if start_date or end_date:
        logger.info(f"Custom date range: {start_date or 'default'} to {end_date or 'default'}")

    settings = Settings.from_toml()
    eodhd_service = EodhdService(settings)
    try:
        # Download based on data parameter
        if data == "exchange":
            logger.info("Downloading exchange data...")
            await eodhd_service.download_exchanges()

        elif data == "us_ticker":
            logger.info("Downloading US ticker data...")
            await eodhd_service.download_us_tickers()

        elif data == "company":
            logger.info("Downloading company data...")
            await eodhd_service.download_company_data(ticker_limit=ticker_limit)

        elif data == "history":
            logger.info("Downloading historical price data...")
            await eodhd_service.download_historical_data(ticker_limit=ticker_limit, start_date=start_date, end_date=end_date)

        logger.info("EODHD data download completed successfully.")
    except Exception as e:
        logger.error(f"EODHD data download script failed: {e}", exc_info=True)
        # Re-raise the exception for the script to exit with an error code
        raise
    finally:
        await eodhd_service.close()
        logger.info("EODHD data download script finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download data from EODHD for US stocks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download exchange data
  python scripts/download_eodhd_data.py --data exchange

  # Download US ticker list
  python scripts/download_eodhd_data.py --data us_ticker

  # Download company data
  python scripts/download_eodhd_data.py --data company --ticker-limit 10

  # Download historical price data
  python scripts/download_eodhd_data.py --data history --start-date 2024-01-01 --end-date 2024-12-31

  # Test historical data with 10 tickers
  python scripts/download_eodhd_data.py --data history --ticker-limit 10

  # Test with limited tickers and custom date range
  python scripts/download_eodhd_data.py --data history --ticker-limit 10 --start-date 2024-06-01 --end-date 2024-06-30
        """,
    )
    parser.add_argument(
        "--data",
        type=str,
        choices=["exchange", "us_ticker", "company", "history"],
        required=True,
        help="Which dataset to download: exchange, us_ticker, company, or history.",
    )
    parser.add_argument("--ticker-limit", type=int, metavar="N", help="Limit data download to first N tickers (for testing)")
    parser.add_argument(
        "--start-date",
        type=str,
        metavar="YYYY-MM-DD",
        help="Start date for historical data (format: YYYY-MM-DD). If not specified, uses default from service.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        metavar="YYYY-MM-DD",
        help="End date for historical data (format: YYYY-MM-DD). If not specified, uses default from service.",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            main(
                data=args.data,
                ticker_limit=args.ticker_limit,
                start_date=args.start_date,
                end_date=args.end_date,
            )
        )
    except Exception:
        # The logger already captured the exception, just exit with error code
        sys.exit(1)
