from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd


class RankingStrategy(ABC):
    """
    Abstract base class for ranking strategies.

    This interface defines the contract for ranking calculation strategies
    that evaluate stocks based on various technical and fundamental criteria.
    """

    @abstractmethod
    def ranking(self, df: pd.DataFrame, date: datetime) -> int:
        """
        Calculate a ranking score for the given signal.

        Args:
            signal: The Signal object containing ticker and date information

        Returns:
            int: Ranking score where higher values indicate better-ranked stocks
        """
        pass
