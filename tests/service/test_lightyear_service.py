"""Tests for LightyearService: statement parsing, filtering and per-file reporting."""

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest

from turtlex.model import LightyearTransaction
from turtlex.service.lightyear_service import LightyearService, TickerGroupNotSeededError

EXAMPLE_CSV = Path(__file__).resolve().parents[2] / "docs" / "specs" / "lightyear-example.csv"

# The leading space before "Date" is deliberate — real statements have it, and it is what
# csv.DictReader(skipinitialspace=True) exists to survive.
HEADER = ' "Date","Reference","Ticker","ISIN","Type","Quantity","CCY","Price/share","Gross Amount","FX Rate","Fee","Net Amt.","Tax Amt."'

BUY_DUOL = (
    '"30/07/2026 14:05:03","OR-YL9Q9LC3ZK","DUOL","US26603R1068","Buy","8.000000000","USD","131.500000000","1053.00","","1.00","1052.00",""'
)
BUY_PRGS = (
    '"30/07/2026 13:30:00","OR-SXH5GJKE2Q","PRGS","US7433121008","Buy","25.000000000","USD","41.170000000","1030.25","","1.00","1029.25",""'
)
SELL_DUOL = (
    '"31/07/2026 15:00:00","OR-SELL111111","DUOL","US26603R1068","Sell",'
    '"3.000000000","USD","140.250000000","420.75","","1.00","419.75","0.10"'
)
SELL_EUR = (
    '"30/07/2026 18:05:48","OR-N7T2WQFB4D","ASML","NL0010273215","Sell",'
    '"1.000000000","EUR","1385.600000000","1385.60","","1.00","1384.60",""'
)
BUY_GENI = (
    '"29/07/2026 15:35:36","OR-5KV9C3VQGF","GENI","GG00BMF1JR16","Buy","150.000000000","USD","7.215000000","1083.25","","1.00","1082.25",""'
)
BUY_UNSEEDED = (
    '"29/07/2026 15:00:00","OR-UNSEEDED01","NVDA","US67066G1040","Buy","5.000000000","USD","100.000000000","501.00","","1.00","500.00",""'
)
DIVIDEND = '"31/07/2026 05:51:36","DD-M5Q6AGAHQL","MRVL","US5738741041","Dividend","","USD","","0.36","","","0.31","0.05"'
CONVERSION = '"30/07/2026 13:05:32","CN-GA8HWYMVR7","USD","","Conversion","","USD","","1052.25","0.87176","","1052.25",""'
BUY_NO_FEE = (
    '"28/07/2026 15:00:00","OR-NOFEE00001","PRGS","US7433121008","Buy","10.000000000","USD","40.000000000","400.00","","","400.00",""'
)


def _write_csv(folder: Path, name: str, *rows: str) -> Path:
    path = folder / name
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def _make_service(group: set[str], inserted: int | None = None) -> tuple[LightyearService, Mock, Mock]:
    repository = Mock()
    repository.insert_transactions.side_effect = (lambda txs: len(txs)) if inserted is None else (lambda txs: inserted)
    ticker_repo = Mock()
    ticker_repo.get_group_ticker_codes.return_value = group
    return LightyearService(repository=repository, ticker_repo=ticker_repo), repository, ticker_repo


def _inserted_transactions(repository: Mock) -> list[LightyearTransaction]:
    return [tx for call in repository.insert_transactions.call_args_list for tx in call.args[0]]


class TestParsing:
    def test_buy_row_parsed_verbatim(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement.csv", BUY_DUOL)

        service.import_folder(tmp_path, "lightyear")

        (tx,) = _inserted_transactions(repository)
        assert tx.reference == "OR-YL9Q9LC3ZK"
        # Day-first: 30/07 is 30 July, not an invalid month
        assert tx.transacted_at == datetime(2026, 7, 30, 14, 5, 3)
        assert tx.ticker_code == "DUOL.US"
        assert tx.isin == "US26603R1068"
        assert tx.transaction_type == "buy"
        assert tx.quantity == Decimal("8.000000000")
        assert tx.currency == "USD"
        assert tx.price == Decimal("131.500000000")
        assert tx.gross_amount == Decimal("1053.00")
        assert tx.fee == Decimal("1.00")
        assert tx.tax == Decimal("0")
        assert tx.net_amount == Decimal("1052.00")
        assert tx.source_file == "statement.csv"

    def test_decimal_precision_preserved(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"GENI.US"})
        _write_csv(tmp_path, "statement.csv", BUY_GENI)

        service.import_folder(tmp_path, "lightyear")

        (tx,) = _inserted_transactions(repository)
        assert tx.price == Decimal("7.215000000")
        assert tx.quantity * tx.price == tx.net_amount
        assert tx.net_amount + tx.fee == tx.gross_amount

    def test_sell_lowercased_and_gross_kept_verbatim(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement.csv", SELL_DUOL)

        service.import_folder(tmp_path, "lightyear")

        (tx,) = _inserted_transactions(repository)
        assert tx.transaction_type == "sell"
        # Gross is proceeds *before* fee on a sell — never derived from net
        assert tx.gross_amount == Decimal("420.75")
        assert tx.net_amount == Decimal("419.75")
        assert tx.tax == Decimal("0.10")

    def test_empty_fee_and_tax_become_zero(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"PRGS.US"})
        _write_csv(tmp_path, "statement.csv", BUY_NO_FEE)

        service.import_folder(tmp_path, "lightyear")

        (tx,) = _inserted_transactions(repository)
        assert tx.fee == Decimal("0")
        assert tx.tax == Decimal("0")


class TestFilters:
    def test_non_buy_sell_rows_skipped_on_type(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"MRVL.US", "DUOL.US"})
        _write_csv(tmp_path, "statement.csv", DIVIDEND, CONVERSION, BUY_DUOL)

        summary = service.import_folder(tmp_path, "lightyear")

        (f,) = summary.files
        assert (f.rows, f.buy_sell, f.matched) == (3, 1, 1)
        assert f.skipped_currency == 0
        assert f.skipped_not_in_group == 0
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US"]

    def test_non_usd_rows_skipped_on_currency(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"ASML.US", "DUOL.US"})
        _write_csv(tmp_path, "statement.csv", SELL_EUR, BUY_DUOL)

        summary = service.import_folder(tmp_path, "lightyear")

        (f,) = summary.files
        assert (f.buy_sell, f.matched, f.skipped_currency) == (2, 1, 1)
        # ASML.US is in the group, so only the currency rule stops the AMS listing
        assert f.unseeded_symbols == set()
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US"]

    def test_symbols_outside_group_skipped_and_named(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement.csv", BUY_DUOL, BUY_UNSEEDED)

        summary = service.import_folder(tmp_path, "lightyear")

        (f,) = summary.files
        assert (f.buy_sell, f.matched, f.skipped_not_in_group) == (2, 1, 1)
        assert f.unseeded_symbols == {"NVDA.US"}
        assert summary.unseeded_symbols == {"NVDA.US"}
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US"]

    def test_empty_group_raises_before_parsing(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service(set())
        _write_csv(tmp_path, "statement.csv", BUY_DUOL)

        with pytest.raises(TickerGroupNotSeededError, match="lightyear"):
            service.import_folder(tmp_path, "lightyear")

        repository.insert_transactions.assert_not_called()


class TestMalformedFiles:
    """A damaged statement must fail loudly and in isolation, never partially."""

    def test_bad_date_names_the_row_and_stores_nothing(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        us_format = BUY_DUOL.replace("30/07/2026 14:05:03", "07/31/2026 13:30:00")
        _write_csv(tmp_path, "statement.csv", us_format)

        with caplog.at_level(logging.ERROR):
            summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["statement.csv"]
        assert "row 2" in caplog.text
        assert "OR-YL9Q9LC3ZK" in caplog.text
        repository.insert_transactions.assert_not_called()

    def test_non_numeric_quantity_is_reported_not_raised(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        # decimal.InvalidOperation is not a ValueError, so this escaped as a raw traceback
        service, repository, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement.csv", BUY_DUOL.replace('"8.000000000"', '"n/a"'))

        with caplog.at_level(logging.ERROR):
            summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["statement.csv"]
        repository.insert_transactions.assert_not_called()

    def test_truncated_row_does_not_silently_zero_a_money_column(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        # Drop the trailing Tax Amt. cell; DictReader pads it with None, which used to
        # reach _decimal and become Decimal("0") on a NOT NULL column
        _write_csv(tmp_path, "statement.csv", BUY_DUOL.rsplit(",", 1)[0])

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["statement.csv"]
        repository.insert_transactions.assert_not_called()

    def test_missing_header_column_fails_at_open(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        (tmp_path / "statement.csv").write_text(HEADER.replace('"Net Amt."', '"Net Amount"') + "\n" + BUY_DUOL + "\n", encoding="utf-8")

        with caplog.at_level(logging.ERROR):
            summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["statement.csv"]
        assert "Net Amt." in caplog.text
        repository.insert_transactions.assert_not_called()

    def test_utf8_bom_is_tolerated(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        # A BOM corrupts only the first column name, so filters 1-3 still run and the file
        # would import nothing while reporting success
        (tmp_path / "statement.csv").write_text("﻿" + HEADER + "\n" + BUY_DUOL + "\n", encoding="utf-8")

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == []
        assert summary.matched == 1
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US"]

    def test_one_bad_file_does_not_block_the_others(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US", "PRGS.US"})
        # Alphabetically first, so before the fix it aborted the run before b and c
        _write_csv(tmp_path, "a-broken.csv", BUY_DUOL.replace("30/07/2026 14:05:03", "not-a-date"))
        _write_csv(tmp_path, "b-good.csv", BUY_DUOL)
        _write_csv(tmp_path, "c-good.csv", BUY_PRGS)

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["a-broken.csv"]
        assert [f.file_name for f in summary.files] == ["a-broken.csv", "b-good.csv", "c-good.csv"]
        assert summary.inserted == 2
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US", "PRGS.US"]

    def test_undecodable_file_fails_in_isolation(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})
        # Latin-1 bytes in a file the reader opens as UTF-8; the decode error surfaces
        # mid-iteration, not at open
        (tmp_path / "a-broken.csv").write_bytes(HEADER.encode() + b"\n" + BUY_DUOL.encode().replace(b"DUOL", b"D\xffOL") + b"\n")
        _write_csv(tmp_path, "b-good.csv", BUY_DUOL)

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["a-broken.csv"]
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US"]

    def test_csv_error_fails_in_isolation_like_any_other_parse_failure(self, tmp_path: Path) -> None:
        # csv.Error is not a ValueError, so it used to escape the per-file guard and abort
        # the whole run, discarding the summaries of the files already imported
        service, repository, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "a-broken.csv", BUY_DUOL.replace("US26603R1068", "x" * 200_000))
        _write_csv(tmp_path, "b-good.csv", BUY_DUOL)

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.failed_files == ["a-broken.csv"]
        assert [tx.ticker_code for tx in _inserted_transactions(repository)] == ["DUOL.US"]

    def test_failed_file_contributes_no_counts(self, tmp_path: Path) -> None:
        service, _, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "broken.csv", BUY_DUOL.replace("30/07/2026 14:05:03", "not-a-date"))

        summary = service.import_folder(tmp_path, "lightyear")

        (f,) = summary.files
        assert f.failed is True
        assert (f.rows, f.buy_sell, f.matched, f.inserted) == (0, 0, 0, 0)
        assert (summary.rows, summary.matched, summary.inserted) == (0, 0, 0)


class TestFolderScan:
    def test_group_fetched_once_per_run_across_files(self, tmp_path: Path) -> None:
        service, repository, ticker_repo = _make_service({"DUOL.US", "PRGS.US"})
        _write_csv(tmp_path, "statement-a.csv", BUY_DUOL)
        _write_csv(tmp_path, "statement-b.csv", BUY_PRGS)

        summary = service.import_folder(tmp_path, "lightyear")

        ticker_repo.get_group_ticker_codes.assert_called_once_with("lightyear")
        assert [f.file_name for f in summary.files] == ["statement-a.csv", "statement-b.csv"]
        assert summary.rows == 2
        assert summary.matched == 2
        assert summary.inserted == 2
        assert [tx.source_file for tx in _inserted_transactions(repository)] == ["statement-a.csv", "statement-b.csv"]

    def test_non_csv_files_ignored(self, tmp_path: Path) -> None:
        service, _, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement.csv", BUY_DUOL)
        (tmp_path / "notes.txt").write_text("ignore me\n", encoding="utf-8")

        summary = service.import_folder(tmp_path, "lightyear")

        assert [f.file_name for f in summary.files] == ["statement.csv"]

    def test_empty_folder_yields_empty_summary(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US"})

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.files == []
        assert (summary.rows, summary.buy_sell, summary.matched, summary.inserted) == (0, 0, 0, 0)
        repository.insert_transactions.assert_not_called()

    def test_already_stored_rows_reported_as_not_inserted(self, tmp_path: Path) -> None:
        service, _, _ = _make_service({"DUOL.US", "PRGS.US"}, inserted=0)
        _write_csv(tmp_path, "statement.csv", BUY_DUOL, BUY_PRGS)

        summary = service.import_folder(tmp_path, "lightyear")

        assert summary.matched == 2
        assert summary.inserted == 0


class TestDuplicateReferences:
    def test_duplicate_reference_within_file_warns(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        service, _, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement.csv", BUY_DUOL, BUY_DUOL)

        with caplog.at_level(logging.WARNING):
            service.import_folder(tmp_path, "lightyear")

        assert "OR-YL9Q9LC3ZK" in caplog.text

    def test_repeated_reference_across_files_does_not_warn(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        service, _, _ = _make_service({"DUOL.US"})
        _write_csv(tmp_path, "statement-a.csv", BUY_DUOL)
        _write_csv(tmp_path, "statement-b.csv", BUY_DUOL)

        with caplog.at_level(logging.WARNING):
            service.import_folder(tmp_path, "lightyear")

        assert caplog.text == ""


class TestCommittedExample:
    """Parses docs/specs/lightyear-example.csv as committed.

    The only test that catches a regression in the leading-space header — a hand-built
    fixture would encode whatever header its author assumed.
    """

    def test_example_csv_yields_the_three_usd_buys(self, tmp_path: Path) -> None:
        service, repository, _ = _make_service({"DUOL.US", "PRGS.US", "GENI.US", "MRVL.US", "ASML.US"})
        # Copied byte for byte so the committed header, leading space included, is what is parsed
        (tmp_path / EXAMPLE_CSV.name).write_bytes(EXAMPLE_CSV.read_bytes())

        summary = service.import_folder(tmp_path, "lightyear")

        (f,) = summary.files
        assert (f.rows, f.buy_sell, f.matched, f.inserted) == (9, 4, 3, 3)
        assert f.skipped_currency == 1
        assert f.skipped_not_in_group == 0

        transactions = _inserted_transactions(repository)
        assert [(tx.ticker_code, tx.transaction_type) for tx in transactions] == [
            ("DUOL.US", "buy"),
            ("PRGS.US", "buy"),
            ("GENI.US", "buy"),
        ]
        for tx in transactions:
            assert tx.quantity * tx.price == tx.net_amount
            assert tx.net_amount + tx.fee == tx.gross_amount
