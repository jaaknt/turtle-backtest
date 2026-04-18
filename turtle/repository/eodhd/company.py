import logging
from turtle.repository.tables import company_table
from turtle.schema import Company

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_batch(self, companies: list[Company]) -> int:
        if not companies:
            return 0

        values = [
            {
                "ticker_code": c.symbol,
                "type": c.type,
                "name": c.name,
                "sector": c.sector,
                "industry": c.industry,
                "average_volume": c.average_volume,
                "average_price": c.fifty_day_average_price,
                "dividend_yield": c.dividend_yield,
                "market_cap": c.market_cap,
                "pe": c.pe,
                "forward_pe": c.forward_pe,
            }
            for c in companies
        ]
        stmt = pg_insert(company_table).values(values)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[company_table.c.ticker_code],
            set_={
                "type": stmt.excluded.type,
                "name": stmt.excluded.name,
                "sector": stmt.excluded.sector,
                "industry": stmt.excluded.industry,
                "average_volume": stmt.excluded.average_volume,
                "average_price": stmt.excluded.average_price,
                "dividend_yield": stmt.excluded.dividend_yield,
                "market_cap": stmt.excluded.market_cap,
                "pe": stmt.excluded.pe,
                "forward_pe": stmt.excluded.forward_pe,
            },
        )
        await self._session.execute(on_conflict_stmt)
        await self._session.commit()
        return len(companies)
