from psycopg import connection
from datetime import datetime, timedelta
from typing import List

import logging

# import pandas as pd
import pandas_ta as ta

from turtle.data import bars_history, symbol
from turtle.strategy import market
from turtle.strategy.market import MarketData

logger = logging.getLogger("__name__")


class MomentumStrategy:
    def __init__(self, connection):
        self.connection = connection
        self.market_data = MarketData(self.connection)

    def weekly_momentum(self, ticker: str, end_date: datetime) -> bool:
        PERIOD_LENGTH: int = 360
        df_weekly = bars_history.get_ticker_history(
            self.connection,
            ticker,
            end_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            "week",
        )

        df_weekly["sma_20"] = ta.sma(df_weekly["close"], length=20)
        df_weekly["max_last_10"] = df_weekly["close"].rolling(window=10).max()

        df_daily = bars_history.get_ticker_history(
            self.connection,
            ticker,
            end_date - timedelta(days=2 * PERIOD_LENGTH),
            end_date,
            "day",
        )
        df_daily["ema_200"] = ta.ema(df_daily["close"], length=200)

        df_daily_filtered = df_daily.loc[
            end_date - timedelta(days=PERIOD_LENGTH) : end_date
        ]
        if df_daily_filtered.shape[0] < 240:
            logger.debug(
                f"{ticker} - not enough data, rows: {df_daily_filtered.shape[0]}"
            )
            return False

        # logger.debug(df_daily_filtered)
        days_below_200_ema = (
            df_daily_filtered["close"] < df_daily_filtered["ema_200"]
        ).sum()

        if days_below_200_ema > 40:
            logger.debug(
                f"{ticker} - too many days below 200 EMA: {days_below_200_ema}"
            )
            return False

        # there must be at least 30 records in DataFrame
        if df_weekly.shape[0] < 30:
            logger.debug(f"{ticker} - not enough data, rows: {df_weekly.shape[0]}")
            return False

        # last close > EMA(close, 20)
        last_record = df_weekly.iloc[-1]
        if last_record["close"] < last_record["sma_20"]:
            logger.debug(
                f"{ticker} close < SMA_20, close: {last_record["close"]} SMA20: {last_record["sma_20"]}"
            )
            return False

        # there has been >10% raise 1, 3 or 6 months ago
        prev_record = df_weekly.iloc[-2]
        month_1_record = df_weekly.iloc[-6]
        month_3_record = df_weekly.iloc[-15]
        month_6_record = df_weekly.iloc[-28]
        if not (
            prev_record["close"]
            > min(
                month_1_record["close"],
                month_3_record["close"],
                month_6_record["close"],
            )
            * 1.1
        ):
            logger.debug(
                f"{ticker} missing 10% raise , close: {prev_record ["close"]} month_1: {month_1_record["close"]} month_3: {month_3_record["close"]} month_6: {month_6_record["close"]}"
            )
            return False

        # close must be > max(last 10 close)
        if not (last_record["close"] > prev_record["max_last_10"]):
            logger.debug(
                f"{ticker} close < max(close 10), prev_close: {last_record["close"]}, max_last_10: {prev_record["max_last_10"]}"
            )
            return False

        # close must be > (high + low) / 2
        if not (
            last_record["close"] > (last_record["high"] + last_record["low"]) / 2.0
        ):
            logger.debug(
                f"{ticker} close < (high + low)/2, close: {last_record["close"]}, high: {last_record["high"]}, low: {last_record["low"]}"
            )
            return False

        # close must be 2-20% higher than in previous week
        if not (
            (last_record["close"] > prev_record["close"] * 1.02)
            and (last_record["close"] < (prev_record["close"] * 1.15))
        ):
            logger.debug(
                f"{ticker} close must be 2-15% higher then previous close: {last_record["close"]}, 1.02 prev_close: {prev_record["close"]*1.02}, 1.15 prev_close: {prev_record["close"]*1.15}"
            )
            return False

        # volume must be >10% higher than in previous week
        if not (last_record["volume"] > prev_record["volume"] * 1.10):
            logger.debug(
                f"{ticker} volume must be >10% higher than in previous week: {last_record["volume"]}, 1.10 * prev_volume: {prev_record["volume"]*1.10}"
            )
            return False

        return True

    def momentum_stocks(self, start_date: datetime) -> List[str]:
        if self.market_data.spy_momentum(start_date):
            symbol_list = symbol.get_symbol_list(self.connection, "USA")
            momentum_stock_list = []
            for ticker in symbol_list:
                if self.weekly_momentum(ticker, start_date):
                    momentum_stock_list.append(ticker)
            return momentum_stock_list
        return []


def weekly_momentum(conn: connection, ticker: str, end_date: datetime) -> bool:
    PERIOD_LENGTH: int = 360
    df_weekly = bars_history.get_ticker_history(
        conn,
        ticker,
        end_date - timedelta(days=PERIOD_LENGTH),
        end_date,
        "week",
    )

    df_weekly["sma_20"] = ta.sma(df_weekly["close"], length=20)
    df_weekly["max_last_10"] = df_weekly["close"].rolling(window=10).max()

    df_daily = bars_history.get_ticker_history(
        conn,
        ticker,
        end_date - timedelta(days=2 * PERIOD_LENGTH),
        end_date,
        "day",
    )
    df_daily["ema_200"] = ta.ema(df_daily["close"], length=200)

    df_daily_filtered = df_daily.loc[
        end_date - timedelta(days=PERIOD_LENGTH) : end_date
    ]
    if df_daily_filtered.shape[0] < 240:
        logger.debug(f"{ticker} - not enough data, rows: {df_daily_filtered.shape[0]}")
        return False

    # logger.debug(df_daily_filtered)
    days_below_200_ema = (
        df_daily_filtered["close"] < df_daily_filtered["ema_200"]
    ).sum()

    if days_below_200_ema > 20:
        logger.debug(f"{ticker} - too many days below 200 EMA: {days_below_200_ema}")
        return False

    # there must be at least 30 records in DataFrame
    if df_weekly.shape[0] < 30:
        logger.debug(f"{ticker} - not enough data, rows: {df_weekly.shape[0]}")
        return False

    # last close > EMA(close, 20)
    last_record = df_weekly.iloc[-1]
    if last_record["close"] < last_record["sma_20"]:
        logger.debug(
            f"{ticker} close < SMA_20, close: {last_record["close"]} SMA20: {last_record["sma_20"]}"
        )
        return False

    # there has been >10% raise 1, 3 or 6 months ago
    prev_record = df_weekly.iloc[-2]
    month_1_record = df_weekly.iloc[-6]
    month_3_record = df_weekly.iloc[-15]
    month_6_record = df_weekly.iloc[-28]
    if not (
        prev_record["close"]
        > min(
            month_1_record["close"],
            month_3_record["close"],
            month_6_record["close"],
        )
        * 1.1
    ):
        logger.debug(
            f"{ticker} missing 10% raise , close: {prev_record ["close"]} month_1: {month_1_record["close"]} month_3: {month_3_record["close"]} month_6: {month_6_record["close"]}"
        )
        return False

    # close must be > max(last 10 close)
    if not (last_record["close"] > prev_record["max_last_10"]):
        logger.debug(
            f"{ticker} close < max(close 10), prev_close: {last_record["close"]}, max_last_10: {prev_record["max_last_10"]}"
        )
        return False

    # close must be > (high + low) / 2
    if not (last_record["close"] > (last_record["high"] + last_record["low"]) / 2.0):
        logger.debug(
            f"{ticker} close < (high + low)/2, close: {last_record["close"]}, high: {last_record["high"]}, low: {last_record["low"]}"
        )
        return False

    # close must be 2-20% higher than in previous week
    if not (
        (last_record["close"] > prev_record["close"] * 1.02)
        and (last_record["close"] < (prev_record["close"] * 1.15))
    ):
        logger.debug(
            f"{ticker} close must be 2-15% higher then previous close: {last_record["close"]}, 1.02 prev_close: {prev_record["close"]*1.02}, 1.15 prev_close: {prev_record["close"]*1.15}"
        )
        return False

    # volume must be >10% higher than in previous week
    if not (last_record["volume"] > prev_record["volume"] * 1.10):
        logger.debug(
            f"{ticker} volume must be >10% higher than in previous week: {last_record["volume"]}, 1.10 * prev_volume: {prev_record["volume"]*1.10}"
        )
        return False

    return True


def momentum_stocks(conn: connection, start_date: datetime) -> List[str]:
    if market.spy_momentum(conn, start_date):
        symbol_list = symbol.get_symbol_list(conn, "USA")
        momentum_stock_list = []
        for ticker in symbol_list:
            if weekly_momentum(conn, ticker, start_date):
                momentum_stock_list.append(ticker)
        return momentum_stock_list
    return []
