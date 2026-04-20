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
