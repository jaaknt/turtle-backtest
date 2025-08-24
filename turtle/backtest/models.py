from dataclasses import dataclass
from datetime import datetime
from typing import Any
import pandas as pd

from turtle.backtest.period_return import PeriodReturn, PeriodReturnResult
from turtle.strategy.models import Signal


@dataclass
class SignalResult:
    """
    Represents a single trading signal and its outcomes.

    Attributes:
        signal: Signal that is input for calculation
        entry_date: Date when position was entered
        entry_price: Price at which position was entered
        exit_date: Date when position was exited
        exit_price: Price at which position was exited
        exit_reason: Reason for exit (e.g., 'period_end', 'profit_target', 'stop_loss', 'ema_exit')
        return_pct: Percentage return between entry_price and exit_price
        return_pct_qqq: QQQ benchmark percentage return for the same period
        return_pct_spy: SPY benchmark percentage return for the same period
    """

    signal: Signal
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    exit_reason: str
    return_pct: float
    return_pct_qqq: float
    return_pct_spy: float


@dataclass
class LegacySignalResult:
    """
    Legacy SignalResult for backward compatibility during transition.
    This class maintains the old API to support existing code.
    """

    ticker: str
    signal_date: datetime
    entry_price: float
    entry_date: datetime
    period_results: dict[str, float | None]
    ranking: int = 0
    period_data: dict[str, dict[str, Any]] | None = None
    closing_date: datetime | None = None
    closing_price: float | None = None

    def get_return_for_period(
        self,
        period_name: str,
        strategy_name: str = 'buy_and_hold',
        **strategy_kwargs: Any
    ) -> float | None:
        """Calculate percentage return for a specific period using specified strategy."""
        # Try new period return calculation first
        if self.period_data and period_name in self.period_data:
            try:
                period_info = self.period_data[period_name]
                target_date = period_info['target_date']
                data = period_info['data']

                period_return = PeriodReturn(strategy_name, **strategy_kwargs)
                result = period_return.calculate_return(
                    data=data,
                    entry_price=self.entry_price,
                    entry_date=self.entry_date,
                    target_date=target_date
                )

                if result:
                    return result.return_pct

            except Exception:
                # Fall back to legacy calculation
                pass

        # Fallback to legacy calculation for backward compatibility
        if period_name not in self.period_results:
            return None

        closing_price = self.period_results[period_name]
        if closing_price is None or self.entry_price <= 0:
            return None

        return ((closing_price - self.entry_price) / self.entry_price) * 100

    def get_return_result_for_period(
        self,
        period_name: str,
        strategy_name: str = 'buy_and_hold',
        **strategy_kwargs: Any
    ) -> PeriodReturnResult | None:
        """Get detailed period return result including exit reason and date."""
        if not self.period_data or period_name not in self.period_data:
            return None

        try:
            period_info = self.period_data[period_name]
            target_date = period_info['target_date']
            data = period_info['data']

            period_return = PeriodReturn(strategy_name, **strategy_kwargs)
            return period_return.calculate_return(
                data=data,
                entry_price=self.entry_price,
                entry_date=self.entry_date,
                target_date=target_date
            )

        except Exception:
            return None



@dataclass
class PerformanceResult:
    """
    Performance statistics for a specific time period.

    Attributes:
        period_name: Name of the time period (e.g., '3d', '1w', '2w', '1m')
        total_signals: Total number of signals analyzed
        valid_signals: Number of signals with complete data
        average_return: Average percentage return
        win_rate: Percentage of profitable trades
        best_return: Best percentage return
        worst_return: Worst percentage return
        returns: List of all percentage returns
    """

    period_name: str
    total_signals: int
    valid_signals: int
    average_return: float
    win_rate: float
    best_return: float
    worst_return: float
    returns: list[float]

    @classmethod
    def from_returns(
        cls, period_name: str, total_signals: int, returns: list[float]
    ) -> "PerformanceResult":
        """
        Create PerformanceResult from a list of returns.

        Args:
            period_name: Name of the time period
            total_signals: Total number of signals that were attempted
            returns: List of percentage returns (only valid ones)

        Returns:
            PerformanceResult instance with calculated statistics
        """
        if not returns:
            return cls(
                period_name=period_name,
                total_signals=total_signals,
                valid_signals=0,
                average_return=0.0,
                win_rate=0.0,
                best_return=0.0,
                worst_return=0.0,
                returns=[],
            )

        valid_signals = len(returns)
        average_return = sum(returns) / valid_signals
        winning_trades = len([r for r in returns if r > 0])
        win_rate = (winning_trades / valid_signals) * 100 if valid_signals > 0 else 0.0
        best_return = max(returns)
        worst_return = min(returns)

        return cls(
            period_name=period_name,
            total_signals=total_signals,
            valid_signals=valid_signals,
            average_return=average_return,
            win_rate=win_rate,
            best_return=best_return,
            worst_return=worst_return,
            returns=returns,
        )


@dataclass
class RankingPerformance:
    """
    Performance statistics grouped by ranking ranges.

    Attributes:
        ranking_range: Description of ranking range (e.g., "0-20", "21-40", "41-60", "61-80", "81-100")
        period_results: Dictionary mapping period names to PerformanceResult
        total_signals: Total number of signals in this ranking range
    """

    ranking_range: str
    period_results: dict[str, PerformanceResult]
    total_signals: int


@dataclass
class TestSummary:
    """
    Summary of strategy testing results across all periods.

    Attributes:
        strategy_name: Name of the tested strategy
        test_start_date: Start date of the testing period
        test_end_date: End date of the testing period
        total_signals_found: Total number of trading signals found
        period_results: Dictionary mapping period names to PerformanceResult
        test_periods: List of pandas.Timedelta objects representing test periods
        benchmark_results: Optional dictionary mapping benchmark symbols to their period results
        ranking_results: Optional dictionary mapping ranking ranges to RankingPerformance
        signal_benchmark_data: Optional list of individual signal benchmark data
    """

    strategy_name: str
    test_start_date: datetime
    test_end_date: datetime
    total_signals_found: int
    period_results: dict[str, PerformanceResult]
    max_holding_period: pd.Timedelta
    benchmark_results: dict | None = None
    ranking_results: dict[str, RankingPerformance] | None = None
    signal_benchmark_data: list[dict[str, Any]] | None = None

    def get_performance_for_period(
        self, period_name: str
    ) -> PerformanceResult | None:
        """Get performance results for a specific period."""
        return self.period_results.get(period_name)

    def get_all_periods(self) -> list[str]:
        """Get list of all tested period names."""
        return list(self.period_results.keys())

    def format_summary(self) -> str:
        """
        Format the test summary as a readable string.

        Returns:
            Formatted string representation of the test results
        """
        lines = [
            f"Strategy: {self.strategy_name}",
            f"Test Period: {self.test_start_date.strftime('%Y-%m-%d')} to {self.test_end_date.strftime('%Y-%m-%d')}",
            f"Signals Found: {self.total_signals_found}",
            "",
            "Strategy Performance:",
        ]

        # Sort periods by length (ascending order: 3d, 1w, 2w, 1m)
        def period_sort_key(period_name: str) -> int:
            if period_name.endswith("d"):
                return int(period_name[:-1])
            elif period_name.endswith("w") or period_name.endswith("W"):
                return int(period_name[:-1]) * 7
            elif period_name.endswith("m") or period_name.endswith("M"):
                return int(period_name[:-1]) * 30
            else:
                return 999  # Unknown format, put at end

        sorted_strategy_periods = sorted(
            self.period_results.keys(), key=period_sort_key
        )

        for period_name in sorted_strategy_periods:
            result = self.period_results[period_name]
            lines.append(
                f"{period_name:8}: Avg: {result.average_return:+5.1f}%  "
                f"Win Rate: {result.win_rate:3.0f}%  "
                f"Best: {result.best_return:+5.1f}%  "
                f"Worst: {result.worst_return:+5.1f}%  "
                f"Valid: {result.valid_signals}/{result.total_signals}"
            )

        # Add benchmark performance if available
        if self.benchmark_results:
            lines.append("")
            lines.append("Benchmark Performance (Buy & Hold - Start to End Period):")

            for benchmark_symbol in ["QQQ", "SPY"]:
                if benchmark_symbol in self.benchmark_results:
                    lines.append(f"\n{benchmark_symbol}:")
                    benchmark_periods = self.benchmark_results[benchmark_symbol]

                    # Sort periods by length (ascending order: 3d, 1w, 2w, 1m)
                    def period_sort_key(period_name: str) -> int:
                        if period_name.endswith("d"):
                            return int(period_name[:-1])
                        elif period_name.endswith("w") or period_name.endswith("W"):
                            return int(period_name[:-1]) * 7
                        elif period_name.endswith("m") or period_name.endswith("M"):
                            return int(period_name[:-1]) * 30
                        else:
                            return 999  # Unknown format, put at end

                    sorted_periods = sorted(
                        benchmark_periods.keys(), key=period_sort_key
                    )

                    for period_name in sorted_periods:
                        result = benchmark_periods[period_name]
                        if result.valid_signals > 0:
                            # For benchmarks, we just show the single period return
                            lines.append(
                                f"{period_name:8}: Return: {result.average_return:+5.1f}% "
                                f"(Start to End of Period)"
                            )
                        else:
                            lines.append(f"{period_name:8}: No data available")

        # Add ranking-based performance if available
        if self.ranking_results:
            lines.append("")
            lines.append("Performance by Ranking Groups:")

            # Sort ranking groups by range start (0-20, 21-40, 41-60, 61-80, 81-100)
            sorted_ranking_groups = sorted(
                self.ranking_results.keys(), key=lambda x: int(x.split("-")[0])
            )

            for ranking_range in sorted_ranking_groups:
                ranking_perf = self.ranking_results[ranking_range]
                lines.append(
                    f"\nRanking {ranking_range} ({ranking_perf.total_signals} signals):"
                )

                sorted_periods = sorted(
                    ranking_perf.period_results.keys(), key=period_sort_key
                )

                for period_name in sorted_periods:
                    result = ranking_perf.period_results[period_name]
                    lines.append(
                        f"{period_name:8}: Avg: {result.average_return:+5.1f}%  "
                        f"Win Rate: {result.win_rate:3.0f}%  "
                        f"Best: {result.best_return:+5.1f}%  "
                        f"Worst: {result.worst_return:+5.1f}%  "
                        f"Valid: {result.valid_signals}/{result.total_signals}"
                    )

        # Add individual signal benchmark data if available
        if self.signal_benchmark_data:
            lines.append("")
            lines.append("Individual Signal Benchmark Performance:")
            lines.append("Ticker    Entry Date   Exit Date    Return%    QQQ%     SPY%")
            lines.append("-" * 60)

            # Sort by entry date
            sorted_signals = sorted(self.signal_benchmark_data, key=lambda x: x.get('entry_date', datetime.min))

            for signal_data in sorted_signals[:10]:  # Show first 10 signals
                ticker = signal_data.get('ticker', 'N/A')[:8]
                entry_date = signal_data.get('entry_date')
                exit_date = signal_data.get('exit_date')
                return_pct = signal_data.get('return_pct')
                return_pct_qqq = signal_data.get('return_pct_qqq')
                return_pct_spy = signal_data.get('return_pct_spy')

                entry_str = entry_date.strftime('%Y-%m-%d') if entry_date else 'N/A'
                exit_str = exit_date.strftime('%Y-%m-%d') if exit_date else 'N/A'
                return_str = f"{return_pct:+6.1f}" if return_pct is not None else "   N/A"
                qqq_str = f"{return_pct_qqq:+6.1f}" if return_pct_qqq is not None else "   N/A"
                spy_str = f"{return_pct_spy:+6.1f}" if return_pct_spy is not None else "   N/A"

                lines.append(f"{ticker:8} {entry_str} {exit_str} {return_str}%  {qqq_str}%  {spy_str}%")

            if len(self.signal_benchmark_data) > 10:
                lines.append(f"... and {len(self.signal_benchmark_data) - 10} more signals")

            # Calculate and display average benchmark returns
            valid_qqq: list[float] = []
            valid_spy: list[float] = []

            for s in self.signal_benchmark_data:
                qqq_val = s.get('return_pct_qqq')
                if qqq_val is not None:
                    valid_qqq.append(float(qqq_val))

                spy_val = s.get('return_pct_spy')
                if spy_val is not None:
                    valid_spy.append(float(spy_val))

            if valid_qqq:
                avg_qqq = sum(valid_qqq) / len(valid_qqq)
                lines.append("")
                lines.append(f"Average QQQ Return: {avg_qqq:+5.1f}% ({len(valid_qqq)} signals)")

            if valid_spy:
                avg_spy = sum(valid_spy) / len(valid_spy)
                lines.append(f"Average SPY Return: {avg_spy:+5.1f}% ({len(valid_spy)} signals)")

        return "\n".join(lines)
