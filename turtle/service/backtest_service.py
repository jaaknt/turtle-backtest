from datetime import datetime

import logging

from turtle.backtest.models import SignalResult
from turtle.backtest.processor import SignalProcessor
from turtle.service.signal_service import SignalService
# from turtle.signal.models import Signal

logger = logging.getLogger(__name__)


class BacktestService:
    def __init__(self, signal_service: SignalService, signal_processor: SignalProcessor) -> None:
        self.signal_service = signal_service
        self.signal_processor = signal_processor

    def run(self, start_date: datetime, end_date: datetime, tickers: list[str] | None) -> list[SignalResult]:
        """
        Run the backtest for the specified date range.

        Args:
            start_date: The start date for the backtest.
            end_date: The end date for the backtest.

        Returns:
            A list of SignalResult objects containing the backtest results.
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
            signal_result: SignalResult | None = self.signal_processor.run(signal)
            if signal_result is not None:
                signal_results.append(signal_result)
        self._print_summary(signal_results)
        self._print_top_signals(signal_results)
        return signal_results

    def _print_summary(self, signal_results: list[SignalResult]) -> None:
        """
        Print average(return_pct), average(return_pct_qqq), average(return_pct_spy)
        Print total trades and winning trades and win rate

        Print average(return_pct), average(return_pct_qqq), average(return_pct_spy)
        for ranking 1-20, 21-40, 41-60, 61-80, 81-100
        """
        if not signal_results:
            logger.warning("No signal results to summarize.")
            return

        avg_return_pct = sum(result.return_pct for result in signal_results) / len(signal_results)
        avg_return_pct_qqq = sum(result.return_pct_qqq for result in signal_results) / len(signal_results)
        avg_return_pct_spy = sum(result.return_pct_spy for result in signal_results) / len(signal_results)

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
                avg_ranked_return_pct = sum(result.return_pct for result in ranked_results) / len(ranked_results)
                print(f" Average Return Rank [{i + 1}-{i + 20}]: {avg_ranked_return_pct:.2f}% count: {len(ranked_results)}")

    def _print_top_signals(self, signal_results: list[SignalResult]) -> None:
        """
        Print the top 5 performing signals by return percentage.

        Args:
            signal_results: List of SignalResult objects to analyze
        """
        if not signal_results:
            logger.warning("No signal results to display top performers.")
            return

        # Sort by return percentage in descending order and take top 5
        top_signals = sorted(signal_results, key=lambda x: x.return_pct, reverse=True)[:5]

        print("\nTop 5 Performing Signals:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Ticker':<8} {'Return%':<8} {'Ranking':<8} {'Entry Date':<12} {'Exit Date':<12} {'Days':<5}")
        print("-" * 80)

        for i, result in enumerate(top_signals, 1):
            days_held = (result.exit.date - result.entry.date).days
            print(f"{i:<4} {result.signal.ticker:<8} {result.return_pct:>7.2f}% "
                  f"{result.signal.ranking:<8} {result.entry.date.strftime('%Y-%m-%d'):<12} "
                  f"{result.exit.date.strftime('%Y-%m-%d'):<12} {days_held:<5}")
        print("-" * 80)
