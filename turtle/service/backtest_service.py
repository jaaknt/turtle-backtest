from datetime import datetime

import logging

from turtle.backtest.models import SignalResult
from turtle.backtest.processor import SignalProcessor
from turtle.service.signal_service import SignalService
# from turtle.strategy.models import Signal

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
        if tickers:
            for ticker in tickers:
                signals = self.signal_service.get_trading_signals(ticker, start_date, end_date)
        else:
            tickers = self.signal_service.get_symbol_list()
            for ticker in tickers:
                signals = self.signal_service.get_trading_signals(ticker, start_date, end_date)

        # raise value error if no signals found
        if not signals:
            raise ValueError("No trading signals found.")

        signal_results = []
        for signal in signals:
            signal_result = self.signal_processor.run(signal)
            signal_results.append(signal_result)
        self._print_summary(signal_results)
        return signal_results

    def _print_summary(self, signal_results: list[SignalResult]) -> None:
        """
        Print average(return_pct), average(return_pct_qqq), average(return_pct_spy)
        Print total trades and winning trades and win rate

        Print average(return_pct), average(return_pct_qqq), average(return_pct_spy)
        for ranking 0-19, 20-39, 40-59, 60-79, 80-100
        """
        if not signal_results:
            logger.warning("No signal results to summarize.")
            return

        avg_return_pct = sum(result.return_pct for result in signal_results) / len(signal_results)
        avg_return_pct_qqq = sum(result.return_pct_qqq for result in signal_results) / len(signal_results)
        avg_return_pct_spy = sum(result.return_pct_spy for result in signal_results) / len(signal_results)

        logger.info(
            f"Backtest Summary:"
            f" Average Return (Ticker): {avg_return_pct:.2f}%"
            f" Average Return (QQQ): {avg_return_pct_qqq:.2f}%"
            f" Average Return (SPY): {avg_return_pct_spy:.2f}%"
        )
        for i in range(0, 101, 20):
            ranked_results = [result for result in signal_results if i <= result.signal.ranking < i + 20]
            if ranked_results:
                avg_ranked_return_pct = sum(result.return_pct for result in ranked_results) / len(ranked_results)
                logger.info(f" Average Return Rank [{i}-{i + 19}]: {avg_ranked_return_pct:.2f}%")
