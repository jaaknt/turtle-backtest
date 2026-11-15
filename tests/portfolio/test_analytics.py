"""Tests for PortfolioAnalytics' trade summary and equity-curve report.

The metric formulas themselves are tested in tests/backtest/test_metrics.py; these cover the
series PortfolioAnalytics builds from snapshots and bars, and what it prints.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

import polars as pl
import pytest

from turtlex.model import DailyPortfolioSnapshot, FutureTrade, PortfolioState, Signal, Trade
from turtlex.portfolio.analytics import DEFAULT_BENCHMARK_TICKER, PortfolioAnalytics


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

    def test_default_benchmark_carries_the_database_ticker_suffix(self) -> None:
        """A bare "QQQ" matches no rows in turtle.daily_bars, which silently dropped the benchmark."""
        assert DEFAULT_BENCHMARK_TICKER.endswith(".US")

    def test_generate_results_summarizes_trades_even_without_snapshots(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Snapshots drive the equity curve; trades are summarized independently of it."""
        state = PortfolioState(future_trades=[make_trade("AAA", 100.0, 110.0)])

        PortfolioAnalytics().generate_results(state, date(2024, 1, 1), date(2024, 3, 1), ohlcv_repo=None)  # type: ignore[arg-type]

        assert "Trade Summary" in capsys.readouterr().out


class TestEquityCurve:
    START = date(2024, 1, 1)
    END = date(2024, 1, 5)

    def _repo_with_bars(self) -> MagicMock:
        """Bars on Jan 2-5 only: Jan 1 is a holiday the backtest still snapshots."""
        repo = MagicMock()
        repo.get_bars_pl.return_value = pl.DataFrame(
            {
                "date": [date(2024, 1, i) for i in range(2, 6)],
                "adjusted_close": [100.0, 101.0, 102.0, 101.0],
            }
        )
        return repo

    def _state(self) -> PortfolioState:
        cash = [30000.0, 30000.0, 30300.0, 30603.0, 30300.0]  # Jan 1 (holiday) to Jan 5
        return PortfolioState(
            daily_snapshots=[DailyPortfolioSnapshot(date=date(2024, 1, i + 1), cash=c, positions=[]) for i, c in enumerate(cash)]
        )

    def test_benchmark_bars_are_the_trading_calendar(self) -> None:
        """The holiday snapshot is not a trading day, and both series share the remaining dates."""
        repo = self._repo_with_bars()

        portfolio, benchmark = PortfolioAnalytics()._daily_returns(self._state(), self.START, self.END, repo, "SPY.US")

        repo.get_bars_pl.assert_called_once_with("SPY.US", self.START, self.END)
        assert benchmark is not None
        assert portfolio.dates == benchmark.dates == [date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
        assert portfolio.values == pytest.approx([0.01, 0.01, 30300.0 / 30603.0 - 1])
        assert benchmark.values == pytest.approx([0.01, 102.0 / 101.0 - 1, 101.0 / 102.0 - 1])

    def test_a_null_or_zero_benchmark_close_leaves_the_calendar(self) -> None:
        """A bad bar would otherwise divide by None or 0 and lose the report at the end of a long run."""
        repo = MagicMock()
        repo.get_bars_pl.return_value = pl.DataFrame(
            {"date": [date(2024, 1, i) for i in range(2, 6)], "adjusted_close": [100.0, None, 0.0, 101.0]}
        )

        portfolio, benchmark = PortfolioAnalytics()._daily_returns(self._state(), self.START, self.END, repo, "SPY.US")

        assert benchmark is not None
        assert portfolio.dates == benchmark.dates == [date(2024, 1, 5)]
        assert benchmark.values == pytest.approx([0.01])

    def test_without_benchmark_bars_the_portfolio_runs_on_every_snapshot_day(self) -> None:
        """The benchmark is dropped rather than faked when the symbol has no rows."""
        repo = MagicMock()
        repo.get_bars_pl.return_value = pl.DataFrame()

        portfolio, benchmark = PortfolioAnalytics()._daily_returns(self._state(), self.START, self.END, repo, "NOPE.US")

        assert benchmark is None
        assert portfolio.dates == [date(2024, 1, i) for i in range(2, 6)]
        assert portfolio.values[0] == 0.0  # the flat holiday-to-Jan-2 step

    def test_generate_results_prints_the_portfolio_beside_the_benchmark(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The --benchmark-ticker flag has to survive the trip from the CLI to the query and the table."""
        repo = self._repo_with_bars()

        PortfolioAnalytics().generate_results(self._state(), self.START, self.END, repo, benchmark_ticker="SPY.US")
        out = capsys.readouterr().out

        repo.get_bars_pl.assert_called_once_with("SPY.US", self.START, self.END)
        assert "Equity Curve (2024-01-03 to 2024-01-05, 3 trading days):" in out
        assert "SPY.US" in out
        assert "Beta" in out
        assert "2024*" in out  # the only year is partial

    def test_generate_results_without_a_benchmark_prints_the_portfolio_alone(self, capsys: pytest.CaptureFixture[str]) -> None:
        repo = MagicMock()
        repo.get_bars_pl.return_value = pl.DataFrame()

        PortfolioAnalytics().generate_results(self._state(), self.START, self.END, repo, benchmark_ticker="NOPE.US")
        out = capsys.readouterr().out

        assert "Equity Curve" in out
        assert "NOPE.US" not in out
        assert "Beta" not in out
