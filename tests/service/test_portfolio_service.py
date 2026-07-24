"""Tests for PortfolioService's entry-signal generation."""

from datetime import date
from unittest.mock import Mock

from turtlex.model import Signal, Trade
from turtlex.service.portfolio_service import PortfolioService

START = date(2024, 1, 2)
END = date(2024, 3, 1)


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
    entry = Trade(ticker="AAPL.US", date=START, price=100.0, reason="next_day_open")
    exit_ = Trade(ticker="AAPL.US", date=START, price=100.0, reason="open")
    service.portfolio_manager.open_position(entry=entry, exit=exit_, position_size=10)

    signals = service._generate_entry_signals(START, ["AAPL.US"])

    assert signals == []
