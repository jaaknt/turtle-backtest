import logging
from collections.abc import Sequence
from datetime import datetime
from turtle.data.tables import company_table, daily_bars_table, exchange_table, ticker_table
from turtle.schemas import Company, Exchange, PriceHistory, Ticker

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

US_EXCHANGES = ["NASDAQ", "NYSE", "NYSE ARCA", "NYSE MKT"]
COMMON_STOCK_TYPE = "Common Stock"


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

    async def fetch_us_stocks(self, limit: int | None = None) -> Sequence[Row]:
        stmt = select(ticker_table.c.exchange_code).where(
            and_(
                ticker_table.c.country == "USA",
                ticker_table.c.exchange.in_(US_EXCHANGES),
                ticker_table.c.type == COMMON_STOCK_TYPE,
            )
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        if limit is not None:
            rows = rows[:limit]
        return rows


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
