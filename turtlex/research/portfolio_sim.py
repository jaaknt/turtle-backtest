"""The fixed-hold portfolio simulator behind `scripts/qullamaggie-portfolio-sim.py`.

Signals are bought at the next trading day's split/dividend-adjusted open (matching
`SignalProcessor.calculate_entry_data`), each sized as a fraction of the portfolio's value
marked to market, and closed at the first close on or after entry + `hold_cal` calendar days.
A signal that cannot be funded in full is skipped. Positions still open on the last day are
marked to market, not force-closed. Fractional shares, no commission or slippage.

The calendar is SPY's trading days (`qm.load_trading_days`), and every equity-curve metric
comes from `turtlex.backtest.metrics`.

Exit rules other than the time cap are measured by `scripts/qullamaggie-exit-sweep.py`, which
reconciles its baseline with this simulator to the dollar.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_daily_cagr, compute_daily_sortino
from turtlex.research import qullamaggie as qm

_EPOCH = date(1970, 1, 1)


def to_dint(d: date) -> int:
    """Days since the epoch: the integer date every array here is keyed on.

    Args:
        d: A date

    Returns:
        Its date-int.
    """
    return (d - _EPOCH).days


@dataclass(frozen=True)
class SimMarket:
    """Per-symbol adjusted prices and the trading calendar the simulation walks.

    Attributes:
        cal: Trading days of the evaluation window, ascending
        cal_int: `cal` as date-ints
        cal_set: `cal_int` as a set, for membership tests
        sym_dates: Each symbol's bar dates as date-ints, ascending
        sym_closes: Each symbol's adjusted closes, aligned with `sym_dates`
        sym_opens: Each symbol's adjusted opens, aligned with `sym_dates`
    """

    cal: list[date]
    cal_int: list[int]
    cal_set: frozenset[int]
    sym_dates: dict[str, np.ndarray]
    sym_closes: dict[str, np.ndarray]
    sym_opens: dict[str, np.ndarray]

    @classmethod
    def from_bars(cls, bars: pl.DataFrame, cal: list[date]) -> SimMarket:
        """Unpack an adjusted bar frame into per-symbol arrays.

        Args:
            bars: Frame with symbol, date, adj_close and adj_open (from `qm.load_bars`)
            cal: Trading days of the evaluation window, from `qm.load_trading_days`

        Returns:
            The market for one evaluation window.
        """
        sym_dates: dict[str, np.ndarray] = {}
        sym_closes: dict[str, np.ndarray] = {}
        sym_opens: dict[str, np.ndarray] = {}
        for (sym,), grp in bars.select("symbol", "date", "adj_close", "adj_open").group_by(["symbol"], maintain_order=False):
            g = grp.sort("date")
            name = str(sym)
            sym_dates[name] = g["date"].cast(pl.Int32).to_numpy().astype(np.int64)  # a Date is stored as days since the epoch
            sym_closes[name] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)
            sym_opens[name] = g["adj_open"].cast(pl.Float64).to_numpy(allow_copy=True)
        cal_int = [to_dint(d) for d in cal]
        return cls(cal, cal_int, frozenset(cal_int), sym_dates, sym_closes, sym_opens)

    def price_on(self, sym: str, dint: int) -> float | None:
        """The symbol's adjusted close on or before `dint`, or None if it has no bar yet.

        Args:
            sym: Symbol
            dint: Date-int

        Returns:
            The close, or None.
        """
        dates = self.sym_dates.get(sym)
        if dates is None:
            return None
        idx = int(np.searchsorted(dates, dint, side="right")) - 1
        return float(self.sym_closes[sym][idx]) if idx >= 0 else None

    def next_open(self, sym: str, dint: int) -> tuple[int, float] | None:
        """First tradeable bar strictly after `dint`, as (date-int, adjusted open).

        Mirrors SignalProcessor.calculate_entry_data: the search skips bars with a
        non-positive open and gives up after qm.ENTRY_SEARCH_DAYS calendar days, and the open
        is already scaled by that bar's own adjustment factor in qm.prepare_bars.

        Args:
            sym: Symbol
            dint: Signal date-int

        Returns:
            (entry date-int, adjusted open), or None if no bar in the search window qualifies.
        """
        dates = self.sym_dates.get(sym)
        if dates is None:
            return None
        idx = int(np.searchsorted(dates, dint, side="right"))
        opens = self.sym_opens[sym]
        while idx < len(dates) and dates[idx] <= dint + qm.ENTRY_SEARCH_DAYS:
            if opens[idx] > 0 and not np.isnan(opens[idx]):
                return int(dates[idx]), float(opens[idx])
            idx += 1
        return None


def resolve_signals(market: SimMarket, sig: pl.DataFrame) -> list[dict]:
    """Score every signal once and attach its fill: the next trading day's adjusted open.

    Done once per config, not per gate or inside run_sim: the gates, the size sweep and the
    decile re-simulations all replay the same signals, and run_sim never mutates them, so
    every gated view can share these dicts.

    Args:
        market: The window's prices and calendar
        sig: Signal frame for one config, from `qm.get_signals`

    Returns:
        One dict per signal carrying `ranking`, plus `entry_dint`/`entry_px` — both None when
        no fillable next-day open falls inside the evaluation calendar.
    """
    resolved: list[dict] = []
    for r in qm.add_ranking(sig).iter_rows(named=True):
        fill = market.next_open(r["symbol"], to_dint(r["date"]))
        r["entry_dint"], r["entry_px"] = fill if fill is not None and fill[0] in market.cal_set else (None, None)
        resolved.append(r)
    return resolved


def gate_signals(resolved: list[dict], min_ranking: int) -> tuple[dict[int, list[dict]], int, int]:
    """Apply one ranking floor to resolved signals, keyed by the day each is funded.

    Signals are keyed by their *entry* day (the next trading day), so run_sim funds a
    position on the day it is actually filled.

    Args:
        resolved: Output of `resolve_signals` for one config
        min_ranking: QullamaggieRanking floor; 0 keeps every signal

    Returns:
        (signals keyed by entry date-int, dropped by the ranking gate, unfilled among the
        signals the gate kept).
    """
    by_day: dict[int, list[dict]] = {}
    n_rank = n_unfilled = 0
    for r in resolved:
        if r["ranking"] < min_ranking:
            n_rank += 1
        elif r["entry_dint"] is None:
            n_unfilled += 1
        else:
            by_day.setdefault(r["entry_dint"], []).append(r)
    return by_day, n_rank, n_unfilled


@dataclass(frozen=True)
class SimParams:
    """How a simulation sizes, funds and holds its positions.

    Attributes:
        pos_fraction: Fraction of the marked-to-market portfolio value per position
        init_equity: Starting cash
        hold_cal: Calendar days a position is held before it is closed
        rank_funding: Fund same-day signals best-ranked first (stable, so ties keep arrival
            order) rather than in arrival order. Entries arrive in bursts and cash runs out
            mid-burst, so this ordering decides which trades exist at all.
    """

    pos_fraction: float
    init_equity: float
    hold_cal: int = qm.HOLD_CAL
    rank_funding: bool = True


@dataclass
class _Position:
    sym: str
    shares: float
    entry_px: float
    entry_date: date
    sig_date: date
    exit_int: int
    ranking: int


def _trade(p: _Position, px: float) -> dict:
    """The trade-log record of `p` closed (or marked) at `px`."""
    return {"entry_date": p.entry_date, "sig_date": p.sig_date, "symbol": p.sym, "ret": px / p.entry_px - 1.0, "ranking": p.ranking}


@dataclass
class _Book:
    """A simulation's running state and everything it records day by day."""

    market: SimMarket
    params: SimParams
    cash: float
    positions: list[_Position] = field(default_factory=list)
    equity: list[float] = field(default_factory=list)
    cash_curve: list[float] = field(default_factory=list)
    entries: list[date] = field(default_factory=list)
    skips: list[date] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)

    def marked_positions(self, dint: int) -> float:
        """Value of the open positions at today's close; a symbol with no bar yet counts as 0."""
        return sum(p.shares * (self.market.price_on(p.sym, dint) or 0.0) for p in self.positions)

    def close_due(self, dint: int) -> None:
        """Close every position whose time cap has come, at today's close.

        Proceeds are added to cash one position at a time, in order, so the float sums do not
        depend on how many positions close together.

        Args:
            dint: Today's date-int
        """
        still_open: list[_Position] = []
        for p in self.positions:
            if dint < p.exit_int:
                still_open.append(p)
                continue
            px = self.market.price_on(p.sym, dint)
            if px is None:  # a position is only ever opened on one of its symbol's bars
                raise ValueError(f"{p.sym} has no bar on or before its exit day {dint}; its proceeds would be lost")
            self.cash += p.shares * px
            self.trades.append(_trade(p, px))
        self.positions = still_open

    def fund_day(self, day: date, dint: int, sigs: list[dict]) -> None:
        """Fund one day's signals, each at `pos_fraction` of the marked value, while the cash lasts.

        Args:
            day: Today
            dint: Today's date-int
            sigs: Today's signals, in arrival order
        """
        if not sigs:
            return
        if self.params.rank_funding:
            sigs = sorted(sigs, key=lambda s: s["ranking"], reverse=True)
        target = self.params.pos_fraction * (self.cash + self.marked_positions(dint))
        for s in sigs:
            if self.cash + 1e-9 < target:
                self.skips.append(day)
                continue
            self.cash -= target
            entry_px = s["entry_px"]  # next trading day's adjusted open, resolved once in resolve_signals
            self.positions.append(
                _Position(s["symbol"], target / entry_px, entry_px, day, s["date"], dint + self.params.hold_cal, s["ranking"])
            )
            self.entries.append(day)

    def close_day(self, dint: int) -> None:
        """Record today's closing equity and cash."""
        self.equity.append(self.cash + self.marked_positions(dint))
        self.cash_curve.append(self.cash)

    def mark_open_trades(self) -> None:
        """Log the positions still open at period end, marked to market, not force-closed."""
        last = self.market.cal_int[-1]
        marks = ((p, self.market.price_on(p.sym, last)) for p in self.positions)
        self.trades.extend(_trade(p, px) for p, px in marks if px is not None)


def month_end_returns(dates: list[date], eq: np.ndarray, init_equity: float) -> pl.DataFrame:
    """Each calendar month's return, from month-end equity.

    Args:
        dates: The equity curve's dates
        eq: Daily equity, aligned with `dates`
        init_equity: Starting equity, the base of the first month's return

    Returns:
        Frame with year, month, eom (month-end equity) and ret, in date order.
    """
    eq_df = pl.DataFrame({"date": pl.Series(dates, dtype=pl.Date), "eq": eq}).with_columns(
        [
            pl.col("date").dt.year().alias("year"),
            pl.col("date").dt.month().alias("month"),
        ]
    )
    eom = eq_df.group_by(["year", "month"]).agg(pl.col("eq").last().alias("eom")).sort(["year", "month"])
    eom = eom.with_columns((pl.col("eom") / pl.col("eom").shift(1) - 1.0).alias("ret"))
    return eom.with_columns(pl.when(pl.col("ret").is_null()).then(pl.col("eom") / init_equity - 1.0).otherwise(pl.col("ret")).alias("ret"))


def _max_drawdown(eq: np.ndarray) -> float:
    """The deepest peak-to-trough fall of an equity curve, as a fraction (<= 0)."""
    return float((eq / np.maximum.accumulate(eq) - 1.0).min())


def equity_curve_metrics(eq: np.ndarray) -> dict:
    """Whole-period metrics of a daily equity curve.

    Args:
        eq: Daily equity, one value per trading day

    Returns:
        dict with final, cagr, max_dd and calmar (fractions) and sortino.
    """
    daily_ret = eq[1:] / eq[:-1] - 1.0
    max_dd = _max_drawdown(eq)
    cagr = compute_daily_cagr(daily_ret)
    return {
        "final": float(eq[-1]),
        "cagr": cagr,
        "max_dd": max_dd,
        "calmar": cagr / abs(max_dd) if max_dd < 0 else float("inf"),
        "sortino": compute_daily_sortino(daily_ret),
    }


def _summarize(book: _Book) -> dict:
    """Turn a finished simulation's book into its result dict."""
    eq = np.array(book.equity)
    cash_arr = np.array(book.cash_curve)
    return {
        **equity_curve_metrics(eq),
        "taken": len(book.entries),
        "skipped": len(book.skips),
        "avg_uninv_pct": float(np.mean(cash_arr / eq) * 100),
        "avg_uninv_usd": float(np.mean(cash_arr)),
        "eom": month_end_returns(book.market.cal, eq, book.params.init_equity),
        "entries": book.entries,
        "skips": book.skips,
        # Daily series kept so the per-year table can re-derive its metrics on a
        # calendar-year slice rather than approximating them from monthly aggregates.
        "dates": list(book.market.cal),
        "eq": eq,
        "cash": cash_arr,
        "trades": book.trades,
    }


def run_sim(market: SimMarket, signals_by_day: dict[int, list[dict]], params: SimParams) -> dict:
    """Simulate the portfolio over the market's calendar.

    Each day closes the positions whose time cap has come, then funds the day's signals against
    the portfolio's value marked after those exits, then records the closing equity.

    Args:
        market: The window's prices and calendar
        signals_by_day: Signals keyed by the date-int they are funded on (`gate_signals`)
        params: Sizing, starting equity, hold and funding order

    Returns:
        dict with final, cagr, max_dd, calmar, sortino (fractions, Sortino a ratio), taken,
        skipped, avg_uninv_pct, avg_uninv_usd, eom (`month_end_returns`), entries and skips
        (one date per funded / skipped signal), the daily dates/eq/cash series and the trade
        log (entry_date, sig_date, symbol, ret, ranking per trade, open positions included).
    """
    book = _Book(market, params, cash=params.init_equity)
    for d, dint in zip(market.cal, market.cal_int, strict=True):
        book.close_due(dint)
        book.fund_day(d, dint, signals_by_day.get(dint, []))
        book.close_day(dint)
    book.mark_open_trades()
    return _summarize(book)


def year_metrics(r: dict) -> list[dict]:
    """Re-derive the sweep metrics on each complete calendar year of one simulation.

    Every figure is computed from that year's own daily slice rather than sliced out of the
    whole-period result: the year's return is its closing equity over the previous year's close
    (the opening equity for the first year), MaxDD is the deepest peak-to-trough *within* the
    year, and Sortino runs on the year's daily returns only. Calmar therefore pairs a one-year
    return with a one-year drawdown, which is not the whole-period Calmar restricted to a year.

    Trades are attributed to the year they were entered, so `taken` and `skip` sum across years
    to the whole-period counts.

    Args:
        r: a `run_sim` result carrying the `dates`/`eq`/`cash` daily series

    Returns:
        One dict per year with year, final, ret, max_dd, calmar, sortino, taken, skipped, uninv.
    """
    dates, eq, cash = r["dates"], r["eq"], r["cash"]
    taken_by_year = Counter(d.year for d in r["entries"])
    skips_by_year = Counter(d.year for d in r["skips"])
    out_rows: list[dict] = []
    prev_close = float(eq[0])
    for year in sorted({d.year for d in dates}):
        idx = [i for i, d in enumerate(dates) if d.year == year]
        year_eq = eq[idx]
        ret = float(year_eq[-1]) / prev_close - 1.0
        max_dd = _max_drawdown(year_eq)
        daily = year_eq[1:] / year_eq[:-1] - 1.0
        out_rows.append(
            {
                "year": year,
                "final": float(year_eq[-1]),
                "ret": ret,
                "max_dd": max_dd,
                "calmar": ret / abs(max_dd) if max_dd < 0 else float("inf"),
                "sortino": compute_daily_sortino(daily) if daily.size else float("nan"),
                "taken": taken_by_year.get(year, 0),
                "skipped": skips_by_year.get(year, 0),
                "uninv": float(np.mean(cash[idx] / year_eq) * 100),
            }
        )
        prev_close = float(year_eq[-1])
    return out_rows
