"""Portfolio replay shared by the ranking-lab study.

A candidate ranking is only interesting if it makes money after cash constrains which
signals actually get taken, so the lab confirms every ordering change with a portfolio
replay rather than stopping at trade-level cohorts.

The replay is deliberately the same one `scripts/qullamaggie-ranking-weights.py` performs:
next trading day's adjusted open, position sized at a fixed fraction of portfolio value,
same-day competitors funded best-scored first, skip when cash is short, fixed calendar-time
exit, still-open positions marked to market at period end. That script keeps its own private
copy of this code — it is a frozen record generator whose committed output must not move, so
it is deliberately left alone rather than repointed here.

Two properties matter for the lab and are easy to lose:

- **Funding priority is the score.** `run_sim` sorts each day's competitors by `score_key`
  descending, so a re-ordering shows up even when the two schemes keep the same signals.
- **`taken` is an outcome, not a control.** Cash runs out on different days under different
  orderings, so two arms given identical candidate counts still execute different numbers of
  trades. Never read `taken` as evidence a comparison was unmatched.
"""

from datetime import date, timedelta

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_daily_sortino

_EPOCH = date(1970, 1, 1)

INIT_EQUITY = 30_000.0
POS_FRACTION = 0.04
HOLD_CAL = 366


class Market:
    """Per-symbol adjusted-close arrays, sorted by date, for the portfolio replay.

    The trading calendar is not held here — `run_sim` takes it as a parameter, so the
    sub-period tables replay the same prices over a shorter calendar without copying.
    """

    def __init__(self, bars: pl.DataFrame) -> None:
        """Index `bars` by symbol into date/close arrays.

        Args:
            bars: Frame with symbol, date and adj_close columns
        """
        self.dates: dict[str, np.ndarray] = {}
        self.closes: dict[str, np.ndarray] = {}
        for (sym,), grp in bars.group_by(["symbol"], maintain_order=False):
            g = grp.sort("date")
            self.dates[str(sym)] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
            self.closes[str(sym)] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    def price_on(self, symbol: str, dint: int) -> float:
        """Last adjusted close at or before `dint`.

        Raises rather than returning a sentinel: every caller is pricing a position the
        replay itself opened from this symbol's own bars, so an absent price means the
        market and the signals were built from different frames. Valuing that position at
        zero — or dropping it without crediting cash — would show up only as an unexplained
        step down in the equity curve.

        Args:
            symbol: Ticker to price
            dint: Date as days since the epoch
        """
        d = self.dates.get(symbol)
        idx = int(np.searchsorted(d, dint, side="right")) - 1 if d is not None else -1
        if idx < 0:
            raise ValueError(f"No bar for {symbol} at or before {_EPOCH + timedelta(days=dint)}")
        return float(self.closes[symbol][idx])


def run_sim(
    market: Market,
    calendar: list[date],
    signals: list[dict],
    score_key: str,
    *,
    init_equity: float = INIT_EQUITY,
    pos_fraction: float = POS_FRACTION,
    hold_cal: int = HOLD_CAL,
    max_new_per_month: int | None = None,
) -> dict:
    """Replay the portfolio over `signals`, funding same-day competitors best-scored first.

    Args:
        market: Per-symbol price arrays
        calendar: Ascending trading days the replay visits
        signals: Signal rows carrying entry_dint, entry_px and the score column
        score_key: Name of the score column deciding funding priority
        init_equity: Starting cash
        pos_fraction: Fraction of marked-to-market portfolio value per position
        hold_cal: Calendar days a position is held before it is closed
        max_new_per_month: Cap on positions opened per calendar month, or None for no cap.
            The cap is causal — within a month signals are taken as they arrive, best-scored
            first on any given day, until it is hit. Selecting "the best N of the month" would
            need to see the month in advance.

    Returns:
        dict with cagr (percent), max_dd (percent), sortino, taken and entries (the date each
        funded position was opened, for measuring how concentrated the entry vintages are).

    Raises:
        ValueError: When `calendar` holds fewer than two days. A caller slicing a sub-period the
            cached data barely covers would otherwise get a numpy reduction error — or, for a
            single day, a ZeroDivisionError — several frames deeper.
    """
    if len(calendar) < 2:
        raise ValueError(
            f"run_sim needs at least two trading days to measure a return, got {len(calendar)}; "
            "a one-day calendar divides by a zero-day span"
        )

    by_day: dict[int, list[dict]] = {}
    for s in signals:
        by_day.setdefault(s["entry_dint"], []).append(s)

    cash = init_equity
    positions: list[dict] = []
    equity: list[float] = []
    entries: list[date] = []
    month: tuple[int, int] | None = None
    opened_this_month = 0

    for day in calendar:
        dint = (day - _EPOCH).days
        if (day.year, day.month) != month:
            month, opened_this_month = (day.year, day.month), 0
        still_open = []
        for p in positions:
            if dint >= p["exit_int"]:
                cash += p["shares"] * market.price_on(p["symbol"], dint)
                continue
            still_open.append(p)
        positions = still_open

        mtm = cash + sum(p["shares"] * market.price_on(p["symbol"], dint) for p in positions)
        for s in sorted(by_day.get(dint, []), key=lambda r: r[score_key], reverse=True):
            if max_new_per_month is not None and opened_this_month >= max_new_per_month:
                break
            target = pos_fraction * mtm
            if cash + 1e-9 < target:
                continue
            cash -= target
            positions.append({"symbol": s["symbol"], "shares": target / s["entry_px"], "exit_int": dint + hold_cal})
            entries.append(day)
            opened_this_month += 1

        equity.append(cash + sum(p["shares"] * market.price_on(p["symbol"], dint) for p in positions))

    eq = np.array(equity)
    daily_ret = eq[1:] / eq[:-1] - 1.0
    max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
    n_days = (calendar[-1] - calendar[0]).days
    cagr = float((eq[-1] / eq[0]) ** (365.0 / n_days) - 1.0)
    return {
        "cagr": cagr * 100,
        "max_dd": max_dd * 100,
        "sortino": compute_daily_sortino(daily_ret),
        "taken": len(entries),
        "entries": entries,
    }


def top_k(signals: list[dict], score_key: str, n_keep: int, rng: np.random.Generator) -> list[dict]:
    """Top `n_keep` signals by score, with ties broken at random rather than by date.

    Coarse score tables leave hundreds of signals sharing one value, and cutting the top-K
    inside a tie group by date silently selects the earliest signals in every group — an
    ordering effect that looks like skill. Redraw across several calls to average it out.

    Args:
        signals: Signal rows to rank
        score_key: Name of the score column
        n_keep: How many signals to keep
        rng: Source of the tie-break jitter
    """
    jitter = rng.random(len(signals))
    order = sorted(range(len(signals)), key=lambda i: (-signals[i][score_key], jitter[i]))
    return [signals[i] for i in order[:n_keep]]
