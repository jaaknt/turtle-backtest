import logging
from datetime import date

import polars as pl
from sqlalchemy import Engine, Select, and_, select

from turtlex.common.enums import TimeFrameUnit
from turtlex.repository.tables import COMMON_STOCK_TYPE, company_table, daily_bars_table, ticker_table

logger = logging.getLogger(__name__)

# Server-side cursor batch for get_qualified_universe_bars_pl; see the note there.
LOAD_BATCH_ROWS = 200_000


class DailyBarsQueryRepository:
    """Dedicated repository for bulk analytical reads from daily_bars.

    Bypasses ORM hydration — returns DataFrames directly.
    Accepts Engine (not Session) because it manages its own connections
    for read-only analytical queries.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _build_stmt(self, ticker: str, start_date: date, end_date: date) -> Select[tuple[object, ...]]:
        t = daily_bars_table
        return (
            select(t.c.date, t.c.open, t.c.high, t.c.low, t.c.close, t.c.adjusted_close, t.c.volume)
            .where(t.c.symbol == ticker)
            .where(t.c.date >= start_date)
            .where(t.c.date <= end_date)
            .order_by(t.c.date)
        )

    def get_bars_pl(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ) -> pl.DataFrame:
        """Return OHLCV bars as a Polars DataFrame.

        Columns: date, open, high, low, close, adjusted_close, volume.
        Supports DAY and WEEK resampling via time_frame_unit.
        Returns empty DataFrame if no data found.
        """
        stmt = self._build_stmt(ticker, start_date, end_date)
        with self._engine.connect() as conn:
            df = pl.read_database(query=stmt, connection=conn)
        if df.is_empty() or time_frame_unit == TimeFrameUnit.DAY:
            return df
        if time_frame_unit != TimeFrameUnit.WEEK:
            raise ValueError(f"Unsupported time_frame_unit: {time_frame_unit!r}")
        return (
            df.sort("date")
            .group_by_dynamic("date", every="1w")
            .agg(
                pl.col("open").first(),
                pl.col("high").max(),
                pl.col("low").min(),
                pl.col("close").last(),
                pl.col("adjusted_close").last(),
                pl.col("volume").sum(),
            )
            .sort("date")
        )

    def get_qualified_universe_bars_pl(
        self,
        start_date: date,
        end_date: date,
        min_market_cap: int = 1_500_000_000,
        max_market_cap: int | None = None,
        excluded_sectors: list[str] | None = None,
    ) -> pl.DataFrame:
        """Return daily bars for every fundamentals-qualified US common stock in one query.

        The per-ticker `get_bars_pl` serves the runner, which walks the universe one ticker at
        a time. This bulk read serves the whole-universe research studies in
        `turtlex/research/`, where a parameter sweep re-filters an in-memory frame instead of
        re-querying. Bars are returned as stored — non-positive or zero-volume rows are the
        caller's concern, so this matches what the per-ticker read returns.

        The result is streamed through a server-side cursor and concatenated batch by batch
        rather than buffered whole. The widest study universe is ~7M rows, and a plain
        buffered read materialises every one of them as a Python row tuple before the
        DataFrame exists — several GB of interpreter objects that live alongside the frame
        being built. On WSL, where every user process shares one unbounded cgroup, that has
        OOM-killed the whole distro. `iter_batches` bounds the tuple spike to LOAD_BATCH_ROWS.

        Args:
            start_date: First bar date to include (inclusive)
            end_date: Last bar date to include (inclusive)
            min_market_cap: Minimum company market capitalisation (inclusive)
            max_market_cap: Optional exclusive upper bound, so a caller that cannot hold the
                whole universe at once can read it in market-cap slabs. Market cap is a
                per-symbol attribute and the studies' per-symbol logic never crosses symbols,
                so slabbed reads reproduce a single wide read exactly.
            excluded_sectors: Sectors to exclude; defaults to Communication Services and Real Estate

        Returns:
            Columns: symbol, date, open, high, low, close, adjusted_close, volume — ordered by
            symbol then date. Empty DataFrame if nothing qualifies.
        """
        if excluded_sectors is None:
            excluded_sectors = ["Communication Services", "Real Estate"]

        b, t, c = daily_bars_table, ticker_table, company_table
        stmt = (
            select(b.c.symbol, b.c.date, b.c.open, b.c.high, b.c.low, b.c.close, b.c.adjusted_close, b.c.volume)
            .select_from(b.join(t, t.c.code == b.c.symbol).join(c, c.c.ticker_code == t.c.code))
            .where(
                and_(
                    t.c.country == "USA",
                    t.c.type == COMMON_STOCK_TYPE,
                    c.c.market_cap >= min_market_cap,
                    *([c.c.market_cap < max_market_cap] if max_market_cap is not None else []),
                    c.c.sector.not_in(excluded_sectors),
                    b.c.date >= start_date,
                    b.c.date <= end_date,
                )
            )
            .order_by(b.c.symbol, b.c.date)
        )
        with self._engine.connect().execution_options(stream_results=True, max_row_buffer=LOAD_BATCH_ROWS) as conn:
            batches = list(pl.read_database(query=stmt, connection=conn, iter_batches=True, batch_size=LOAD_BATCH_ROWS))
        if not batches:
            return pl.DataFrame()
        return pl.concat(batches, rechunk=True)
