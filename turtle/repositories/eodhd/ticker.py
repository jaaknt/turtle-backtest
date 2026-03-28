import logging
from collections.abc import Sequence
from turtle.repositories.tables import ticker_group_table, ticker_table
from turtle.schemas import Ticker

from sqlalchemy import Engine, and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

US_EXCHANGES = ["NASDAQ", "NYSE", "NYSE ARCA", "NYSE MKT"]
COMMON_STOCK_TYPE = "Common Stock"


class TickerQueryRepository:
    """Sync Engine-based repository for ticker list reads."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_symbol_list(
        self,
        country: str,
        min_code: str = "",
        limit: int | None = None,
    ) -> list[str]:
        t = ticker_table
        tg = ticker_group_table
        stmt = (
            select(t.c.code)
            .select_from(t.join(tg, (and_(t.c.code == tg.c.ticker_code, tg.c.code == "active"))))
            .where(
                and_(
                    ticker_table.c.country == country,
                    ticker_table.c.exchange.in_(US_EXCHANGES),
                    # ticker_table.c.type == COMMON_STOCK_TYPE,
                )
            )
            .order_by(t.c.code)
        )
        with self._engine.connect() as conn:
            codes = [row.code for row in conn.execute(stmt).fetchall()]
        if min_code:
            codes = [c for c in codes if c >= min_code]
        if limit is not None:
            codes = codes[:limit]
        return codes


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

    async def fetch_group_tickers(self, country: str, group_code: str, limit: int | None = None) -> Sequence[Row]:
        """Fetch tickers that belong to a named symbol group for a given country.

        Used for historical OHLCV downloads where the group defines the
        universe of interest regardless of exchange or instrument type.
        Returns rows with code in "TICKER.US" format.
        """
        if not group_code:
            raise ValueError("group_code must be a non-empty string")
        stmt = (
            select(ticker_table.c.code)
            .select_from(
                ticker_table.join(
                    ticker_group_table,
                    (and_(ticker_table.c.code == ticker_group_table.c.ticker_code, ticker_group_table.c.code == group_code)),
                )
            )
            .where(
                and_(
                    ticker_table.c.country == country,
                )
            )
            .order_by(ticker_table.c.code)
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        if limit is not None:
            rows = rows[:limit]
        return rows
