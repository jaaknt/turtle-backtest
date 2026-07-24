"""Tests for the shared CLI bootstrap helpers used by backtest_runner and signal_runner."""

import argparse
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from turtlex.cli import common as common_cli
from turtlex.cli.common import build_common_analysis_parser, resolve_trading_strategy, run_cli


class TestBuildCommonAnalysisParser:
    def test_defaults(self) -> None:
        args = build_common_analysis_parser().parse_args(["--start-date", "2024-06-03", "--end-date", "2024-06-07"])
        assert args.trading_strategy == "darvas_box"
        assert args.ranking_strategy == "momentum"
        assert args.verbose is False

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
        args = argparse.Namespace(trading_strategy="darvas_box", ranking_strategy="momentum")

        result_strategy, result_bars_history = resolve_trading_strategy(args, MagicMock())

        assert result_strategy is trading_strategy
        assert result_bars_history is bars_history
        get_trading_strategy_mock.assert_called_once_with("darvas_box", ranking_strategy, bars_history)

    def test_propagates_value_error_for_unknown_strategy(self, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository")
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=MagicMock())
        mocker.patch("turtlex.cli.common.get_trading_strategy", side_effect=ValueError("Unknown trading strategy: nope"))
        args = argparse.Namespace(trading_strategy="nope", ranking_strategy="momentum")

        with pytest.raises(ValueError, match="Unknown trading strategy"):
            resolve_trading_strategy(args, MagicMock())


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
