import logging
from datetime import date, datetime
from turtle.backtest.benchmark_utils import calculate_benchmark_list
from turtle.backtest.processor import SignalProcessor
from turtle.model import FutureTrade
from turtle.service.signal_service import SignalService

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
        benchmark_map = {b.ticker: b for b in benchmarks}
        qqq = benchmark_map.get("QQQ.US")
        spy = benchmark_map.get("SPY.US")

        qqq_return = qqq.return_pct if qqq else 0.0
        qqq_annual = qqq.annualized_pct if qqq else 0.0
        spy_return = spy.return_pct if spy else 0.0
        spy_annual = spy.annualized_pct if spy else 0.0

        avg_days_held = sum((result.exit.date - result.entry.date).days for result in signal_results) / len(signal_results)
        print(
            f"Backtest Summary:"
            f" Average Return (Ticker): {avg_return_pct:.2f}% count: {len(signal_results)}"
            f" Average Days Held: {avg_days_held:.2f}"
            f"\n QQQ: Period: {qqq_return:.2f}% Annual: {qqq_annual:.2f}%"
            f"\n SPY: Period: {spy_return:.2f}% Annual: {spy_annual:.2f}%"
        )
        for i in range(0, 100, 20):
            ranked_results = [result for result in signal_results if i < result.signal.ranking < i + 21]
            if ranked_results:
                avg_ranked_return_pct = sum(result.realized_pct for result in ranked_results) / len(ranked_results)
                avg_ranked_annual_pct = sum(min(result.annualized_pct, 9999.0) for result in ranked_results) / len(ranked_results)
                print(
                    f" Average Return Rank [{i + 1}-{i + 20}]: {avg_ranked_return_pct:.2f}%"
                    f" Annual: {avg_ranked_annual_pct:,.0f}%"
                    f" count: {len(ranked_results)}"
                )
                if i in (60, 80):
                    self._print_pnl_distribution(ranked_results, rank_label=f"{i + 1}-{i + 20}")

    def _print_pnl_distribution(self, results: list[FutureTrade], rank_label: str = "") -> None:
        """Print PnL distribution across fixed return buckets."""
        buckets: list[tuple[str, float, float]] = [
            ("<-5%", float("-inf"), -5.0),
            ("-5%:-3%", -5.0, -3.0),
            ("-3%:-1%", -3.0, -1.0),
            ("-1%:0%", -1.0, 0.0),
            ("0%:1%", 0.0, 1.0),
            ("1%:3%", 1.0, 3.0),
            ("3%:5%", 3.0, 5.0),
            ("5%:10%", 5.0, 10.0),
            (">10%", 10.0, float("inf")),
        ]
        n = len(results)
        print("   PnL Distribution:")
        for label, lo, hi in buckets:
            count = sum(1 for r in results if lo <= r.realized_pct < hi)
            pct = count / n * 100 if n else 0.0
            bar = "#" * int(pct / 2)
            print(f"   {label:>10}  {count:>4} ({pct:>5.1f}%)  {bar}")

        sorted_results = sorted(results, key=lambda r: r.realized_pct, reverse=True)
        header = f"   {'Ticker':<10} {'Return%':>8}  {'Annual%':>9}  {'Entry':>10}  {'Exit':>10}  {'Days':>5}"
        sep = "   " + "-" * 60

        label_suffix = f" (rank {rank_label})" if rank_label else ""

        top_n = sorted_results[:10]
        print(f"\n   Top {len(top_n)}{label_suffix}:")
        print(header)
        print(sep)
        for r in top_n:
            days = (r.exit.date - r.entry.date).days
            annual_str = f"{min(r.annualized_pct, 9999.0):>8.0f}%"
            print(
                f"   {r.signal.ticker:<10} {r.realized_pct:>7.2f}%  {annual_str}  "
                f"{r.entry.date.strftime('%Y-%m-%d')}  {r.exit.date.strftime('%Y-%m-%d')}  {days:>5}"
            )

        bottom_n = sorted_results[-10:][::-1]
        print(f"\n   Bottom {len(bottom_n)}{label_suffix}:")
        print(header)
        print(sep)
        for r in bottom_n:
            days = (r.exit.date - r.entry.date).days
            annual_str = f"{min(r.annualized_pct, 9999.0):>8.0f}%"
            print(
                f"   {r.signal.ticker:<10} {r.realized_pct:>7.2f}%  {annual_str}  "
                f"{r.entry.date.strftime('%Y-%m-%d')}  {r.exit.date.strftime('%Y-%m-%d')}  {days:>5}"
            )

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
        print("-" * 100)
        print(f"{'Rank':<4} {'Ticker':<10} {'Return%':<9} {'Annual%':<10} {'Ranking':<8} {'Entry Date':<12} {'Exit Date':<12} {'Days':<5}")
        print("-" * 100)

        for i, result in enumerate(top_signals, 1):
            days_held = (result.exit.date - result.entry.date).days
            annual_str = f"{min(result.annualized_pct, 9999.0):>8.0f}%"
            print(
                f"{i:<4} {result.signal.ticker:<10} {result.realized_pct:>7.2f}%  "
                f"{annual_str:<10}"
                f"{result.signal.ranking:<8} {result.entry.date.strftime('%Y-%m-%d'):<12} "
                f"{result.exit.date.strftime('%Y-%m-%d'):<12} {days_held:<5}"
            )
        print("-" * 100)
