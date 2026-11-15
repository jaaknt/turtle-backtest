"""Portfolio performance analytics: the trade summary and the equity curve's metrics against a benchmark."""

import logging
import math
from collections.abc import Callable
from datetime import date
from itertools import pairwise

from turtlex.backtest.metrics import DailyMetrics, DailyReturns, compute_daily_metrics, metrics_from_future_trades, yearly_returns
from turtlex.model import PortfolioState
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository

logger = logging.getLogger(__name__)

# Database convention keeps the `.US` suffix (turtle.daily_bars); a bare "QQQ" matches no rows.
DEFAULT_BENCHMARK_TICKER = "QQQ.US"


def _pct(v: float | None) -> str:
    return f"{v * 100:+.2f}%" if v is not None else "n/a"


def _share(v: float | None) -> str:
    return f"{v * 100:.2f}%" if v is not None else "n/a"


def _ratio(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "n/a"


# One row per printed metric: label and how to render it from DailyMetrics
_METRIC_ROWS: list[tuple[str, Callable[[DailyMetrics], str]]] = [
    ("Cumulative return", lambda m: _pct(m.cumulative_return)),
    ("CAGR", lambda m: _pct(m.cagr)),
    ("Volatility (ann.)", lambda m: _share(m.volatility)),
    ("Sharpe", lambda m: _ratio(m.sharpe)),
    ("Sortino", lambda m: _ratio(m.sortino)),
    ("Calmar", lambda m: _ratio(m.calmar)),
    ("Max drawdown", lambda m: _pct(m.max_drawdown)),
    ("Longest drawdown", lambda m: f"{m.longest_drawdown_days}d"),
    ("Best day", lambda m: _pct(m.best_day)),
    ("Worst day", lambda m: _pct(m.worst_day)),
    ("Best month", lambda m: _pct(m.best_month)),
    ("Worst month", lambda m: _pct(m.worst_month)),
    ("Win rate (days)", lambda m: _share(m.win_rate_days)),
    ("Win rate (months)", lambda m: _share(m.win_rate_months)),
]


class PortfolioAnalytics:
    """
    Portfolio performance analytics: prints the closed trades' summary and the daily equity
    curve's metrics beside a benchmark's, using the quantstats conventions of
    `turtlex.backtest.metrics`.
    """

    def generate_results(
        self,
        portfolio_state: PortfolioState,
        start_date: date,
        end_date: date,
        ohlcv_repo: DailyBarsQueryRepository,
        benchmark_ticker: str = DEFAULT_BENCHMARK_TICKER,
    ) -> None:
        """Print the trade summary and the equity-curve metrics.

        Args:
            portfolio_state: Portfolio state holding the daily snapshots and trades
            start_date: Backtest start date, used for the benchmark window
            end_date: Backtest end date, used for the benchmark window
            ohlcv_repo: Repository the benchmark bars are read from
            benchmark_ticker: Symbol the portfolio is compared against, in database convention
                (with the `.US` suffix)
        """
        logger.info("Generating portfolio performance results")

        # Trades are summarized independently of the snapshots the equity curve needs
        self.print_trade_summary(portfolio_state)

        if len(portfolio_state.daily_snapshots) < 2:
            logger.warning("Fewer than 2 daily snapshots: no equity curve to analyze")
            return

        portfolio, benchmark = self._daily_returns(portfolio_state, start_date, end_date, ohlcv_repo, benchmark_ticker)
        self.print_equity_metrics(portfolio, benchmark, benchmark_ticker)

    def print_trade_summary(self, portfolio_state: PortfolioState) -> None:
        """
        Print aggregate metrics for the portfolio's round-trip trades.

        The equity metrics describe the curve; this describes the trades that produced it.
        Columns match the backtest runner's bucket table so the two reports are comparable.

        Args:
            portfolio_state: Portfolio state holding the completed trades
        """
        metrics = metrics_from_future_trades(portfolio_state.future_trades)
        if metrics is None:
            logger.warning("No closed trades to summarize")
            return

        header = f"{'N':>4}  {'Mean%':>8}  {'Med%':>8}  {'AnnMean%':>9}  {'Win%':>6}  {'PF':>6}  {'Sortino':>7}  {'CVaR95%':>8}"
        pf_str = f"{metrics.profit_factor:>6.2f}" if math.isfinite(metrics.profit_factor) else f"{'inf':>6}"
        sortino_str = f"{metrics.sortino:>7.2f}" if not math.isnan(metrics.sortino) else f"{'n/a':>7}"
        print("\nTrade Summary:")
        print(header)
        print("─" * len(header))
        print(
            f"{metrics.n:>4}  {metrics.mean_pct:>+7.2f}%  {metrics.median_pct:>+7.2f}%  {metrics.ann_mean_pct:>+8.2f}%  "
            f"{metrics.win_pct:>5.1f}%  {pf_str}  {sortino_str}  {metrics.cvar95_pct:>+7.2f}%"
        )

    def print_equity_metrics(self, portfolio: DailyReturns, benchmark: DailyReturns | None, benchmark_ticker: str) -> None:
        """
        Print the equity curve's metrics and yearly returns, beside the benchmark's when given.

        Args:
            portfolio: The portfolio's daily returns; must not be empty
            benchmark: The benchmark's daily returns on the same dates, or None to print the
                portfolio alone
            benchmark_ticker: Benchmark symbol, for the column header
        """
        port_m = compute_daily_metrics(portfolio, benchmark)
        columns = [("Portfolio", port_m)]
        years = [yearly_returns(portfolio)]
        if benchmark is not None:
            columns.append((benchmark_ticker, compute_daily_metrics(benchmark)))
            years.append(yearly_returns(benchmark))

        print(f"\nEquity Curve ({portfolio.dates[0]} to {portfolio.dates[-1]}, {len(portfolio.values)} trading days):")
        header = f"{'Metric':<18}" + "".join(f"  {name:>10}" for name, _ in columns)
        print(header)
        print("─" * len(header))
        for label, render in _METRIC_ROWS:
            print(f"{label:<18}" + "".join(f"  {render(m):>10}" for _, m in columns))
        if benchmark is not None:
            print(f"{'Beta':<18}  {_ratio(port_m.beta):>10}")
            print(f"{'Correlation':<18}  {_ratio(port_m.correlation):>10}")

        print("\nYearly Returns (* partial year):")
        print(f"{'Year':<18}" + "".join(f"  {name:>10}" for name, _ in columns))
        for row in zip(*years, strict=True):
            label = f"{row[0].year}{'*' if row[0].partial else ''}"
            print(f"{label:<18}" + "".join(f"  {_pct(y.value):>10}" for y in row))

    def _daily_returns(
        self,
        portfolio_state: PortfolioState,
        start_date: date,
        end_date: date,
        ohlcv_repo: DailyBarsQueryRepository,
        benchmark_ticker: str,
    ) -> tuple[DailyReturns, DailyReturns | None]:
        """
        Build the portfolio's and the benchmark's daily returns on a shared trading calendar.

        PortfolioService steps through the benchmark's bar dates, so its snapshots are already
        trading days; only snapshot dates with a usable benchmark close are kept, so both series
        share one calendar. Without benchmark bars the portfolio is returned alone, on every
        snapshot day, and the benchmark is None.

        Args:
            portfolio_state: Portfolio state holding at least 2 daily snapshots
            start_date: Benchmark window start
            end_date: Benchmark window end
            ohlcv_repo: Repository the benchmark bars are read from
            benchmark_ticker: Benchmark symbol, in database convention

        Returns:
            The portfolio's returns and the benchmark's on the same dates (or None)
        """
        values = {s.date: s.total_value for s in portfolio_state.daily_snapshots}
        bars = ohlcv_repo.get_bars_pl(benchmark_ticker, start_date, end_date)
        closes: dict[date, float] = {}
        if not bars.is_empty():
            # A null or non-positive close has no return to take; that day leaves the calendar
            pairs = zip(bars["date"].to_list(), bars["adjusted_close"].to_list(), strict=True)
            closes = {d: c for d, c in pairs if d in values and c is not None and c > 0}

        if len(closes) < 2:
            logger.warning(f"Insufficient {benchmark_ticker} bars: reporting the portfolio alone, on every snapshot day")
            calendar = sorted(values)
            bench = None
        else:
            calendar = sorted(closes)
            bench = DailyReturns(calendar[1:], [closes[b] / closes[a] - 1.0 for a, b in pairwise(calendar)])
        portfolio = DailyReturns(calendar[1:], [values[b] / values[a] - 1.0 for a, b in pairwise(calendar)])
        return portfolio, bench
