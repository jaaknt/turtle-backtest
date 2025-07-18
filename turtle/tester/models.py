from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import pandas as pd


@dataclass
class SignalResult:
    """
    Represents a single trading signal and its outcomes.
    
    Attributes:
        ticker: Stock symbol that generated the signal
        signal_date: Date when the trading signal was generated
        entry_price: Opening price of the next trading day after signal
        entry_date: Date when entry price was recorded
        period_results: Dictionary mapping period names to closing prices
        ranking: Strategy ranking score (0-100) for this signal
    """
    ticker: str
    signal_date: datetime
    entry_price: float
    entry_date: datetime
    period_results: dict[str, Optional[float]]  # period_name -> closing_price
    ranking: int = 0

    def get_return_for_period(self, period_name: str) -> Optional[float]:
        """
        Calculate percentage return for a specific period.
        
        Args:
            period_name: Name of the period (e.g., '3d', '1w', '2w', '1m')
            
        Returns:
            Percentage return or None if data not available
        """
        if period_name not in self.period_results:
            return None
            
        closing_price = self.period_results[period_name]
        if closing_price is None or self.entry_price <= 0:
            return None
            
        return ((closing_price - self.entry_price) / self.entry_price) * 100


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
    returns: List[float]

    @classmethod
    def from_returns(cls, period_name: str, total_signals: int, returns: List[float]) -> 'PerformanceResult':
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
                returns=[]
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
            returns=returns
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
    """
    strategy_name: str
    test_start_date: datetime
    test_end_date: datetime
    total_signals_found: int
    period_results: dict[str, PerformanceResult]
    test_periods: List[pd.Timedelta]
    benchmark_results: Optional[dict] = None
    ranking_results: Optional[dict[str, RankingPerformance]] = None

    def get_performance_for_period(self, period_name: str) -> Optional[PerformanceResult]:
        """Get performance results for a specific period."""
        return self.period_results.get(period_name)
    
    def get_all_periods(self) -> List[str]:
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
            "Strategy Performance:"
        ]
        
        # Sort periods by length (ascending order: 3d, 1w, 2w, 1m)
        def period_sort_key(period_name):
            if period_name.endswith('d'):
                return int(period_name[:-1])
            elif period_name.endswith('w') or period_name.endswith('W'):
                return int(period_name[:-1]) * 7
            elif period_name.endswith('m') or period_name.endswith('M'):
                return int(period_name[:-1]) * 30
            else:
                return 999  # Unknown format, put at end
        
        sorted_strategy_periods = sorted(self.period_results.keys(), key=period_sort_key)
        
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
            
            for benchmark_symbol in ['QQQ', 'SPY']:
                if benchmark_symbol in self.benchmark_results:
                    lines.append(f"\n{benchmark_symbol}:")
                    benchmark_periods = self.benchmark_results[benchmark_symbol]
                    
                    # Sort periods by length (ascending order: 3d, 1w, 2w, 1m)
                    def period_sort_key(period_name):
                        if period_name.endswith('d'):
                            return int(period_name[:-1])
                        elif period_name.endswith('w') or period_name.endswith('W'):
                            return int(period_name[:-1]) * 7
                        elif period_name.endswith('m') or period_name.endswith('M'):
                            return int(period_name[:-1]) * 30
                        else:
                            return 999  # Unknown format, put at end
                    
                    sorted_periods = sorted(benchmark_periods.keys(), key=period_sort_key)
                    
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
            sorted_ranking_groups = sorted(self.ranking_results.keys(), 
                                         key=lambda x: int(x.split('-')[0]))
            
            for ranking_range in sorted_ranking_groups:
                ranking_perf = self.ranking_results[ranking_range]
                lines.append(f"\nRanking {ranking_range} ({ranking_perf.total_signals} signals):")
                
                sorted_periods = sorted(ranking_perf.period_results.keys(), key=period_sort_key)
                
                for period_name in sorted_periods:
                    result = ranking_perf.period_results[period_name]
                    lines.append(
                        f"{period_name:8}: Avg: {result.average_return:+5.1f}%  "
                        f"Win Rate: {result.win_rate:3.0f}%  "
                        f"Best: {result.best_return:+5.1f}%  "
                        f"Worst: {result.worst_return:+5.1f}%  "
                        f"Valid: {result.valid_signals}/{result.total_signals}"
                    )
        
        return "\n".join(lines)