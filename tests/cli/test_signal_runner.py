"""Tests for the signal-runner CLI: argument parsing, handlers, and main() wiring."""

from datetime import date
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from turtlex.cli.signal_runner import create_argument_parser, main, run_signal
from turtlex.model import Signal

START, END = date(2024, 6, 3), date(2024, 6, 7)
DATE_ARGS = ["--start-date", "2024-06-03", "--end-date", "2024-06-07"]


def _signal(ticker: str, day: date, ranking: int) -> Signal:
    return Signal(ticker=ticker, date=day, ranking=ranking)


class TestArgumentParser:
    def test_tickers_required(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args(DATE_ARGS)

    def test_dates_required(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args(["AAPL.US"])

    def test_parses_tickers_and_dates(self) -> None:
        args = create_argument_parser().parse_args(["AAPL.US", "MSFT.US", *DATE_ARGS])
        assert args.tickers == ["AAPL.US", "MSFT.US"]
        assert args.start_date == START
        assert args.end_date == END

    def test_defaults(self) -> None:
        args = create_argument_parser().parse_args(["AAPL.US", *DATE_ARGS])
        assert args.trading_strategy == "darvas_box"
        assert args.ranking_strategy == "momentum"

    def test_invalid_trading_strategy_rejected(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args(["AAPL.US", *DATE_ARGS, "--trading-strategy", "nope"])


class TestHandlers:
    def test_run_signal_queries_each_ticker(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.trading_strategy.get_signals.side_effect = lambda ticker, start, end: (
            [_signal(ticker, START, 42)] if ticker == "AAPL.US" else []
        )
        args = create_argument_parser().parse_args(["AAPL.US", "MSFT.US", *DATE_ARGS])

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
        mocker.patch("sys.argv", ["signal-runner", "AAPL.US", *DATE_ARGS])

        assert main() == 0
        strategy.get_signals.assert_called_once_with("AAPL.US", START, END)

    def test_main_returns_one_on_factory_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", side_effect=ValueError("Unknown trading strategy"))
        mocker.patch("sys.argv", ["signal-runner", "AAPL.US", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_unexpected_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_signals.side_effect = RuntimeError("db down")
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", "AAPL.US", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_keyboard_interrupt(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_signals.side_effect = KeyboardInterrupt
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", "AAPL.US", *DATE_ARGS])

        assert main() == 1
