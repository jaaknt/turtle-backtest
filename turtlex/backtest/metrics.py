"""Trade-level (round-trip) metrics shared by the backtest, portfolio and research paths.

Equity-curve metrics are a different problem: they live in `turtlex/portfolio/analytics.py`,
which renders them with quantstats. Per-trade returns must never be fed to quantstats — it
assumes a regularly sampled series at `periods_per_year=252`, so on a trade series its
calendar-aware metrics (Sharpe, Sortino, CAGR, Calmar) come back silently wrong by orders of
magnitude. That is why this module exists instead of a library call.

Canonical conventions for the whole repo, resolving the variants that grew across
`turtlex/service/backtest_service.py` and the `scripts/` studies:

- Sortino's downside deviation is the RMS of `min(return, 0)` over **all N** trades, not over
  the losers only. The negatives-only variant measures loss severity *conditional on losing*,
  so it ranks a cohort with few large losses above one with many small ones — an inversion of
  what the cohort tables compare.
- The Sortino *ratio* is annualized (`* sqrt(365 / mean_holding_days)`), not its inputs.
- `ann_mean_pct` compounds the mean return over the mean holding period, so short trades
  cannot dominate the average the way per-trade annualization does.

All returns are in percent (e.g. 12.5 for +12.5%), matching `FutureTrade.realized_pct` and
every table this repo prints.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from turtlex.model import FutureTrade

FloatSeq = Sequence[float] | npt.NDArray[np.floating]


@dataclass(frozen=True)
class TradeMetrics:
    """Aggregate return/risk metrics for a group of round-trip trades."""

    n: int
    win_pct: float
    mean_pct: float
    median_pct: float
    ann_mean_pct: float
    profit_factor: float
    sortino: float
    cvar95_pct: float
    mean_trade_mdd_pct: float | None


def compute_trade_metrics(
    returns_pct: FloatSeq,
    holding_days: FloatSeq | float,
    *,
    trade_drawdowns_pct: FloatSeq | None = None,
    min_losers: int = 0,
) -> TradeMetrics | None:
    """
    Compute aggregate metrics for a group of trades from their returns and holding periods.

    Args:
        returns_pct: Realized return of each trade, in percent
        holding_days: Holding period of each trade in calendar days, or a single value when
            every trade shares one (the fixed-hold research studies). Pass 0 to skip
            annualization entirely, for open positions marked to the latest price.
        trade_drawdowns_pct: Optional per-trade intra-hold drawdown, in percent, averaged into
            `mean_trade_mdd_pct`. Callers that no longer hold the price path omit it.
        min_losers: Minimum number of losing trades required before Sortino is reported;
            below it the ratio is `nan` but every other metric is still returned.

    Returns:
        TradeMetrics, or None if `returns_pct` is empty
    """
    arr = np.asarray(returns_pct, dtype=float)
    n = int(arr.size)
    if n == 0:
        return None

    hold_arr = np.asarray(holding_days, dtype=float)
    mean_hold = float(hold_arr.mean()) if hold_arr.size else 0.0

    mean_pct = float(arr.mean())
    gross_win = float(arr[arr > 0].sum())
    gross_loss = -float(arr[arr < 0].sum())

    downside_dev = float(np.sqrt(np.mean(np.minimum(arr, 0.0) ** 2)))
    n_losers = int((arr < 0).sum())
    ann_factor = math.sqrt(365.0 / mean_hold) if mean_hold > 0 else 1.0
    sortino = mean_pct / downside_dev * ann_factor if downside_dev > 0 and n_losers >= min_losers else float("nan")

    k = max(1, math.floor(0.05 * n))

    dd_mean: float | None = None
    if trade_drawdowns_pct is not None:
        dd_arr = np.asarray(trade_drawdowns_pct, dtype=float)
        dd_mean = float(dd_arr.mean()) if dd_arr.size else None

    return TradeMetrics(
        n=n,
        win_pct=float((arr > 0).sum()) / n * 100.0,
        mean_pct=mean_pct,
        median_pct=float(np.median(arr)),
        ann_mean_pct=_annualize(mean_pct, mean_hold),
        profit_factor=gross_win / gross_loss if gross_loss > 0 else float("inf"),
        sortino=sortino,
        cvar95_pct=float(np.sort(arr)[:k].mean()),
        mean_trade_mdd_pct=dd_mean,
    )


def metrics_from_future_trades(trades: Sequence[FutureTrade], *, min_losers: int = 0) -> TradeMetrics | None:
    """
    Compute aggregate metrics for a group of FutureTrade objects.

    Args:
        trades: Round-trip trades to aggregate
        min_losers: Minimum number of losing trades required before Sortino is reported

    Returns:
        TradeMetrics, or None if `trades` is empty
    """
    if not trades:
        return None
    return compute_trade_metrics(
        [t.realized_pct for t in trades],
        [float(t.holding_days) for t in trades],
        min_losers=min_losers,
    )


def _annualize(mean_pct: float, mean_hold: float) -> float:
    """Compound `mean_pct` over `mean_hold` calendar days out to a full year."""
    growth = 1.0 + mean_pct / 100.0
    if mean_hold <= 0:
        return mean_pct
    if growth <= 0:  # a mean loss of 100% or worse never recovers, whatever the horizon
        return -100.0
    try:
        return (math.pow(growth, 365.0 / mean_hold) - 1.0) * 100.0
    except OverflowError:  # a large mean return over a very short mean hold
        return float("inf")
