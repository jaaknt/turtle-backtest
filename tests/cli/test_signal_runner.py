"""Tests for the signal-runner CLI: argument parsing, handlers, and main() wiring."""

from datetime import date
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from turtlex.cli.signal_runner import create_argument_parser, main, run_list, run_signal, run_top
from turtlex.model import Signal

START, END = date(2024, 6, 3), date(2024, 6, 7)
DATE_ARGS = ["--start-date", "2024-06-03", "--end-date", "2024-06-07"]


def _signal(ticker: str, day: date, ranking: int) -> Signal:
    return Signal(ticker=ticker, date=day, ranking=ranking)


class TestArgumentParser:
    def test_subcommand_is_required(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args([])

    def test_signal_requires_tickers(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args(["signal", *DATE_ARGS])

    def test_signal_parses_tickers_and_dates(self) -> None:
        args = create_argument_parser().parse_args(["signal", "AAPL.US", "MSFT.US", *DATE_ARGS])
        assert args.tickers == ["AAPL.US", "MSFT.US"]
        assert args.start_date == START
        assert args.end_date == END
        assert args.handler is run_signal

    def test_defaults(self) -> None:
        args = create_argument_parser().parse_args(["list", *DATE_ARGS])
        assert args.trading_strategy == "darvas_box"
        assert args.ranking_strategy == "momentum"
        assert args.max_tickers == 10000
        assert args.handler is run_list

    def test_top_limit_default(self) -> None:
        args = create_argument_parser().parse_args(["top", *DATE_ARGS])
        assert args.limit == 20
        assert args.handler is run_top

    def test_invalid_trading_strategy_rejected(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args(["list", *DATE_ARGS, "--trading-strategy", "nope"])

    def test_max_tickers_not_available_on_signal(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args(["signal", "AAPL.US", *DATE_ARGS, "--max-tickers", "5"])


class TestHandlers:
    def test_run_list_prints_sorted_by_date_and_ticker(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.scan.return_value = [
            _signal("MSFT.US", END, 60),
            _signal("MSFT.US", START, 70),
            _signal("AAPL.US", START, 80),
        ]
        args = create_argument_parser().parse_args(["list", *DATE_ARGS, "--max-tickers", "50"])

        assert run_list(service, args) == 0

        service.scan.assert_called_once_with(START, END, max_tickers=50)
        lines = capsys.readouterr().out.strip().splitlines()
        assert [line.split()[2] for line in lines] == ["AAPL.US", "MSFT.US", "MSFT.US"]

    def test_run_top_prints_top_ranked_within_limit(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.scan.return_value = [_signal(f"T{i}.US", START, i) for i in (10, 90, 50)]
        args = create_argument_parser().parse_args(["top", *DATE_ARGS, "--limit", "2"])

        assert run_top(service, args) == 0

        lines = capsys.readouterr().out.strip().splitlines()
        assert [line.split()[2] for line in lines] == ["T90.US", "T50.US"]

    def test_run_signal_queries_each_ticker(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.trading_strategy.get_signals.side_effect = lambda ticker, start, end: (
            [_signal(ticker, START, 42)] if ticker == "AAPL.US" else []
        )
        args = create_argument_parser().parse_args(["signal", "AAPL.US", "MSFT.US", *DATE_ARGS])

        assert run_signal(service, args) == 0

        assert service.trading_strategy.get_signals.call_count == 2
        out = capsys.readouterr().out
        assert "AAPL.US" in out
        assert "MSFT.US" not in out


class TestMain:
    def _patch_wiring(self, mocker: MockerFixture) -> None:
        mocker.patch("turtlex.cli.signal_runner.Settings")
        mocker.patch("turtlex.cli.signal_runner.LogConfig")
        mocker.patch("turtlex.cli.signal_runner.TickerQueryRepository")

    def test_main_returns_zero_on_success(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_signals.return_value = []
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", "signal", "AAPL.US", *DATE_ARGS])

        assert main() == 0
        strategy.get_signals.assert_called_once_with("AAPL.US", START, END)

    def test_main_returns_one_on_factory_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", side_effect=ValueError("Unknown trading strategy"))
        mocker.patch("sys.argv", ["signal-runner", "list", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_unexpected_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_signals.side_effect = RuntimeError("db down")
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", "signal", "AAPL.US", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_keyboard_interrupt(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_signals.side_effect = KeyboardInterrupt
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", "signal", "AAPL.US", *DATE_ARGS])

        assert main() == 1
