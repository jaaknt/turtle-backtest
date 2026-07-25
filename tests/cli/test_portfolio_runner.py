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
        assert args.benchmark_ticker == "QQQ.US"
        assert args.exit_param == []
        assert args.verbose is False

    def test_exit_params_are_repeatable(self) -> None:
        args = create_argument_parser().parse_args([*DATE_ARGS, "--exit-param", "holding_days=365", "--exit-param", "profit_target=15"])
        assert args.exit_param == [("holding_days", "365"), ("profit_target", "15")]

    def test_exit_param_without_equals_rejected(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args([*DATE_ARGS, "--exit-param", "holding_days"])

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

    def test_main_forwards_resolved_exit_params_to_the_service(self, mocker: MockerFixture) -> None:
        """Coerced by the exit strategy's initialize() signature, then handed to the SignalProcessor."""
        service = self._patch_wiring(mocker)
        mocker.patch("turtlex.cli.portfolio_runner.resolve_exit_strategy_kwargs", return_value={"holding_days": 365})
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS, "--exit-param", "holding_days=365"])

        assert main() == 0
        assert service.call_args.kwargs["exit_strategy_kwargs"] == {"holding_days": 365}

    def test_main_returns_one_on_unknown_exit_param(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        mocker.patch(
            "turtlex.cli.portfolio_runner.resolve_exit_strategy_kwargs",
            side_effect=ValueError("Unknown parameter 'nope' for BuyAndHoldExitStrategy"),
        )
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS, "--exit-param", "nope=1"])

        assert main() == 1

    def test_main_forwards_the_benchmark_ticker_to_the_service(self, mocker: MockerFixture) -> None:
        """The flag was previously parsed and dropped, leaving the tearsheet benchmark unconfigurable."""
        service = self._patch_wiring(mocker)
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS, "--benchmark-ticker", "SPY.US"])

        assert main() == 0
        assert service.call_args.kwargs["benchmark_ticker"] == "SPY.US"

    def test_main_uses_explicit_tickers_when_given(self, mocker: MockerFixture) -> None:
        service = self._patch_wiring(mocker)
        mocker.patch("sys.argv", ["portfolio-runner", *DATE_ARGS, "--tickers", "AAPL.US", "MSFT.US"])

        assert main() == 0
        assert service.return_value.run_backtest.call_args.kwargs["universe"] == ["AAPL.US", "MSFT.US"]
