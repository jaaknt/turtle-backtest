"""Tests for the signal-runner CLI: argument parsing, handlers, and main() wiring."""

from datetime import date
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from turtlex.cli.signal_runner import _INDICATOR_COLUMNS, create_argument_parser, format_signal_table, main, run_list
from turtlex.config.model import JobRunsConfig
from turtlex.model import Signal
from turtlex.strategy.trading.qullamaggie import QullamaggieStrategy

START, END = date(2024, 6, 3), date(2024, 6, 7)
DATE_ARGS = ["--start-date", "2024-06-03", "--end-date", "2024-06-07"]


def _signal(
    ticker: str,
    day: date,
    ranking: int,
    indicators: dict[str, float] | None = None,
    signal_close: float | None = None,
    next_open: float | None = None,
) -> Signal:
    return Signal(
        ticker=ticker,
        date=day,
        ranking=ranking,
        signal_close=signal_close,
        next_open=next_open,
        indicators=indicators or {},
    )


class TestArgumentParser:
    def test_dates_required(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args([])

    def test_defaults(self) -> None:
        args = create_argument_parser().parse_args(DATE_ARGS)
        assert args.trading_strategy == "qullamaggie"
        assert args.ranking_strategy == "qullamaggie"
        assert args.max_tickers == 10000
        assert args.min_signal_ranking == 0  # no gate unless asked for

    def test_invalid_trading_strategy_rejected(self) -> None:
        with pytest.raises(SystemExit):
            create_argument_parser().parse_args([*DATE_ARGS, "--trading-strategy", "nope"])


class TestHandlers:
    def test_run_list_prints_sorted_by_date_and_ticker(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.scan.return_value = [
            _signal("MSFT.US", END, 60),
            _signal("MSFT.US", START, 70),
            _signal("AAPL.US", START, 80),
        ]
        service.ticker_repo.get_sectors.return_value = {"AAPL.US": "Information Technology"}
        args = create_argument_parser().parse_args([*DATE_ARGS, "--max-tickers", "50"])

        assert run_list(service, args) == 0

        service.scan.assert_called_once_with(START, END, max_tickers=50)
        # two header lines, then one row per signal
        rows = capsys.readouterr().out.strip().splitlines()[2:]
        assert [row.split("│")[1].strip() for row in rows] == ["AAPL.US", "MSFT.US", "MSFT.US"]
        # the sector map really reaches the row, rather than the call being optimised away
        assert rows[0].split("│")[2].strip() == "Information Technology"

    def test_min_signal_ranking_drops_low_scores(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.scan.return_value = [
            _signal("LOW.US", START, 34),
            _signal("HIGH.US", START, 44),  # the gate is >=, so an exact match is kept
        ]
        service.ticker_repo.get_sectors.return_value = {}
        args = create_argument_parser().parse_args([*DATE_ARGS, "--min-signal-ranking", "44"])

        assert run_list(service, args) == 0

        rows = capsys.readouterr().out.strip().splitlines()[2:]
        assert [row.split("│")[1].strip() for row in rows] == ["HIGH.US"]

    def test_min_signal_ranking_zero_keeps_every_signal(self, capsys: pytest.CaptureFixture[str]) -> None:
        service = Mock()
        service.scan.return_value = [_signal("LOW.US", START, 1), _signal("HIGH.US", START, 100)]
        service.ticker_repo.get_sectors.return_value = {}
        args = create_argument_parser().parse_args(DATE_ARGS)

        assert run_list(service, args) == 0

        rows = capsys.readouterr().out.strip().splitlines()[2:]
        assert [row.split("│")[1].strip() for row in rows] == ["HIGH.US", "LOW.US"]


class TestFormatSignalTable:
    def test_next_open_blank_when_no_later_bar(self) -> None:
        """A signal on the newest bar has no next open yet; the rest of the row still renders."""
        signal = _signal("AAPL.US", START, 80, signal_close=199.93, next_open=None)
        cells = [c.strip() for c in format_signal_table([signal], {}).splitlines()[2].split("│")]

        assert cells[-2] == "199.93"
        assert cells[-1] == "--"

    def test_no_signals(self) -> None:
        assert format_signal_table([], {}) == "No signals in the requested period."

    def test_indicator_columns_match_strategy(self) -> None:
        """A drifted key renders "--" forever instead of failing, so pin the two lists together."""
        assert tuple(key for _, key, *_ in _INDICATOR_COLUMNS) == QullamaggieStrategy.REPORTED_INDICATORS

    def test_renders_every_column_in_order(self) -> None:
        signal = _signal(
            "AAPL.US",
            START,
            80,
            indicators={
                "pct_vs_sma50": 0.301,
                "adr_pct": 0.054,
                "adr_pct_change": 0.83,
                "vol_dry_up_ratio": 0.62,
                "rsi14": 50.5,
                "tight_range_ratio": 0.074,
                "roc_252d": 0.002,
            },
            signal_close=199.93,
            next_open=201.50,
        )
        table = format_signal_table([signal], {"AAPL.US": "Information Technology"}).splitlines()
        cells = [c.strip() for c in table[2].split("│")]

        # asserted by position, not substring: the column order is the point of this table
        assert cells == [
            "2024-06-03",
            "AAPL.US",
            "Information Technology",
            "+30.1%",  # pct_vs_sma50, scaled to a percent
            "5.4%",  # adr_pct, scaled
            "0.83",  # adr_pct_change, unscaled
            "0.62",  # vol_dry_up_ratio, unscaled
            "50.5",  # rsi14, unscaled
            "7.4%",  # tight_range_ratio, scaled
            "+0.2%",  # roc_252d, scaled
            "80",
            "199.93",
            "201.50",
        ]
        assert len(table[2]) == len(table[0])  # row and header stay aligned

    def test_missing_indicators_render_as_dashes(self) -> None:
        row = format_signal_table([_signal("AAPL.US", START, 80)], {}).splitlines()[2]

        cells = [c.strip() for c in row.split("│")]
        assert cells[2] == "--"  # sector
        assert cells[3:10] == ["--"] * 7  # every indicator column
        assert cells[10] == "80"  # Ranking is the one column every strategy fills
        assert cells[-2:] == ["--", "--"]  # Signal $ and Next Open $


class TestMain:
    def _patch_wiring(self, mocker: MockerFixture) -> None:
        settings_cls = mocker.patch("turtlex.cli.signal_runner.Settings")
        # Without this settings.job_runs.enabled is a truthy MagicMock, so every test
        # would take the enabled branch and shell out to git via resolve_version()
        settings_cls.from_toml.return_value.job_runs = JobRunsConfig(enabled=False)
        mocker.patch("turtlex.cli.signal_runner.setup_logging")
        mocker.patch("turtlex.cli.signal_runner.TickerQueryRepository")

    def test_main_returns_zero_on_success(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_universe.return_value = ["AAPL.US"]
        strategy.get_signals.return_value = []
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", *DATE_ARGS])

        assert main() == 0
        strategy.get_signals.assert_called_once_with("AAPL.US", START, END)

    def test_main_returns_one_on_factory_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", side_effect=ValueError("Unknown trading strategy"))
        mocker.patch("sys.argv", ["signal-runner", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_unexpected_error(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_universe.return_value = ["AAPL.US"]
        strategy.get_signals.side_effect = RuntimeError("db down")
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", *DATE_ARGS])

        assert main() == 1

    def test_main_returns_one_on_keyboard_interrupt(self, mocker: MockerFixture) -> None:
        self._patch_wiring(mocker)
        strategy = MagicMock()
        strategy.get_universe.return_value = ["AAPL.US"]
        strategy.get_signals.side_effect = KeyboardInterrupt
        mocker.patch("turtlex.cli.signal_runner.resolve_trading_strategy", return_value=(strategy, MagicMock()))
        mocker.patch("sys.argv", ["signal-runner", *DATE_ARGS])

        assert main() == 1
