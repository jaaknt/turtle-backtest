import logging
from turtle.repository.eodhd.ticker import COMMON_STOCK_TYPE, US_EXCHANGES
from turtle.repository.tables import company_table, ticker_group_table, ticker_table

from sqlalchemy import Engine, and_, select

logger = logging.getLogger(__name__)


class TickerQueryRepository:
    """Sync Engine-based repository for ticker list reads."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_symbol_list(
        self,
        country: str,
        min_code: str = "",
        limit: int | None = None,
        ticker_group: str = "active",
    ) -> list[str]:
        t = ticker_table
        tg = ticker_group_table
        stmt = (
            select(t.c.code)
            .select_from(t.join(tg, (and_(t.c.code == tg.c.ticker_code, tg.c.code == ticker_group))))
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

    def get_qualified_symbols(
        self,
        min_market_cap: int = 1_500_000_000,
        excluded_sectors: list[str] | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """Return the Qullamaggie backtest universe: US common stocks by fundamentals.

        Mirrors the universe query of scripts/qullamaggie-backtest-v4.py:
        USA common stocks with a minimum market cap, excluding the given sectors.
        Membership reflects the current company snapshot (market_cap/sector are
        not point-in-time values).

        Args:
            min_market_cap: Minimum company market cap in USD
            excluded_sectors: Company sectors to exclude (default:
                Communication Services and Real Estate)
            limit: Optional maximum number of symbols to return
        """
        if excluded_sectors is None:
            excluded_sectors = ["Communication Services", "Real Estate"]
        t = ticker_table
        c = company_table
        stmt = (
            select(t.c.code)
            .select_from(t.join(c, t.c.code == c.c.ticker_code))
            .where(
                and_(
                    t.c.country == "USA",
                    t.c.type == COMMON_STOCK_TYPE,
                    c.c.market_cap >= min_market_cap,
                    c.c.sector.not_in(excluded_sectors),
                )
            )
            .order_by(t.c.code)
        )
        with self._engine.connect() as conn:
            codes = [row.code for row in conn.execute(stmt).fetchall()]
        if limit is not None:
            codes = codes[:limit]
        return codes
