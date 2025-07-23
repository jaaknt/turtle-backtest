from datetime import datetime, timedelta
import logging
import pandas as pd
import talib
import numpy as np

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.strategy.trading_strategy import TradingStrategy

logger = logging.getLogger(__name__)


# Darvas Box Strategy description
# https://www.tradingview.com/script/ygJLhYt4-Darvas-Box-Theory-Tracking-Uptrends/
class DarvasBoxStrategy(TradingStrategy):
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
        min_bars: int = 420,
    ):
        super().__init__(bars_history, time_frame_unit, warmup_period, min_bars)

    @staticmethod
    def check_local_max(
        row_index: int,
        series: pd.Series,
        preceding_count: int = 10,
        following_count: int = 4,
    ) -> bool:
        # return False if there are not enough preceding values
        if row_index < preceding_count:
            return False

        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 10 previous values (handling start of DataFrame edge cases)
        preceding_values = series.iloc[max(0, row_index - preceding_count) : row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[
            row_index + 1 : min(row_index + following_count + 1, len(series))
        ]

        # Check if all previous 10 and next 3 values are less than current
        if (preceding_values < current_value).all() and (
            following_values < current_value
        ).all():
            return True
        else:
            return False

    @staticmethod
    def check_local_min(
        row_index: int, series: pd.Series, following_count: int = 3
    ) -> bool:
        # return False if there are not enough following values
        if row_index + following_count >= len(series):
            return False

        # Get the current value
        current_value = series.iloc[row_index]

        # Get the 3 next values (handling end of DataFrame edge cases)
        following_values = series.iloc[
            row_index + 1 : min(row_index + following_count + 1, len(series))
        ]

        # Check if all next 3 values are less than current
        if (following_values >= current_value).all():
            return True
        else:
            return False

    @staticmethod
    def is_local_max_valid(
        df: pd.DataFrame, local_max: float, following_count: int = 3
    ):
        # iterate over the following rows
        # return True if 0:following_count high values after is_local_min are less than local_max
        following: int = -1
        for _, row in df.iterrows():
            if following >= 0:
                following += 1
            if row["high"] > local_max:
                return False
            if row["is_local_min"]:
                following = 0
            if following == following_count:
                return True
        return True

    def collect_historical_data(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> bool:
        self.df = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=self.warmup_period),
            end_date,
            self.time_frame_unit,
        )
        return not (self.df.empty or self.df.shape[0] < self.min_bars)

    def calculate_indicators(self) -> None:
        """Calculate technical indicators for the strategy.

        Adds the following columns to self.df:
        - max_close_20: 20-period rolling maximum of close prices
        - ema_10/20/50/200: Exponential moving averages of close prices
        - ema_volume_10: 10-period EMA of volume
        - buy_signal: Boolean column initialized to False
        """
        # Pre-convert arrays once for performance optimization
        close_values = self.df["close"].values.astype(float)
        volume_values = self.df["volume"].values.astype(float)

        # Rolling window indicators
        self.df["max_close_20"] = self.df["close"].rolling(window=20).max()

        # Exponential Moving Averages for close prices
        self.df["ema_10"] = talib.EMA(close_values, timeperiod=10)
        self.df["ema_20"] = talib.EMA(close_values, timeperiod=20)
        self.df["ema_50"] = talib.EMA(close_values, timeperiod=50)
        self.df["ema_200"] = talib.EMA(close_values, timeperiod=200)

        # Volume indicators
        self.df["ema_volume_10"] = talib.EMA(volume_values, timeperiod=10)

        # Initialize buy signal column
        self.df["buy_signal"] = False

        self.df = self.df.reset_index()

        # self.darvas_box_breakout()

    def darvas_box_breakout(self, lookback_period=10, validation_period=3) -> None:
        # status values: unknown, box_top_set, box_bottom_set, box_formed, breakout_up, breakout_down
        self.df["status"] = "unknown"
        self.df["box_top"] = np.nan
        self.df["box_bottom"] = np.nan
        self.df["is_local_max"] = self.df.index.to_series().apply(
            lambda i: self.check_local_max(
                i, self.df["high"], lookback_period, validation_period
            )
        )
        self.df["is_local_min"] = self.df.index.to_series().apply(
            lambda i: self.check_local_min(i, self.df["low"], validation_period)
        )

        # Initialize variables for box formation
        status: str = "unknown"
        # box_top_index: int = 0
        # box_bottom_index: int = 0
        box_top = pd.Float64Dtype()
        box_bottom = pd.Float64Dtype()

        # iterate over the self.df_weekly rows
        for i, row in self.df.iterrows():
            # if status is unknown, check if the current row is a local max
            if status == "unknown":
                if row["is_local_max"]:
                    if self.is_local_max_valid(
                        self.df[i:], row["high"], validation_period
                    ):
                        status = "box_top_set"
                        box_top = row["high"]
                        # self.df_weekly.at[i, "status"] = status
                        self.df.at[i, "box_top"] = box_top
                    else:
                        # fixing local max value
                        self.df["is_local_max"] = False
                        # status = "unknown"
                        continue
                else:
                    continue
            # if status is box_top_set, check if the current row is a local min
            # there can be local max and min in the same bar
            if status == "box_top_set":
                if row["is_local_min"]:
                    status = "box_bottom_set"
                    box_bottom = row["low"]
                    # self.df_weekly.at[i, "status"] = status
                    self.df.at[i, "box_bottom"] = box_bottom
            # if status is box_bottom_set, check if the current row is a local max
            elif status == "box_bottom_set":
                if row["is_local_min"]:
                    status = "box_formed"
            # if status is box_formed, check if the current row is a breakout
            elif status == "box_formed":
                if row["close"] > box_top:
                    status = "breakout_up"
                    # for further filtering afterwards
                    self.df.at[i, "box_bottom"] = box_bottom
                    self.df.at[i, "box_top"] = box_top
                elif row["close"] < box_bottom:
                    status = "breakout_down"
            elif status == "breakout_up" or status == "breakout_down":
                status = "unknown"

            # update the status
            self.df.at[i, "status"] = status

        # check if the last or previous row was a breakout up
        return (
            self.df.iloc[-1]["status"] == "breakout_up"
            # or self.df.iloc[-2]["status"] == "breakout_up"
        )

    def is_buy_signal(self, ticker: str, row: pd.Series) -> bool:
        # last_record: pd.Series = self.df.iloc[-1]

        # is darvas_box breakout up
        # if not row["status"] == "breakout_up":
        #    logger.debug(f"{ticker} darvas_box_breakout failed")
        #    return False

        # last close > max(close, 20)
        if row["close"] < row["max_close_20"]:
            logger.debug(
                f"{ticker} close < max_close_20, close: {row['close']} max_close_20: {row['max_close_20']}"
            )
            return False

        # last close > EMA(close, 10)
        if row["close"] < row["ema_10"]:
            logger.debug(
                f"{ticker} close < EMA_10, close: {row['close']} EMA10: {row['ema_10']}"
            )
            return False

        # last close > EMA(close, 20)
        if row["close"] < row["ema_20"]:
            logger.debug(
                f"{ticker} close < EMA_20, close: {row['close']} EMA20: {row['ema_20']}"
            )
            return False

        # EMA(close, 10) > EMA(close, 20)
        if row["ema_10"] < row["ema_20"]:
            logger.debug(
                f"{ticker} EMA_10 < EMA_20, EMA10: {row['ema_10']} EMA20: {row['ema_20']}"
            )
            return False

        # last close > EMA(close, 50)
        if row["close"] < row["ema_50"]:
            logger.debug(
                f"{ticker} close < EMA_50, close: {row['close']} EMA50: {row['ema_50']}"
            )
            return False

        if self.time_frame_unit == TimeFrameUnit.DAY:
            # last close > EMA(close, 200)
            if row["close"] < row["ema_200"]:
                logger.debug(
                    f"{ticker} close < EMA_200, close: {row['close']} EMA200: {row['ema_200']}"
                )
                return False

            # EMA(close, 50) > EMA(close, 200)
            if row["ema_50"] < row["ema_200"]:
                logger.debug(
                    f"{ticker} EMA_50 < EMA_200, EMA50: {row['ema_50']} EMA200: {row['ema_200']}"
                )
                return False

        # if last volume < EMA(volume, 10)*1.10
        if row["volume"] < row["ema_volume_10"] * 1.10:
            logger.debug(
                f"{ticker} volume < EMA_volume_10 * 1.10, volume: {row['volume']} EMA_volume_10 * 1.10: {row['ema_volume_10'] * 1.10}"
            )
            return False

        # At least 1% raise between close and open
        if (row["close"] - row["open"]) / row["close"] < 0.01:
            logger.debug(
                f"{ticker} (close - open) / close < 0.01, close: {row['close']} open: {row['open']}"
            )
            return False

        return True

    def is_trading_signal(self, ticker: str, date_to_check: datetime) -> bool:
        if not self.collect_historical_data(ticker, date_to_check, date_to_check):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return False

        self.calculate_indicators()

        # compare last row [hdate] with the date_to_check
        if self.df.iloc[-1]["hdate"] != date_to_check:
            logger.warning(
                f"{ticker} - last row date {self.df.iloc[-1]['hdate']} does not match {date_to_check}"
            )

        return self.is_buy_signal(ticker, self.df.iloc[-1])

    # create similar procedure as is_trading_signal that will calculate trading signals for all dates in df DataFrame
    # parameters - self, ticker, start_date, end_date
    # adds a new column to the DataFrame - df["buy_signal"] with boolean values
    # returns count of buy signals
    def trading_signals_count(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> int:
        # collect data for the ticker and end_date
        if not self.collect_historical_data(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return 0

        self.calculate_indicators()
        
        # Filter data to target date range
        filtered_df = self.df[self.df["hdate"] >= start_date].copy()
        if filtered_df.empty:
            logger.debug(f"{ticker} - no data after date filtering")
            return 0

        # Vectorized buy signal calculation - much faster than iterrows()
        buy_signals = (
            (filtered_df["close"] >= filtered_df["max_close_20"]) &
            (filtered_df["close"] >= filtered_df["ema_10"]) &
            (filtered_df["close"] >= filtered_df["ema_20"]) &
            (filtered_df["ema_10"] >= filtered_df["ema_20"]) &
            (filtered_df["close"] >= filtered_df["ema_50"]) &
            (filtered_df["volume"] >= filtered_df["ema_volume_10"] * 1.10) &
            ((filtered_df["close"] - filtered_df["open"]) / filtered_df["close"] >= 0.01)
        )
        
        # Add EMA200 conditions only for daily timeframe
        if self.time_frame_unit == TimeFrameUnit.DAY:
            buy_signals = buy_signals & (
                (filtered_df["close"] >= filtered_df["ema_200"]) &
                (filtered_df["ema_50"] >= filtered_df["ema_200"])
            )
        
        # Update original dataframe with results
        self.df.loc[filtered_df.index, "buy_signal"] = buy_signals

        return buy_signals.sum()

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

        if len(self.df) < 21:  # Need at least 21 rows for 20-day lookback
            return 0

        # Get current EMA200 (last row)
        current_ema200 = self.df.at[self.df.index[-1], "ema_200"]

        # Get EMA200 from 20 trading days ago
        past_ema200 = self.df.at[self.df.index[-21], "ema_200"]
        logger.debug(f"EMA200 1M - Current: {current_ema200}, Past: {past_ema200}")

        # Handle invalid data
        if pd.isna(current_ema200) or pd.isna(past_ema200) or past_ema200 <= 0:
            return 0

        # Calculate percentage change
        pct_change = (current_ema200 - past_ema200) / past_ema200
        logger.debug(
            f"EMA200 1M - Current: {current_ema200}, Past: {past_ema200}, Pct Change: {pct_change}"
        )

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
        if len(self.df) < 66:  # Need at least 66 rows for 65-day lookback
            return 0

        # Get current EMA200 (last row)
        current_ema200 = self.df.iloc[-1]["ema_200"]

        # Get EMA200 from 65 trading days ago (approximately 3 months)
        past_ema200 = self.df.iloc[-66]["ema_200"]

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
        if len(self.df) < 131:  # Need at least 131 rows for 130-day lookback
            return 0

        # Get current EMA200 (last row)
        current_ema200 = self.df.iloc[-1]["ema_200"]

        # Get EMA200 from 130 trading days ago (approximately 6 months)
        past_ema200 = self.df.iloc[-131]["ema_200"]

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
        if len(self.df) < 2:  # Need at least 2 rows
            return 0

        # Get current close (last row)
        current_close = self.df.iloc[-1]["close"]

        # Handle invalid data
        if pd.isna(current_close):
            return 0

        # Determine how far back we can look (up to 365 days)
        max_lookback = min(365, len(self.df))

        # Get the close prices for the lookback period
        close_prices = self.df.iloc[-max_lookback:]["close"]

        # Find the maximum close in this period
        max_close = close_prices.max()

        # If current close is not the maximum, return 0
        if current_close < max_close:
            return 0

        # Find how many days back the current close has been the highest
        days_as_high = 0
        for i in range(1, max_lookback + 1):
            if i > len(self.df):
                break

            # Check if current close is still >= the close from i days ago
            past_close = self.df.iloc[-i]["close"]
            if pd.isna(past_close) or current_close < past_close:
                break

            days_as_high = i

        # Scale score: 365 days = 20 points, 1 day = minimal points
        # Use linear scaling with a minimum threshold
        score = int(20 * (days_as_high / 365))

        # Ensure minimum score of 1 if current close is at least a 1-day high
        return max(1, score) if days_as_high > 0 else 0

    def ranking(self, ticker: str, date_to_check: datetime) -> int:
        """
        Calculate a combined ranking score for a ticker based on price and EMA200 performance.

        Args:
            ticker: The stock symbol to rank
            date_to_check: The specific date to evaluate the stock

        Returns:
            int: Combined ranking score (0-100):
                 - Price component: 0-20 (higher scores for lower-priced stocks)
                 - EMA200 1-month component: 0-20 (higher scores for EMA200 growth vs 1 month ago)
                 - EMA200 3-month component: 0-20 (higher scores for EMA200 growth vs 3 months ago)
                 - EMA200 6-month component: 0-20 (higher scores for EMA200 growth vs 6 months ago)
                 - Period high component: 0-20 (higher scores for longer period as highest close)
        """
        # Collect data for the specific date
        if not self.collect_historical_data(ticker, date_to_check, date_to_check):
            logger.warning(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return 0

        self.calculate_indicators()

        # Get the closing price from the target date
        closing_price = self.df.iloc[-1]["close"]

        # Calculate all ranking components
        price_ranking = self._price_to_ranking(closing_price)
        ema200_1month_ranking = self._ranking_ema200_1month()
        ema200_3month_ranking = self._ranking_ema200_3month()
        ema200_6month_ranking = self._ranking_ema200_6month()
        period_high_ranking = self._ranking_period_high()
        logger.info(
            f"{ticker} - Price Ranking: {price_ranking}, "
            f"EMA200 1M: {ema200_1month_ranking}, "
            f"EMA200 3M: {ema200_3month_ranking}, "
            f"EMA200 6M: {ema200_6month_ranking}, "
            f"Period High: {period_high_ranking}"
        )
        # Return combined score
        return (
            price_ranking
            + ema200_1month_ranking
            + ema200_3month_ranking
            + ema200_6month_ranking
            + period_high_ranking
        )
