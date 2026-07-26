"""Tests for PortfolioService's entry-signal generation."""

import logging
from datetime import date
from unittest.mock import Mock

import pytest

from turtlex.model import FutureTrade, Signal, Trade
from turtlex.service.portfolio_service import MIN_CASH_FOR_ENTRY, PortfolioService

START = date(2024, 1, 2)
END = date(2024, 3, 1)


def _open_position(service: PortfolioService, ticker: str) -> None:
    """Open a position so further signals for that ticker are excluded."""
    entry = Trade(ticker=ticker, date=START, price=100.0, reason="next_day_open")
    exit_ = Trade(ticker=ticker, date=START, price=100.0, reason="open")
    service.portfolio_manager.open_position(entry=entry, exit=exit_, position_size=1)


def _future_trade(ticker: str, price: float) -> FutureTrade:
    """Build a FutureTrade priced so position sizing decides whether it can be taken."""
    return FutureTrade(
        signal=Signal(ticker=ticker, date=START, ranking=80),
        entry=Trade(ticker=ticker, date=START, price=price, reason="next_day_open"),
        exit=Trade(ticker=ticker, date=END, price=price, reason="max_holding_period"),
        benchmark_list=[],
    )


def _make_service(signals_by_ticker: dict[str, list[Signal]], min_signal_ranking: int = 40) -> PortfolioService:
    trading_strategy = Mock()
    trading_strategy.get_signals.side_effect = lambda ticker, start_date, end_date: signals_by_ticker.get(ticker, [])
    service = PortfolioService(
        trading_strategy=trading_strategy,
        exit_strategy=Mock(),
        bars_history=Mock(),
        start_date=START,
        end_date=END,
        min_signal_ranking=min_signal_ranking,
    )
    service.portfolio_manager.record_daily_snapshot(START)
    return service


def test_generate_entry_signals_filters_by_ranking_and_sorts_descending() -> None:
    signals_by_ticker = {
        "AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=60)],  # below threshold
        "MSFT.US": [Signal(ticker="MSFT.US", date=START, ranking=80)],
        "NVDA.US": [Signal(ticker="NVDA.US", date=START, ranking=90)],
    }
    service = _make_service(signals_by_ticker, min_signal_ranking=70)

    signals = service._generate_entry_signals(START, ["AAPL.US", "MSFT.US", "NVDA.US"])

    assert [s.ticker for s in signals] == ["NVDA.US", "MSFT.US"]


def test_generate_entry_signals_excludes_existing_positions() -> None:
    signals_by_ticker = {"AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=80)]}
    service = _make_service(signals_by_ticker)
    _open_position(service, "AAPL.US")

    signals = service._generate_entry_signals(START, ["AAPL.US"])

    assert signals == []


def test_generate_entry_signals_does_not_cap_the_number_of_entries() -> None:
    """Position count is bounded by cash alone; the selector imposes no slot limit."""
    tickers = [f"T{i}.US" for i in range(12)]
    signals_by_ticker = {t: [Signal(ticker=t, date=START, ranking=80 + i)] for i, t in enumerate(tickers)}
    service = _make_service(signals_by_ticker)

    signals = service._generate_entry_signals(START, tickers)

    assert [s.ticker for s in signals] == [f"T{i}.US" for i in range(11, -1, -1)]  # all 12, highest ranked first


def test_generate_entry_signals_skips_the_universe_sweep_when_cash_is_low() -> None:
    """Walking the universe costs a query per ticker, so it is gated on having cash to deploy."""
    signals_by_ticker = {"AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=99)]}
    service = _make_service(signals_by_ticker)
    service.portfolio_manager.current_snapshot.cash = MIN_CASH_FOR_ENTRY - 1

    assert service._generate_entry_signals(START, ["AAPL.US"]) == []
    service.trading_strategy.get_signals.assert_not_called()  # type: ignore[attr-defined]


def test_generate_entry_signals_logs_generated_and_selected_counts(caplog: pytest.LogCaptureFixture) -> None:
    """The old message reported survivors as if they were strategy output, hiding the ranking filter."""
    signals_by_ticker = {
        "AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=30)],  # below threshold
        "MSFT.US": [Signal(ticker="MSFT.US", date=START, ranking=80)],
    }
    service = _make_service(signals_by_ticker)

    with caplog.at_level(logging.INFO):
        service._generate_entry_signals(START, ["AAPL.US", "MSFT.US"])

    assert "Generated 2 signals" in caplog.text
    assert "1 selected for entry" in caplog.text
    assert "ranking >= 40" in caplog.text


def test_process_signals_skips_unfundable_entries_without_stopping_the_loop() -> None:
    """A skipped entry stays out of the trade log, and must not block later affordable entries."""
    service = _make_service({})
    # Default sizing: 4% of $30,000 = a $1,200 target, so one $5,000 share cannot be bought.
    trades = {"RICH.US": _future_trade("RICH.US", 5000.0), "CHEAP.US": _future_trade("CHEAP.US", 100.0)}
    service.signal_processor.run = Mock(side_effect=lambda signal, end_date: trades[signal.ticker])  # type: ignore[method-assign]

    service._process_signals([trades["RICH.US"].signal, trades["CHEAP.US"].signal], START, END)

    assert [t.entry.ticker for t in service.portfolio_manager.state.future_trades] == ["CHEAP.US"]
    assert [p.ticker for p in service.portfolio_manager.current_snapshot.positions] == ["CHEAP.US"]


def test_process_signals_does_not_open_a_position_for_a_negative_share_count() -> None:
    """A negative size must never reach open_position, where it would credit cash."""
    service = _make_service({})
    trade = _future_trade("AAPL.US", 100.0)
    service.signal_processor.run = Mock(return_value=trade)  # type: ignore[method-assign]
    service.portfolio_manager.calculate_position_size = Mock(return_value=-4)  # type: ignore[method-assign]
    cash_before = service.portfolio_manager.current_snapshot.cash

    service._process_signals([trade.signal], START, END)

    assert service.portfolio_manager.state.future_trades == []
    assert service.portfolio_manager.current_snapshot.positions == []
    assert service.portfolio_manager.current_snapshot.cash == cash_before
