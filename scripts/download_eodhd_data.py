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


async def main(stocks_limit: int | None = None) -> None:
    """
    Main function to download EODHD data.

    Args:
        stocks_limit: Optional limit on number of stocks to download historical data for.
                     If None, downloads all stocks. Useful for testing.
    """
    # Force logging to stdout for this script
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="[%(levelname)s|%(module)s|%(funcName)s] %(message)s")
    logger.info("Starting EODHD data download script.")
    if stocks_limit is not None:
        logger.info(f"Running in TEST MODE - limiting to {stocks_limit} stocks")

    settings = Settings.from_toml()
    eodhd_service = EodhdService(settings)
    try:
        await eodhd_service.download_exchanges()
        await eodhd_service.download_us_tickers()
        await eodhd_service.download_historical_data(stocks_limit=stocks_limit)
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
  # Download all stocks (production mode)
  python scripts/download_eodhd_data.py

  # Test with 10 stocks
  python scripts/download_eodhd_data.py --stocks-limit 10

  # Test with 50 stocks
  python scripts/download_eodhd_data.py --stocks-limit 50
        """,
    )
    parser.add_argument("--stocks-limit", type=int, metavar="N", help="Limit historical data download to first N stocks (for testing)")

    args = parser.parse_args()

    try:
        asyncio.run(main(stocks_limit=args.stocks_limit))
    except Exception:
        # The logger already captured the exception, just exit with error code
        sys.exit(1)
