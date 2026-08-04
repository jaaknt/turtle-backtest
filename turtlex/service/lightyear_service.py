"""Parse Lightyear account-statement CSVs and store their Buy/Sell rows.

Statements overlap in date range, so the same transaction appears in many downloaded
files. Idempotency is handled by the repository (``reference`` is the unique key);
this module handles parsing, watchlist filtering and per-file reporting.
"""

import csv
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from turtlex.model import LightyearTransaction
from turtlex.repository.ingest.lightyear import LightyearRepository
from turtlex.repository.query.ticker import TickerQueryRepository

logger = logging.getLogger(__name__)

# Statement timestamps are day-first, e.g. "31/07/2026 05:51:36"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
IMPORTED_TYPES = {"Buy", "Sell"}
IMPORTED_CURRENCY = "USD"

# Every column this importer reads. "FX Rate" is in the statement but unused, so a
# statement that drops it still parses.
REQUIRED_COLUMNS = frozenset(
    {"Date", "Reference", "Ticker", "ISIN", "Type", "Quantity", "CCY", "Price/share", "Gross Amount", "Fee", "Net Amt.", "Tax Amt."}
)


class TickerGroupNotSeededError(ValueError):
    """The hand-maintained watchlist group is empty or misspelled."""


class StatementParseError(ValueError):
    """A statement CSV could not be parsed. Nothing from that file was stored."""


@dataclass
class FileImportSummary:
    """
    Per-file outcome of a statement import.

    Attributes:
        file_name: Name of the parsed CSV
        rows: Data rows read from the file
        buy_sell: Rows whose Type is Buy or Sell
        matched: Rows that also passed the currency and watchlist filters
        inserted: Rows the database actually accepted (the rest were already stored)
        skipped_currency: Buy/Sell rows rejected because CCY is not USD
        skipped_not_in_group: USD Buy/Sell rows rejected because the symbol is not in the group
        unseeded_symbols: Ticker codes behind skipped_not_in_group, for the operator warning
        failed: True if the file could not be parsed, in which case none of it was stored
            and every counter above is left at 0
    """

    file_name: str
    rows: int = 0
    buy_sell: int = 0
    matched: int = 0
    inserted: int = 0
    skipped_currency: int = 0
    skipped_not_in_group: int = 0
    unseeded_symbols: set[str] = field(default_factory=set)
    failed: bool = False

    @property
    def already_stored(self) -> int:
        """Matched rows the database did not accept because the reference was known.

        Derived as matched minus inserted, so a reference repeated within one file — the
        case ``_warn_on_duplicate_references`` reports — also lands here.
        """
        return self.matched - self.inserted


@dataclass
class ImportSummary:
    """
    Run-level outcome of a folder import.

    Attributes:
        files: Per-file summaries, in the order the files were parsed
    """

    files: list[FileImportSummary] = field(default_factory=list)

    @property
    def rows(self) -> int:
        """Total data rows read across all files."""
        return sum(f.rows for f in self.files)

    @property
    def buy_sell(self) -> int:
        """Total Buy/Sell rows across all files."""
        return sum(f.buy_sell for f in self.files)

    @property
    def matched(self) -> int:
        """Total rows that passed every filter across all files."""
        return sum(f.matched for f in self.files)

    @property
    def inserted(self) -> int:
        """Total rows the database accepted across all files."""
        return sum(f.inserted for f in self.files)

    @property
    def already_stored(self) -> int:
        """Total matched rows the database already held, across all files."""
        return sum(f.already_stored for f in self.files)

    @property
    def skipped_not_in_group(self) -> int:
        """Total USD Buy/Sell rows rejected for not being in the group, across all files."""
        return sum(f.skipped_not_in_group for f in self.files)

    @property
    def unseeded_symbols(self) -> set[str]:
        """Every USD Buy/Sell symbol missing from the ticker group, across all files."""
        return {symbol for f in self.files for symbol in f.unseeded_symbols}

    @property
    def failed_files(self) -> list[str]:
        """Names of files that could not be parsed; nothing from them was stored."""
        return [f.file_name for f in self.files if f.failed]


def _decimal(value: str) -> Decimal:
    """Parse a statement money cell; an empty cell means zero."""
    return Decimal(value) if value else Decimal("0")


def _build_transaction(row: dict[str, str], row_number: int, ticker_code: str, file_name: str) -> LightyearTransaction:
    # ArithmeticError covers decimal.InvalidOperation, which is not a ValueError; ValueError
    # covers strptime. Both would otherwise surface as a bare traceback naming neither the
    # file nor the row.
    try:
        return LightyearTransaction(
            reference=row["Reference"],
            transacted_at=datetime.strptime(row["Date"], DATE_FORMAT),
            ticker_code=ticker_code,
            isin=row["ISIN"],
            transaction_type=row["Type"].lower(),
            quantity=Decimal(row["Quantity"]),
            currency=row["CCY"],
            price=Decimal(row["Price/share"]),
            gross_amount=Decimal(row["Gross Amount"]),
            fee=_decimal(row["Fee"]),
            tax=_decimal(row["Tax Amt."]),
            net_amount=Decimal(row["Net Amt."]),
            source_file=file_name,
        )
    except (ValueError, ArithmeticError) as e:
        raise StatementParseError(f"row {row_number} ({row['Reference']}): {e}") from e


class LightyearService:
    """Imports Lightyear statement CSVs into turtle.lightyear_transaction."""

    def __init__(self, repository: LightyearRepository, ticker_repo: TickerQueryRepository) -> None:
        """
        Initialize the Lightyear import service.

        Args:
            repository: Write repository for turtle.lightyear_transaction
            ticker_repo: Repository used to read the watchlist group membership
        """
        self.repository = repository
        self.ticker_repo = ticker_repo

    def import_folder(self, folder: Path, group_code: str) -> ImportSummary:
        """
        Parse every CSV in a folder and insert the Buy/Sell rows matching the watchlist.

        Args:
            folder: Directory holding the downloaded statement CSVs; files are left in place
            group_code: turtle.ticker_group code listing the symbols to import

        Returns:
            ImportSummary: Per-file and run-level counts

        Raises:
            TickerGroupNotSeededError: If the ticker group is empty — the group is
                hand-maintained, so an empty set means it was never seeded or the code is
                misspelled, and every row would be silently dropped
        """
        group_tickers = self.ticker_repo.get_group_ticker_codes(group_code)
        if not group_tickers:
            raise TickerGroupNotSeededError(f"Ticker group '{group_code}' is empty or does not exist")
        logger.debug("Ticker group '%s' holds %d symbols", group_code, len(group_tickers))

        summary = ImportSummary()
        for path in sorted(folder.glob("*.csv")):
            # One damaged statement must not block the ones sorting after it, nor discard
            # the summary for the ones already imported. The insert happens once at the end
            # of _import_file, so a file that raises stored nothing at all.
            try:
                summary.files.append(self._import_file(path, group_tickers))
            except StatementParseError as e:
                logger.error("%s: parse failed, nothing from this file was stored: %s", path.name, e)
                summary.files.append(FileImportSummary(file_name=path.name, failed=True))
        return summary

    def _import_file(self, path: Path, group_tickers: set[str]) -> FileImportSummary:
        result = FileImportSummary(file_name=path.name)
        # Every way the file itself can be unreadable — a bad encoding, an unterminated
        # quote — is normalised to StatementParseError here, so import_folder isolates a
        # damaged statement on one exception type instead of a growing tuple of them.
        try:
            candidates = self._read_transactions(path, group_tickers, result)
        except (UnicodeDecodeError, csv.Error) as e:
            raise StatementParseError(f"unreadable CSV: {e}") from e

        self._warn_on_duplicate_references(path.name, candidates)
        result.inserted = self.repository.insert_transactions(candidates)
        return result

    def _read_transactions(self, path: Path, group_tickers: set[str], result: FileImportSummary) -> list[LightyearTransaction]:
        candidates: list[LightyearTransaction] = []

        # utf-8-sig, not utf-8: a BOM would otherwise corrupt only the first column name,
        # letting every filter run normally and failing later on row["Date"] — or, in a file
        # with no matched rows, importing nothing while reporting success.
        with path.open(newline="", encoding="utf-8-sig") as f:
            # skipinitialspace is mandatory: the header line starts with a literal space,
            # which would otherwise name the first column ' "Date"' instead of 'Date'.
            reader = csv.DictReader(f, skipinitialspace=True)
            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing_columns:
                raise StatementParseError(f"header is missing {sorted(missing_columns)} — got {reader.fieldnames}")

            for row_number, row in enumerate(reader, start=2):
                result.rows += 1
                # DictReader pads a short row with None, which would otherwise reach
                # _decimal and silently become 0 on a NOT NULL money column.
                truncated = sorted(column for column in REQUIRED_COLUMNS if row.get(column) is None)
                if truncated:
                    raise StatementParseError(f"row {row_number} is truncated, missing {truncated}")
                if row["Type"] not in IMPORTED_TYPES:
                    continue
                result.buy_sell += 1
                if row["CCY"] != IMPORTED_CURRENCY:
                    result.skipped_currency += 1
                    continue
                ticker_code = f"{row['Ticker']}.US"
                if ticker_code not in group_tickers:
                    result.skipped_not_in_group += 1
                    result.unseeded_symbols.add(ticker_code)
                    continue
                result.matched += 1
                candidates.append(_build_transaction(row, row_number, ticker_code, path.name))

        return candidates

    def _warn_on_duplicate_references(self, file_name: str, candidates: list[LightyearTransaction]) -> None:
        # Per file, not per run: overlapping statements repeat references across files by
        # design, so a per-run check would fire on every correct re-import. Within one file
        # a repeated reference means ON CONFLICT DO NOTHING will silently drop a row.
        duplicates = sorted(ref for ref, count in Counter(t.reference for t in candidates).items() if count > 1)
        if duplicates:
            logger.warning(
                "%s: duplicate references within the file, only the first row of each is stored: %s", file_name, ", ".join(duplicates)
            )
