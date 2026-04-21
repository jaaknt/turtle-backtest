import math
from abc import ABC, abstractmethod
from datetime import date

import polars as pl


class RankingStrategy(ABC):
    """
    Abstract base class for ranking strategies.

    This interface defines the contract for ranking calculation strategies
    that evaluate stocks based on various technical and fundamental criteria.
    """

    @abstractmethod
    def ranking(self, df: pl.DataFrame, date: date) -> int:
        """
        Calculate a ranking score for the given signal.

        Args:
            df: OHLCV DataFrame with indicator columns
            date: The date for which to calculate the ranking

        Returns:
            int: Ranking score where higher values indicate better-ranked stocks 1-100
        """
        pass

    @staticmethod
    def _linear_rank(value: float, floor: float, ceiling: float, max_score: int = 20) -> int:
        if not math.isfinite(value):
            return 0
        if value >= ceiling:
            return max_score
        if value < floor:
            return 0
        return int(max_score * ((value - floor) / (ceiling - floor)))

    @staticmethod
    def _ranking_col_change(filtered_df: pl.DataFrame, col: str, neg_idx: int, floor: float, ceiling: float) -> int:
        """Rank percentage change of a column over a lookback period."""
        if filtered_df.height < neg_idx:
            return 0
        current = filtered_df[col][-1]
        past = filtered_df[col][-neg_idx]
        if current is None or past is None or past <= 0:
            return 0
        return RankingStrategy._linear_rank((current - past) / past, floor, ceiling)
