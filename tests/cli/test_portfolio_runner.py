"""Tests for the portfolio-runner CLI: argument parsing and main() wiring."""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from turtlex.cli.portfolio_runner import create_argument_parser, main

DATE_ARGS = ["--start-date", "2024-01-01", "--end-date", "2024-03-31"]


class TestArgumentParser:
    def test_dates_required(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args([])

    def test_defaults(self) -> None:
        args = create_argument_parser().parse_args(DATE_ARGS)
        assert args.trading_strategy == "darvas_box"
        assert args.ranking_strategy == "momentum"
        assert args.exit_strategy == "buy_and_hold"
        assert args.initial_capital == 30000.0
        assert args.min_signal_ranking == 70
        assert args.max_holding_days == 365
        assert args.verbose is False

    def test_shared_and_portfolio_flags_coexist(self) -> None:
        args = create_argument_parser().parse_args([*DATE_ARGS, "--verbose", "--exit-strategy", "atr", "--initial-capital", "50000"])
        assert args.verbose is True
        assert args.exit_strategy == "atr"
        assert args.initial_capital == 50000.0

    def test_invalid_exit_strategy_rejected(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args([*DATE_ARGS, "--exit-strategy", "nope"])


class TestMain:
    def _patch_wiring(self, mocker: MockerFixture) -> MagicMock:
        mocker.patch("turtlex.cli.portfolio_runner.Settings")
        mocker.patch("turtlex.cli.portfolio_runner.setup_logging")
        mocker.patch("turtlex.cli.portfolio_runner.TickerQueryRepository")
        mocker.patch("turtlex.cli.portfolio_runner.get_exit_strategy")
        strategy = MagicMock()
        strategy.get_universe.return_value = ["AAPL.US"]
        mocker.patch("turtlex.cli.portfolio_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        return mocker.patch("turtlex.cli.portfolio_runner.PortfolioService")

    def test_main_returns_zero_on_success(self, mocker: MockerFixture) -> None:
        service = self._patch_wiring(mocker)
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS])

        assert main() == 0
        service.return_value.run_backtest.assert_called_once()

    def test_main_returns_one_on_factory_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        mocker.patch("turtlex.cli.portfolio_runner.resolve_trading_strategy", side_effect=ValueError("Unknown exit strategy"))
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_unexpected_error(self, mocker: MockerFixture) -> None:
        service = self._patch_wiring(mocker)
        service.return_value.run_backtest.side_effect = RuntimeError("db down")
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_keyboard_interrupt(self, mocker: MockerFixture) -> None:
        service = self._patch_wiring(mocker)
        service.return_value.run_backtest.side_effect = KeyboardInterrupt
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS])

        assert main() == 1

    def test_main_uses_explicit_tickers_when_given(self, mocker: MockerFixture) -> None:
        service = self._patch_wiring(mocker)
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS, "--tickers", "AAPL.US", "MSFT.US"])

        assert main() == 0
        assert service.return_value.run_backtest.call_args.kwargs["universe"] == ["AAPL.US", "MSFT.US"]
