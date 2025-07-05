from datetime import datetime, timedelta
import logging
import pandas as pd
import talib

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


# Mars Strategy (@marsrides)
# https://docs.google.com/document/d/1BZgaYWFOnsOFMFWRt0jJgNVeLicEMB-ccf9kUwtIxYI/edit?tab=t.0
class MarsStrategy:
    def __init__(
        self,
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.WEEK,
        warmup_period: int = 300,
        min_bars: int = 30,
    ):
        self.bars_history = bars_history

        self.df = pd.DataFrame()
        self.df_orig = pd.DataFrame()
        self.time_frame_unit: TimeFrameUnit = time_frame_unit
        self.warmup_period = warmup_period
        self.min_bars = min_bars

    def collect(self, ticker: str, start_date: datetime, end_date: datetime) -> bool:
        self.df = self.bars_history.get_ticker_history(
            ticker,
            start_date - timedelta(days=self.warmup_period),
            end_date,
            self.time_frame_unit,
        )
        return not (self.df.empty or self.df.shape[0] < self.min_bars)

    def add_indicators(self) -> None:
        # calculate min and max over last 4 period open and close (excluding current period)
        self.df["max_box_4"] = (
            self.df[["open", "close"]].shift(1).rolling(window=4).max().max(axis=1)
        )
        self.df["min_box_4"] = (
            self.df[["open", "close"]].shift(1).rolling(window=4).min().min(axis=1)
        )

        # consolidation_change (max_box_4 - min_box_4) / close
        self.df["consolidation_change"] = (
            self.df["max_box_4"] - self.df["min_box_4"]
        ) / self.df["close"]
        self.df["hard_stoploss"] = (
            self.df["max_box_4"] + self.df["min_box_4"]
        ) / 2 - 0.02

        self.df["ema_10"] = talib.EMA(
            self.df["close"].values.astype(float), timeperiod=10
        )
        self.df["ema_20"] = talib.EMA(
            self.df["close"].values.astype(float), timeperiod=20
        )

        macd_line, macd_signal, macd_histogram = talib.MACD(
            self.df["close"].values.astype(float),
            fastperiod=12,
            slowperiod=26,
            signalperiod=9,
        )
        self.df["macd"] = macd_line
        self.df["macd_histogram"] = macd_histogram
        self.df["macd_signal"] = macd_signal

        self.df["max_close_10"] = self.df["close"].rolling(window=10).max()

        # volume indicators
        self.df["ema_volume_4"] = talib.SMA(
            self.df["volume"].shift(1).values.astype(float), timeperiod=4
        )
        self.df["volume_change"] = self.df["volume"] / self.df["ema_volume_4"]

        self.df["buy_signal"] = False

        self.df = self.df.reset_index()
        self.df["hdate"] = pd.to_datetime(self.df["hdate"]) - pd.Timedelta(days=6)

    def is_buy_signal(self, ticker: str, row: pd.Series) -> bool:
        # last close > max(close, 10)
        if row["close"] < row["max_close_10"]:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} close < max_close_10, close: {row['close']} max_close_10: {row['max_close_10']}"
            )
            return False

        # EMA(close, 10) > EMA(close, 20)
        if row["ema_10"] < row["ema_20"]:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} EMA_10 < EMA_20, EMA10: {row['ema_10']} EMA20: {row['ema_20']}"
            )
            return False

        # MACD_signal is not NaN or MACD is not NaN
        if pd.isna(row["macd"]) or pd.isna(row["macd_signal"]):
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} MACD_signal is NaN"
            )
            return False

        # consolidation_change < 0.12
        if row["consolidation_change"] > 0.12:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} consolidation_change > 0.12, consolidation_change: {row['consolidation_change']}"
            )
            return False

        # (close - hard_stoploss / close < 0.16
        if (row["close"] - row["hard_stoploss"]) / row["close"] > 0.25:
            logger.debug(
                f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} (close - (max_box_4 - min_box_4) / 2) / close < 0.16, close: {row['close']} hard_stoploss: {row['hard_stoploss']}"
            )
            return False

        """
        # if last volume < EMA(volume, 4)*1.10
        if row["volume"] < row["ema_volume_4"] * 0.9:
            logger.debug(
                f"{ticker} {row["hdate"].strftime('%Y-%m-%d')} volume < EMA_volume_4 * 1.10, volume: {row["volume"]} EMA_volume_4 * 1.10: {row["ema_volume_4"]*1.10}"
            )
            return False
        """

        logger.debug(f"{ticker} {row['hdate'].strftime('%Y-%m-%d')} buy signal")
        return True

    def calculate_entries(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> None:
        # collect data for the ticker and end_date
        if not self.collect(ticker, start_date, end_date):
            logger.debug(f"{ticker} - not enough data, rows: {self.df.shape[0]}")
            return

        self.add_indicators()

        self.df_orig = self.df.copy()
        self.df = self.df.query("hdate >= @start_date and hdate <= @end_date")

        # skip rows before start_date and after end_date
        for i, row in self.df.iterrows():
            self.df.at[i, "buy_signal"] = self.is_buy_signal(ticker, row)
