import logging
from datetime import date
from turtle.strategy.ranking.base import RankingStrategy

import pandas as pd
import polars as pl

_PRICE_BANDS = [(10.0, 20), (20.0, 16), (60.0, 12), (240.0, 8), (1000.0, 4)]
_EMA_PARAMS = {
    "1month": (21, 0.00, 0.10),
    "3month": (66, -0.05, 0.20),
    "6month": (131, -0.10, 0.30),
}

logger = logging.getLogger(__name__)


class MomentumRanking(RankingStrategy):
    """
    Momentum-based ranking strategy that evaluates stocks based on price and EMA200 performance.

    This implementation calculates ranking scores considering:
    - Stock price (lower prices get higher scores)
    - EMA200 performance over different time periods (1, 3, 6 months)
    - Period high performance (how long the stock has been at its highest close)
    """

    def __init__(self, use_polars: bool = False) -> None:
        super().__init__(use_polars=use_polars)

    def _price_to_ranking(self, price: float) -> int:
        """
        Convert stock price to ranking score based on predefined price ranges.

        Args:
            price: The stock price to convert

        Returns:
            int: Ranking score (1-20)
        """
        if price <= 0.0:
            return 1
        return next((score for limit, score in _PRICE_BANDS if price <= limit), 1)

    @staticmethod
    def _linear_rank(pct: float, floor: float, ceiling: float) -> int:
        if pct >= ceiling:
            return 20
        if pct < floor:
            return 0
        return int(20 * ((pct - floor) / (ceiling - floor)))

    def _ranking_ema200_1month(self) -> int:
        """
        Calculate ranking score based on EMA200 performance vs 20 trading days ago.

        Returns:
            int: Ranking score (0-20) where 20 = EMA200 is 10% higher than 20 days ago
        """
        neg_idx, floor, ceiling = _EMA_PARAMS["1month"]
        if self.filtered_pl_df.height < neg_idx:
            return 0
        current_ema200 = self.filtered_pl_df["ema_200"][-1]
        past_ema200 = self.filtered_pl_df["ema_200"][-neg_idx]
        if current_ema200 is None or past_ema200 is None or past_ema200 <= 0:
            return 0
        pct_change = (current_ema200 - past_ema200) / past_ema200
        logger.debug(f"EMA200 1M - Current: {current_ema200}, Past: {past_ema200}, Pct Change: {pct_change}")
        return self._linear_rank(pct_change, floor, ceiling)

    def _ranking_ema200_3month(self) -> int:
        """
        Calculate ranking score based on EMA200 performance vs 3 months ago.

        Returns:
            int: Ranking score (0-20) where 20 = EMA200 is 20% higher than 3 months ago
        """
        neg_idx, floor, ceiling = _EMA_PARAMS["3month"]
        if self.filtered_pl_df.height < neg_idx:
            return 0
        current_ema200 = self.filtered_pl_df["ema_200"][-1]
        past_ema200 = self.filtered_pl_df["ema_200"][-neg_idx]
        if current_ema200 is None or past_ema200 is None or past_ema200 <= 0:
            return 0
        pct_change = (current_ema200 - past_ema200) / past_ema200
        return self._linear_rank(pct_change, floor, ceiling)

    def _ranking_ema200_6month(self) -> int:
        """
        Calculate ranking score based on EMA200 performance vs 6 months ago.

        Returns:
            int: Ranking score (0-20) where 20 = EMA200 is 30% higher than 6 months ago
        """
        neg_idx, floor, ceiling = _EMA_PARAMS["6month"]
        if self.filtered_pl_df.height < neg_idx:
            return 0
        current_ema200 = self.filtered_pl_df["ema_200"][-1]
        past_ema200 = self.filtered_pl_df["ema_200"][-neg_idx]
        if current_ema200 is None or past_ema200 is None or past_ema200 <= 0:
            return 0
        pct_change = (current_ema200 - past_ema200) / past_ema200
        return self._linear_rank(pct_change, floor, ceiling)

    def _ranking_period_high(self) -> int:
        """
        Calculate ranking score based on how long the current close has been the highest close.

        Returns:
            int: Ranking score (0-20) where 20 = current close is highest in 365 days
        """
        if self.filtered_pl_df.height < 2:
            return 0

        current_close = self.filtered_pl_df["close"][-1]
        if current_close is None:
            return 0

        max_lookback = min(365, self.filtered_pl_df.height)
        close_series = self.filtered_pl_df["close"][-max_lookback:]

        max_close = close_series.max()
        if max_close is None or current_close < max_close:
            return 0

        reversed_vals = close_series.reverse()
        break_mask = reversed_vals.is_null() | (reversed_vals > current_close)
        days_as_high = int(break_mask.arg_true()[0]) if break_mask.any() else max_lookback

        return max(1, int(20 * (days_as_high / 365))) if days_as_high > 0 else 0

    def ranking(self, df: pd.DataFrame | pl.DataFrame, date: date) -> int:
        """
        Calculate a combined ranking score for a signal based on price and EMA200 performance.

        Args:
            df: OHLCV DataFrame (pandas or polars) containing price and indicator columns
            date: The date for which to calculate the ranking

        Returns:
            int: Combined ranking score (1-100):
                 - Price component: 1-20 (higher scores for lower-priced stocks)
                 - EMA200 1-month component: 0-20 (higher scores for EMA200 growth vs 1 month ago)
                 - EMA200 3-month component: 0-20 (higher scores for EMA200 growth vs 3 months ago)
                 - EMA200 6-month component: 0-20 (higher scores for EMA200 growth vs 6 months ago)
                 - Period high component: 0-20 (higher scores for longer period as highest close)
        """
        pl_df = self._to_polars(df)
        self.filtered_pl_df = pl_df.filter(pl.col("date") <= date)

        if self.filtered_pl_df.is_empty():
            return 0

        closing_price = self.filtered_pl_df["close"][-1]

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
        return price_ranking + ema200_1month_ranking + ema200_3month_ranking + ema200_6month_ranking + period_high_ranking
