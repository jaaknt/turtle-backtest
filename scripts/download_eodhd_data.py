import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path to import turtle modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtle.config.settings import Settings
from turtle.service.eodhd_service import EodhdService

logger = logging.getLogger(__name__)


async def main(ticker_limit: int | None = None, start_date: str | None = None, end_date: str | None = None) -> None:
    """
    Main function to download EODHD data.

    Args:
        ticker_limit: Optional limit on number of tickers to download historical data for.
                     If None, downloads all tickers. Useful for testing.
        start_date: Optional start date for historical data (format: YYYY-MM-DD).
                   If None, uses default from service configuration.
        end_date: Optional end date for historical data (format: YYYY-MM-DD).
                 If None, uses default from service configuration.
    """
    # Force logging to stdout for this script
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="[%(levelname)s|%(module)s|%(funcName)s] %(message)s")
    logger.info("Starting EODHD data download script.")
    if ticker_limit is not None:
        logger.info(f"Running in TEST MODE - limiting to {ticker_limit} tickers")
    if start_date or end_date:
        logger.info(f"Custom date range: {start_date or 'default'} to {end_date or 'default'}")

    settings = Settings.from_toml()
    eodhd_service = EodhdService(settings)
    try:
        await eodhd_service.download_exchanges()
        await eodhd_service.download_us_tickers()
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
        description="Download historical data from EODHD for US stocks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all tickers with default date range (2000-01-01 to 2025-12-30)
  python scripts/download_eodhd_data.py

  # Test with 10 tickers
  python scripts/download_eodhd_data.py --ticker-limit 10

  # Download with custom date range
  python scripts/download_eodhd_data.py --start-date 2024-01-01 --end-date 2024-12-31

  # Test with limited tickers and custom date range
  python scripts/download_eodhd_data.py --ticker-limit 10 --start-date 2024-06-01 --end-date 2024-06-30
        """,
    )
    parser.add_argument("--ticker-limit", type=int, metavar="N", help="Limit historical data download to first N tickers (for testing)")
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
        asyncio.run(main(ticker_limit=args.ticker_limit, start_date=args.start_date, end_date=args.end_date))
    except Exception:
        # The logger already captured the exception, just exit with error code
        sys.exit(1)
