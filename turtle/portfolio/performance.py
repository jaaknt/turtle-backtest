"""Portfolio performance analytics and quantstats integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
import pandas as pd
import numpy as np

try:
    import quantstats as qs  # type: ignore[import-untyped]
    QUANTSTATS_AVAILABLE = True
except ImportError:
    QUANTSTATS_AVAILABLE = False
    qs = None  # type: ignore[assignment]

from turtle.data.bars_history import BarsHistoryRepo
from turtle.backtest.benchmark_utils import calculate_benchmark_list
from .models import PortfolioState, PortfolioResults

logger = logging.getLogger(__name__)


class PortfolioAnalytics:
    """
    Comprehensive portfolio performance analytics with quantstats integration.

    Calculates portfolio metrics, benchmark comparisons, and risk analytics.
    """

    def __init__(self) -> None:
        """Initialize portfolio analytics."""
        pass

    def generate_results(
        self,
        portfolio_state: PortfolioState,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        benchmark_tickers: list[str],
        bars_history: BarsHistoryRepo,
    ) -> PortfolioResults:
        """
        Generate comprehensive portfolio results with performance analytics.

        Args:
            portfolio_state: Final portfolio state
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital amount
            benchmark_tickers: Benchmark ticker symbols
            bars_history: Data repository for benchmark data

        Returns:
            Complete PortfolioResults with analytics
        """
        logger.info("Generating portfolio performance results")

        # Calculate basic metrics from final snapshot
        final_snapshot = portfolio_state.daily_snapshots[-1] if portfolio_state.daily_snapshots else None
        final_value = final_snapshot.total_value if final_snapshot else initial_capital
        total_return_dollars = final_value - initial_capital
        total_return_pct = (total_return_dollars / initial_capital) * 100.0

        # Extract daily data
        daily_returns, daily_values = self._extract_daily_series(portfolio_state)

        # Calculate trade statistics
        trade_stats = self._calculate_trade_statistics(portfolio_state.closed_trades)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(daily_returns, daily_values)

        # Calculate benchmark returns
        benchmark_returns = calculate_benchmark_list(
            start_date, end_date, benchmark_tickers, bars_history
        )

        # Create results object
        results = PortfolioResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            final_cash=final_snapshot.cash if final_snapshot else 0.0,
            total_return_pct=total_return_pct,
            total_return_dollars=total_return_dollars,
            daily_returns=daily_returns,
            daily_values=daily_values,
            closed_positions=portfolio_state.closed_trades,
            max_positions_held=self._calculate_max_positions_held(portfolio_state),
            total_trades=int(trade_stats["total_trades"]),
            winning_trades=int(trade_stats["winning_trades"]),
            losing_trades=int(trade_stats["losing_trades"]),
            win_rate=trade_stats["win_rate"],
            avg_win_pct=trade_stats["avg_win_pct"],
            avg_loss_pct=trade_stats["avg_loss_pct"],
            avg_holding_period=trade_stats["avg_holding_period"],
            max_drawdown_pct=risk_metrics["max_drawdown_pct"],
            sharpe_ratio=risk_metrics["sharpe_ratio"],
            volatility=risk_metrics["volatility"],
            benchmark_returns=benchmark_returns,
        )

        logger.info(
            f"Results generated: {results.total_return_pct:.2f}% return, "
            f"{results.total_trades} trades, {results.win_rate:.1f}% win rate"
        )

        return results

    def _extract_daily_series(self, portfolio_state: PortfolioState) -> tuple[pd.Series, pd.Series]:
        """
        Extract daily returns and values from portfolio snapshots.

        Args:
            portfolio_state: Portfolio state with daily snapshots

        Returns:
            Tuple of (daily_returns_series, daily_values_series)
        """
        if not portfolio_state.daily_snapshots:
            return pd.Series(dtype=float), pd.Series(dtype=float)

        dates = [snapshot.date for snapshot in portfolio_state.daily_snapshots]
        returns = [snapshot.daily_return for snapshot in portfolio_state.daily_snapshots]
        values = [snapshot.total_value for snapshot in portfolio_state.daily_snapshots]

        daily_returns = pd.Series(returns, index=dates, name="daily_returns")
        daily_values = pd.Series(values, index=dates, name="portfolio_value")

        return daily_returns, daily_values

    def _calculate_trade_statistics(self, closed_positions: list) -> dict[str, float]:
        """
        Calculate comprehensive trade statistics.

        Args:
            closed_positions: List of closed positions

        Returns:
            Dictionary with trade statistics
        """
        if not closed_positions:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win_pct": 0.0,
                "avg_loss_pct": 0.0,
                "avg_holding_period": 0.0,
            }

        total_trades = len(closed_positions)
        winning_trades = len([p for p in closed_positions if p.realized_pnl > 0])
        losing_trades = total_trades - winning_trades

        win_rate = (winning_trades / total_trades) * 100.0 if total_trades > 0 else 0.0

        # Calculate average win/loss percentages
        winning_positions = [p for p in closed_positions if p.realized_pnl > 0]
        losing_positions = [p for p in closed_positions if p.realized_pnl <= 0]

        avg_win_pct = (
            sum(p.realized_pct for p in winning_positions) / len(winning_positions)
            if winning_positions else 0.0
        )

        avg_loss_pct = (
            sum(p.realized_pct for p in losing_positions) / len(losing_positions)
            if losing_positions else 0.0
        )

        # Calculate average holding period
        avg_holding_period = (
            sum(p.holding_days for p in closed_positions) / total_trades
            if total_trades > 0 else 0.0
        )

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_win_pct": avg_win_pct,
            "avg_loss_pct": avg_loss_pct,
            "avg_holding_period": avg_holding_period,
        }

    def _calculate_risk_metrics(self, daily_returns: pd.Series, daily_values: pd.Series) -> dict[str, float]:
        """
        Calculate portfolio risk metrics.

        Args:
            daily_returns: Series of daily returns
            daily_values: Series of daily portfolio values

        Returns:
            Dictionary with risk metrics
        """
        if daily_returns.empty or len(daily_returns) < 2:
            return {
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0,
                "volatility": 0.0,
            }

        # Calculate maximum drawdown
        max_drawdown_pct = self._calculate_max_drawdown(daily_values)

        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        annual_return = daily_returns.mean() * 252  # Annualized
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0.0

        return {
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe_ratio,
            "volatility": volatility,
        }

    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """
        Calculate maximum drawdown percentage.

        Args:
            values: Series of portfolio values

        Returns:
            Maximum drawdown as percentage
        """
        if values.empty or len(values) < 2:
            return 0.0

        # Calculate running maximum
        cummax = values.cummax()

        # Calculate drawdown
        drawdown = (values - cummax) / cummax * 100.0

        # Return maximum drawdown (most negative value)
        return float(abs(drawdown.min()))


    def _calculate_max_positions_held(self, portfolio_state: PortfolioState) -> int:
        """
        Calculate maximum number of positions held simultaneously.

        Args:
            portfolio_state: Portfolio state with daily snapshots

        Returns:
            Maximum number of positions held at any time
        """
        if not portfolio_state.daily_snapshots:
            return 0

        return max(snapshot.positions_count for snapshot in portfolio_state.daily_snapshots)

    def print_performance_summary(self, results: PortfolioResults, include_quantstats: bool = True) -> None:
        """
        Print formatted performance summary with optional quantstats metrics.

        Args:
            results: Portfolio results to summarize
            include_quantstats: Whether to include additional quantstats metrics
        """
        print(f"\n{'='*60}")
        print("PORTFOLIO BACKTEST RESULTS")
        print(f"{'='*60}")
        print(f"Period: {results.start_date.date()} to {results.end_date.date()}")
        print(f"Initial Capital: ${results.initial_capital:,.2f}")
        print(f"Final Value: ${results.final_value:,.2f}")
        print(f"Total Return: ${results.total_return_dollars:,.2f} ({results.total_return_pct:.2f}%)")
        print("\nTRADE STATISTICS:")
        print(f"Total Trades: {results.total_trades}")
        print(f"Winning Trades: {results.winning_trades} ({results.win_rate:.1f}%)")
        print(f"Losing Trades: {results.losing_trades}")
        print(f"Average Win: {results.avg_win_pct:.2f}%")
        print(f"Average Loss: {results.avg_loss_pct:.2f}%")
        print(f"Average Holding Period: {results.avg_holding_period:.1f} days")
        print("\nRISK METRICS:")
        print(f"Maximum Drawdown: {results.max_drawdown_pct:.2f}%")
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print(f"Volatility: {results.volatility:.2f}%")
        print(f"Max Positions Held: {results.max_positions_held}")

        if results.benchmark_returns:
            print("\nBENCHMARK COMPARISON:")
            for benchmark in results.benchmark_returns:
                print(f"{benchmark.ticker}: {benchmark.return_pct:.2f}%")

        # Add quantstats metrics if available and requested
        if include_quantstats and QUANTSTATS_AVAILABLE and not results.daily_returns.empty:
            qs_metrics = self.get_quantstats_metrics(results)
            if qs_metrics:
                print("\nQUANTSTATS ENHANCED METRICS:")
                print(f"CAGR: {qs_metrics['cagr']:.2f}%")
                print(f"Sortino Ratio: {qs_metrics['sortino_ratio']:.2f}")
                print(f"Calmar Ratio: {qs_metrics['calmar_ratio']:.2f}")
                print(f"Value at Risk (95%): {qs_metrics['value_at_risk']:.2f}%")
                print(f"Conditional VaR (95%): {qs_metrics['conditional_value_at_risk']:.2f}%")
                print(f"Profit Factor: {qs_metrics['profit_factor']:.2f}")
                print(f"Gain to Pain Ratio: {qs_metrics['gain_to_pain_ratio']:.2f}")
                print(f"Tail Ratio: {qs_metrics['tail_ratio']:.2f}")
                print(f"Skewness: {qs_metrics['skewness']:.3f}")
                print(f"Kurtosis: {qs_metrics['kurtosis']:.3f}")

        print(f"{'='*60}")

    def create_quantstats_report(
        self,
        results: PortfolioResults,
        benchmark_ticker: str = "SPY",
        output_file: str | None = None,
        title: str = "Portfolio Performance Report",
    ) -> str | None:
        """
        Create comprehensive quantstats HTML tearsheet report.

        Args:
            results: Portfolio results with daily returns and performance data
            benchmark_ticker: Benchmark ticker for comparison (default: SPY)
            output_file: Optional file path to save HTML report
            title: Report title

        Returns:
            HTML report as string, or None if quantstats unavailable
        """
        if not QUANTSTATS_AVAILABLE:
            logger.warning("QuantStats library not available. Install with: pip install quantstats")
            return None

        if results.daily_returns.empty:
            logger.warning("No daily returns data available for quantstats report")
            return None

        try:
            # Prepare portfolio returns for quantstats
            portfolio_returns = self._prepare_returns_for_quantstats(results.daily_returns)

            # Get benchmark returns if available
            benchmark_returns = None
            if benchmark_ticker and results.benchmark_returns and benchmark_ticker in results.benchmark_returns:
                # If we have benchmark returns in results, we need daily data for quantstats
                logger.info(f"Benchmark {benchmark_ticker} total return available, but daily data needed for full analysis")

            # Generate comprehensive HTML report
            logger.info(f"Generating quantstats tearsheet with {len(portfolio_returns)} return periods")

            # Create the HTML tearsheet
            # Only pass download_filename if output_file is provided
            if output_file:
                html_report = qs.reports.html(  # type: ignore[union-attr]
                    portfolio_returns,
                    benchmark=benchmark_returns,
                    output=output_file,
                    title=title,
                    download_filename=output_file
                )
            else:
                html_report = qs.reports.html(  # type: ignore[union-attr]
                    portfolio_returns,
                    benchmark=benchmark_returns,
                    title=title
                )

            logger.info(f"QuantStats report generated successfully"
                       f"{f' and saved to {output_file}' if output_file else ''}")

            return str(html_report)

        except Exception as e:
            logger.error(f"Error generating quantstats report: {e}")
            return None

    def get_quantstats_metrics(self, results: PortfolioResults) -> dict[str, Any] | None:
        """
        Get comprehensive quantstats metrics for programmatic access.

        Args:
            results: Portfolio results with daily returns

        Returns:
            Dictionary of quantstats metrics, or None if unavailable
        """
        if not QUANTSTATS_AVAILABLE:
            logger.warning("QuantStats library not available")
            return None

        if results.daily_returns.empty:
            logger.warning("No daily returns data available for quantstats metrics")
            return None

        try:
            # Prepare portfolio returns for quantstats
            portfolio_returns = self._prepare_returns_for_quantstats(results.daily_returns)

            # Calculate comprehensive metrics
            metrics = {
                # Basic Performance
                "total_return": qs.stats.comp(portfolio_returns),  # type: ignore[union-attr]
                "cagr": qs.stats.cagr(portfolio_returns),  # type: ignore[union-attr]
                "volatility": qs.stats.volatility(portfolio_returns),  # type: ignore[union-attr]

                # Risk Metrics
                "sharpe_ratio": qs.stats.sharpe(portfolio_returns),  # type: ignore[union-attr]
                "sortino_ratio": qs.stats.sortino(portfolio_returns),  # type: ignore[union-attr]
                "calmar_ratio": qs.stats.calmar(portfolio_returns),  # type: ignore[union-attr]
                "max_drawdown": qs.stats.max_drawdown(portfolio_returns),  # type: ignore[union-attr]
                "value_at_risk": qs.stats.value_at_risk(portfolio_returns),  # type: ignore[union-attr]
                "conditional_value_at_risk": qs.stats.conditional_value_at_risk(portfolio_returns),  # type: ignore[union-attr]

                # Trade Statistics
                "win_rate": qs.stats.win_rate(portfolio_returns),  # type: ignore[union-attr]
                "profit_factor": qs.stats.profit_factor(portfolio_returns),  # type: ignore[union-attr]
                "profit_ratio": qs.stats.profit_ratio(portfolio_returns),  # type: ignore[union-attr]
                "gain_to_pain_ratio": qs.stats.gain_to_pain_ratio(portfolio_returns),  # type: ignore[union-attr]

                # Distribution Metrics
                "skewness": qs.stats.skew(portfolio_returns),  # type: ignore[union-attr]
                "kurtosis": qs.stats.kurtosis(portfolio_returns),  # type: ignore[union-attr]
                "tail_ratio": qs.stats.tail_ratio(portfolio_returns),  # type: ignore[union-attr]

                # Risk Measures
                "ulcer_index": qs.stats.ulcer_index(portfolio_returns),  # type: ignore[union-attr]
                "recovery_factor": qs.stats.recovery_factor(portfolio_returns),  # type: ignore[union-attr]
                "expected_return": qs.stats.expected_return(portfolio_returns),  # type: ignore[union-attr]
            }

            # Add time-based metrics if sufficient data
            if len(portfolio_returns) >= 12:  # At least 12 periods for meaningful monthly analysis
                metrics.update({
                    "best_month": qs.stats.best(portfolio_returns),  # type: ignore[union-attr]
                    "worst_month": qs.stats.worst(portfolio_returns),  # type: ignore[union-attr]
                    "avg_win": qs.stats.avg_win(portfolio_returns),  # type: ignore[union-attr]
                    "avg_loss": qs.stats.avg_loss(portfolio_returns),  # type: ignore[union-attr]
                })

            logger.info(f"Generated {len(metrics)} quantstats metrics")
            return metrics

        except Exception as e:
            logger.error(f"Error calculating quantstats metrics: {e}")
            return None

    def _prepare_returns_for_quantstats(self, daily_returns: pd.Series) -> pd.Series:
        """
        Prepare daily returns data for quantstats analysis.

        Args:
            daily_returns: Portfolio daily returns as percentage

        Returns:
            Returns series formatted for quantstats (decimal format)
        """
        # Ensure returns are in decimal format (quantstats expects this)
        # If returns are in percentage format, convert to decimal
        returns_decimal = daily_returns / 100.0 if daily_returns.abs().mean() > 1.0 else daily_returns

        # Ensure datetime index
        if not isinstance(returns_decimal.index, pd.DatetimeIndex):
            returns_decimal.index = pd.to_datetime(returns_decimal.index)

        # Remove any NaN or infinite values
        returns_decimal = returns_decimal.dropna()
        returns_decimal = returns_decimal.replace([np.inf, -np.inf], 0)

        # Set name for better reporting
        returns_decimal.name = "Portfolio Returns"

        return returns_decimal
