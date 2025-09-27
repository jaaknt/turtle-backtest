"""Data models for Google Sheets integration."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from turtle.signal.models import Signal


@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets integration.

    Attributes:
        sheet_id: Google Sheets document ID (from URL)
        worksheet_name: Name of the specific worksheet/tab
        credentials_path: Path to service account JSON file or OAuth credentials
        auth_type: Authentication type ('service_account' or 'oauth')
        create_worksheet_if_missing: Whether to create worksheet if it doesn't exist
        clear_before_export: Whether to clear existing data before adding new data
    """

    sheet_id: str
    worksheet_name: str
    credentials_path: str | Path
    auth_type: str = "service_account"  # 'service_account' or 'oauth'
    create_worksheet_if_missing: bool = True
    clear_before_export: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.auth_type not in ["service_account", "oauth"]:
            raise ValueError("auth_type must be 'service_account' or 'oauth'")

        if isinstance(self.credentials_path, str):
            self.credentials_path = Path(self.credentials_path)

        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")


@dataclass
class SignalRow:
    """Formatted signal data for Google Sheets export.

    Attributes:
        date: Signal date in YYYY-MM-DD format
        ticker: Stock symbol
        ranking: Signal ranking (1-100)
        strategy_name: Name of the trading strategy
        export_timestamp: When this data was exported
        price: Current stock price (if available)
        volume: Trading volume (if available)
    """

    date: str
    ticker: str
    ranking: int
    strategy_name: str
    export_timestamp: str
    price: float | None = None
    volume: int | None = None

    @classmethod
    def from_signal(cls, signal: Signal, strategy_name: str, price: float | None = None, volume: int | None = None) -> "SignalRow":
        """Create SignalRow from Signal object.

        Args:
            signal: Signal object to convert
            strategy_name: Name of the trading strategy
            price: Current stock price (optional)
            volume: Trading volume (optional)

        Returns:
            SignalRow instance
        """
        return cls(
            date=signal.date.strftime("%Y-%m-%d"),
            ticker=signal.ticker,
            ranking=signal.ranking,
            strategy_name=strategy_name,
            export_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            price=price,
            volume=volume,
        )

    def to_row(self) -> list[str | int | float]:
        """Convert to list format for Google Sheets.

        Returns:
            List of values for spreadsheet row
        """
        return [
            self.date,
            self.ticker,
            self.ranking,
            self.strategy_name,
            self.export_timestamp,
            self.price or "",
            self.volume or "",
        ]

    @staticmethod
    def get_headers() -> list[str]:
        """Get column headers for Google Sheets.

        Returns:
            List of column headers
        """
        return [
            "Date",
            "Ticker",
            "Ranking",
            "Strategy",
            "Export Timestamp",
            "Price",
            "Volume",
        ]
