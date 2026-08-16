import argparse
import asyncio
import logging
import sys
from datetime import date, timedelta

from turtlex.cli.common import add_logging_args, run_job
from turtlex.common.cli import iso_date_type
from turtlex.config.logging import setup_logging
from turtlex.config.settings import Settings
from turtlex.service.eodhd_service import EodhdService
from turtlex.service.job_run_service import JobRunRecorder

logger = logging.getLogger(__name__)


async def download(
    settings: Settings,
    data: str,
    start_date: date,
    end_date: date,
    ticker_limit: int | None = None,
) -> None:
    """
    Download the requested EODHD dataset.

    Args:
        settings: Loaded application settings. Loaded by the caller rather than here so the
                 job-run recorder can use the same engine before this coroutine starts.
        data: Which dataset to download - exchange, us_ticker, company, or history.
        ticker_limit: Optional limit on number of tickers to download data for.
                     If None, downloads all tickers. Useful for testing.
        start_date: Start date for historical data. Defaults to 2026-01-01.
        end_date: End date for historical data. Defaults to today minus 30 days.
    """
    logger.info("Starting EODHD data download script.")
    logger.info(f"Dataset to download: {data}")
    if ticker_limit is not None:
        logger.info(f"Running in TEST MODE - limiting to {ticker_limit} tickers")
    if start_date or end_date:
        logger.info(f"Custom date range: {start_date or 'default'} to {end_date or 'default'}")

    eodhd_service = None
    try:
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


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Download data from EODHD for US stocks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download exchange data
  uv run download-eodhd-data --data exchange

  # Download US ticker list
  uv run download-eodhd-data --data us_ticker

  # Download company data
  uv run download-eodhd-data --data company --ticker-limit 10

  # Download historical price data
  uv run download-eodhd-data --data history --start-date 2024-01-01 --end-date 2024-12-31

  # Test historical data with 10 tickers
  uv run download-eodhd-data --data history --ticker-limit 10

  # Test with limited tickers and custom date range
  uv run download-eodhd-data --data history --ticker-limit 10 --start-date 2024-06-01 --end-date 2024-06-30
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
    add_logging_args(parser)

    return parser


def main() -> int:
    """Main entry point for the EODHD download CLI."""
    args = create_argument_parser().parse_args()

    setup_logging(args.verbose)
    settings = Settings.from_toml()

    def body(_recorder: JobRunRecorder) -> int:
        asyncio.run(
            download(
                settings,
                data=args.data,
                start_date=args.start_date,
                end_date=args.end_date,
                ticker_limit=args.ticker_limit,
            )
        )
        return 0

    return run_job("download-eodhd-data", args, settings, body)


if __name__ == "__main__":
    sys.exit(main())
