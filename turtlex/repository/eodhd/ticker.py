import logging
from collections.abc import Sequence

from sqlalchemy import and_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from turtlex.repository.tables import ticker_table
from turtlex.schema import Ticker

logger = logging.getLogger(__name__)

US_EXCHANGES = ["NASDAQ", "NYSE", "NYSE ARCA", "NYSE MKT"]
COMMON_STOCK_TYPE = "Common Stock"


class TickerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, tickers: list[Ticker], batch_size: int = 1000) -> int:
        total = 0
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i : i + batch_size]
            values = [
                {
                    "code": t.code + ".US",
                    "exchange_code": t.code,
                    "name": t.name,
                    "country": t.country,
                    "exchange": t.exchange,
                    "currency": t.currency,
                    "type": t.type,
                    "isin": t.isin,
                    "source": "eodhd",
                    "status": "active",
                }
                for t in batch
            ]
            stmt = pg_insert(ticker_table).values(values)
            on_conflict_stmt = stmt.on_conflict_do_update(
                index_elements=[ticker_table.c.code],
                set_={
                    "exchange_code": stmt.excluded.exchange_code,
                    "name": stmt.excluded.name,
                    "country": stmt.excluded.country,
                    "exchange": stmt.excluded.exchange,
                    "currency": stmt.excluded.currency,
                    "type": stmt.excluded.type,
                    "isin": stmt.excluded.isin,
                    "source": stmt.excluded.source,
                    "status": stmt.excluded.status,
                },
            )
            await self._session.execute(on_conflict_stmt)
            total += len(batch)
            logger.info(f"Processed batch {i // batch_size + 1}: {total}/{len(tickers)} tickers")

        await self._session.commit()
        return total

    async def fetch_tickers(self, country: str, limit: int | None = None) -> Sequence[Row]:
        """Fetch all common stocks on major US exchanges for a given country.

        Used for bulk data downloads (e.g. company fundamentals) where exchange
        and type filters matter but active-group membership does not.
        Returns rows with code in "TICKER.US" format.
        """
        stmt = (
            select(ticker_table.c.code)
            .where(
                and_(
                    ticker_table.c.country == country,
                    ticker_table.c.exchange.in_(US_EXCHANGES),
                    ticker_table.c.type == COMMON_STOCK_TYPE,
                )
            )
            .order_by(ticker_table.c.code)
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        if limit is not None:
            rows = rows[:limit]
        return rows

    async def fetch_us_downloadable_tickers(self) -> Sequence[Row]:
        """Fetch the full ticker universe for historical OHLCV downloads.

        Common Stock tickers with a company sector, plus a fixed set of index
        and sector ETFs. Returns rows with code in "TICKER.US" format.
        """
        stmt = text("""
            select t.code
              from turtle.ticker t
                   inner join turtle.company c
                           on c.ticker_code = t.code
             where t.type = 'Common Stock'
               and c.sector is not null
            union
            select t.code
              from turtle.ticker t
             where t.code in ('SPY.US', 'QQQ.US', 'XLB.US', 'XLC.US', 'XLE.US', 'XLF.US',
                              'XLI.US', 'XLK.US', 'XLP.US', 'XLRE.US', 'XLU.US', 'XLV.US',
                              'XLY.US', 'XBI.US', 'XAR.US')
             order by code
        """)
        result = await self._session.execute(stmt)
        return result.fetchall()
