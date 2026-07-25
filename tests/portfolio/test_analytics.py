"""Tests for PortfolioAnalytics' trade summary.

The quantstats tearsheet path is not covered here — it writes an HTML file through the
library and has no return value to assert on.
"""

from datetime import date, timedelta

import pytest

from turtlex.model import FutureTrade, PortfolioState, Signal, Trade
from turtlex.portfolio.analytics import PortfolioAnalytics


def make_trade(ticker: str, entry_price: float, exit_price: float, holding_days: int = 30) -> FutureTrade:
    """Build a FutureTrade with a given entry/exit price and holding period."""
    entry_date = date(2024, 1, 1)
    exit_date = entry_date + timedelta(days=holding_days)
    return FutureTrade(
        signal=Signal(ticker=ticker, date=entry_date, ranking=50),
        entry=Trade(ticker=ticker, date=entry_date, price=entry_price, reason="next_day_open"),
        exit=Trade(ticker=ticker, date=exit_date, price=exit_price, reason="period_end"),
        benchmark_list=[],
    )


class TestPrintTradeSummary:
    def test_prints_metrics_for_closed_trades(self, capsys: pytest.CaptureFixture[str]) -> None:
        state = PortfolioState(
            future_trades=[
                make_trade("AAA", 100.0, 110.0, holding_days=365),
                make_trade("BBB", 100.0, 120.0, holding_days=365),
                make_trade("CCC", 100.0, 90.0, holding_days=365),
                make_trade("DDD", 100.0, 95.0, holding_days=365),
            ]
        )

        PortfolioAnalytics().print_trade_summary(state)
        out = capsys.readouterr().out

        assert "Trade Summary:" in out
        assert "Sortino" in out
        assert "+3.75%" in out  # mean of +10/+20/-10/-5
        assert " 50.0%" in out  # win rate
        assert "  2.00" in out  # profit factor (10+20)/(10+5)

    def test_renders_undefined_sortino_as_na(self, capsys: pytest.CaptureFixture[str]) -> None:
        """All-winning trades have zero downside deviation, so the ratio has no value to print."""
        state = PortfolioState(future_trades=[make_trade("AAA", 100.0, 110.0), make_trade("BBB", 100.0, 105.0)])

        PortfolioAnalytics().print_trade_summary(state)
        out = capsys.readouterr().out

        assert "n/a" in out
        assert "inf" in out  # profit factor with no losers

    def test_reported_n_covers_every_trade_that_reaches_the_csv(self, capsys: pytest.CaptureFixture[str]) -> None:
        """PortfolioService writes state.future_trades to CSV and summarizes the same list, so the counts must agree."""
        trades = [make_trade(f"T{i}", 100.0, 100.0 + i, holding_days=20 + i) for i in range(7)]
        state = PortfolioState(future_trades=trades)

        PortfolioAnalytics().print_trade_summary(state)
        out = capsys.readouterr().out

        assert f"{len(state.future_trades):>4}" in out

    def test_prints_nothing_without_trades(self, capsys: pytest.CaptureFixture[str]) -> None:
        PortfolioAnalytics().print_trade_summary(PortfolioState())

        assert "Trade Summary" not in capsys.readouterr().out

    def test_generate_results_summarizes_trades_even_without_snapshots(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Snapshots drive the tearsheet; trades are summarized independently of it."""
        state = PortfolioState(future_trades=[make_trade("AAA", 100.0, 110.0)])

        PortfolioAnalytics().generate_results(state, date(2024, 1, 1), date(2024, 3, 1), ohlcv_repo=None)  # type: ignore[arg-type]

        assert "Trade Summary" in capsys.readouterr().out
