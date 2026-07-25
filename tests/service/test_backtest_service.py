from datetime import date, timedelta
from unittest.mock import Mock

import pytest

from turtlex.backtest.metrics import metrics_from_future_trades
from turtlex.model import FutureTrade, Signal, Trade
from turtlex.service.backtest_service import BacktestService


def make_trade(ticker: str, entry_price: float, exit_price: float, holding_days: int = 30, ranking: int = 50) -> FutureTrade:
    """Build a FutureTrade with a given entry/exit price and holding period."""
    entry_date = date(2024, 1, 1)
    exit_date = entry_date + timedelta(days=holding_days)
    return FutureTrade(
        signal=Signal(ticker=ticker, date=entry_date, ranking=ranking),
        entry=Trade(ticker=ticker, date=entry_date, price=entry_price, reason="next_day_open"),
        exit=Trade(ticker=ticker, date=exit_date, price=exit_price, reason="period_end"),
        benchmark_list=[],
    )


class TestFormatBucketRow:
    """Test cases for BacktestService._format_bucket_row.

    The metric definitions themselves live in tests/backtest/test_metrics.py.
    """

    def test_none_metrics_renders_dashes(self) -> None:
        row = BacktestService._format_bucket_row("[1-20]", None)

        assert row.startswith("[1-20]")
        assert "—" in row
        assert "0" in row

    def test_renders_trade_metrics_fields(self) -> None:
        trades = [
            make_trade("AAA", 100.0, 110.0, holding_days=365),
            make_trade("BBB", 100.0, 90.0, holding_days=365),
        ]
        row = BacktestService._format_bucket_row("ALL", metrics_from_future_trades(trades))

        assert row.startswith("ALL")
        assert "2" in row
        assert "+0.00%" in row  # mean of +10% and -10%
        assert "50.0%" in row  # win rate


class TestBacktestServiceRun:
    """Test cases for BacktestService.run's signal aggregation."""

    START = date(2024, 1, 1)
    END = date(2024, 1, 5)

    def _make_service(self, universe: list[str], signals_by_ticker: dict[str, list[Signal]]) -> tuple[BacktestService, Mock, Mock]:
        trading_strategy = Mock()
        trading_strategy.get_universe.return_value = universe
        trading_strategy.get_signals.side_effect = lambda ticker, start_date, end_date: signals_by_ticker.get(ticker, [])
        signal_processor = Mock()
        signal_processor.run.return_value = None
        symbol_repo = Mock()
        service = BacktestService(trading_strategy=trading_strategy, signal_processor=signal_processor, symbol_repo=symbol_repo)
        return service, trading_strategy, symbol_repo

    def test_run_with_explicit_tickers_bypasses_universe_resolution(self) -> None:
        signals_by_ticker = {"AAPL.US": [Signal(ticker="AAPL.US", date=self.START, ranking=80)]}
        service, trading_strategy, _ = self._make_service(["MSFT.US"], signals_by_ticker)

        results = service.run(self.START, self.END, ["AAPL.US"])

        assert results == []
        trading_strategy.get_universe.assert_not_called()
        trading_strategy.get_signals.assert_called_once_with("AAPL.US", self.START, self.END)

    def test_run_without_tickers_resolves_universe_via_get_universe(self) -> None:
        signals_by_ticker = {"MSFT.US": [Signal(ticker="MSFT.US", date=self.START, ranking=80)]}
        service, trading_strategy, symbol_repo = self._make_service(["MSFT.US"], signals_by_ticker)

        service.run(self.START, self.END, None, max_tickers=20)

        trading_strategy.get_universe.assert_called_once_with(symbol_repo, limit=20)

    def test_run_raises_when_no_signals_found(self) -> None:
        service, _, _ = self._make_service([], {})

        with pytest.raises(ValueError, match="No trading signals found"):
            service.run(self.START, self.END, None)
