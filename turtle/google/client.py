"""Google Sheets API client wrapper."""

import logging
import time
from typing import Any

import gspread
from gspread.exceptions import APIError, WorksheetNotFound
from gspread import Spreadsheet, Worksheet

from .auth import GoogleAuthenticator
from .models import GoogleSheetsConfig

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Google Sheets API client with retry logic and error handling."""

    def __init__(self, config: GoogleSheetsConfig):
        """Initialize client with configuration.

        Args:
            config: Google Sheets configuration
        """
        self.config = config
        self.authenticator = GoogleAuthenticator(config.credentials_path, config.auth_type)
        self._client: gspread.Client | None = None
        self._spreadsheet: Spreadsheet | None = None
        self._worksheet: Worksheet | None = None

    def connect(self) -> None:
        """Establish connection to Google Sheets.

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info("Connecting to Google Sheets")
            self._client = self.authenticator.authenticate()
            self._spreadsheet = self._client.open_by_key(self.config.sheet_id)
            logger.info(f"Connected to spreadsheet: {self._spreadsheet.title}")

            # Get or create worksheet
            self._worksheet = self._get_or_create_worksheet()
            logger.info(f"Using worksheet: {self._worksheet.title}")

        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    def _get_or_create_worksheet(self) -> Worksheet:
        """Get existing worksheet or create new one if configured.

        Returns:
            Worksheet object

        Raises:
            WorksheetNotFound: If worksheet doesn't exist and create_worksheet_if_missing is False
        """
        if not self._spreadsheet:
            raise RuntimeError("Not connected to spreadsheet")

        try:
            # Try to get existing worksheet
            worksheet = self._spreadsheet.worksheet(self.config.worksheet_name)
            logger.info(f"Found existing worksheet: {worksheet.title}")
            return worksheet

        except WorksheetNotFound:
            if self.config.create_worksheet_if_missing:
                logger.info(f"Creating new worksheet: {self.config.worksheet_name}")
                worksheet = self._spreadsheet.add_worksheet(title=self.config.worksheet_name, rows=1000, cols=10)
                return worksheet
            else:
                logger.error(f"Worksheet '{self.config.worksheet_name}' not found")
                raise

    def append_rows(self, rows: list[list[Any]], retry_count: int = 3) -> None:
        """Append rows to the worksheet with retry logic.

        Args:
            rows: List of rows to append
            retry_count: Number of retries for API errors

        Raises:
            Exception: If all retries fail
        """
        if not self._worksheet:
            raise RuntimeError("Not connected to worksheet")

        if not rows:
            logger.warning("No rows to append")
            return

        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Appending {len(rows)} rows to worksheet")
                self._worksheet.append_rows(rows)
                logger.info("Rows appended successfully")
                return

            except APIError as e:
                if "Quota exceeded" in str(e) and attempt < retry_count:
                    wait_time = (attempt + 1) * 10  # Exponential backoff
                    logger.warning(f"API quota exceeded, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error after {attempt + 1} attempts: {e}")
                    raise

            except Exception as e:
                logger.error(f"Failed to append rows: {e}")
                if attempt < retry_count:
                    logger.info(f"Retrying in 5 seconds (attempt {attempt + 1})")
                    time.sleep(5)
                    continue
                raise

    def clear_worksheet(self) -> None:
        """Clear all data from the worksheet.

        Raises:
            Exception: If clearing fails
        """
        if not self._worksheet:
            raise RuntimeError("Not connected to worksheet")

        try:
            logger.info("Clearing worksheet data")
            self._worksheet.clear()
            logger.info("Worksheet cleared successfully")

        except Exception as e:
            logger.error(f"Failed to clear worksheet: {e}")
            raise

    def setup_headers(self, headers: list[str]) -> None:
        """Set up column headers in the worksheet.

        Args:
            headers: List of column headers

        Raises:
            Exception: If setting headers fails
        """
        if not self._worksheet:
            raise RuntimeError("Not connected to worksheet")

        try:
            logger.info(f"Setting up headers: {headers}")
            # Check if headers already exist
            existing_headers = self._worksheet.row_values(1) if self._worksheet.row_count > 0 else []

            if existing_headers != headers:
                # Clear and set new headers
                if existing_headers:
                    self._worksheet.delete_rows(1)
                self._worksheet.insert_row(headers, 1)
                logger.info("Headers set up successfully")
            else:
                logger.info("Headers already match, skipping setup")

        except Exception as e:
            logger.error(f"Failed to setup headers: {e}")
            raise

    def batch_update(self, data: list[list[Any]], start_row: int = 1) -> None:
        """Batch update worksheet data for better performance.

        Args:
            data: List of rows to update
            start_row: Starting row number (1-based)

        Raises:
            Exception: If batch update fails
        """
        if not self._worksheet:
            raise RuntimeError("Not connected to worksheet")

        if not data:
            logger.warning("No data to update")
            return

        try:
            logger.info(f"Batch updating {len(data)} rows starting from row {start_row}")

            # Calculate range
            end_row = start_row + len(data) - 1
            end_col = len(data[0]) if data else 1
            range_name = f"A{start_row}:{chr(64 + end_col)}{end_row}"

            # Update range
            self._worksheet.update(values=data, range_name=range_name)
            logger.info("Batch update completed successfully")

        except Exception as e:
            logger.error(f"Failed to batch update: {e}")
            raise

    def get_worksheet_info(self) -> dict[str, Any]:
        """Get information about the current worksheet.

        Returns:
            Dictionary with worksheet information
        """
        if not self._worksheet:
            raise RuntimeError("Not connected to worksheet")

        return {
            "title": self._worksheet.title,
            "row_count": self._worksheet.row_count,
            "col_count": self._worksheet.col_count,
            "url": self._worksheet.url,
        }

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to worksheet."""
        return all([self._client, self._spreadsheet, self._worksheet])

    def disconnect(self) -> None:
        """Clean up connections."""
        logger.info("Disconnecting from Google Sheets")
        self._worksheet = None
        self._spreadsheet = None
        self._client = None
