import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from turtle.data.bars_history import BarsHistoryRepo
from turtle.signal.base import TradingStrategy
from turtle.backtest.models import LegacySignalResult, PerformanceResult, TestSummary, RankingPerformance
from turtle.backtest.period_return import TradeExitStrategy, BuyAndHoldStrategy, PeriodReturnResult

logger = logging.getLogger(__name__)


class StrategyPerformanceTester:
    """
    Core class for testing trading strategy performance by analyzing historical signals
    and calculating returns over various time periods.
    """

    def __init__(
        self,
        strategy: TradingStrategy,
        bars_history: BarsHistoryRepo,
        start_date: datetime,
        end_date: datetime,
        max_holding_period: pd.Timedelta,
        period_return_strategy: TradeExitStrategy | None = None,
        period_return_strategy_kwargs: dict | None = None,
    ):
        """
        Initialize the strategy performance tester.

        Args:
            strategy: Trading strategy instance to test
            bars_history: Repository for accessing historical bar data
            start_date: Start date for signal generation
            end_date: End date for signal generation
            max_holding_period: Maximum holding period for analysis (e.g., pd.Timedelta(days=30))
            period_return_strategy: Optional TradeExitStrategy instance to use for return calculations
                                   If None, defaults to BuyAndHoldStrategy()
            period_return_strategy_kwargs: Optional kwargs to pass to period return strategy calculations
        """
        self.strategy = strategy
        self.bars_history = bars_history
        self.start_date = start_date
        self.end_date = end_date
        self.max_holding_period = max_holding_period
        self.period_return_strategy = period_return_strategy or BuyAndHoldStrategy()
        self.period_return_strategy_kwargs = period_return_strategy_kwargs or {}
        self.signal_results: list[LegacySignalResult] = []

    def generate_signals(self, tickers: list[str]) -> list[LegacySignalResult]:
        """
        Generate trading signals for given tickers within the date range.

        Args:
            tickers: List of stock symbols to analyze

        Returns:
            List of LegacySignalResult objects containing signal information
        """
        signal_results = []

        for ticker in tickers:
            try:
                logger.debug(f"Analyzing signals for {ticker}")

                # Collect historical data for the ticker
                if not self.strategy.collect_data(ticker, self.start_date, self.end_date):
                    logger.warning(f"Insufficient data for {ticker}")
                    continue

                # Calculate indicators
                self.strategy.calculate_indicators()

                # Find all trading signals in the date range
                signals_count = len(self.strategy.get_signals(ticker, self.start_date, self.end_date))

                if signals_count > 0:
                    # Get the DataFrame with buy signals
                    df = self.strategy.df
                    signal_dates = df[df["buy_signal"]]["hdate"].tolist()

                    for signal_date in signal_dates:
                        signal_result = self._process_signal(ticker, signal_date)
                        if signal_result:
                            signal_results.append(signal_result)

            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                continue

        self.signal_results = signal_results
        return signal_results

    def _process_signal(self, ticker: str, signal_date: datetime) -> LegacySignalResult | None:
        """
        Process a single trading signal and calculate returns for all test periods.

        Args:
            ticker: Stock symbol
            signal_date: Date when the signal was generated

        Returns:
            LegacySignalResult object or None if processing failed
        """
        try:
            # Get entry price (opening price of next trading day)
            entry_date, entry_price = self._get_entry_price(ticker, signal_date)
            if entry_price is None or entry_date is None:
                logger.debug(f"No entry price found for {ticker} on {signal_date}")
                return None

            # Calculate period results (backward compatibility)
            # Single period analysis
            period_name = self._format_period_name(self.max_holding_period)

            # Legacy closing price calculation for backward compatibility
            closing_price = self._get_closing_price_after_period(ticker, entry_date, self.max_holding_period)
            period_results = {period_name: closing_price}

            # Get full OHLCV data for the period
            target_date = entry_date + self.max_holding_period
            ohlcv_data = self._get_period_data(ticker, entry_date, target_date)
            period_data = {}
            if ohlcv_data is not None:
                period_data[period_name] = {"target_date": target_date, "data": ohlcv_data}

            # Calculate ranking for this signal
            # ranking = self.strategy.ranking(ticker, signal_date)
            ranking = 0

            return LegacySignalResult(
                ticker=ticker,
                signal_date=signal_date,
                entry_price=entry_price,
                entry_date=entry_date,
                period_results=period_results,
                ranking=ranking,
                period_data=period_data if period_data else None,
            )

        except Exception as e:
            logger.error(f"Error processing signal for {ticker} on {signal_date}: {str(e)}")
            return None

    def _get_entry_price(self, ticker: str, signal_date: datetime) -> tuple[datetime | None, float | None]:
        """
        Get the opening price of the next trading day after the signal.

        Args:
            ticker: Stock symbol
            signal_date: Date when signal was generated

        Returns:
            Tuple of (entry_date, entry_price) or (None, None) if not found
        """
        try:
            # Get data starting from signal date + 1 day for up to 5 days to find next trading day
            start_search = signal_date + timedelta(days=1)
            end_search = signal_date + timedelta(days=5)

            df = self.bars_history.get_ticker_history(ticker, start_search, end_search, self.strategy.time_frame_unit)

            if df.empty:
                return None, None

            # Get the first available trading day's opening price
            first_row = df.iloc[0]
            entry_date = pd.to_datetime(df.index[0]) if isinstance(df.index[0], str | pd.Timestamp) else df.index[0]
            entry_price = first_row["open"]

            return entry_date, float(entry_price)

        except Exception as e:
            logger.error(f"Error getting entry price for {ticker} after {signal_date}: {str(e)}")
            return None, None

    def _get_closing_price_after_period(self, ticker: str, entry_date: datetime, period: pd.Timedelta) -> float | None:
        """
        Get the closing price after a specific period from entry date.

        Args:
            ticker: Stock symbol
            entry_date: Date when position was entered
            period: Time period to wait before getting closing price

        Returns:
            Closing price or None if not available
        """
        try:
            # Calculate target date using business days for more accurate trading day calculation
            if period.days <= 7:
                # For shorter periods, use exact date calculation
                target_date = entry_date + period
            else:
                # For longer periods, use business day calculation
                business_days = period.days * (5 / 7)  # Approximate business days
                target_date = entry_date + pd.Timedelta(days=business_days)

            # Get data around the target date (±5 days to handle weekends/holidays)
            start_search = target_date - timedelta(days=2)
            end_search = target_date + timedelta(days=5)

            df = self.bars_history.get_ticker_history(ticker, start_search, end_search, self.strategy.time_frame_unit)

            if df.empty:
                return None

            # Find the closest trading day to our target date
            df_copy = df.copy()
            # Calculate date differences in days using simple subtraction
            date_diffs = []
            for idx in df_copy.index:
                if isinstance(idx, pd.Timestamp):
                    diff_days = abs((idx - target_date).days)
                else:
                    diff_days = abs((pd.to_datetime(idx) - target_date).days)
                date_diffs.append(diff_days)

            df_copy["date_diff"] = date_diffs
            closest_idx = df_copy["date_diff"].idxmin()
            closest_row = df_copy.loc[closest_idx]

            # Ensure we get a scalar value from the Series
            close_value = closest_row["close"]

            # Handle various pandas types to get a scalar value
            import numpy as np

            if isinstance(close_value, pd.Series | pd.DataFrame):
                if len(close_value) > 0:
                    close_value = close_value.iloc[0]
                else:
                    return None
            elif hasattr(close_value, "item"):
                # Use .item() for numpy scalars
                close_value = close_value.item()

            # Convert to Python float with comprehensive type handling
            if isinstance(close_value, int | float | np.number):
                return float(close_value)
            else:
                try:
                    return float(str(close_value))
                except (ValueError, TypeError) as e:
                    logger.error(f"Cannot convert close value to float: {close_value} (type: {type(close_value)}), error: {e}")
                    return None

        except Exception as e:
            logger.error(f"Error getting closing price for {ticker} after period {period}: {str(e)}")
            return None

    def _get_period_data(self, ticker: str, entry_date: datetime, target_date: datetime) -> pd.DataFrame | None:
        """
        Get OHLCV data for the entire period from entry to target date.

        Args:
            ticker: Stock symbol
            entry_date: Date when position was entered
            target_date: Target end date for the period

        Returns:
            DataFrame with OHLCV data or None if not available
        """
        try:
            # Get data with some buffer before entry date for EMA calculations
            buffer_days = 30  # Buffer for technical indicators
            start_date = entry_date - timedelta(days=buffer_days)
            end_date = target_date + timedelta(days=5)  # Buffer after target

            df = self.bars_history.get_ticker_history(ticker, start_date, end_date, self.strategy.time_frame_unit)

            if df.empty:
                return None

            # Ensure we have the required columns
            required_columns = ["open", "high", "low", "close", "volume"]
            if not all(col in df.columns for col in required_columns):
                logger.warning(f"Missing required OHLCV columns for {ticker}")
                return None

            return df

        except Exception as e:
            logger.error(f"Error getting period data for {ticker} from {entry_date} to {target_date}: {str(e)}")
            return None

    def _calculate_benchmark_returns(self, entry_date: datetime, exit_date: datetime) -> tuple[float | None, float | None]:
        """
        Calculate QQQ and SPY benchmark returns for the same period as a signal.

        Args:
            entry_date: Date when position was entered
            exit_date: Date when position was exited

        Returns:
            Tuple of (qqq_return_pct, spy_return_pct) or (None, None) if data not available
        """
        qqq_return = None
        spy_return = None

        for symbol in ["QQQ", "SPY"]:
            try:
                # Get data for the benchmark symbol for the same period
                # Add small buffer to ensure we have data
                start_date = entry_date - timedelta(days=1)
                end_date = exit_date + timedelta(days=2)

                df = self.bars_history.get_ticker_history(symbol, start_date, end_date, self.strategy.time_frame_unit)

                if df.empty:
                    logger.debug(f"No benchmark data available for {symbol}")
                    continue

                # Find opening price on or after entry_date
                entry_mask = df.index >= pd.Timestamp(entry_date)
                entry_data = df[entry_mask]
                if entry_data.empty:
                    logger.debug(f"No entry data for {symbol} on {entry_date}")
                    continue

                entry_price = entry_data.iloc[0]["open"]

                # Find closing price on or closest to exit_date
                exit_mask = df.index <= pd.Timestamp(exit_date)
                exit_data = df[exit_mask]
                if exit_data.empty:
                    logger.debug(f"No exit data for {symbol} on {exit_date}")
                    continue

                # Get the closest trading day to exit date
                target_timestamp = pd.Timestamp(exit_date)
                date_diffs = np.abs((exit_data.index - target_timestamp).astype("timedelta64[ns]"))
                min_diff_idx = int(np.argmin(date_diffs))
                closest_idx = exit_data.index[min_diff_idx]
                exit_price = exit_data.loc[closest_idx, "close"]

                # Calculate percentage return
                if entry_price > 0:
                    return_pct = ((exit_price - entry_price) / entry_price) * 100
                    if symbol == "QQQ":
                        qqq_return = return_pct
                    elif symbol == "SPY":
                        spy_return = return_pct

                    logger.debug(f"Benchmark {symbol}: {return_pct:.2f}% ({entry_price:.2f} -> {exit_price:.2f})")

            except Exception as e:
                logger.error(f"Error calculating {symbol} benchmark return: {e}")
                continue

        return qqq_return, spy_return

    def _calculate_signal_return_with_benchmarks(self, signal_result: LegacySignalResult, period_name: str) -> PeriodReturnResult | None:
        """
        Calculate return for a signal with benchmark data using the configured period return strategy.

        Args:
            signal_result: LegacySignalResult to calculate return for
            period_name: Name of the period (e.g., '1W', '2W', '1M')

        Returns:
            PeriodReturnResult with benchmark data or None if calculation failed
        """

        # If we have period data, use the period return strategy directly
        if signal_result.period_data and period_name in signal_result.period_data:
            try:
                period_info = signal_result.period_data[period_name]
                target_date = period_info["target_date"]
                data = period_info["data"]

                result = self.period_return_strategy.calculate_return(
                    data=data, entry_price=signal_result.entry_price, entry_date=signal_result.entry_date, target_date=target_date
                )

                if result:
                    # Calculate benchmark returns for the same period
                    qqq_return, spy_return = self._calculate_benchmark_returns(
                        result.entry_date or signal_result.entry_date, result.exit_date
                    )

                    # Update the result with benchmark data
                    result.return_pct_qqq = qqq_return
                    result.return_pct_spy = spy_return

                    return result

            except Exception:
                # Fall back to SignalResult method
                pass

        # Fallback to SignalResult's method (for backward compatibility)
        return_pct = signal_result.get_return_for_period(period_name, **self.period_return_strategy_kwargs)
        if return_pct is not None:
            # Create a simple PeriodReturnResult for backward compatibility
            # We don't have exit date/price from the legacy method, so we'll estimate
            target_date = signal_result.entry_date + self.max_holding_period

            # Calculate benchmark returns
            qqq_return, spy_return = self._calculate_benchmark_returns(signal_result.entry_date, target_date)

            return PeriodReturnResult(
                return_pct=return_pct,
                exit_price=0.0,  # Not available from legacy method
                exit_date=target_date,
                exit_reason="period_end",
                entry_date=signal_result.entry_date,
                entry_price=signal_result.entry_price,
                return_pct_qqq=qqq_return,
                return_pct_spy=spy_return,
            )

        return None

    def _calculate_signal_return(self, signal_result: LegacySignalResult, period_name: str) -> float | None:
        """
        Calculate return for a signal using the configured period return strategy.

        Args:
            signal_result: LegacySignalResult to calculate return for
            period_name: Name of the period (e.g., '1W', '2W', '1M')

        Returns:
            Percentage return or None if calculation failed
        """
        # If we have period data, use the period return strategy directly
        if signal_result.period_data and period_name in signal_result.period_data:
            try:
                period_info = signal_result.period_data[period_name]
                target_date = period_info["target_date"]
                data = period_info["data"]

                result = self.period_return_strategy.calculate_return(
                    data=data, entry_price=signal_result.entry_price, entry_date=signal_result.entry_date, target_date=target_date
                )

                if result:
                    return result.return_pct

            except Exception:
                # Fall back to SignalResult method
                pass

        # Fallback to SignalResult's method (for backward compatibility)
        return signal_result.get_return_for_period(period_name, **self.period_return_strategy_kwargs)

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

    def calculate_performance(self) -> TestSummary:
        """
        Calculate performance statistics from generated signals.

        Returns:
            TestSummary object containing aggregated performance results
        """
        if not self.signal_results:
            logger.warning("No signal results to analyze")
            return TestSummary(
                strategy_name=self.strategy.__class__.__name__,
                test_start_date=self.start_date,
                test_end_date=self.end_date,
                total_signals_found=0,
                period_results={},
                max_holding_period=self.max_holding_period,
            )

        # Calculate performance for single holding period
        period_name = self._format_period_name(self.max_holding_period)
        returns = []
        benchmark_data = []  # Store individual signal benchmark data

        for signal_result in self.signal_results:
            # Use the period return strategy with benchmarks to calculate returns
            result = self._calculate_signal_return_with_benchmarks(signal_result, period_name)
            if result is not None:
                returns.append(result.return_pct)
                # Store benchmark data for this signal
                benchmark_data.append(
                    {
                        "ticker": signal_result.ticker,
                        "entry_date": result.entry_date,
                        "exit_date": result.exit_date,
                        "return_pct": result.return_pct,
                        "return_pct_qqq": result.return_pct_qqq,
                        "return_pct_spy": result.return_pct_spy,
                    }
                )

        performance = PerformanceResult.from_returns(period_name=period_name, total_signals=len(self.signal_results), returns=returns)
        period_results = {period_name: performance}

        # Calculate ranking-based performance
        ranking_results = self._calculate_ranking_performance()

        return TestSummary(
            strategy_name=self.strategy.__class__.__name__,
            test_start_date=self.start_date,
            test_end_date=self.end_date,
            total_signals_found=len(self.signal_results),
            period_results=period_results,
            max_holding_period=self.max_holding_period,
            ranking_results=ranking_results,
            signal_benchmark_data=benchmark_data,
        )

    def _calculate_ranking_performance(self) -> dict[str, "RankingPerformance"]:
        """
        Calculate performance statistics grouped by ranking ranges.

        Returns:
            Dictionary mapping ranking ranges to RankingPerformance objects
        """
        from turtle.backtest.models import RankingPerformance

        # Define ranking ranges
        ranking_ranges = {"0-20": (0, 20), "21-40": (21, 40), "41-60": (41, 60), "61-80": (61, 80), "81-100": (81, 100)}

        ranking_results = {}

        for range_name, (min_rank, max_rank) in ranking_ranges.items():
            # Filter signals by ranking range
            range_signals = [signal for signal in self.signal_results if min_rank <= signal.ranking <= max_rank]

            if not range_signals:
                # Create empty performance results for this range
                period_performance = {}
                period_name = self._format_period_name(self.max_holding_period)
                performance = PerformanceResult.from_returns(period_name=period_name, total_signals=0, returns=[])
                period_performance = {period_name: performance}

                ranking_results[range_name] = RankingPerformance(
                    ranking_range=range_name, period_results=period_performance, total_signals=0
                )
                continue

            # Calculate performance for single holding period for this ranking range
            period_name = self._format_period_name(self.max_holding_period)
            returns = []

            for signal_result in range_signals:
                return_pct = self._calculate_signal_return(signal_result, period_name)
                if return_pct is not None:
                    returns.append(return_pct)

            performance = PerformanceResult.from_returns(period_name=period_name, total_signals=len(range_signals), returns=returns)
            period_performance = {period_name: performance}

            ranking_results[range_name] = RankingPerformance(
                ranking_range=range_name, period_results=period_performance, total_signals=len(range_signals)
            )

        return ranking_results

    def get_results(self) -> TestSummary:
        """
        Get the complete test results.

        Returns:
            TestSummary object with all performance statistics
        """
        return self.calculate_performance()
