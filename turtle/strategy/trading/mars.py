import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy
from typing import Any

import polars as pl

from .base import TradingStrategy

logger = logging.getLogger(__name__)


# Mars Strategy (@marsrides)
# https://docs.google.com/document/d/1BZgaYWFOnsOFMFWRt0jJgNVeLicEMB-ccf9kUwtIxYI/edit?tab=t.0
class MarsStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: OhlcvAnalyticsRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.WEEK,
        warmup_period: int = 720,  # 2 years for daily EMA200 + weekly data
        min_bars: int = 240,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

    def calculate_indicators_pl(self) -> None:
        """Calculate technical indicators using the polars DataFrame (self.pl_df).

        Adds the following columns:
        - max_box_4 / min_box_4: 4-bar rolling max/min of prior open/close (box boundaries)
        - max_close_10: 10-bar rolling maximum of close
        - ema_10 / ema_20: exponential moving averages of close
        - macd: difference between 12-bar and 26-bar EMA of close
        - ema_volume_4: 4-bar rolling mean of prior volume
        - macd_signal: 9-bar EMA of macd
        - macd_histogram: macd - macd_signal
        - consolidation_change: (max_box_4 - min_box_4) / close
        - hard_stoploss: midpoint of box minus 0.02
        - volume_change: current volume / 4-bar rolling mean of prior volume
        """
        self.pl_df = self.pl_df.with_columns(
            pl.max_horizontal(
                pl.col("open").shift(1).rolling_max(4),
                pl.col("close").shift(1).rolling_max(4),
            ).alias("max_box_4"),
            pl.min_horizontal(
                pl.col("open").shift(1).rolling_min(4),
                pl.col("close").shift(1).rolling_min(4),
            ).alias("min_box_4"),
            pl.col("close").rolling_max(10).alias("max_close_10"),
            pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
            pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
            (pl.col("close").ewm_mean(span=12, adjust=False) - pl.col("close").ewm_mean(span=26, adjust=False)).alias("macd"),
            pl.col("volume").shift(1).rolling_mean(4).alias("ema_volume_4"),
        ).with_columns(
            pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal"),
            (pl.col("macd") - pl.col("macd").ewm_mean(span=9, adjust=False)).alias("macd_histogram"),
            ((pl.col("max_box_4") - pl.col("min_box_4")) / pl.col("close")).alias("consolidation_change"),
            ((pl.col("max_box_4") + pl.col("min_box_4")) / 2 - 0.02).alias("hard_stoploss"),
            (pl.col("volume") / pl.col("volume").shift(1).rolling_mean(4)).alias("volume_change"),
        )

    def is_buy_signal(self, ticker: str, row: dict[str, Any]) -> bool:
        """Check whether a single row (from iter_rows) satisfies all buy conditions.

        Args:
            ticker: Stock symbol, used only for debug logging.
            row: Named row dict from polars iter_rows(named=True).

        Returns:
            bool: True if all buy conditions are met, False otherwise.
        """
        if row["max_close_10"] is None or row["max_box_4"] is None or row["min_box_4"] is None:
            return False

        # last close > max(close, 10)
        if row["close"] < row["max_close_10"]:
            logger.debug(
                f"{ticker} {row['date'].strftime('%Y-%m-%d')} close < max_close_10, "
                f"close: {row['close']} max_close_10: {row['max_close_10']}"
            )
            return False

        # EMA(close, 10) > EMA(close, 20)
        if row["ema_10"] < row["ema_20"]:
            logger.debug(f"{ticker} {row['date'].strftime('%Y-%m-%d')} EMA_10 < EMA_20, EMA10: {row['ema_10']} EMA20: {row['ema_20']}")
            return False

        # MACD or MACD signal is null
        if row["macd"] is None or row["macd_signal"] is None:
            logger.debug(f"{ticker} {row['date'].strftime('%Y-%m-%d')} MACD or MACD_signal is null")
            return False

        # consolidation_change < 0.12
        if row["consolidation_change"] > 0.12:
            logger.debug(
                f"{ticker} {row['date'].strftime('%Y-%m-%d')} consolidation_change > 0.12, "
                f"consolidation_change: {row['consolidation_change']}"
            )
            return False

        # (close - hard_stoploss / close < 0.16
        if (row["close"] - row["hard_stoploss"]) / row["close"] > 0.25:
            logger.debug(
                f"{ticker} {row['date'].strftime('%Y-%m-%d')} (close - (max_box_4 - min_box_4) / 2) / close < 0.16, "
                f"close: {row['close']} hard_stoploss: {row['hard_stoploss']}"
            )
            return False

        """
        # if last volume < EMA(volume, 4)*1.10
        if row["volume"] < row["ema_volume_4"] * 0.9:
            logger.debug(
                f"{ticker} {row['date'].strftime('%Y-%m-%d')} volume < EMA_volume_4 * 1.10, "
                f"volume: {row['volume']} EMA_volume_4 * 1.10: {row['ema_volume_4']*1.10}"
            )
            return False
        """

        logger.debug(f"{ticker} {row['date'].strftime('%Y-%m-%d')} buy signal")
        return True

    def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
        self.calculate_indicators_pl()
        filtered = self.pl_df.filter(pl.col("date") >= start_date)
        if filtered.is_empty():
            logger.debug(f"{ticker} - no data after date filtering")
            return []
        signals = []
        for row in filtered.iter_rows(named=True):
            if self.is_buy_signal(ticker, row):
                signals.append(Signal(ticker=ticker, date=row["date"], ranking=self.ranking_strategy.ranking(self.pl_df, date=row["date"])))
        return signals

    def _price_to_ranking(self, price: float) -> int:
        """
        Convert stock price to ranking score based on predefined price ranges.

        Args:
            price: The stock price to convert

        Returns:
            int: Ranking score; one of {0, 4, 8, 12, 16, 20}
        """
        if price <= 0:
            return 0
        elif price <= 10:
            return 20
        elif price <= 20:
            return 16
        elif price <= 60:
            return 12
        elif price <= 240:
            return 8
        elif price <= 1000:
            return 4
        else:
            return 0

    def ranking(self, ticker: str, date_to_check: date) -> int:
        """
        Calculate a ranking score for a ticker based on its closing price on a given date.

        Args:
            ticker: The stock symbol to rank
            date_to_check: The specific date to evaluate the stock price

        Returns:
            int: Ranking score; one of {0, 4, 8, 12, 16, 20}
        """
        if not self.collect_data(ticker, date_to_check, date_to_check):
            logger.debug(f"{ticker} - not enough data for ranking on date {date_to_check}")
            return 0
        target = self.pl_df.filter(pl.col("date") == date_to_check)
        if target.is_empty():
            logger.debug(f"{ticker} - no data for ranking on date {date_to_check}")
            return 0
        return self._price_to_ranking(float(target["close"][-1]))
