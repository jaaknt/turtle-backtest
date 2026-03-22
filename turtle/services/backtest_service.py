import logging
from datetime import date, datetime
from turtle.backtest.benchmark_utils import calculate_benchmark_list
from turtle.backtest.models import FutureTrade
from turtle.backtest.processor import SignalProcessor
from turtle.services.signal_service import SignalService

logger = logging.getLogger(__name__)


class BacktestService:
    def __init__(self, signal_service: SignalService, signal_processor: SignalProcessor) -> None:
        self.signal_service = signal_service
        self.signal_processor = signal_processor

    def run(self, start_date: date, end_date: date, tickers: list[str] | None) -> list[FutureTrade]:
        """
        Run the backtest for the specified date range.

        Args:
            start_date: The start date for the backtest.
            end_date: The end date for the backtest.

        Returns:
            A list of FutureTrade objects containing the backtest results.
        """
        signals: list = []
        if tickers:
            for ticker in tickers:
                signals.extend(self.signal_service.get_signals(ticker, start_date, end_date))
        else:
            tickers = self.signal_service.get_symbol_list()
            logger.info(f"Running backtest for {len(tickers)} tickers")
            for ticker in tickers:
                signals.extend(self.signal_service.get_signals(ticker, start_date, end_date))

        # raise value error if no signals found
        if not signals:
            raise ValueError("No trading signals found.")

        signal_results = []
        for signal in signals:
            signal_result: FutureTrade | None = self.signal_processor.run(signal)
            if signal_result is not None:
                signal_results.append(signal_result)
        self._print_summary(signal_results, start_date, end_date)
        self._print_top_signals(signal_results)
        return signal_results

    def _print_summary(self, signal_results: list[FutureTrade], start_date: date, end_date: date) -> None:
        """
        Print average(return_pct), average benchmark returns
        Print total trades and winning trades and win rate

        Print average returns by ranking buckets 1-20, 21-40, 41-60, 61-80, 81-100
        """
        if not signal_results:
            logger.warning("No signal results to summarize.")
            return

        avg_return_pct = sum(result.realized_pct for result in signal_results) / len(signal_results)

        # Calculate full-period benchmark returns (start_date to end_date)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())
        benchmarks = calculate_benchmark_list(
            start_dt,
            end_dt,
            self.signal_processor.benchmark_tickers,
            self.signal_processor.bars_history,
            self.signal_processor.time_frame_unit,
        )
        benchmark_returns = {b.ticker: b.return_pct for b in benchmarks}
        avg_return_pct_qqq = benchmark_returns.get("QQQ.US", 0.0)
        avg_return_pct_spy = benchmark_returns.get("SPY.US", 0.0)

        print(
            f"Backtest Summary:"
            f" Average Return (Ticker): {avg_return_pct:.2f}% count: {len(signal_results)}"
            f" Average Days Held: {sum((result.exit.date - result.entry.date).days for result in signal_results) / len(signal_results):.2f}"
            f" Average Return (QQQ): {avg_return_pct_qqq:.2f}%"
            f" Average Return (SPY): {avg_return_pct_spy:.2f}%"
        )
        for i in range(0, 100, 20):
            ranked_results = [result for result in signal_results if i < result.signal.ranking < i + 21]
            if ranked_results:
                avg_ranked_return_pct = sum(result.realized_pct for result in ranked_results) / len(ranked_results)
                print(f" Average Return Rank [{i + 1}-{i + 20}]: {avg_ranked_return_pct:.2f}% count: {len(ranked_results)}")

    def _print_top_signals(self, signal_results: list[FutureTrade]) -> None:
        """
        Print the top 20 performing signals by return percentage.

        Args:
            signal_results: List of FutureTrade objects to analyze
        """
        if not signal_results:
            logger.warning("No signal results to display top performers.")
            return

        # Sort by return percentage in descending order and take top 20
        top_signals = sorted(signal_results, key=lambda x: x.realized_pct, reverse=True)[:20]

        print("\nTop 20 Performing Signals:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Ticker':<8} {'Return%':<8} {'Ranking':<8} {'Entry Date':<12} {'Exit Date':<12} {'Days':<5}")
        print("-" * 80)

        for i, result in enumerate(top_signals, 1):
            days_held = (result.exit.date - result.entry.date).days
            print(
                f"{i:<4} {result.signal.ticker:<8} {result.realized_pct:>7.2f}% "
                f"{result.signal.ranking:<8} {result.entry.date.strftime('%Y-%m-%d'):<12} "
                f"{result.exit.date.strftime('%Y-%m-%d'):<12} {days_held:<5}"
            )
        print("-" * 80)
