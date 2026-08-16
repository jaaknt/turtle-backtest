"""Tests for turtlex/service/job_run_service.py JobRunRecorder."""

import logging
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from turtlex.service.job_run_service import JobRunRecorder, _jsonable


@pytest.fixture
def repository() -> MagicMock:
    repo = MagicMock()
    repo.start_run.return_value = 7
    return repo


class TestJsonable:
    def test_passes_through_json_native_types(self) -> None:
        assert _jsonable({"a": 1, "b": 1.5, "c": "s", "d": True, "e": None}) == {"a": 1, "b": 1.5, "c": "s", "d": True, "e": None}

    def test_converts_dates_to_iso(self) -> None:
        assert _jsonable(date(2024, 6, 1)) == "2024-06-01"

    def test_converts_paths_to_strings(self) -> None:
        assert _jsonable(Path("data/lightyear")) == "data/lightyear"

    def test_converts_key_value_tuples_to_lists(self) -> None:
        assert _jsonable([("sma_thresh", "0.20")]) == [["sma_thresh", "0.20"]]

    def test_falls_back_to_str_for_unknown_types(self) -> None:
        class Opaque:
            def __str__(self) -> str:
                return "opaque"

        assert _jsonable(Opaque()) == "opaque"

    def test_serializes_a_realistic_namespace(self) -> None:
        # Every type here comes out of a real parsed argparse namespace
        params = {"start_date": date(2024, 6, 1), "folder": Path("data"), "trading_param": [("k", "v")], "verbose": False}

        assert _jsonable(params) == {"start_date": "2024-06-01", "folder": "data", "trading_param": [["k", "v"]], "verbose": False}


class TestDisabled:
    def test_start_and_finish_do_nothing_without_a_repository(self) -> None:
        recorder = JobRunRecorder(None, "signal-runner", {"verbose": False})

        recorder.start()
        recorder.add_parameters("strategy", {"sma_thresh": 0.12})
        recorder.finish(0)

        # No handler may be left behind when logging is switched off
        assert not [h for h in logging.getLogger().handlers if h.__class__.__name__ == "_LastErrorCapture"]


class TestRecording:
    def test_start_records_the_cli_section(self, repository: MagicMock) -> None:
        recorder = JobRunRecorder(repository, "signal-runner", {"start_date": date(2024, 6, 1)})

        recorder.start()

        assert repository.start_run.call_args.kwargs["parameters"] == {"cli": {"start_date": "2024-06-01"}}
        assert repository.start_run.call_args.kwargs["name"] == "signal-runner"

    def test_finish_writes_success_for_exit_code_zero(self, repository: MagicMock) -> None:
        recorder = JobRunRecorder(repository, "signal-runner", {})

        recorder.start()
        recorder.finish(0)

        assert repository.finish_run.call_args.kwargs["status"] == "success"
        assert repository.finish_run.call_args.kwargs["exit_code"] == 0
        assert repository.finish_run.call_args.kwargs["error"] is None

    def test_finish_writes_failed_for_non_zero_exit_code(self, repository: MagicMock) -> None:
        recorder = JobRunRecorder(repository, "signal-runner", {})

        recorder.start()
        recorder.finish(1)

        assert repository.finish_run.call_args.kwargs["status"] == "failed"
        assert repository.finish_run.call_args.kwargs["run_id"] == 7

    def test_add_parameters_lands_in_the_finish_update(self, repository: MagicMock) -> None:
        recorder = JobRunRecorder(repository, "signal-runner", {"trading_strategy": "qullamaggie"})

        recorder.start()
        recorder.add_parameters("strategy", {"sma_thresh": 0.12})
        recorder.finish(0)

        assert repository.finish_run.call_args.kwargs["parameters"] == {
            "cli": {"trading_strategy": "qullamaggie"},
            "strategy": {"sma_thresh": 0.12},
        }


class TestErrorCapture:
    def test_captures_the_last_error_log_of_a_failed_run(self, repository: MagicMock) -> None:
        recorder = JobRunRecorder(repository, "signal-runner", {})

        recorder.start()
        logging.getLogger("turtlex.cli.signal_runner").error("Unknown trading strategy 'nope'")
        recorder.finish(1)

        assert repository.finish_run.call_args.kwargs["error"] == "Unknown trading strategy 'nope'"

    def test_ignores_earlier_errors_when_the_run_succeeds(self, repository: MagicMock) -> None:
        recorder = JobRunRecorder(repository, "signal-runner", {})

        recorder.start()
        logging.getLogger("httpx").error("transient blip")
        recorder.finish(0)

        assert repository.finish_run.call_args.kwargs["error"] is None

    def test_detaches_the_handler_after_finish(self, repository: MagicMock) -> None:
        before = list(logging.getLogger().handlers)
        recorder = JobRunRecorder(repository, "signal-runner", {})

        recorder.start()
        recorder.finish(0)

        assert logging.getLogger().handlers == before

    def test_detaches_the_handler_even_when_the_update_fails(self, repository: MagicMock) -> None:
        before = list(logging.getLogger().handlers)
        repository.finish_run.side_effect = SQLAlchemyError("connection lost")
        recorder = JobRunRecorder(repository, "signal-runner", {})

        recorder.start()
        recorder.finish(0)

        assert logging.getLogger().handlers == before


class TestFailureIsolation:
    def test_a_failing_start_makes_finish_skip_the_update(self, repository: MagicMock) -> None:
        # Also covers "does not propagate": neither call may raise for this to reach its assertion
        repository.start_run.side_effect = SQLAlchemyError("connection refused")
        recorder = JobRunRecorder(repository, "download-eodhd-data", {})

        recorder.start()
        recorder.finish(0)

        repository.finish_run.assert_not_called()

    def test_a_failing_start_is_logged_as_a_warning(self, repository: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        repository.start_run.side_effect = SQLAlchemyError("connection refused")
        recorder = JobRunRecorder(repository, "download-eodhd-data", {})

        with caplog.at_level(logging.WARNING):
            recorder.start()

        assert "Could not record start of job run 'download-eodhd-data'" in caplog.text
