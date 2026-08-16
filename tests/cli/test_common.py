"""Tests for the shared CLI bootstrap helpers used by backtest_runner and signal_runner."""

import argparse
import logging
from datetime import date
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from turtlex.cli import common as common_cli
from turtlex.cli.common import build_common_analysis_parser, resolve_trading_strategy, run_cli, run_job
from turtlex.config.model import JobRunsConfig
from turtlex.service.job_run_service import JobRunRecorder


class TestBuildCommonAnalysisParser:
    def test_defaults(self) -> None:
        args = build_common_analysis_parser().parse_args(["--start-date", "2024-06-03", "--end-date", "2024-06-07"])
        assert args.trading_strategy == "darvas_box"
        assert args.ranking_strategy == "momentum"
        assert args.trading_param == []
        assert args.verbose is False

    def test_parses_repeated_trading_params(self) -> None:
        args = build_common_analysis_parser().parse_args(
            [
                "--start-date",
                "2024-06-03",
                "--end-date",
                "2024-06-07",
                "--trading-param",
                "sma_thresh=0.2",
                "--trading-param",
                "min_bars=120",
            ]
        )
        assert args.trading_param == [("sma_thresh", "0.2"), ("min_bars", "120")]

    def test_rejects_trading_param_without_equals(self) -> None:
        with pytest.raises(SystemExit):
            build_common_analysis_parser().parse_args(
                ["--start-date", "2024-06-03", "--end-date", "2024-06-07", "--trading-param", "sma_thresh"]
            )

    def test_requires_dates(self) -> None:
        with pytest.raises(SystemExit):
            build_common_analysis_parser().parse_args([])

    def test_rejects_unknown_trading_strategy(self) -> None:
        with pytest.raises(SystemExit):
            build_common_analysis_parser().parse_args(
                ["--start-date", "2024-06-03", "--end-date", "2024-06-07", "--trading-strategy", "nope"]
            )

    def test_rejects_unknown_ranking_strategy(self) -> None:
        with pytest.raises(SystemExit):
            build_common_analysis_parser().parse_args(
                ["--start-date", "2024-06-03", "--end-date", "2024-06-07", "--ranking-strategy", "nope"]
            )


class TestResolveTradingStrategy:
    def test_builds_trading_strategy_from_args(self, mocker: MockerFixture) -> None:
        bars_history = MagicMock()
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository", return_value=bars_history)
        ranking_strategy = MagicMock()
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=ranking_strategy)
        trading_strategy = MagicMock()
        get_trading_strategy_mock = mocker.patch("turtlex.cli.common.get_trading_strategy", return_value=trading_strategy)
        args = argparse.Namespace(trading_strategy="darvas_box", ranking_strategy="momentum", trading_param=[])

        result_strategy, result_bars_history = resolve_trading_strategy(args, MagicMock(), MagicMock())

        assert result_strategy is trading_strategy
        assert result_bars_history is bars_history
        get_trading_strategy_mock.assert_called_once_with("darvas_box", ranking_strategy, bars_history, [])

    def test_forwards_trading_param_overrides(self, mocker: MockerFixture) -> None:
        bars_history = MagicMock()
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository", return_value=bars_history)
        ranking_strategy = MagicMock()
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=ranking_strategy)
        get_trading_strategy_mock = mocker.patch("turtlex.cli.common.get_trading_strategy", return_value=MagicMock())
        params = [("sma_thresh", "0.2")]
        args = argparse.Namespace(trading_strategy="qullamaggie", ranking_strategy="qullamaggie", trading_param=params)

        resolve_trading_strategy(args, MagicMock(), MagicMock())

        get_trading_strategy_mock.assert_called_once_with("qullamaggie", ranking_strategy, bars_history, params)

    def test_logs_resolved_strategy_parameters(self, mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository", return_value=MagicMock())
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=MagicMock())
        trading_strategy = MagicMock()
        trading_strategy.describe_parameters.return_value = {"sma_thresh": 0.2, "rsi_cap": 70.0}
        mocker.patch("turtlex.cli.common.get_trading_strategy", return_value=trading_strategy)
        args = argparse.Namespace(trading_strategy="qullamaggie", ranking_strategy="qullamaggie", trading_param=[])

        with caplog.at_level(logging.INFO, logger="turtlex.cli.common"):
            resolve_trading_strategy(args, MagicMock(), MagicMock())

        assert "qullamaggie parameters: sma_thresh=0.2, rsi_cap=70.0" in caplog.text

    def test_records_resolved_parameters_on_the_job_run(self, mocker: MockerFixture) -> None:
        # The same dict reaches both sinks, so the log and the job_runs row cannot drift apart
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository", return_value=MagicMock())
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=MagicMock())
        trading_strategy = MagicMock()
        trading_strategy.describe_parameters.return_value = {"sma_thresh": 0.2}
        mocker.patch("turtlex.cli.common.get_trading_strategy", return_value=trading_strategy)
        args = argparse.Namespace(trading_strategy="qullamaggie", ranking_strategy="qullamaggie", trading_param=[])
        recorder = MagicMock()

        resolve_trading_strategy(args, MagicMock(), recorder)

        recorder.add_parameters.assert_called_once_with("strategy", {"sma_thresh": 0.2})
        trading_strategy.describe_parameters.assert_called_once()

    def test_propagates_value_error_for_unknown_strategy(self, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository")
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=MagicMock())
        mocker.patch("turtlex.cli.common.get_trading_strategy", side_effect=ValueError("Unknown trading strategy: nope"))
        args = argparse.Namespace(trading_strategy="nope", ranking_strategy="momentum", trading_param=[])

        with pytest.raises(ValueError, match="Unknown trading strategy"):
            resolve_trading_strategy(args, MagicMock(), MagicMock())


class TestRunCli:
    def test_returns_body_result_on_success(self) -> None:
        assert run_cli(argparse.Namespace(verbose=False), lambda: 0) == 0

    def test_catches_keyboard_interrupt(self) -> None:
        def body() -> int:
            raise KeyboardInterrupt

        assert run_cli(argparse.Namespace(verbose=False), body) == 1

    def test_catches_unexpected_exception(self) -> None:
        def body() -> int:
            raise RuntimeError("boom")

        assert run_cli(argparse.Namespace(verbose=False), body) == 1

    def test_logs_full_traceback_only_when_verbose(self, mocker: MockerFixture) -> None:
        exception_spy = mocker.spy(common_cli.logger, "exception")

        def body() -> int:
            raise RuntimeError("boom")

        run_cli(argparse.Namespace(verbose=True), body)

        exception_spy.assert_called_once()


class TestRunJob:
    @pytest.fixture
    def settings(self) -> MagicMock:
        settings = MagicMock()
        settings.job_runs = JobRunsConfig(enabled=True)
        return settings

    @pytest.fixture
    def repository(self, mocker: MockerFixture) -> MagicMock:
        repository = MagicMock()
        repository.start_run.return_value = 7
        mocker.patch.object(common_cli, "JobRunRepository", return_value=repository)
        return repository

    def test_returns_the_body_exit_code(self, settings: MagicMock, repository: MagicMock) -> None:
        assert run_job("signal-runner", argparse.Namespace(verbose=False), settings, lambda _recorder: 0) == 0

    def test_records_success_for_exit_code_zero(self, settings: MagicMock, repository: MagicMock) -> None:
        run_job("signal-runner", argparse.Namespace(verbose=False), settings, lambda _recorder: 0)

        assert repository.finish_run.call_args.kwargs["status"] == "success"

    def test_records_failed_for_a_non_zero_exit_code(self, settings: MagicMock, repository: MagicMock) -> None:
        run_job("signal-runner", argparse.Namespace(verbose=False), settings, lambda _recorder: 1)

        assert repository.finish_run.call_args.kwargs["status"] == "failed"
        assert repository.finish_run.call_args.kwargs["exit_code"] == 1

    def test_a_raising_body_still_finishes_the_row(self, settings: MagicMock, repository: MagicMock) -> None:
        def body(_recorder: JobRunRecorder) -> int:
            raise RuntimeError("boom")

        assert run_job("signal-runner", argparse.Namespace(verbose=False), settings, body) == 1
        # run_cli logs the exception before returning 1, which is how the error text is captured
        assert repository.finish_run.call_args.kwargs["status"] == "failed"
        assert "boom" in repository.finish_run.call_args.kwargs["error"]

    def test_body_receives_the_recorder_and_its_sections_are_stored(self, settings: MagicMock, repository: MagicMock) -> None:
        def body(recorder: JobRunRecorder) -> int:
            recorder.add_parameters("strategy", {"sma_thresh": 0.12})
            return 0

        run_job("signal-runner", argparse.Namespace(verbose=False), settings, body)

        assert repository.finish_run.call_args.kwargs["parameters"]["strategy"] == {"sma_thresh": 0.12}

    def test_cli_arguments_are_recorded(self, settings: MagicMock, repository: MagicMock) -> None:
        args = argparse.Namespace(verbose=False, start_date=date(2024, 6, 1))

        run_job("signal-runner", args, settings, lambda _recorder: 0)

        assert repository.start_run.call_args.kwargs["parameters"] == {"cli": {"verbose": False, "start_date": "2024-06-01"}}

    def test_writes_nothing_when_disabled(self, mocker: MockerFixture) -> None:
        settings = MagicMock()
        settings.job_runs = JobRunsConfig(enabled=False)
        repository_cls = mocker.patch.object(common_cli, "JobRunRepository")

        assert run_job("signal-runner", argparse.Namespace(verbose=False), settings, lambda _recorder: 0) == 0

        repository_cls.assert_not_called()
