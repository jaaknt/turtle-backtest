import logging
from turtle.data.tables import exchange_table
from turtle.schemas import Exchange

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ExchangeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, exchanges: list[Exchange]) -> None:
        if not exchanges:
            return
        values = [
            {
                "code": ex.code,
                "name": ex.name,
                "country": ex.country,
                "currency": ex.currency,
                "country_iso3": ex.country_iso3,
            }
            for ex in exchanges
        ]
        stmt = pg_insert(exchange_table).values(values)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[exchange_table.c.code],
            set_={
                "name": stmt.excluded.name,
                "country": stmt.excluded.country,
                "currency": stmt.excluded.currency,
                "country_iso3": stmt.excluded.country_iso3,
            },
        )
        await self._session.execute(on_conflict_stmt)
        await self._session.commit()
