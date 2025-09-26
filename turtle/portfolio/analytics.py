"""Portfolio performance analytics using quantstats library."""

import logging
import pandas as pd
import numpy as np

import quantstats as qs  # type: ignore[import-untyped]
from .models import PortfolioState

# Configure matplotlib to use available fonts instead of Arial
# import matplotlib.pyplot as plt
# plt.rcParams["font.family"] = ["DejaVu Sans", "Liberation Sans", "Arial", "sans-serif"]


logger = logging.getLogger(__name__)


class PortfolioAnalytics:
    """
    Portfolio performance analytics using quantstats library.
    """

    def generate_results(
        self,
        portfolio_state: PortfolioState,
        output_file: str | None = None,
    ) -> None:
        """Generate portfolio analysis with printed metrics and tearsheet report."""
        logger.info("Generating portfolio performance results")

        if not portfolio_state.daily_snapshots:
            logger.warning("No portfolio data available")
            return

        daily_returns = self._extract_daily_series(portfolio_state)
        portfolio_returns = self._prepare_returns_for_quantstats(daily_returns)

        print(daily_returns)
        print(portfolio_returns)

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

                    qs.reports.html(portfolio_returns, output=output_file, title="Portfolio Performance Report")
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
