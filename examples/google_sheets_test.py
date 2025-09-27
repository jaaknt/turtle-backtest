#!/usr/bin/env python3
"""Test script for Google Sheets integration."""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to import turtle package
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtle.google.models import GoogleSheetsConfig, SignalRow
from turtle.google.signal_exporter import SignalExporter
from turtle.signal.models import Signal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_signals() -> list[Signal]:
    """Create sample signals for testing."""
    base_date = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)

    sample_signals = [
        Signal(ticker="AAPL", date=base_date, ranking=85),
        Signal(ticker="GOOGL", date=base_date, ranking=78),
        Signal(ticker="MSFT", date=base_date, ranking=92),
        Signal(ticker="TSLA", date=base_date, ranking=73),
        Signal(ticker="NVDA", date=base_date, ranking=89),
    ]

    return sample_signals


def test_signal_row_formatting() -> None:
    """Test SignalRow formatting functionality."""
    logger.info("Testing SignalRow formatting...")

    sample_signal = Signal(ticker="AAPL", date=datetime.now(), ranking=85)
    signal_row = SignalRow.from_signal(sample_signal, "TestStrategy", price=150.25, volume=1000000)

    logger.info(f"Signal row data: {signal_row}")
    logger.info(f"Headers: {SignalRow.get_headers()}")
    logger.info(f"Row values: {signal_row.to_row()}")


def test_google_sheets_config() -> None:
    """Test Google Sheets configuration."""
    logger.info("Testing Google Sheets configuration...")

    # Example configuration (you'll need to replace with actual values)
    try:
        config = GoogleSheetsConfig(
            sheet_id="your_spreadsheet_id_here",
            worksheet_name="test_signals",
            credentials_path="path/to/your/service_account.json",
            auth_type="service_account",
            create_worksheet_if_missing=True,
            clear_before_export=False
        )
        logger.info(f"Config created successfully: {config}")

    except FileNotFoundError as e:
        logger.warning(f"Credentials file not found (expected for test): {e}")
        logger.info("To use Google Sheets integration, you need to:")
        logger.info("1. Create a Google Cloud project")
        logger.info("2. Enable Google Sheets API")
        logger.info("3. Create a service account and download JSON credentials")
        logger.info("4. Share your spreadsheet with the service account email")


def test_export_summary() -> None:
    """Test export summary functionality."""
    logger.info("Testing export summary...")

    signals = create_sample_signals()

    # Create a temporary dummy credentials file for testing
    dummy_creds_path = Path("/tmp/dummy_creds.json")
    dummy_creds_path.write_text('{"type": "service_account", "project_id": "test"}')

    try:
        # Create a mock config for testing
        config = GoogleSheetsConfig(
            sheet_id="test_sheet_id",
            worksheet_name="test_signals",
            credentials_path=dummy_creds_path,  # Won't be used for summary
            create_worksheet_if_missing=True
        )

        # Create exporter (without bars_history for this test)
        exporter = SignalExporter(config)

        # Get export summary
        summary = exporter.get_export_summary(signals, "TestStrategy")

        logger.info("Export Summary:")
        logger.info(f"  Signal count: {summary['signal_count']}")
        logger.info(f"  Strategy: {summary['strategy_name']}")
        logger.info(f"  Date range: {summary['date_range']}")
        logger.info(f"  Tickers: {summary['tickers']}")
        logger.info(f"  Ranking stats: {summary['ranking_stats']}")

    finally:
        # Clean up temporary file
        if dummy_creds_path.exists():
            dummy_creds_path.unlink()


def test_daily_worksheet_naming() -> None:
    """Test daily worksheet naming functionality."""
    logger.info("Testing daily worksheet naming...")

    signals = create_sample_signals()
    signal_date = signals[0].date.strftime("%Y-%m-%d")

    logger.info(f"Sample signals date: {signal_date}")
    logger.info(f"Daily worksheet would be named: signals_{signal_date}")


def main() -> None:
    """Run all tests."""
    logger.info("Starting Google Sheets integration tests...")

    test_signal_row_formatting()
    test_google_sheets_config()
    test_export_summary()
    test_daily_worksheet_naming()

    logger.info("Tests completed!")

    # Usage example
    logger.info("\n" + "="*50)
    logger.info("USAGE EXAMPLE:")
    logger.info("="*50)

    usage_example = '''
# 1. Set up Google Sheets credentials
config = GoogleSheetsConfig(
    sheet_id="your_google_sheet_id",
    worksheet_name="daily_signals",
    credentials_path="path/to/service_account.json"
)

# 2. Use with PortfolioService
from turtle.service.portfolio_service import PortfolioService

service = PortfolioService(
    trading_strategy=your_strategy,
    exit_strategy=your_exit_strategy,
    bars_history=your_bars_repo,
    start_date=start_date,
    end_date=end_date,
    google_sheets_config=config  # Add this parameter
)

# 3. Run backtest - signals will be automatically exported
service.run_backtest(start_date, end_date, universe)
'''

    logger.info(usage_example)


if __name__ == "__main__":
    main()
