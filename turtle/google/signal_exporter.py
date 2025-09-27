"""Signal exporter service for Google Sheets integration."""

import logging

from turtle.signal.models import Signal
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from .models import GoogleSheetsConfig, SignalRow
from .client import GoogleSheetsClient

logger = logging.getLogger(__name__)


class SignalExporter:
    """Service for exporting trading signals to Google Sheets."""

    def __init__(self, config: GoogleSheetsConfig, bars_history: BarsHistoryRepo | None = None):
        """Initialize signal exporter.

        Args:
            config: Google Sheets configuration
            bars_history: Optional bars history repository for price/volume data
        """
        self.config = config
        self.bars_history = bars_history
        self.client = GoogleSheetsClient(config)

    def export_signals(
        self,
        signals: list[Signal],
        strategy_name: str,
        include_price_data: bool = False,
        setup_headers: bool = True,
    ) -> bool:
        """Export signals to Google Sheets.

        Args:
            signals: List of signals to export
            strategy_name: Name of the trading strategy
            include_price_data: Whether to include current price/volume data
            setup_headers: Whether to set up column headers

        Returns:
            True if export successful, False otherwise
        """
        if not signals:
            logger.warning("No signals to export")
            return True

        try:
            # Connect to Google Sheets
            self.client.connect()
            logger.info(f"Exporting {len(signals)} signals for strategy: {strategy_name}")

            # Clear worksheet if configured
            if self.config.clear_before_export:
                self.client.clear_worksheet()

            # Set up headers if needed
            if setup_headers:
                headers = SignalRow.get_headers()
                self.client.setup_headers(headers)

            # Format signals for export
            signal_rows = self._format_signals(signals, strategy_name, include_price_data)

            # Convert to list format for sheets
            rows_data = [row.to_row() for row in signal_rows]

            # Export to sheets
            if self.config.clear_before_export:
                # Use batch update for better performance when clearing
                self.client.batch_update(rows_data, start_row=2)  # Start after headers
            else:
                # Append to existing data
                self.client.append_rows(rows_data)

            worksheet_info = self.client.get_worksheet_info()
            logger.info(f"Successfully exported {len(signals)} signals to '{worksheet_info['title']}'")
            logger.info(f"Worksheet URL: {worksheet_info['url']}")

            return True

        except Exception as e:
            logger.error(f"Failed to export signals: {e}")
            return False

        finally:
            # Clean up connection
            self.client.disconnect()

    def _format_signals(self, signals: list[Signal], strategy_name: str, include_price_data: bool) -> list[SignalRow]:
        """Format signals into SignalRow objects.

        Args:
            signals: List of signals to format
            strategy_name: Name of the trading strategy
            include_price_data: Whether to include price/volume data

        Returns:
            List of formatted SignalRow objects
        """
        signal_rows = []

        for signal in signals:
            price = None
            volume = None

            # Get price and volume data if requested and available
            if include_price_data and self.bars_history:
                try:
                    # Get the most recent bar for the ticker
                    bars_df = self.bars_history.get_ticker_history(
                        signal.ticker, signal.date, signal.date, TimeFrameUnit.DAY
                    )

                    if not bars_df.empty:
                        latest_bar = bars_df.iloc[-1]
                        price = float(latest_bar["close"])
                        volume = int(latest_bar["volume"]) if "volume" in latest_bar else None

                except Exception as e:
                    logger.warning(f"Failed to get price data for {signal.ticker}: {e}")

            # Create SignalRow
            signal_row = SignalRow.from_signal(signal, strategy_name, price, volume)
            signal_rows.append(signal_row)

        return signal_rows

    def export_daily_signals(
        self,
        signals: list[Signal],
        strategy_name: str,
        include_price_data: bool = False,
    ) -> bool:
        """Export signals with automatic daily worksheet naming.

        Creates or uses a worksheet named with the current date.

        Args:
            signals: List of signals to export
            strategy_name: Name of the trading strategy
            include_price_data: Whether to include price/volume data

        Returns:
            True if export successful, False otherwise
        """
        if not signals:
            logger.warning("No signals to export")
            return True

        # Get date from first signal for worksheet naming
        signal_date = signals[0].date.strftime("%Y-%m-%d")
        original_worksheet_name = self.config.worksheet_name

        try:
            # Update config to use date-based worksheet name
            self.config.worksheet_name = f"{original_worksheet_name}_{signal_date}"
            logger.info(f"Using daily worksheet: {self.config.worksheet_name}")

            # Export signals
            return self.export_signals(signals, strategy_name, include_price_data, setup_headers=True)

        finally:
            # Restore original worksheet name
            self.config.worksheet_name = original_worksheet_name

    def test_connection(self) -> bool:
        """Test connection to Google Sheets.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing Google Sheets connection")
            self.client.connect()
            worksheet_info = self.client.get_worksheet_info()
            logger.info(f"Connection test successful - Worksheet: {worksheet_info['title']}")
            return True

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

        finally:
            self.client.disconnect()

    def get_export_summary(self, signals: list[Signal], strategy_name: str) -> dict:
        """Get summary information about the export without actually exporting.

        Args:
            signals: List of signals to analyze
            strategy_name: Name of the trading strategy

        Returns:
            Dictionary with export summary information
        """
        if not signals:
            return {"signal_count": 0, "date_range": None, "tickers": [], "avg_ranking": 0}

        dates = [signal.date for signal in signals]
        tickers = list({signal.ticker for signal in signals})
        rankings = [signal.ranking for signal in signals]

        return {
            "signal_count": len(signals),
            "strategy_name": strategy_name,
            "date_range": {
                "start": min(dates).strftime("%Y-%m-%d"),
                "end": max(dates).strftime("%Y-%m-%d"),
            },
            "tickers": sorted(tickers),
            "ranking_stats": {
                "min": min(rankings),
                "max": max(rankings),
                "avg": sum(rankings) / len(rankings),
            },
            "config": {
                "sheet_id": self.config.sheet_id,
                "worksheet_name": self.config.worksheet_name,
                "auth_type": self.config.auth_type,
            },
        }
