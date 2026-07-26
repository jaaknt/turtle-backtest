"""Tests for PortfolioService's entry-signal generation."""

import logging
from datetime import date
from unittest.mock import Mock

import pytest

from turtlex.model import Signal, Trade
from turtlex.service.portfolio_service import PortfolioService

START = date(2024, 1, 2)
END = date(2024, 3, 1)


def _open_position(service: PortfolioService, ticker: str) -> None:
    """Open a position so it occupies a slot and excludes further signals for that ticker."""
    entry = Trade(ticker=ticker, date=START, price=100.0, reason="next_day_open")
    exit_ = Trade(ticker=ticker, date=START, price=100.0, reason="open")
    service.portfolio_manager.open_position(entry=entry, exit=exit_, position_size=1)


def _make_service(signals_by_ticker: dict[str, list[Signal]], min_signal_ranking: int = 70) -> PortfolioService:
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


def test_generate_entry_signals_caps_entries_at_the_free_position_slots() -> None:
    """max_positions was unenforced: the selector was handed the signal count as its slot count."""
    tickers = [f"T{i}.US" for i in range(12)]
    signals_by_ticker = {t: [Signal(ticker=t, date=START, ranking=80 + i)] for i, t in enumerate(tickers)}
    service = _make_service(signals_by_ticker)

    signals = service._generate_entry_signals(START, tickers)

    assert len(signals) == service.signal_selector.max_positions  # 12 qualify, 10 slots
    assert [s.ticker for s in signals] == [f"T{i}.US" for i in range(11, 1, -1)]  # highest ranked first


def test_generate_entry_signals_returns_nothing_when_the_portfolio_is_full() -> None:
    held = [f"H{i}.US" for i in range(10)]
    signals_by_ticker = {"AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=99)]}
    service = _make_service(signals_by_ticker)
    for ticker in held:
        _open_position(service, ticker)

    assert service._generate_entry_signals(START, ["AAPL.US"]) == []


def test_generate_entry_signals_logs_generated_and_selected_counts(caplog: pytest.LogCaptureFixture) -> None:
    """The old message reported survivors as if they were strategy output, hiding the ranking filter."""
    signals_by_ticker = {
        "AAPL.US": [Signal(ticker="AAPL.US", date=START, ranking=60)],  # below threshold
        "MSFT.US": [Signal(ticker="MSFT.US", date=START, ranking=80)],
    }
    service = _make_service(signals_by_ticker)

    with caplog.at_level(logging.INFO):
        service._generate_entry_signals(START, ["AAPL.US", "MSFT.US"])

    assert "Generated 2 signals" in caplog.text
    assert "1 selected for entry" in caplog.text
    assert "ranking >= 70" in caplog.text
