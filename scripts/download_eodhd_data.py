import argparse
import asyncio
import logging
import re
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path to import turtle modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtle.config.settings import Settings
from turtle.services.eodhd_service import EodhdService

logger = logging.getLogger(__name__)


class _ApiTokenFilter(logging.Filter):
    """Redact api_token query parameter from httpx request log messages.

    httpx logs via format-string args (e.g. "HTTP Request: %s %s ..."),
    so the URL lives in record.args, not record.msg.
    """

    _PATTERN = re.compile(r"api_token=[^&\s\"]+")

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._PATTERN.sub("api_token=***", str(record.msg))
        if record.args:
            args = record.args if isinstance(record.args, tuple) else (record.args,)
            record.args = tuple(self._PATTERN.sub("api_token=***", s) if "api_token=" in (s := str(arg)) else arg for arg in args)
        return True


async def main(
    data: str,
    start_date: date,
    end_date: date,
    ticker_limit: int | None = None,
) -> None:
    """
    Main function to download EODHD data.

    Args:
        data: Which dataset to download - exchange, us_ticker, company, or history.
        ticker_limit: Optional limit on number of tickers to download data for.
                     If None, downloads all tickers. Useful for testing.
        start_date: Start date for historical data. Defaults to 2026-01-01.
        end_date: End date for historical data. Defaults to today minus 30 days.
    """
    # Force logging to stdout for this script
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="[%(levelname)s|%(module)s|%(funcName)s] %(message)s")
    # Redact api_token from all handlers — filter must be on the handler, not the
    # logger, because httpx logs from httpx._client propagate to root without
    # passing through filters attached to the parent httpx logger.
    token_filter = _ApiTokenFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(token_filter)
    logger.info("Starting EODHD data download script.")
    logger.info(f"Dataset to download: {data}")
    if ticker_limit is not None:
        logger.info(f"Running in TEST MODE - limiting to {ticker_limit} tickers")
    if start_date or end_date:
        logger.info(f"Custom date range: {start_date or 'default'} to {end_date or 'default'}")

    eodhd_service = None
    try:
        settings = Settings.from_toml()
        eodhd_service = EodhdService(settings)
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
            await eodhd_service.download_historical_data(
                ticker_limit=ticker_limit,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

        logger.info("EODHD data download completed successfully.")
    except Exception as e:
        logger.error(f"EODHD data download script failed: {e}", exc_info=True)
        # Re-raise the exception for the script to exit with an error code
        raise
    finally:
        if eodhd_service is not None:
            await eodhd_service.close()
        logger.info("EODHD data download script finished.")


def iso_date_type(date_string: str) -> date:
    """Custom argparse type for ISO date validation."""
    try:
        return date.fromisoformat(date_string)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Expected ISO format (YYYY-MM-DD)") from err


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
        type=iso_date_type,
        metavar="YYYY-MM-DD",
        default=date.today() - timedelta(days=30),
        help="Start date for historical data (YYYY-MM-DD). Default: 30 days ago.",
    )
    parser.add_argument(
        "--end-date",
        type=iso_date_type,
        metavar="YYYY-MM-DD",
        default=date.today(),
        help="End date for historical data (YYYY-MM-DD). Default: today",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            main(
                data=args.data,
                start_date=args.start_date,
                end_date=args.end_date,
                ticker_limit=args.ticker_limit,
            )
        )
    except Exception:
        # The logger already captured the exception, just exit with error code
        sys.exit(1)
