"""Return/risk metrics shared by the backtest, portfolio and research paths.

Two sampling regimes live here, and they must not be mixed:

- `compute_trade_metrics` takes round-trip trades — irregularly spaced, annualized by the
  mean holding period.
- `compute_daily_sortino` and `compute_daily_metrics` take a daily equity-curve return
  series — regularly sampled, annualized by 252 periods a year.

The daily half follows quantstats' conventions (risk-free rate 0, 252 periods a year, sample
standard deviation, years = number of returns / 252), so its figures read like a quantstats
tearsheet; `tests/backtest/test_metrics.py` holds them to quantstats' own numbers on a fixed
series (`quantstats_oracle.json`) without quantstats being installed. The same functions live in
turtle-web's `api/turtleweb/analytics.py`, checked against the same oracle.

Per-trade returns must never go through the daily functions: they assume a regularly sampled
series, so on a trade series the calendar-aware metrics (Sharpe, Sortino, CAGR, Calmar) come
back silently wrong by orders of magnitude. That is why the trade-level half exists.

Canonical conventions for the whole repo, resolving the variants that grew across
`turtlex/service/backtest_service.py` and the `scripts/` studies:

- Sortino's downside deviation is the RMS of `min(return, 0)` over **all N** trades, not over
  the losers only. The negatives-only variant measures loss severity *conditional on losing*,
  so it ranks a cohort with few large losses above one with many small ones — an inversion of
  what the cohort tables compare.
- The Sortino *ratio* is annualized (`* sqrt(365 / mean_holding_days)`), not its inputs.
- `ann_mean_pct` compounds the mean return over the mean holding period, so short trades
  cannot dominate the average the way per-trade annualization does.

Trade returns are in percent (e.g. 12.5 for +12.5%), matching `FutureTrade.realized_pct` and
every table this repo prints; daily returns are fractions (0.01 for +1%).
"""

import math
import operator
import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from itertools import accumulate, groupby

import numpy as np
import numpy.typing as npt

from turtlex.model import FutureTrade

FloatSeq = Sequence[float] | npt.NDArray[np.floating]

PERIODS_PER_YEAR = 252
# A drawdown shallower than this is float noise: a recovery to the exact old peak can compute as
# peak * (1 - 2e-16), which would otherwise keep the drawdown open. quantstats compares with 0.
_DD_NOISE = 1e-12


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


def compute_daily_sortino(daily_returns: FloatSeq, *, periods_per_year: int = PERIODS_PER_YEAR) -> float:
    """
    Compute the annualized Sortino ratio of a daily equity-curve return series.

    Downside deviation is the RMS of `min(return, 0)` over **all N** days, not over the down
    days only — the same convention `compute_trade_metrics` applies to trades, and the same
    one `quantstats.stats.sortino` applies to a daily series. The negatives-only variant
    measures loss severity conditional on losing, which is not comparable between series with
    different down-day frequencies.

    Args:
        daily_returns: Daily simple returns as fractions (0.01 for +1%). Scale is irrelevant —
            the ratio is scale-invariant — but mixing percent and fractional inputs across
            callers makes the intermediate downside deviation incomparable, so keep to
            fractions here and percent in `compute_trade_metrics`.
        periods_per_year: Trading periods per year used to annualize; 252 for daily bars

    Returns:
        The annualized ratio, or `nan` when the series is empty or has no down day
    """
    arr = np.asarray(daily_returns, dtype=float)
    if arr.size == 0:
        return float("nan")

    downside_dev = float(np.sqrt(np.mean(np.minimum(arr, 0.0) ** 2)))
    if downside_dev <= 0:
        return float("nan")
    return float(arr.mean() / downside_dev * math.sqrt(periods_per_year))


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


@dataclass(frozen=True)
class DailyReturns:
    """One simple return per trading day, as fractions (0.01 for +1%)."""

    dates: list[date]
    values: list[float]


@dataclass(frozen=True)
class DailyMetrics:
    """Equity-curve metrics of one daily return series, as quantstats computes them.

    Fractions throughout (0.05 for +5%). A ratio over a zero denominator is None.
    """

    cumulative_return: float
    cagr: float
    volatility: float | None  # None with fewer than 2 returns
    sharpe: float | None  # None with fewer than 2 returns, or none of them different
    sortino: float | None  # None without a down day
    calmar: float | None  # None without a drawdown
    max_drawdown: float  # <= 0
    longest_drawdown_days: int  # calendar days, as quantstats counts them; 0 without a drawdown
    best_day: float
    worst_day: float
    last_day: float  # the last trading day's return
    best_month: float
    worst_month: float
    win_rate_days: float | None  # of non-zero days; None when every day is 0
    win_rate_months: float | None
    beta: float | None  # vs the benchmark passed in; None without one
    correlation: float | None


@dataclass(frozen=True)
class PeriodReturn:
    """A calendar month's or year's compounded return."""

    year: int
    month: int | None  # None for a yearly return
    value: float
    partial: bool  # the series' first or last period, so it may not cover the whole of it


@dataclass(frozen=True)
class DrawdownPeriod:
    """One stretch under water, with quantstats' dates: end is the last day under water."""

    start: date
    valley: date
    end: date
    depth: float  # <= 0
    days: int  # calendar days from start to end, both included
    ongoing: bool  # still under water on the last day


def _compound(values: Sequence[float]) -> float:
    return math.prod(1.0 + v for v in values) - 1.0


def underwater(r: DailyReturns) -> list[float]:
    """
    Compute the drawdown from the running peak at the end of each day.

    The growth index starts at 1 before the first return, as quantstats' phantom baseline does,
    so a loss on day one is a drawdown. Drawdowns shallower than float noise are reported as 0.

    Args:
        r: Daily returns

    Returns:
        index / running peak - 1 per day, each <= 0
    """
    growth = list(accumulate((1.0 + v for v in r.values), operator.mul))
    peaks = accumulate(growth, max, initial=1.0)
    next(peaks)  # the phantom baseline itself
    return [dd if (dd := i / peak - 1.0) < -_DD_NOISE else 0.0 for i, peak in zip(growth, peaks, strict=True)]


def drawdown_periods(r: DailyReturns) -> list[DrawdownPeriod]:
    """
    List every stretch the series spends under water.

    Args:
        r: Daily returns

    Returns:
        The drawdown periods, deepest first
    """
    periods = []
    for under, group in groupby(zip(r.dates, underwater(r), strict=True), key=lambda d: d[1] < 0):
        if under:
            run = list(group)
            (start, _), (end, _) = run[0], run[-1]
            valley, depth = min(run, key=lambda d: d[1])
            periods.append(DrawdownPeriod(start, valley, end, depth, (end - start).days + 1, ongoing=end == r.dates[-1]))
    return sorted(periods, key=lambda p: p.depth)


def _period_returns(r: DailyReturns, key: Callable[[date], tuple[int, int | None]]) -> list[PeriodReturn]:
    groups = [
        (y, m, _compound([v for _, v in days])) for (y, m), days in groupby(zip(r.dates, r.values, strict=True), key=lambda d: key(d[0]))
    ]
    last = len(groups) - 1
    return [PeriodReturn(year, month, value, partial=i in (0, last)) for i, (year, month, value) in enumerate(groups)]


def monthly_returns(r: DailyReturns) -> list[PeriodReturn]:
    """
    Compound the daily returns into calendar months.

    Args:
        r: Daily returns, in date order

    Returns:
        One return per month; the first and the last month are flagged partial
    """
    return _period_returns(r, lambda d: (d.year, d.month))


def yearly_returns(r: DailyReturns) -> list[PeriodReturn]:
    """
    Compound the daily returns into calendar years.

    Args:
        r: Daily returns, in date order

    Returns:
        One return per year; the first and the last year are flagged partial
    """
    return _period_returns(r, lambda d: (d.year, None))


def _win_rate(values: Sequence[float]) -> float | None:
    non_zero = [v for v in values if v != 0]
    return sum(v > 0 for v in non_zero) / len(non_zero) if non_zero else None


def compute_daily_metrics(r: DailyReturns, benchmark: DailyReturns | None = None) -> DailyMetrics:
    """
    Compute every equity-curve metric of one daily return series, as quantstats does.

    Args:
        r: Daily returns, in date order; must not be empty
        benchmark: Optional benchmark returns on the same dates, for beta and correlation

    Returns:
        DailyMetrics for the series

    Raises:
        ValueError: If `r` is empty, or `benchmark` is on other dates
    """
    values = r.values
    if not values:
        raise ValueError("daily metrics need at least one return")
    if benchmark is not None and benchmark.dates != r.dates:
        raise ValueError("the benchmark's returns must be on the same dates as the series'")
    n = len(values)
    total = _compound(values)
    cagr = (1.0 + total) ** (PERIODS_PER_YEAR / n) - 1.0  # quantstats: years = number of returns / 252
    stdev = statistics.stdev(values) if n > 1 else None
    sortino = compute_daily_sortino(values)
    drawdowns = drawdown_periods(r)
    max_dd = min((p.depth for p in drawdowns), default=0.0)
    months = [m.value for m in monthly_returns(r)]
    beta = correlation = None
    if benchmark is not None and n > 1 and (var_b := statistics.variance(benchmark.values)) > 0:
        beta = statistics.covariance(values, benchmark.values) / var_b
        correlation = statistics.correlation(values, benchmark.values) if stdev else None
    return DailyMetrics(
        cumulative_return=total,
        cagr=cagr,
        volatility=stdev * math.sqrt(PERIODS_PER_YEAR) if stdev is not None else None,
        sharpe=statistics.fmean(values) / stdev * math.sqrt(PERIODS_PER_YEAR) if stdev else None,
        sortino=None if math.isnan(sortino) else sortino,
        calmar=cagr / abs(max_dd) if max_dd < 0 else None,
        max_drawdown=max_dd,
        longest_drawdown_days=max((p.days for p in drawdowns), default=0),
        best_day=max(values),
        worst_day=min(values),
        last_day=values[-1],
        best_month=max(months),
        worst_month=min(months),
        win_rate_days=_win_rate(values),
        win_rate_months=_win_rate(months),
        beta=beta,
        correlation=correlation,
    )
