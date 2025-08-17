import os
import logging
import pandas as pd
from datetime import datetime
from typing import List, Type, Optional
from psycopg_pool import ConnectionPool
from psycopg.rows import TupleRow
from psycopg import Connection

from turtle.data.symbol import SymbolRepo
from turtle.data.bars_history import BarsHistoryRepo
from turtle.strategy.trading_strategy import TradingStrategy
from turtle.strategy.darvas_box import DarvasBoxStrategy
from turtle.strategy.mars import MarsStrategy
from turtle.strategy.momentum import MomentumStrategy
from turtle.common.enums import TimeFrameUnit
from turtle.performance.strategy_performance import StrategyPerformanceTester

# from turtle.performance.period_return import ProfitLossTargetStrategy
from turtle.performance.period_return import EMAExitStrategy
from turtle.performance.models import TestSummary, PerformanceResult

logger = logging.getLogger(__name__)


class StrategyPerformanceService:
    """
    Service for orchestrating strategy performance testing across multiple symbols and time periods.
    """

    # Mapping of strategy names to strategy classes
    AVAILABLE_STRATEGIES = {
        "darvas_box": DarvasBoxStrategy,
        "mars": MarsStrategy,
        "momentum": MomentumStrategy,
    }

    # Default test periods
    DEFAULT_TEST_PERIODS = [
        pd.Timedelta(days=3),  # 3 days
        pd.Timedelta(weeks=1),  # 1 week
        pd.Timedelta(weeks=2),  # 2 weeks
        pd.Timedelta(days=30),  # 1 month
        pd.Timedelta(days=90),  # 3 months
        pd.Timedelta(days=180),  # 6 months
    ]

    def __init__(
        self,
        strategy_class: Type[TradingStrategy],
        signal_start_date: datetime,
        signal_end_date: datetime,
        test_periods: Optional[List[pd.Timedelta]] = None,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        dsn: str = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres",
    ):
        """
        Initialize the strategy tester service.

        Args:
            strategy_class: Strategy class to test
            signal_start_date: Start date for signal generation
            signal_end_date: End date for signal generation
            test_periods: List of time periods to test (defaults to 3d, 1w, 2w, 1m)
            time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
            dsn: Database connection string
        """
        self.strategy_class = strategy_class
        self.signal_start_date = signal_start_date
        self.signal_end_date = signal_end_date
        self.test_periods = test_periods or self.DEFAULT_TEST_PERIODS
        self.time_frame_unit = time_frame_unit

        # Initialize database connection and repositories
        self.pool: ConnectionPool[Connection[TupleRow]] = ConnectionPool(
            conninfo=dsn, min_size=5, max_size=50, max_idle=600
        )
        self.symbol_repo = SymbolRepo(self.pool, str(os.getenv("EODHD_API_KEY")))
        self.bars_history = BarsHistoryRepo(
            self.pool,
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )

        # Initialize strategy instance
        self.strategy = self.strategy_class(
            bars_history=self.bars_history, time_frame_unit=self.time_frame_unit
        )

    @classmethod
    def from_strategy_name(
        cls,
        strategy_name: str,
        signal_start_date: datetime,
        signal_end_date: datetime,
        test_periods: Optional[List[pd.Timedelta]] = None,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        dsn: str = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres",
    ) -> "StrategyPerformanceService":
        """
        Create StrategyPerformanceService instance from strategy name.

        Args:
            strategy_name: Name of the strategy ('darvas_box', 'mars', 'momentum')
            signal_start_date: Start date for signal generation
            signal_end_date: End date for signal generation
            test_periods: List of time periods to test
            time_frame_unit: Time frame for analysis
            dsn: Database connection string

        Returns:
            StrategyPerformanceService instance

        Raises:
            ValueError: If strategy name is not recognized
        """
        if strategy_name not in cls.AVAILABLE_STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. Available: {list(cls.AVAILABLE_STRATEGIES.keys())}"
            )

        strategy_class = cls.AVAILABLE_STRATEGIES[strategy_name]

        return cls(
            strategy_class=strategy_class,
            signal_start_date=signal_start_date,
            signal_end_date=signal_end_date,
            test_periods=test_periods,
            time_frame_unit=time_frame_unit,
            dsn=dsn,
        )

    def run_test(
        self,
        symbols: Optional[List[str]] = None,
        symbol_filter: str = "USA",
        max_symbols: Optional[int] = None,
    ) -> TestSummary:
        """
        Execute complete strategy performance test.

        Args:
            symbols: Optional list of specific symbols to test
            symbol_filter: Symbol filter for database query (default: "USA")
            max_symbols: Optional limit on number of symbols to test

        Returns:
            TestSummary object containing all test results
        """
        logger.info(f"Starting strategy test for {self.strategy_class.__name__}")
        logger.info(
            f"Signal period: {self.signal_start_date} to {self.signal_end_date}"
        )
        logger.info(f"Test periods: {[str(p) for p in self.test_periods]}")

        # Get symbols to test
        if symbols is None:
            symbols = self._get_symbol_list(symbol_filter, max_symbols)

        logger.info(f"Testing {len(symbols)} symbols")

        # Create performance tester
        performance_tester = StrategyPerformanceTester(
            strategy=self.strategy,
            bars_history=self.bars_history,
            start_date=self.signal_start_date,
            end_date=self.signal_end_date,
            test_periods=self.test_periods,
            # period_return_strategy=ProfitLossTargetStrategy(profit_target=15.0, stop_loss=10.0),
            period_return_strategy=EMAExitStrategy(ema_period=10),
        )

        # Generate signals for all symbols
        logger.info("Generating trading signals...")
        signal_results = performance_tester.generate_signals(symbols)
        logger.info(f"Found {len(signal_results)} trading signals")

        # Calculate performance statistics
        logger.info("Calculating performance statistics...")
        test_summary = performance_tester.calculate_performance()

        # Add benchmark performance (QQQ and SPY)
        logger.info("Calculating benchmark performance (QQQ, SPY)...")
        benchmark_results = self._calculate_benchmark_performance()
        test_summary.benchmark_results = benchmark_results

        logger.info("Strategy test completed")
        return test_summary

    def _get_symbol_list(
        self, symbol_filter: str = "USA", max_symbols: Optional[int] = None
    ) -> List[str]:
        """
        Get list of symbols to test.

        Args:
            symbol_filter: Filter for symbol selection
            max_symbols: Optional limit on number of symbols

        Returns:
            List of symbol strings
        """
        try:
            symbols = self.symbol_repo.get_symbol_list(symbol_filter)
            symbol_list = [symbol.symbol for symbol in symbols]

            if max_symbols and len(symbol_list) > max_symbols:
                symbol_list = symbol_list[:max_symbols]
                logger.info(f"Limited symbol list to {max_symbols} symbols")

            return symbol_list

        except Exception as e:
            logger.error(f"Error getting symbol list: {str(e)}")
            return []

    def _calculate_benchmark_performance(self) -> dict:
        """
        Calculate benchmark performance for QQQ and SPY over the same test periods.

        Returns:
            Dictionary mapping benchmark symbols to their PerformanceResult objects
        """
        benchmark_symbols = ["QQQ", "SPY"]
        benchmark_results = {}

        for symbol in benchmark_symbols:
            try:
                logger.debug(f"Calculating benchmark performance for {symbol}")

                # Calculate returns for each test period
                period_performance = {}
                for period in self.test_periods:
                    period_name = self._format_period_name(period)
                    returns = self._calculate_benchmark_returns_for_period(
                        symbol, period
                    )

                    performance = PerformanceResult.from_returns(
                        period_name=period_name,
                        total_signals=len(returns),
                        returns=returns,
                    )
                    period_performance[period_name] = performance

                benchmark_results[symbol] = period_performance

            except Exception as e:
                logger.error(
                    f"Error calculating benchmark performance for {symbol}: {str(e)}"
                )
                continue

        return benchmark_results

    def _calculate_benchmark_returns_for_period(
        self, symbol: str, period: pd.Timedelta
    ) -> List[float]:
        """
        Calculate percentage change for the specific period from signal start date.

        Args:
            symbol: Benchmark symbol (QQQ or SPY)
            period: Time period to calculate return for

        Returns:
            List with single percentage return for the specified period
        """
        returns = []

        try:
            # Calculate the end date for this specific period
            period_end_date = self.signal_start_date + period

            # Get benchmark data for this specific period range
            df = self.bars_history.get_ticker_history(
                symbol,
                self.signal_start_date,
                period_end_date,
                self.time_frame_unit,
            )

            if df.empty or len(df) < 2:
                logger.warning(
                    f"Insufficient data for benchmark {symbol} for period {period}"
                )
                return returns

            # Get start and end prices
            start_price = df.iloc[0]["close"]
            end_price = df.iloc[-1]["close"]

            if start_price > 0:
                return_pct = ((end_price - start_price) / start_price) * 100
                returns.append(return_pct)
                period_name = self._format_period_name(period)
                logger.debug(
                    f"Benchmark {symbol} {period_name} return: {return_pct:.2f}% "
                    f"(from {start_price:.2f} to {end_price:.2f}, "
                    f"{self.signal_start_date.strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')})"
                )

        except Exception as e:
            logger.error(
                f"Error calculating benchmark return for {symbol} period {period}: {e}"
            )

        return returns

    def _format_period_name(self, period: pd.Timedelta) -> str:
        """
        Format a pandas Timedelta into a readable period name.

        Args:
            period: pandas Timedelta object

        Returns:
            Formatted period name (e.g., '3d', '1W', '2W', '1M')
        """
        if period.days < 7:
            return f"{period.days}d"
        elif period.days < 30:
            weeks = period.days // 7
            return f"{weeks}W"
        else:
            months = period.days // 30
            return f"{months}M"

    def _generate_report(
        self, test_summary: TestSummary, output_format: str = "console"
    ) -> str:
        """
        Generate formatted report from test results.

        Args:
            test_summary: TestSummary object with results
            output_format: Output format ('console', 'csv', 'json')

        Returns:
            Formatted report string
        """
        if output_format == "console":
            return test_summary.format_summary()
        elif output_format == "csv":
            return self._format_csv_report(test_summary)
        elif output_format == "json":
            return self._format_json_report(test_summary)
        else:
            raise ValueError(f"Unknown output format: {output_format}")

    def _format_csv_report(self, test_summary: TestSummary) -> str:
        """Format test results as CSV."""
        lines = [
            "Type,Symbol,Period,Total_Signals,Valid_Signals,Avg_Return,Win_Rate,Best_Return,Worst_Return,Period_Return"
        ]

        # Sort periods by length (ascending order: 3d, 1w, 2w, 1m)
        def period_sort_key(period_name):
            if period_name.endswith("d"):
                return int(period_name[:-1])
            elif period_name.endswith("w") or period_name.endswith("W"):
                return int(period_name[:-1]) * 7
            elif period_name.endswith("m") or period_name.endswith("M"):
                return int(period_name[:-1]) * 30
            else:
                return 999  # Unknown format, put at end

        # Add strategy results (sorted by period length)
        sorted_strategy_periods = sorted(
            test_summary.period_results.keys(), key=period_sort_key
        )
        for period_name in sorted_strategy_periods:
            result = test_summary.period_results[period_name]
            lines.append(
                f"Strategy,{test_summary.strategy_name},{period_name},{result.total_signals},{result.valid_signals},"
                f"{result.average_return:.2f},{result.win_rate:.1f},"
                f"{result.best_return:.2f},{result.worst_return:.2f},"
            )

        # Add benchmark results if available (sorted by period length)
        if test_summary.benchmark_results:
            for benchmark_symbol in ["QQQ", "SPY"]:
                if benchmark_symbol in test_summary.benchmark_results:
                    benchmark_periods = test_summary.benchmark_results[benchmark_symbol]
                    sorted_benchmark_periods = sorted(
                        benchmark_periods.keys(), key=period_sort_key
                    )

                    for period_name in sorted_benchmark_periods:
                        result = benchmark_periods[period_name]
                        # For benchmarks, the period return is the simple start-to-end return
                        period_return = (
                            result.average_return if result.valid_signals > 0 else 0.0
                        )
                        lines.append(
                            f"Benchmark,{benchmark_symbol},{period_name},1,{result.valid_signals},"
                            f"{result.average_return:.2f},N/A,N/A,N/A,{period_return:.2f}"
                        )

        return "\n".join(lines)

    def _format_json_report(self, test_summary: TestSummary) -> str:
        """Format test results as JSON."""
        import json

        data = {
            "strategy_name": test_summary.strategy_name,
            "test_start_date": test_summary.test_start_date.isoformat(),
            "test_end_date": test_summary.test_end_date.isoformat(),
            "total_signals_found": test_summary.total_signals_found,
            "strategy_results": {},
            "benchmark_results": {},
        }

        # Add strategy results
        for period_name, result in test_summary.period_results.items():
            data["strategy_results"][period_name] = {
                "total_signals": result.total_signals,
                "valid_signals": result.valid_signals,
                "average_return": result.average_return,
                "win_rate": result.win_rate,
                "best_return": result.best_return,
                "worst_return": result.worst_return,
            }

        # Add benchmark results if available
        if test_summary.benchmark_results:
            for (
                benchmark_symbol,
                benchmark_periods,
            ) in test_summary.benchmark_results.items():
                data["benchmark_results"][benchmark_symbol] = {}
                for period_name, result in benchmark_periods.items():
                    data["benchmark_results"][benchmark_symbol][period_name] = {
                        "total_signals": result.total_signals,
                        "valid_signals": result.valid_signals,
                        "average_return": result.average_return,
                        "win_rate": result.win_rate,
                        "best_return": result.best_return,
                        "worst_return": result.worst_return,
                    }

        return json.dumps(data, indent=2)

    def print_results(
        self, test_summary: TestSummary, output_format: str = "console"
    ) -> None:
        """
        Print test results in specified format.

        Args:
            test_summary: TestSummary object with results
            output_format: Output format ('console', 'csv', 'json')
        """
        report = self._generate_report(test_summary, output_format)
        print(report)

    def save_results(
        self, test_summary: TestSummary, filename: str, output_format: str = "csv"
    ) -> None:
        """
        Save test results to file.

        Args:
            test_summary: TestSummary object with results
            filename: Output filename
            output_format: Output format ('csv', 'json')
        """
        report = self._generate_report(test_summary, output_format)

        with open(filename, "w") as f:
            f.write(report)

        logger.info(f"Results saved to {filename}")

    def __del__(self):
        """Clean up database connection pool."""
        if hasattr(self, "pool"):
            self.pool.close()
