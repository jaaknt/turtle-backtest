import logging
from datetime import datetime

import pandas as pd
from turtle.ranking.ranking_strategy import RankingStrategy

logger = logging.getLogger(__name__)


class MomentumRanking(RankingStrategy):
    """
    Momentum-based ranking strategy that evaluates stocks based on price and EMA200 performance.

    This implementation calculates ranking scores considering:
    - Stock price (lower prices get higher scores)
    - EMA200 performance over different time periods (1, 3, 6 months)
    - Period high performance (how long the stock has been at its highest close)
    """

    def __init__(self):
        """
        Initialize MomentumRanking strategy.

        """

    def _price_to_ranking(self, price: float) -> int:
        """
        Convert stock price to ranking score based on predefined price ranges.

        Args:
            price: The stock price to convert

        Returns:
            int: Ranking score (0-20)
        """
        if price <= 0.0:
            return 0
        elif price <= 10.0:
            return 20
        elif price <= 20.0:
            return 16
        elif price <= 60.0:
            return 12
        elif price <= 240.0:
            return 8
        elif price <= 1000.0:
            return 4
        else:
            return 0

    def _ranking_ema200_1month(self) -> int:
        """
        Calculate ranking score based on EMA200 performance vs 20 trading days ago.

        Returns:
            int: Ranking score (0-20) where 20 = EMA200 is 10% higher than 20 days ago
        """
        if len(self.filtered_df) < 21:  # Need at least 21 rows for 20-day lookback
            return 0

        # Get current EMA200 (last row)
        current_ema200 = self.filtered_df.at[self.filtered_df.index[-1], "ema_200"]

        # Get EMA200 from 20 trading days ago
        past_ema200 = self.filtered_df.at[self.filtered_df.index[-21], "ema_200"]
        logger.debug(f"EMA200 1M - Current: {current_ema200}, Past: {past_ema200}")

        # Handle invalid data
        if pd.isna(current_ema200) or pd.isna(past_ema200) or past_ema200 <= 0:
            return 0

        # Calculate percentage change
        pct_change = (current_ema200 - past_ema200) / past_ema200
        logger.debug(f"EMA200 1M - Current: {current_ema200}, Past: {past_ema200}, Pct Change: {pct_change}")

        # Convert to ranking score: 20 for +10%, scale linearly
        # Positive changes get higher scores, negative changes get lower scores
        if pct_change >= 0.10:  # 10% or more increase
            return 20
        elif pct_change >= 0.0:  # 0% to 10% increase
            return int(20 * (pct_change / 0.10))
        else:  # Less than 0% decrease
            return 0

    def _ranking_ema200_3month(self) -> int:
        """
        Calculate ranking score based on EMA200 performance vs 3 months ago.

        Returns:
            int: Ranking score (0-20) where 20 = EMA200 is 20% higher than 3 months ago
        """
        if len(self.filtered_df) < 66:  # Need at least 66 rows for 65-day lookback
            return 0

        # Get current EMA200 (last row)
        current_ema200 = self.filtered_df.iloc[-1]["ema_200"]

        # Get EMA200 from 65 trading days ago (approximately 3 months)
        past_ema200 = self.filtered_df.iloc[-66]["ema_200"]

        # Handle invalid data
        if pd.isna(current_ema200) or pd.isna(past_ema200) or past_ema200 <= 0:
            return 0

        # Calculate percentage change
        pct_change = (current_ema200 - past_ema200) / past_ema200

        # Convert to ranking score: 20 for +20%, scale linearly down to 0 at -5%
        if pct_change >= 0.20:  # 20% or more increase
            return 20
        elif pct_change >= -0.05:  # -5% to 20% range
            # Linear scaling: 0 at -5%, 20 at 20%
            return int(20 * (pct_change + 0.05) / 0.25)
        else:  # Less than -5% decrease
            return 0

    def _ranking_ema200_6month(self) -> int:
        """
        Calculate ranking score based on EMA200 performance vs 6 months ago.

        Returns:
            int: Ranking score (0-20) where 20 = EMA200 is 30% higher than 6 months ago
        """
        if len(self.filtered_df) < 131:  # Need at least 131 rows for 130-day lookback
            return 0

        # Get current EMA200 (last row)
        current_ema200 = self.filtered_df.iloc[-1]["ema_200"]

        # Get EMA200 from 130 trading days ago (approximately 6 months)
        past_ema200 = self.filtered_df.iloc[-131]["ema_200"]

        # Handle invalid data
        if pd.isna(current_ema200) or pd.isna(past_ema200) or past_ema200 <= 0:
            return 0

        # Calculate percentage change
        pct_change = (current_ema200 - past_ema200) / past_ema200

        # Convert to ranking score: 20 for +30%, scale linearly down to 0 at -10%
        if pct_change >= 0.30:  # 30% or more increase
            return 20
        elif pct_change >= -0.10:  # -10% to 30% range
            # Linear scaling: 0 at -10%, 20 at 30%
            return int(20 * (pct_change + 0.10) / 0.40)
        else:  # Less than -10% decrease
            return 0

    def _ranking_period_high(self) -> int:
        """
        Calculate ranking score based on how long the current close has been the highest close.

        Returns:
            int: Ranking score (0-20) where 20 = current close is highest in 365 days
        """
        if len(self.filtered_df) < 2:  # Need at least 2 rows
            return 0

        # Get current close (last row)
        current_close = self.filtered_df.iloc[-1]["close"]

        # Handle invalid data
        if pd.isna(current_close):
            return 0

        # Determine how far back we can look (up to 365 days)
        max_lookback = min(365, len(self.filtered_df))

        # Get the close prices for the lookback period
        close_prices = self.filtered_df.iloc[-max_lookback:]["close"]

        # Find the maximum close in this period
        max_close = close_prices.max()

        # If current close is not the maximum, return 0
        if current_close < max_close:
            return 0

        # Find how many days back the current close has been the highest
        days_as_high = 0
        for i in range(1, max_lookback + 1):
            if i > len(self.filtered_df):
                break

            # Check if current close is still >= the close from i days ago
            past_close = self.filtered_df.iloc[-i]["close"]
            if pd.isna(past_close) or current_close < past_close:
                break

            days_as_high = i

        # Scale score: 365 days = 20 points, 1 day = minimal points
        # Use linear scaling with a minimum threshold
        score = int(20 * (days_as_high / 365))

        # Ensure minimum score of 1 if current close is at least a 1-day high
        return max(1, score) if days_as_high > 0 else 0

    def ranking(self, df: pd.DataFrame, date: datetime) -> int:
        """
        Calculate a combined ranking score for a signal based on price and EMA200 performance.

        Args:
            date: The date for which to calculate the ranking

        Returns:
            int: Combined ranking score (0-100):
                 - Price component: 0-20 (higher scores for lower-priced stocks)
                 - EMA200 1-month component: 0-20 (higher scores for EMA200 growth vs 1 month ago)
                 - EMA200 3-month component: 0-20 (higher scores for EMA200 growth vs 3 months ago)
                 - EMA200 6-month component: 0-20 (higher scores for EMA200 growth vs 6 months ago)
                 - Period high component: 0-20 (higher scores for longer period as highest close)
        """

        self.filtered_df = df[df["hdate"] <= date].copy()

        # Get the closing price from the target date
        closing_price = self.filtered_df.iloc[-1]["close"]

        # Calculate all ranking components
        price_ranking = self._price_to_ranking(closing_price)
        ema200_1month_ranking = self._ranking_ema200_1month()
        ema200_3month_ranking = self._ranking_ema200_3month()
        ema200_6month_ranking = self._ranking_ema200_6month()
        period_high_ranking = self._ranking_period_high()

        logger.debug(
            f"Price Ranking: {price_ranking}, "
            f"EMA200 1M: {ema200_1month_ranking}, "
            f"EMA200 3M: {ema200_3month_ranking}, "
            f"EMA200 6M: {ema200_6month_ranking}, "
            f"Period High: {period_high_ranking}"
        )

        # Return combined score
        return price_ranking + ema200_1month_ranking + ema200_3month_ranking + ema200_6month_ranking + period_high_ranking
