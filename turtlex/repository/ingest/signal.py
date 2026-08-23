"""Signal write repository.

The module name does not shadow the stdlib `signal`: Python 3 uses absolute imports and this is a
package submodule, so `import signal` elsewhere still reaches the standard library.
"""

import logging

from sqlalchemy import Engine, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from turtlex.model import Signal
from turtlex.repository.tables import signal_table

logger = logging.getLogger(__name__)


def _parameters(signal: Signal) -> dict[str, float]:
    """Per-signal jsonb payload: the reported indicators plus next_open.

    None is omitted rather than stored as JSON null, matching Signal.indicators, which already
    drops an indicator whose signal-date value is missing. An absent key therefore means "not
    reported or not computed" - a strategy may report an indicator that was null on the day.

    The signal-date close is absent because no reported indicator is named for it, not because
    anything here removes it; it lives in the signal_close column. A future strategy that put a
    close under some key in `indicators` would duplicate the column into the payload.

    Args:
        signal: Signal whose reporting fields form the payload

    Returns:
        dict[str, float]: JSONB takes this dict directly, with no json.dumps. Values must be
            finite: NaN and Inf are floats but not JSON, and Postgres rejects the whole
            statement if one reaches it.
    """
    params = dict(signal.indicators)
    if signal.next_open is not None:
        params["next_open"] = signal.next_open
    return params


class SignalRepository:
    """Sync Engine-based repository for strategy-signal writes."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert_signals(self, signals: list[Signal], *, trading_strategy: str, ranking_strategy: str) -> int:
        """Store signals under `trading_strategy`, overwriting any already stored for the same key.

        Args:
            signals: Signals to store, ungated -- the caller must not have applied a ranking filter
            trading_strategy: Variant label written to the trading_strategy column, e.g. bk50d_s12_v2.0
            ranking_strategy: Name of the scheme that produced each ranking

        Returns:
            int: Number of signals sent to the database

        Raises:
            ValueError: If any signal carries no signal_close, which turtle.signal requires
        """
        if not signals:
            return 0

        # Checked here rather than left to the NOT NULL constraint: the database message names
        # neither the strategy nor the reason, and by then a universe scan has already run.
        missing = [s for s in signals if s.signal_close is None]
        if missing:
            raise ValueError(
                f"{len(missing)} of {len(signals)} signals carry no signal_close (first: {missing[0].ticker} "
                f"{missing[0].date}); turtle.signal requires it, so --persist needs a strategy that reports "
                "the signal-date close -- currently only qullamaggie"
            )

        values = [
            {
                "trading_strategy": trading_strategy,
                "ranking_strategy": ranking_strategy,
                "symbol": s.ticker,
                "signal_date": s.date,
                "ranking": s.ranking,
                "signal_close": s.signal_close,
                "parameters": _parameters(s),
            }
            for s in signals
        ]
        stmt = pg_insert(signal_table).values(values)
        # DO UPDATE, not DO NOTHING: next_open arrives once a bar after the signal date is loaded,
        # and ranking itself can move because pct_vs_sma50 derives from adjusted_close, which EODHD
        # rewrites retroactively on every dividend. ranking_strategy is rewritten alongside ranking
        # and never without it - the column names the scheme that produced the stored score, so
        # leaving it behind would make the row lie about itself.
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[signal_table.c.trading_strategy, signal_table.c.symbol, signal_table.c.signal_date],
            set_={
                "ranking_strategy": stmt.excluded.ranking_strategy,
                "ranking": stmt.excluded.ranking,
                "signal_close": stmt.excluded.signal_close,
                # The incoming payload is authoritative for every key EXCEPT next_open, which is
                # carried over when the incoming run lacks it. A narrower --end-date makes the signal
                # the last loaded bar again, so _parameters omits next_open -- and a plain assignment
                # would then DELETE one an earlier, wider run had backfilled, the exact inverse of why
                # this is DO UPDATE rather than DO NOTHING.
                # Deliberately narrower than a blanket `existing || incoming`: that would also preserve
                # every indicator the current run stopped reporting, so a retired key could never be
                # cleared, and an empty payload would leave a whole stale object beside a freshly
                # overwritten ranking. jsonb_strip_nulls drops the next_open key when neither side has
                # one, keeping "absent, never null" true.
                "parameters": func.jsonb_strip_nulls(
                    stmt.excluded.parameters.op("||")(
                        func.jsonb_build_object(
                            "next_open",
                            func.coalesce(stmt.excluded.parameters["next_open"], signal_table.c.parameters["next_open"]),
                        )
                    )
                ),
            },
        )
        with self._engine.begin() as conn:
            conn.execute(on_conflict_stmt)
        # len(values), not RETURNING: DO UPDATE writes every row, so the count is the input length.
        # lightyear.py needs RETURNING because DO NOTHING makes the input length meaningless and
        # psycopg reports rowcount as -1.
        logger.debug("Upserted %d signals for trading strategy %s", len(values), trading_strategy)
        return len(values)
