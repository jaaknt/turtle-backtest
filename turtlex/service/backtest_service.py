import logging
import math
from datetime import date

from turtlex.backtest.benchmark_utils import calculate_benchmark_list
from turtlex.backtest.metrics import TradeMetrics, metrics_from_future_trades
from turtlex.backtest.processor import SignalProcessor
from turtlex.model import FutureTrade
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.service.signal_service import SignalService
from turtlex.strategy.trading.base import TradingStrategy

logger = logging.getLogger(__name__)


class BacktestService:
    def __init__(self, trading_strategy: TradingStrategy, signal_processor: SignalProcessor, symbol_repo: TickerQueryRepository) -> None:
        self.trading_strategy = trading_strategy
        self.signal_processor = signal_processor
        self.symbol_repo = symbol_repo
        self.signal_service = SignalService(trading_strategy=trading_strategy, ticker_repo=symbol_repo)

    def run(self, start_date: date, end_date: date, tickers: list[str] | None, max_tickers: int | None = None) -> list[FutureTrade]:
        """
        Run the backtest for the specified date range.

        Args:
            start_date: The start date for the backtest.
            end_date: The end date for the backtest.
            tickers: Optional explicit ticker list to test. If not given, scans the trading
                strategy's universe.
            max_tickers: Optional maximum number of universe tickers to scan. Ignored if
                `tickers` is given.

        Returns:
            A list of FutureTrade objects containing the backtest results.
        """
        signals = self.signal_service.scan(start_date, end_date, max_tickers=max_tickers, tickers=tickers)

        # raise value error if no signals found
        if not signals:
            raise ValueError("No trading signals found.")

        signal_results = []
        for signal in signals:
            signal_result: FutureTrade | None = self.signal_processor.run(signal)
            if signal_result is not None:
                signal_results.append(signal_result)
        self._print_summary(signal_results, start_date, end_date)
        self._print_trade_listing(signal_results)
        return signal_results

    def _print_summary(self, signal_results: list[FutureTrade], start_date: date, end_date: date) -> None:
        """
        Print the benchmark comparison and the ranking-bucket comparison table.

        Args:
            signal_results: FutureTrade objects to summarize
            start_date: Backtest start date, used for the benchmark period
            end_date: Backtest end date, used for the benchmark period
        """
        if not signal_results:
            logger.warning("No signal results to summarize.")
            return

        # Calculate full-period benchmark returns (start_date to end_date)
        benchmarks = calculate_benchmark_list(
            start_date,
            end_date,
            self.signal_processor.benchmark_tickers,
            self.signal_processor.bars_history,
            self.signal_processor.time_frame_unit,
        )
        benchmark_map = {b.ticker: b for b in benchmarks}
        qqq = benchmark_map.get("QQQ.US")
        spy = benchmark_map.get("SPY.US")

        qqq_return = qqq.return_pct if qqq else 0.0
        qqq_annual = qqq.annualized_pct if qqq else 0.0
        spy_return = spy.return_pct if spy else 0.0
        spy_annual = spy.annualized_pct if spy else 0.0

        trading_strategy_name = type(self.trading_strategy).__name__
        exit_strategy_name = type(self.signal_processor.exit_strategy).__name__
        print(
            f"Backtest Summary: {trading_strategy_name} / {exit_strategy_name} | Period: {start_date} - {end_date}"
            f"\n QQQ: Period: {qqq_return:+.2f}% Annual: {qqq_annual:+.2f}%"
            f"\n SPY: Period: {spy_return:+.2f}% Annual: {spy_annual:+.2f}%"
        )
        self._print_bucket_table(signal_results)

    def _print_bucket_table(self, signal_results: list[FutureTrade]) -> None:
        """
        Print per-ranking-bucket group metrics plus an ALL row.

        Buckets a strategy never scores into still print (N=0, dashes) rather
        than being omitted, since that's informative when comparing runs.

        Args:
            signal_results: FutureTrade objects to bucket by signal.ranking
        """
        header = f"{'Bucket':<10}  {'N':>4}  {'Mean%':>8}  {'AnnMean%':>9}  {'Win%':>6}  {'PF':>6}  {'Sortino':>7}  {'CVaR95%':>8}"
        sep = "─" * len(header)
        print("\nRank Bucket Comparison (higher bucket should trend better = ranking validates itself):")
        print(header)
        print(sep)
        for i in range(0, 100, 20):
            bucket_results = [r for r in signal_results if i < r.signal.ranking < i + 21]
            print(self._format_bucket_row(f"[{i + 1}-{i + 20}]", metrics_from_future_trades(bucket_results)))
        print(sep)
        print(self._format_bucket_row("ALL", metrics_from_future_trades(signal_results)))

    @staticmethod
    def _format_bucket_row(label: str, m: TradeMetrics | None) -> str:
        """Format one bucket-table row; dashes when the bucket has no trades."""
        if m is None:
            return f"{label:<10}  {0:>4}  {'—':>8}  {'—':>9}  {'—':>6}  {'—':>6}  {'—':>7}  {'—':>8}"
        pf_str = f"{m.profit_factor:>6.2f}" if math.isfinite(m.profit_factor) else f"{'inf':>6}"
        sortino_str = f"{m.sortino:>7.2f}" if not math.isnan(m.sortino) else f"{'n/a':>7}"
        return (
            f"{label:<10}  {m.n:>4}  {m.mean_pct:>+7.2f}%  {m.ann_mean_pct:>+8.2f}%  "
            f"{m.win_pct:>5.1f}%  {pf_str}  {sortino_str}  {m.cvar95_pct:>+7.2f}%"
        )

    def _print_trade_listing(self, signal_results: list[FutureTrade]) -> None:
        """
        Print every trade if there are fewer than 30, otherwise the top 20 and bottom 20 by return.

        Args:
            signal_results: FutureTrade objects to list
        """
        if not signal_results:
            logger.warning("No signal results to list.")
            return

        sorted_results = sorted(signal_results, key=lambda r: r.realized_pct, reverse=True)
        header = f"{'Ticker':<10} {'Return%':>8}  {'Annual%':>8}  {'Ranking':>7}  {'Entry':>10}  {'Exit':>10}  {'Days':>5}"
        sep = "─" * len(header)

        def print_rows(rows: list[FutureTrade]) -> None:
            for r in rows:
                annual_str = f"{min(r.annualized_pct, 9999.0):>7.0f}%"
                print(
                    f"{r.signal.ticker:<10} {r.realized_pct:>+7.2f}%  {annual_str}  {r.signal.ranking:>7}  "
                    f"{r.entry.date.strftime('%Y-%m-%d')}  {r.exit.date.strftime('%Y-%m-%d')}  {r.holding_days:>5}"
                )

        n = len(sorted_results)
        if n < 30:
            print(f"\nAll Trades (N={n}):")
            print(header)
            print(sep)
            print_rows(sorted_results)
        else:
            print(f"\nTop 20 (N={n} ≥ 30):")
            print(header)
            print(sep)
            print_rows(sorted_results[:20])

            print(f"\nBottom 20 (N={n} ≥ 30):")
            print(header)
            print(sep)
            print_rows(sorted_results[-20:][::-1])
