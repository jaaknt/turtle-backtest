import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy

import polars as pl

from .base import TradingStrategy

logger = logging.getLogger(__name__)


# https://www.tradingview.com/script/ygJLhYt4-Darvas-Box-Theory-Tracking-Uptrends/
class DarvasBoxStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: OhlcvAnalyticsRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
        min_bars: int = 420,
    ):
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

    @staticmethod
    def check_local_max(
        row_index: int,
        series: list[float],
        preceding_count: int = 10,
        following_count: int = 4,
    ) -> bool:
        if row_index < preceding_count:
            return False
        current_value = series[row_index]
        preceding_values = series[max(0, row_index - preceding_count) : row_index]
        following_values = series[row_index + 1 : min(row_index + following_count + 1, len(series))]
        return all(v < current_value for v in preceding_values) and all(v < current_value for v in following_values)

    @staticmethod
    def check_local_min(row_index: int, series: list[float], following_count: int = 3) -> bool:
        if row_index + following_count >= len(series):
            return False
        current_value = series[row_index]
        following_values = series[row_index + 1 : min(row_index + following_count + 1, len(series))]
        return all(v >= current_value for v in following_values)

    @staticmethod
    def is_local_max_valid(df: pl.DataFrame, local_max: float, following_count: int = 3) -> bool:
        following: int = -1
        for row in df.iter_rows(named=True):
            if following >= 0:
                following += 1
            if row["high"] > local_max:
                return False
            if row["is_local_min"]:
                following = 0
            if following == following_count:
                return True
        return True

    def calculate_indicators_pl(self) -> None:
        """Calculate technical indicators using the polars DataFrame (self.pl_df).

        Adds the following columns:
        - max_close_20: 20-bar rolling maximum of close
        - max_high_20: 20-bar rolling maximum of high
        - ema_10 / ema_20 / ema_50 / ema_200: exponential moving averages of close
        - ema_volume_10: 10-bar EMA of volume
        - macd: difference between 12-bar and 26-bar EMA of close
        - macd_signal: 9-bar EMA of macd
        """
        self.pl_df = self.pl_df.with_columns(
            pl.col("close").rolling_max(20).alias("max_close_20"),
            pl.col("high").rolling_max(20).alias("max_high_20"),
            pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
            pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
            pl.col("close").ewm_mean(span=50, adjust=False).alias("ema_50"),
            pl.col("close").ewm_mean(span=200, adjust=False).alias("ema_200"),
            pl.col("volume").ewm_mean(span=10, adjust=False).alias("ema_volume_10"),
            (pl.col("close").ewm_mean(span=12, adjust=False) - pl.col("close").ewm_mean(span=26, adjust=False)).alias("macd"),
        ).with_columns(
            pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal"),
        )

    def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
        self.calculate_indicators_pl()
        filtered = self.pl_df.filter(pl.col("date") >= start_date)
        if filtered.is_empty():
            logger.debug(f"{ticker} - no data after date filtering")
            return []
        buy_mask = (
            (pl.col("close") >= pl.col("max_close_20"))
            & (pl.col("close") >= pl.col("ema_10"))
            & (pl.col("close") >= pl.col("ema_20"))
            & (pl.col("ema_10") >= pl.col("ema_20"))
            & (pl.col("close") >= pl.col("ema_50"))
            & (pl.col("volume") >= pl.col("ema_volume_10") * 1.10)
            & (pl.col("macd") > pl.col("macd_signal"))
            & ((pl.col("close") - pl.col("open")) / pl.col("close") >= 0.008)
        )
        if self.time_frame_unit == TimeFrameUnit.DAY:
            buy_mask = buy_mask & (pl.col("close") >= pl.col("ema_200")) & (pl.col("ema_50") >= pl.col("ema_200"))
        signal_dates = filtered.filter(buy_mask)["date"].to_list()
        return [Signal(ticker=ticker, date=d, ranking=self.ranking_strategy.ranking(self.pl_df, date=d)) for d in signal_dates]

    def darvas_box_breakout(self, lookback_period: int = 10, validation_period: int = 3) -> bool:
        highs = self.pl_df["high"].to_list()
        lows = self.pl_df["low"].to_list()
        closes = self.pl_df["close"].to_list()

        is_local_max = [self.check_local_max(i, highs, lookback_period, validation_period) for i in range(len(highs))]
        is_local_min = [self.check_local_min(i, lows, validation_period) for i in range(len(lows))]

        status = "unknown"
        box_top = 0.0
        box_bottom = 0.0

        for idx in range(len(closes)):
            if status == "unknown":
                if is_local_max[idx]:
                    df_slice = pl.DataFrame({"high": highs[idx:], "is_local_min": is_local_min[idx:]})
                    if self.is_local_max_valid(df_slice, highs[idx], validation_period):
                        status = "box_top_set"
                        box_top = highs[idx]
                    else:
                        is_local_max[idx] = False
                        continue
                else:
                    continue
            if status == "box_top_set":
                if is_local_min[idx]:
                    status = "box_bottom_set"
                    box_bottom = lows[idx]
            elif status == "box_bottom_set":
                if is_local_min[idx]:
                    status = "box_formed"
            elif status == "box_formed":
                if closes[idx] > box_top:
                    status = "breakout_up"
                elif closes[idx] < box_bottom:
                    status = "breakout_down"
            elif status in ("breakout_up", "breakout_down"):
                status = "unknown"

        return status == "breakout_up"
