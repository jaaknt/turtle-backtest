from abc import ABC, abstractmethod
from datetime import date

import pandas as pd
import polars as pl


class RankingStrategy(ABC):
    """
    Abstract base class for ranking strategies.

    This interface defines the contract for ranking calculation strategies
    that evaluate stocks based on various technical and fundamental criteria.
    """

    def __init__(self, use_polars: bool = False) -> None:
        self.use_polars = use_polars

    @abstractmethod
    def ranking(self, df: pd.DataFrame | pl.DataFrame, date: date) -> int:
        """
        Calculate a ranking score for the given signal.

        Args:
            signal: The Signal object containing ticker and date information

        Returns:
            int: Ranking score where higher values indicate better-ranked stocks 1-100
        """
        pass

    @staticmethod
    def _to_pandas(df: pd.DataFrame | pl.DataFrame) -> pd.DataFrame:
        if isinstance(df, pl.DataFrame):
            pd_df = df.to_pandas()
            if "date" in pd_df.columns and pd.api.types.is_datetime64_any_dtype(pd_df["date"]):
                pd_df["date"] = pd_df["date"].dt.date
            return pd_df
        return df

    @staticmethod
    def _to_polars(df: pd.DataFrame | pl.DataFrame) -> pl.DataFrame:
        if isinstance(df, pd.DataFrame):
            pl_df = pl.from_pandas(df)
            if "date" in pl_df.columns and pl_df["date"].dtype == pl.Datetime:
                pl_df = pl_df.with_columns(pl.col("date").cast(pl.Date))
            return pl_df
        return df
