import logging

from sqlalchemy import Engine, and_, select

from turtlex.repository.tables import (
    COMMON_STOCK_TYPE,
    US_EXCHANGES,
    company_table,
    ticker_group_table,
    ticker_table,
)

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
        """Return ticker codes of a symbol group for the given country on US exchanges.

        This is the default strategy universe: members of the named group in
        ``turtle.ticker_group``, restricted to US exchanges (NASDAQ, NYSE,
        NYSE ARCA, NYSE MKT). The ``min_code`` and ``limit`` filters are
        applied in Python after the fetch, not in SQL.

        Generated SQL (PostgreSQL)::

            SELECT turtle.ticker.code
            FROM turtle.ticker
            JOIN turtle.ticker_group
              ON turtle.ticker.code = turtle.ticker_group.ticker_code
             AND turtle.ticker_group.code = :ticker_group
            WHERE turtle.ticker.country = :country
              AND turtle.ticker.exchange IN ('NASDAQ', 'NYSE', 'NYSE ARCA', 'NYSE MKT')
            ORDER BY turtle.ticker.code

        Args:
            country: Ticker country filter (e.g. "USA")
            min_code: Skip codes sorting lexicographically before this value
            limit: Optional maximum number of symbols to return
            ticker_group: Symbol group name in turtle.ticker_group (default "active")

        Returns:
            list[str]: Ticker codes in "TICKER.US" format, ordered by code
        """
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

    def get_group_ticker_codes(self, group_code: str) -> set[str]:
        """Return every ticker code in a ticker_group, unfiltered by exchange or country.

        Unlike ``get_symbol_list`` this reads ``turtle.ticker_group`` alone, without
        joining ``turtle.ticker``. Membership tests must not drop AMEX or non-USA
        listings a group may legitimately contain.

        Generated SQL (PostgreSQL)::

            SELECT turtle.ticker_group.ticker_code
            FROM turtle.ticker_group
            WHERE turtle.ticker_group.code = :group_code

        Args:
            group_code: Group identifier in turtle.ticker_group (e.g. "lightyear")

        Returns:
            set[str]: Ticker codes in "TICKER.US" format; empty if the group does not exist
        """
        tg = ticker_group_table
        stmt = select(tg.c.ticker_code).where(tg.c.code == group_code)
        with self._engine.connect() as conn:
            return {row.ticker_code for row in conn.execute(stmt).fetchall()}

    def get_qullamaggie_qualified_symbols(
        self,
        min_market_cap: int = 1_500_000_000,
        excluded_sectors: list[str] | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """Return the Qullamaggie backtest universe: US common stocks by fundamentals.

        Mirrors the universe query of scripts/qullamaggie-backtest-v4.py:
        USA common stocks with a minimum market cap, excluding the given sectors.
        Membership reflects the current company snapshot (market_cap/sector are
        not point-in-time values). The ``limit`` is applied in Python after the
        fetch, not in SQL.

        Generated SQL (PostgreSQL)::

            SELECT turtle.ticker.code
            FROM turtle.ticker
            JOIN turtle.company
              ON turtle.ticker.code = turtle.company.ticker_code
            WHERE turtle.ticker.country = 'USA'
              AND turtle.ticker.type = 'Common Stock'
              AND turtle.company.market_cap >= :min_market_cap
              AND turtle.company.sector NOT IN (:excluded_sectors)
            ORDER BY turtle.ticker.code

        Args:
            min_market_cap: Minimum company market cap in USD
            excluded_sectors: Company sectors to exclude (default:
                Communication Services and Real Estate)
            limit: Optional maximum number of symbols to return

        Returns:
            list[str]: Ticker codes in "TICKER.US" format, ordered by code
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

    def get_sectors(self) -> dict[str, str]:
        """Return the sector of every company that has one, for reporting.

        Generated SQL (PostgreSQL)::

            SELECT turtle.company.ticker_code, turtle.company.sector
            FROM turtle.company
            WHERE turtle.company.sector IS NOT NULL

        Returns:
            dict[str, str]: Ticker code -> sector name. A ticker with no company row, or
            with a null sector, is simply absent; callers render those as "--".
        """
        c = company_table
        stmt = select(c.c.ticker_code, c.c.sector).where(c.c.sector.is_not(None))
        with self._engine.connect() as conn:
            return {row.ticker_code: row.sector for row in conn.execute(stmt).fetchall()}
