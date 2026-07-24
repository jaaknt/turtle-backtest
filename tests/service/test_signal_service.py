"""Tests for SignalService universe scanning and signal delegation."""

from datetime import date
from unittest.mock import Mock

from turtlex.model import Signal
from turtlex.service.signal_service import SignalService

START = date(2024, 6, 3)
END = date(2024, 6, 7)


def _make_service(universe: list[str], signals_by_ticker: dict[str, list[Signal]]) -> tuple[SignalService, Mock, Mock]:
    trading_strategy = Mock()
    trading_strategy.get_universe.return_value = universe
    trading_strategy.get_signals.side_effect = lambda ticker, start_date, end_date: signals_by_ticker.get(ticker, [])
    ticker_repo = Mock()
    return SignalService(trading_strategy=trading_strategy, ticker_repo=ticker_repo), trading_strategy, ticker_repo


def test_scan_aggregates_signals_across_universe() -> None:
    signals_by_ticker = {
        "AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=80)],
        "MSFT.US": [
            Signal(ticker="MSFT.US", date=START, ranking=60),
            Signal(ticker="MSFT.US", date=END, ranking=70),
        ],
    }
    service, trading_strategy, _ = _make_service(["AAPL.US", "MSFT.US", "NVDA.US"], signals_by_ticker)

    signals = service.scan(START, END)

    assert [s.ticker for s in signals] == ["AAPL.US", "MSFT.US", "MSFT.US"]
    assert trading_strategy.get_signals.call_count == 3


def test_scan_passes_max_tickers_as_universe_limit() -> None:
    service, trading_strategy, ticker_repo = _make_service([], {})

    service.scan(START, END, max_tickers=50)

    trading_strategy.get_universe.assert_called_once_with(ticker_repo, limit=50)


def test_scan_empty_universe_returns_no_signals() -> None:
    service, trading_strategy, _ = _make_service([], {})

    assert service.scan(START, END) == []
    trading_strategy.get_signals.assert_not_called()


def test_scan_explicit_tickers_bypasses_universe_resolution() -> None:
    signals_by_ticker = {"AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=80)]}
    service, trading_strategy, _ = _make_service(["MSFT.US"], signals_by_ticker)

    signals = service.scan(START, END, tickers=["AAPL.US"])

    assert [s.ticker for s in signals] == ["AAPL.US"]
    trading_strategy.get_universe.assert_not_called()


def test_scan_empty_tickers_list_falls_back_to_universe() -> None:
    service, trading_strategy, ticker_repo = _make_service(["MSFT.US"], {})

    service.scan(START, END, tickers=[])

    trading_strategy.get_universe.assert_called_once_with(ticker_repo, limit=None)


def test_scan_ignores_max_tickers_when_tickers_given() -> None:
    signals_by_ticker = {"AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=80)]}
    service, trading_strategy, _ = _make_service(["MSFT.US"], signals_by_ticker)

    signals = service.scan(START, END, max_tickers=5, tickers=["AAPL.US"])

    assert [s.ticker for s in signals] == ["AAPL.US"]
    trading_strategy.get_universe.assert_not_called()
