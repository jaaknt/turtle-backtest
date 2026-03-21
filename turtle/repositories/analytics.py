import logging
from datetime import date
from turtle.data.tables import daily_bars_table

import pandas as pd
from sqlalchemy import Engine, select

logger = logging.getLogger(__name__)


class OhlcvAnalyticsRepository:
    """Dedicated repository for bulk analytical reads from daily_bars.

    Bypasses ORM hydration — returns DataFrames directly.
    Accepts Engine (not Session) because it manages its own connections
    for read-only analytical queries.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_bars(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Return OHLCV bars as a DataFrame with date as index.

        Columns: open, high, low, close, adjusted_close, volume.
        Returns empty DataFrame if no data found.
        """
        t = daily_bars_table
        stmt = (
            select(t.c.date, t.c.open, t.c.high, t.c.low, t.c.close, t.c.adjusted_close, t.c.volume)
            .where(t.c.symbol == ticker)
            .where(t.c.date >= start_date)
            .where(t.c.date <= end_date)
            .order_by(t.c.date)
        )
        with self._engine.connect() as conn:
            return pd.read_sql(stmt, conn, index_col="date")
