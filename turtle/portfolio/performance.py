"""Portfolio performance analytics and quantstats integration."""

import logging
from datetime import datetime
import pandas as pd
import numpy as np

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
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

        # Calculate basic metrics
        final_value = portfolio_state.total_value
        total_return_dollars = final_value - initial_capital
        total_return_pct = (total_return_dollars / initial_capital) * 100.0

        # Extract daily data
        daily_returns, daily_values = self._extract_daily_series(portfolio_state)

        # Calculate trade statistics
        trade_stats = self._calculate_trade_statistics(portfolio_state.closed_positions)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(daily_returns, daily_values)

        # Calculate benchmark returns
        benchmark_returns = self._calculate_benchmark_returns(
            start_date, end_date, benchmark_tickers, bars_history
        )

        # Create results object
        results = PortfolioResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            final_cash=portfolio_state.cash,
            total_return_pct=total_return_pct,
            total_return_dollars=total_return_dollars,
            daily_returns=daily_returns,
            daily_values=daily_values,
            closed_positions=portfolio_state.closed_positions,
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
            sum(p.realized_pnl_pct for p in winning_positions) / len(winning_positions)
            if winning_positions else 0.0
        )

        avg_loss_pct = (
            sum(p.realized_pnl_pct for p in losing_positions) / len(losing_positions)
            if losing_positions else 0.0
        )

        # Calculate average holding period
        avg_holding_period = (
            sum(p.holding_period_days for p in closed_positions) / total_trades
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

    def _calculate_benchmark_returns(
        self,
        start_date: datetime,
        end_date: datetime,
        benchmark_tickers: list[str],
        bars_history: BarsHistoryRepo,
    ) -> dict[str, float] | None:
        """
        Calculate benchmark returns for comparison.

        Args:
            start_date: Start date for benchmark calculation
            end_date: End date for benchmark calculation
            benchmark_tickers: List of benchmark ticker symbols
            bars_history: Data repository

        Returns:
            Dictionary mapping benchmark ticker to total return percentage
        """
        try:
            benchmark_returns = {}

            for ticker in benchmark_tickers:
                df = bars_history.get_ticker_history(
                    ticker, start_date, end_date, TimeFrameUnit.DAY
                )

                if not df.empty:
                    start_price = float(df.iloc[0]["open"])
                    end_price = float(df.iloc[-1]["close"])
                    total_return = ((end_price - start_price) / start_price) * 100.0
                    benchmark_returns[ticker] = total_return

            return benchmark_returns

        except Exception as e:
            logger.error(f"Error calculating benchmark returns: {e}")
            return None

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

    def print_performance_summary(self, results: PortfolioResults) -> None:
        """
        Print formatted performance summary.

        Args:
            results: Portfolio results to summarize
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
            for ticker, return_pct in results.benchmark_returns.items():
                print(f"{ticker}: {return_pct:.2f}%")

        print(f"{'='*60}")

    def create_quantstats_report(self, results: PortfolioResults) -> object | None:
        """
        Create quantstats report (placeholder for future implementation).

        Args:
            results: Portfolio results

        Returns:
            Quantstats report object (when implemented)
        """
        logger.info("Quantstats integration not implemented yet")
        return None
