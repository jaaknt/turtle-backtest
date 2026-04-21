from datetime import date
from turtle.strategy.ranking.base import RankingStrategy

import polars as pl

# (price_ceiling, score) — stocks priced above 1000 default to score 1
_PRICE_BANDS = [(10.0, 20), (20.0, 16), (60.0, 12), (240.0, 8), (1000.0, 4)]

# (lookback_bars, pct_change_floor, pct_change_ceiling) passed to _ranking_col_change
_EMA_PARAMS = {
    "1month": (21, 0.00, 0.10),
    "3month": (66, -0.05, 0.20),
    "6month": (131, -0.10, 0.30),
}


class MomentumRanking(RankingStrategy):
    """
    Momentum-based ranking strategy that evaluates stocks based on price and EMA200 performance.

    This implementation calculates ranking scores considering:
    - Stock price (lower prices get higher scores)
    - EMA200 performance over different time periods (1, 3, 6 months)
    - Period high performance (how long the stock has been at its highest close)
    """

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

    def _ranking_period_high(self, filtered_df: pl.DataFrame) -> int:
        """
        Calculate ranking score based on how long the current close has been the highest close.

        Args:
            filtered_df: Date-filtered OHLCV DataFrame with close column.

        Returns:
            int: Ranking score (0-20) where 20 = current close is highest in 365 days
        """
        if filtered_df.height < 2:
            return 0

        current_close = filtered_df["close"][-1]
        if current_close is None:
            return 0

        max_lookback = min(365, filtered_df.height)
        close_series = filtered_df["close"][-max_lookback:]

        max_close = close_series.max()
        if max_close is None or current_close < max_close:
            return 0

        reversed_vals = close_series.reverse()
        break_mask = reversed_vals.is_null() | (reversed_vals > current_close)
        days_as_high = int(break_mask.arg_true()[0]) if break_mask.any() else max_lookback

        return max(1, int(20 * (days_as_high / 365))) if days_as_high > 0 else 0

    def ranking(self, df: pl.DataFrame, date: date) -> int:
        """
        Calculate a combined ranking score for a signal based on price and EMA200 performance.

        Args:
            df: Polars OHLCV DataFrame containing price and indicator columns
            date: The date for which to calculate the ranking

        Returns:
            int: Combined ranking score (0-100):
                 - Price component: 1-20 (higher scores for lower-priced stocks)
                 - EMA200 1-month component: 0-20 (higher scores for EMA200 growth vs 1 month ago)
                 - EMA200 3-month component: 0-20 (higher scores for EMA200 growth vs 3 months ago)
                 - EMA200 6-month component: 0-20 (higher scores for EMA200 growth vs 6 months ago)
                 - Period high component: 0-20 (higher scores for longer period as highest close)
        """
        filtered_df = df.filter(pl.col("date") <= date)

        if filtered_df.is_empty():
            return 0

        closing_price = filtered_df["close"][-1]
        if closing_price is None:
            return 0

        price_ranking = self._price_to_ranking(closing_price)
        ema200_ranking = sum(self._ranking_col_change(filtered_df, "ema_200", *p) for p in _EMA_PARAMS.values())
        period_high_ranking = self._ranking_period_high(filtered_df)
        return price_ranking + ema200_ranking + period_high_ranking
