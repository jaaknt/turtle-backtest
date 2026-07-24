import math
from datetime import date, timedelta
from unittest.mock import Mock

import pytest

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


class TestComputeGroupMetrics:
    """Test cases for BacktestService._compute_group_metrics."""

    def test_empty_list_returns_none(self) -> None:
        assert BacktestService._compute_group_metrics([]) is None

    def test_all_winning_trades_pf_is_inf_and_sortino_is_nan(self) -> None:
        """No losing trades means the downside deviation is zero: PF is infinite, Sortino is undefined."""
        trades = [
            make_trade("AAA", 100.0, 110.0, holding_days=365),
            make_trade("BBB", 100.0, 105.0, holding_days=365),
        ]
        metrics = BacktestService._compute_group_metrics(trades)

        assert metrics is not None
        assert metrics.pf == float("inf")
        assert math.isnan(metrics.sortino)

    def test_known_returns_match_hand_computed_stats(self) -> None:
        """4 trades at +10%/+20%/-10%/-5%, all 365-day holds (so annualized_pct == realized_pct exactly)."""
        trades = [
            make_trade("AAA", 100.0, 110.0, holding_days=365),
            make_trade("BBB", 100.0, 120.0, holding_days=365),
            make_trade("CCC", 100.0, 90.0, holding_days=365),
            make_trade("DDD", 100.0, 95.0, holding_days=365),
        ]
        metrics = BacktestService._compute_group_metrics(trades)

        assert metrics is not None
        assert metrics.n == 4
        assert metrics.mean_pct == pytest.approx(3.75)
        assert metrics.ann_mean_pct == pytest.approx(3.75)
        assert metrics.win_pct == pytest.approx(50.0)
        # PF = gross_win / gross_loss = (10 + 20) / (10 + 5) = 2.0
        assert metrics.pf == pytest.approx(2.0)
        # downside_dev = sqrt(mean([0, 0, 10**2, 5**2])) = sqrt(125 / 4)
        assert metrics.sortino == pytest.approx(3.75 / math.sqrt(125 / 4))
        # CVaR95%: n=4 -> k=max(1, floor(0.2))=1 -> worst single return
        assert metrics.cvar95 == pytest.approx(-10.0)

    def test_cvar_uses_worst_five_percent_of_larger_group(self) -> None:
        """n=20 -> k=max(1, floor(1.0))=1 -> CVaR95 is just the single worst return."""
        trades = [make_trade(f"T{i}", 100.0, 100.0 + i, holding_days=365) for i in range(-10, 10)]
        metrics = BacktestService._compute_group_metrics(trades)

        assert metrics is not None
        assert metrics.n == 20
        assert metrics.cvar95 == pytest.approx(-10.0)


class TestFormatBucketRow:
    """Test cases for BacktestService._format_bucket_row."""

    def test_none_metrics_renders_dashes(self) -> None:
        row = BacktestService._format_bucket_row("[1-20]", None)

        assert row.startswith("[1-20]")
        assert "—" in row
        assert "0" in row


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
