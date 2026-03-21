import logging
from datetime import datetime
from turtle.data.tables import daily_bars_table
from turtle.schemas import PriceHistory

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DailyBarsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_batch(self, records: list[PriceHistory]) -> int:
        if not records:
            return 0

        values_to_insert = []
        for record in records:
            try:
                record_date = datetime.fromisoformat(record.date)
            except ValueError as e:
                logger.warning(f"Invalid date format for {record.ticker}: {record.date}, skipping. Error: {e}")
                continue
            values_to_insert.append(
                {
                    "symbol": record.ticker,
                    "date": record_date,
                    "open": record.open,
                    "high": record.high,
                    "low": record.low,
                    "close": record.close,
                    "adjusted_close": record.adjusted_close,
                    "volume": record.volume,
                    "source": "eodhd",
                }
            )

        if not values_to_insert:
            return 0

        stmt = pg_insert(daily_bars_table).values(values_to_insert)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[daily_bars_table.c.symbol, daily_bars_table.c.date],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "adjusted_close": stmt.excluded.adjusted_close,
                "volume": stmt.excluded.volume,
                "source": stmt.excluded.source,
            },
        )
        await self._session.execute(on_conflict_stmt)
        await self._session.commit()
        return len(values_to_insert)
