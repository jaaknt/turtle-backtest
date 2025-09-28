"""Portfolio performance analytics using quantstats library."""

import logging
import pandas as pd
import numpy as np
from datetime import datetime

import quantstats as qs  # type: ignore[import-untyped]
from .models import PortfolioState
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

import warnings
import matplotlib

# Suppress font warnings
warnings.filterwarnings("ignore", message=".*findfont.*")
warnings.filterwarnings("ignore", message=".*Font family.*not found.*")
# Configure matplotlib to use available fonts instead of Arial
matplotlib.rcParams["font.family"] = ["DejaVu Sans", "Ubuntu", "sans-serif"]
# Remove Arial from sans-serif font list to prevent warnings
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "Ubuntu", "Bitstream Vera Sans", "Computer Modern Sans Serif", "sans-serif"]


logger = logging.getLogger(__name__)


class PortfolioAnalytics:
    """
    Portfolio performance analytics using quantstats library.
    """

    def generate_results(
        self,
        portfolio_state: PortfolioState,
        start_date: datetime,
        end_date: datetime,
        bars_history: BarsHistoryRepo,
        output_file: str | None = None,
    ) -> None:
        """Generate portfolio analysis with printed metrics and tearsheet report."""
        logger.info("Generating portfolio performance results")

        if not portfolio_state.daily_snapshots:
            logger.warning("No portfolio data available")
            return

        # Generate unique filename if output_file is None
        if output_file is None:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            output_file = f"reports/portfolio_report_{timestamp}.html"

        daily_returns = self._extract_daily_series(portfolio_state)
        portfolio_returns = self._prepare_returns_for_quantstats(daily_returns)

        # Calculate QQQ benchmark returns
        benchmark_returns = self._calculate_benchmark_returns(start_date, end_date, bars_history)

        # Generate tearsheet report if we have returns data
        if not portfolio_returns.empty:
            try:
                # Suppress specific warnings during quantstats processing
                import warnings

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message=".*No non-zero returns.*")
                    warnings.filterwarnings("ignore", message=".*invalid value encountered.*")
                    warnings.filterwarnings("ignore", message=".*Mean of empty slice.*")
                    warnings.filterwarnings("ignore", message=".*Dataset has 0 variance.*")

                    qs.reports.html(
                        portfolio_returns,
                        benchmark=benchmark_returns if not benchmark_returns.empty else None,
                        output=output_file,
                        title="Portfolio Performance Report",
                    )
                    logger.info(f"Tearsheet report saved to {output_file}")
            except Exception as e:
                logger.error(f"Failed to generate tearsheet report: {e}")
                logger.info("Continuing without tearsheet generation")
        else:
            logger.warning("No returns data available for tearsheet report")

    def _extract_daily_series(self, portfolio_state: PortfolioState) -> pd.Series:
        """Calculate daily returns from portfolio snapshots."""
        if not portfolio_state.daily_snapshots or len(portfolio_state.daily_snapshots) < 2:
            return pd.Series(dtype=float)

        dates = []
        returns = []

        for i in range(1, len(portfolio_state.daily_snapshots)):
            prev_snapshot = portfolio_state.daily_snapshots[i - 1]
            curr_snapshot = portfolio_state.daily_snapshots[i]

            prev_value = prev_snapshot.total_value
            curr_value = curr_snapshot.total_value

            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                dates.append(curr_snapshot.date)
                returns.append(daily_return)

        return pd.Series(returns, index=dates, name="daily_returns")

    def _prepare_returns_for_quantstats(self, daily_returns: pd.Series) -> pd.Series:
        """Prepare returns for quantstats (decimal format)."""
        returns = daily_returns / 100.0 if daily_returns.abs().mean() > 1.0 else daily_returns
        if not isinstance(returns.index, pd.DatetimeIndex):
            returns.index = pd.to_datetime(returns.index)

        # Clean and validate returns data
        returns = returns.dropna().replace([np.inf, -np.inf], 0)

        # Check if we have sufficient data for meaningful analysis
        if len(returns) < 2:
            logger.warning("Insufficient return data for analysis (less than 2 data points)")
            return pd.Series(dtype=float)

        # Check for zero variance (all returns are the same)
        if returns.std() == 0:
            logger.warning("Returns have zero variance - portfolio performance is flat")
            # Add minimal noise to prevent division by zero in quantstats
            returns = returns + np.random.normal(0, 1e-8, len(returns))

        return returns

    def _calculate_benchmark_returns(self, start_date: datetime, end_date: datetime, bars_history: BarsHistoryRepo) -> pd.Series:
        """Calculate QQQ benchmark returns for comparison."""
        try:
            # Fetch QQQ historical data
            qqq_df = bars_history.get_ticker_history("QQQ", start_date, end_date, TimeFrameUnit.DAY)

            if qqq_df.empty or len(qqq_df) < 2:
                logger.warning("Insufficient QQQ data for benchmark calculation")
                return pd.Series(dtype=float)

            # Calculate daily returns (index is already datetime from hdate)
            qqq_df = qqq_df.sort_index()  # Sort by date index
            qqq_returns = qqq_df["close"].pct_change().dropna()
            qqq_returns.name = "QQQ_returns"

            # Clean and validate returns data
            qqq_returns = qqq_returns.replace([np.inf, -np.inf], 0).dropna()

            logger.info(f"Calculated QQQ benchmark returns for {len(qqq_returns)} trading days")
            return qqq_returns

        except Exception as e:
            logger.warning(f"Failed to calculate QQQ benchmark returns: {e}")
            return pd.Series(dtype=float)
