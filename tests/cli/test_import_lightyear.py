"""Tests for the lightyear-import CLI: argument parsing and main() wiring."""

import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from turtlex.cli.import_lightyear import create_argument_parser, main
from turtlex.config.model import JobRunsConfig
from turtlex.service.lightyear_service import FileImportSummary, ImportSummary, TickerGroupNotSeededError


class TestArgumentParser:
    def test_defaults(self) -> None:
        args = create_argument_parser().parse_args([])
        assert args.folder == Path("data/lightyear")
        assert args.ticker_group == "lightyear"
        assert args.verbose is False

    def test_overrides(self) -> None:
        args = create_argument_parser().parse_args(["--folder", "/tmp/ly", "--ticker-group", "other", "--verbose"])
        assert args.folder == Path("/tmp/ly")
        assert args.ticker_group == "other"
        assert args.verbose is True


class TestMain:
    def _patch_wiring(self, mocker: MockerFixture, summary: ImportSummary | Exception) -> MockerFixture:
        settings_cls = mocker.patch("turtlex.cli.import_lightyear.Settings")
        # Without this settings.job_runs.enabled is a truthy MagicMock, so every test
        # would take the enabled branch and shell out to git via resolve_version()
        settings_cls.from_toml.return_value.job_runs = JobRunsConfig(enabled=False)
        mocker.patch("turtlex.cli.import_lightyear.setup_logging")
        mocker.patch("turtlex.cli.import_lightyear.LightyearRepository")
        mocker.patch("turtlex.cli.import_lightyear.TickerQueryRepository")
        service_cls = mocker.patch("turtlex.cli.import_lightyear.LightyearService")
        if isinstance(summary, Exception):
            service_cls.return_value.import_folder.side_effect = summary
        else:
            service_cls.return_value.import_folder.return_value = summary
        return service_cls

    def test_main_returns_zero_and_logs_summary(self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        summary = ImportSummary(files=[FileImportSummary(file_name="statement.csv", rows=51, buy_sell=14, matched=12, inserted=3)])
        service_cls = self._patch_wiring(mocker, summary)
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path)])

        with caplog.at_level(logging.INFO):
            assert main() == 0

        service_cls.return_value.import_folder.assert_called_once_with(tmp_path, "lightyear")
        assert "statement.csv: 51 rows, 14 buy/sell, 12 matched, 3 inserted, 9 already stored" in caplog.text

    def test_main_warns_about_unseeded_symbols(self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        summary = ImportSummary(
            files=[
                FileImportSummary(
                    file_name="statement.csv",
                    rows=10,
                    buy_sell=4,
                    matched=2,
                    inserted=2,
                    skipped_not_in_group=2,
                    unseeded_symbols={"NVDA.US", "AMD.US"},
                )
            ]
        )
        self._patch_wiring(mocker, summary)
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path)])

        with caplog.at_level(logging.WARNING):
            assert main() == 0

        assert "skipped 2 USD buy/sell rows for symbols not in group 'lightyear': AMD.US, NVDA.US" in caplog.text

    def test_main_returns_zero_and_warns_on_empty_folder(
        self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        self._patch_wiring(mocker, ImportSummary())
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path)])

        with caplog.at_level(logging.WARNING):
            assert main() == 0

        assert "No CSV files found" in caplog.text

    def test_main_returns_one_on_missing_folder(self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        service_cls = self._patch_wiring(mocker, ImportSummary())
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path / "nope")])

        with caplog.at_level(logging.ERROR):
            assert main() == 1

        service_cls.return_value.import_folder.assert_not_called()
        assert "Folder does not exist" in caplog.text

    def test_main_returns_one_on_empty_ticker_group(self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        self._patch_wiring(mocker, TickerGroupNotSeededError("Ticker group 'lightyear' is empty"))
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path)])

        with caplog.at_level(logging.ERROR):
            assert main() == 1

        assert "seed turtle.ticker_group" in caplog.text

    def test_main_returns_one_when_a_file_failed_but_still_reports_the_good_ones(
        self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        summary = ImportSummary(
            files=[
                FileImportSummary(file_name="broken.csv", failed=True),
                FileImportSummary(file_name="good.csv", rows=9, buy_sell=4, matched=3, inserted=3),
            ]
        )
        self._patch_wiring(mocker, summary)
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path)])

        with caplog.at_level(logging.INFO):
            assert main() == 1

        # The healthy file's numbers must survive the failure, not be replaced by it
        assert "good.csv: 9 rows, 4 buy/sell, 3 matched, 3 inserted, 0 already stored" in caplog.text
        assert "broken.csv: FAILED to parse" in caplog.text
        assert "1 of 2 files could not be parsed" in caplog.text

    def test_main_does_not_report_a_parse_error_as_a_seeding_problem(
        self, mocker: MockerFixture, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # A bare ValueError is not swallowed by the ticker-group handler. It reaches run_cli via
        # run_job, which reports it as-is and exits 1 rather than letting a raw traceback escape.
        self._patch_wiring(mocker, ValueError("time data '07/31/2026' does not match format"))
        mocker.patch("sys.argv", ["lightyear-import", "--folder", str(tmp_path)])

        with caplog.at_level(logging.ERROR):
            assert main() == 1

        assert "does not match format" in caplog.text
        assert "seed turtle.ticker_group" not in caplog.text
