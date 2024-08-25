from psycopg import connection
from datetime import datetime, timedelta

import logging
import pandas_ta as ta

from turtle.data import bars_history

logger = logging.getLogger("__name__")


class MarketData:
    def __init__(self, connection):
        self.connection = connection

    def spy_momentum(self, end_date: datetime) -> bool:
        PERIOD_LENGTH: int = 360
        df_weekly = bars_history.get_ticker_history(
            self.connection,
            "SPY",
            end_date - timedelta(days=PERIOD_LENGTH),
            end_date,
            "week",
        )

        df_weekly["EMA_20"] = ta.ema(df_weekly["close"], length=20)
        df_weekly["EMA_10"] = ta.ema(df_weekly["close"], length=10)
        last_record = df_weekly.iloc[-1]

        logger.info(
            f"SPY EMA10 - {last_record["EMA_10"]} EMA20: {last_record["EMA_20"]}"
        )
        return last_record["EMA_10"] > last_record["EMA_20"]


def spy_momentum(conn: connection, end_date: datetime) -> bool:
    PERIOD_LENGTH: int = 360
    df_weekly = bars_history.get_ticker_history(
        conn,
        "SPY",
        end_date - timedelta(days=PERIOD_LENGTH),
        end_date,
        "week",
    )

    df_weekly["EMA_20"] = ta.ema(df_weekly["close"], length=20)
    df_weekly["EMA_10"] = ta.ema(df_weekly["close"], length=10)
    last_record = df_weekly.iloc[-1]

    logger.info(f"SPY EMA10 - {last_record["EMA_10"]} EMA20: {last_record["EMA_20"]}")
    return last_record["EMA_10"] > last_record["EMA_20"]
