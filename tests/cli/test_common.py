"""Tests for the shared CLI bootstrap helpers used by backtest_runner and signal_runner."""

import argparse
import logging
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

        result_strategy, result_bars_history = resolve_trading_strategy(args, MagicMock())

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

        resolve_trading_strategy(args, MagicMock())

        get_trading_strategy_mock.assert_called_once_with("qullamaggie", ranking_strategy, bars_history, params)

    def test_logs_resolved_strategy_parameters(self, mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository", return_value=MagicMock())
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=MagicMock())
        trading_strategy = MagicMock()
        trading_strategy.describe_parameters.return_value = {"sma_thresh": 0.2, "rsi_cap": 70.0}
        mocker.patch("turtlex.cli.common.get_trading_strategy", return_value=trading_strategy)
        args = argparse.Namespace(trading_strategy="qullamaggie", ranking_strategy="qullamaggie", trading_param=[])

        with caplog.at_level(logging.INFO, logger="turtlex.cli.common"):
            resolve_trading_strategy(args, MagicMock())

        assert "qullamaggie parameters: sma_thresh=0.2, rsi_cap=70.0" in caplog.text

    def test_propagates_value_error_for_unknown_strategy(self, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.cli.common.DailyBarsQueryRepository")
        mocker.patch("turtlex.cli.common.get_ranking_strategy", return_value=MagicMock())
        mocker.patch("turtlex.cli.common.get_trading_strategy", side_effect=ValueError("Unknown trading strategy: nope"))
        args = argparse.Namespace(trading_strategy="nope", ranking_strategy="momentum", trading_param=[])

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
