#!/usr/bin/env python3
"""
Exit-strategy sweep for bk50d_s12_v2.0 at 3% position sizing.

scripts/qullamaggie-portfolio-sim.py has exactly one exit: a 366-calendar-day time cap. This
study asks whether a smarter exit raises portfolio CAGR% and Sortino on that one configuration,
holding entries, sizing and universe fixed.

Two observations from docs/research/result-qullamaggie-portfolio-v4.md motivated the ideas (figures
from the July 2026 run the study was designed on):

  - The worst months contain zero entries. Entries are gated on SPY > 200d SMA, so through
    Apr-Dec 2022 and Jun-Dec 2023 the strategy refused to open the exposure it was still
    holding. The drawdown comes from legacy positions carried through a tape the entry logic
    had already disqualified.
  - Entries arrive in bursts right after the regime flips back on (33 in Jan 2021, 23 in
    Mar 2022, 19 in May 2025), and 714 signals were skipped for lack of cash against 194
    taken. Capital available *at the burst* is what caps trade count.

Five ideas are swept, each with the 366d time cap still active underneath as a backstop:

  1. regime  — exit when SPY has closed below its 200d SMA for N consecutive days
  2. trail   — trail T% below the running peak close, armed only once the trade is up A%
  3. dead    — exit if the trade is not up at least R% after N trading bars
  4. trend   — exit after N consecutive closes below the position's own EMA20/SMA50/SMA200
  5. atr     — fixed stop at entry - k x ATR(14) measured at entry

Signal generation is imported from turtlex.research.qullamaggie, which is parity-tested against
QullamaggieStrategy, so entries here match the production runner. Exits fill at the day's
adjusted close, matching the baseline's convention: this measures rule *timing*, not fill
quality, and every variant shares the convention so the ranking stays fair.

Outputs: full metric surface per idea (not just the winning cell), finalist trade metrics and
exit attribution, per-year decomposition, a block-bootstrap win rate against the baseline, and
a robustness matrix re-running the sweep's winner across s20/s16/s12 and three disjoint periods.

That last section is the one that matters most. In the July 2026 run, `<+5% after 90 bars` cleared
every single-window guard and still failed 7 of the 9 matrix cells; on the 2026-11-15 data no
variant clears the single-window bar at all, and the same rule passes 1 of 9. Read the matrix
before acting on the sweep.
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_daily_cagr, compute_daily_sortino, compute_trade_metrics
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.research.portfolio_sim import equity_curve_metrics

_EPOCH = date(1970, 1, 1)

EVAL_START = date(2021, 1, 1)
EVAL_END = date(2026, 6, 26)
INIT_EQUITY = 30_000.0
POS_FRACTION = 0.03
SMA_THRESH = 0.12  # s12

# Baseline from qullamaggie-portfolio-sim.py, s12 / R>=44 / 3% / 366d over this study's window
# (2021-01-01 – 2026-06-26) — the `3%  R>=44` row of the s12 section in
# docs/research/result-qullamaggie-portfolio-v4.md (REF_RUN_DATE run). Reproduced by this harness as
# a validity check before any sweep is believed. Refresh all four together — a partial update
# makes the reconciliation table lie.
#
# The two simulators agree to the dollar on the same day's data, but hetzner's data does not hold
# still: on 2026-11-15 the same portfolio-sim code moved this row from +51.52% to +52.98% CAGR
# within hours (both figures on the old 365-calendar-day CAGR base; the same 307,819 row reads
# +53.22% on the 252-trading-day base every equity curve has used since). So a miss here is read
# as drift first: re-run portfolio-sim on the same data
# (`--output` to a scratch file, so the committed docs are untouched) and compare with that.
# Until 2026-11-15 this harness funded same-day signals in arrival order rather than best-ranked
# first, which alone put it ~1.5pp off portfolio-sim.
#
# These are gate-dependent, so qm.MIN_RANKING and this block move together. When the gate went
# 40 -> 44 on 2026-08-07 these four were left on the R>=40 row for one commit, and the 2026-08-09
# sweep reconciled 2.80pp out. Note what that does and does not break: the per-variant pass/fail
# column is scored against *this harness's own* baseline, so those verdicts stayed correct — what
# a blown reconciliation invalidates is the claim that the harness reproduces portfolio-sim at
# all. If it reappears, check this block against portfolio-v4.md before rereading the sweep.
REF_MIN_RANKING = 44  # the gate the four numbers below were run at
REF_RUN_DATE = date(2026, 11, 15)  # the day portfolio-sim produced them; the data they reflect
REF_CAGR_PCT = 53.22  # compute_daily_cagr: years = trading-day returns / 252
REF_SORTINO = 2.210
REF_MAXDD_PCT = -31.15
REF_FINAL = 307_819.0
RECONCILE_TOL_PP = 1.0  # max acceptable CAGR divergence, in percentage points

MAXDD_GUARD_PP = 5.0  # a variant may not worsen baseline MaxDD by more than this

BOOT_RESAMPLES = 1_000
BOOT_BLOCK = 21  # trading days per block, ~one month
BOOT_SEED = 20260729

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-exit-sweep.md"


@dataclass(frozen=True)
class ExitRule:
    """One composable exit configuration. Unset fields mean that rule is inactive."""

    name: str
    hold_cal: int = qm.HOLD_CAL  # time-cap backstop, always active
    regime_days: int | None = None  # SPY below its 200d SMA for this many consecutive days
    regime_losers_only: bool = False  # only close positions currently under water
    trail_pct: float | None = None  # trail this far below the running peak close
    trail_arm_pct: float | None = None  # ... but only once the trade is up this much
    dead_days: int | None = None  # exit if return < dead_min_ret after this many bars
    dead_cal_days: int | None = None  # ... the same test on calendar days, as the dead120 control measures it
    dead_min_ret: float = 0.0
    trend_ma: str | None = None  # "ema20" | "sma50" | "sma200"
    trend_days: int = 1  # consecutive closes below trend_ma
    stop_atr: float | None = None  # fixed stop at entry - k x ATR(14) at entry
    stop_pct: float | None = None  # fixed stop at entry x (1 - pct)


@dataclass(frozen=True)
class Signal:
    """A ranked, entry-resolved breakout signal ready to be funded."""

    symbol: str
    entry_dint: int
    entry_price: float
    ranking: int


@dataclass
class Position:
    """An open position and the per-position state the exit rules need."""

    symbol: str
    shares: float
    entry_px: float
    entry_dint: int
    entry_idx: int
    exit_int: int
    entry_atr: float
    peak: float
    trend_cnt: int = 0


@dataclass(frozen=True)
class ClosedTrade:
    """A round trip, tagged with the rule that closed it."""

    symbol: str
    entry_date: date
    exit_date: date
    entry_px: float
    exit_px: float
    ret_pct: float
    hold_days: float
    reason: str


@dataclass
class SimResult:
    """Portfolio outcome of one exit rule over the evaluation window."""

    rule: ExitRule
    final: float
    cagr: float
    max_dd: float
    calmar: float
    sortino: float
    avg_uninv_pct: float
    taken: int
    skipped: int
    eq: np.ndarray
    daily_ret: np.ndarray
    trades: list[ClosedTrade] = field(default_factory=list)
    exit_counts: dict[str, int] = field(default_factory=dict)


BASELINE = ExitRule(name="366d time cap only")

IDEAS: dict[str, list[ExitRule]] = {
    "1. regime — SPY below its 200d SMA": [
        ExitRule(
            name=f"regime {d}d{' (losers only)' if losers else ''}",
            regime_days=d,
            regime_losers_only=losers,
        )
        for d in (1, 3, 5, 10)
        for losers in (False, True)
    ],
    "2. trail — profit-armed trailing stop": [
        ExitRule(name=f"arm +{arm}% / trail {t}%", trail_pct=t / 100, trail_arm_pct=arm / 100)
        for arm in (15, 25, 40)
        for t in (15, 20, 25, 30)
    ],
    # dead_days runs well past the point where it stops helping: the first pass put the whole
    # passing region at 90d, the grid edge, and a boundary optimum is indistinguishable from an
    # artifact until you can see its far side.
    "3. dead — dead-money time stop": [
        ExitRule(name=f"<{ret:+d}% after {n} bars", dead_days=n, dead_min_ret=ret / 100)
        for n in (20, 40, 60, 90, 120, 150, 180, 240)
        for ret in (0, 5, 10)
    ],
    # sma200 is here because the identically-named control beat the baseline while every fast
    # MA collapsed — testing only fast MAs would have mis-scored the whole idea.
    "4. trend — closes below own MA": [
        ExitRule(name=f"{ma} x {n}d", trend_ma=ma, trend_days=n) for ma in ("ema20", "sma50", "sma200") for n in (1, 3, 5)
    ],
    "5. atr — volatility-normalised stop": [ExitRule(name=f"entry - {k}x ATR14", stop_atr=float(k)) for k in (3, 4, 5, 6, 8)],
}

# The four exit modes qullamaggie-portfolio-sim.py carried but never selected (its EXIT_MODES
# was ["time"]), at the constants it used for them. They were removed from it on 2026-11-15;
# this is the only place they are measured.
CONTROLS = [
    ExitRule(name="stop30 — fixed -30% stop", stop_pct=0.30),
    ExitRule(name="trail25 — 25% from day one", trail_pct=0.25),
    # Named exactly as idea 4 names the same cell, so the finalist dedup collapses the two.
    ExitRule(name="sma200 x 5d", trend_ma="sma200", trend_days=5),
    ExitRule(name="dead120 — <+5% after 120 cal days", dead_cal_days=120, dead_min_ret=0.05),
]

# Robustness matrix: the July 2026 sweep's winning rule re-run across every entry threshold and
# three disjoint periods. It is fixed rather than re-picked each run, so the matrix stays
# comparable across re-runs. Its parameters were chosen on s12 / 2021-2026, so the other eight
# cells are out-of-sample for them.
WINNER = ExitRule(name="<+5% after 90 bars", dead_days=90, dead_min_ret=0.05)
VALIDATION_CONFIGS = [("s20", 0.20), ("s16", 0.16), ("s12", 0.12)]
VALIDATION_PERIODS = [
    (date(2010, 1, 1), date(2015, 12, 31)),
    (date(2016, 1, 1), date(2020, 12, 31)),
    (date(2021, 1, 1), EVAL_END),
]


def mechanisms(rule: ExitRule) -> frozenset[str]:
    """Which exit mechanisms a rule has switched on, for checking two rules can be composed."""
    active: set[str] = set()
    if rule.regime_days is not None:
        active.add("regime")
    if rule.trail_pct is not None:
        active.add("trail")
    if rule.dead_days is not None or rule.dead_cal_days is not None:
        active.add("dead")
    if rule.trend_ma is not None:
        active.add("trend")
    if rule.stop_atr is not None or rule.stop_pct is not None:
        active.add("stop")
    return frozenset(active)


def compose(first: ExitRule, second: ExitRule) -> ExitRule:
    """Merge two rules, `first` winning any field both set. Intended for disjoint mechanisms.

    Args:
        first: Rule whose settings take precedence
        second: Rule contributing the mechanisms `first` leaves unset

    Returns:
        A rule with both mechanisms active and a combined name.
    """
    first_dead = "dead" in mechanisms(first)
    return ExitRule(
        name=f"{first.name} + {second.name}",
        hold_cal=first.hold_cal,
        regime_days=first.regime_days if first.regime_days is not None else second.regime_days,
        regime_losers_only=first.regime_losers_only if first.regime_days is not None else second.regime_losers_only,
        trail_pct=first.trail_pct if first.trail_pct is not None else second.trail_pct,
        trail_arm_pct=first.trail_arm_pct if first.trail_pct is not None else second.trail_arm_pct,
        dead_days=first.dead_days if first_dead else second.dead_days,
        dead_cal_days=first.dead_cal_days if first_dead else second.dead_cal_days,
        dead_min_ret=first.dead_min_ret if first_dead else second.dead_min_ret,
        trend_ma=first.trend_ma if first.trend_ma is not None else second.trend_ma,
        trend_days=first.trend_days if first.trend_ma is not None else second.trend_days,
        stop_atr=first.stop_atr if first.stop_atr is not None else second.stop_atr,
        stop_pct=first.stop_pct if first.stop_pct is not None else second.stop_pct,
    )


def add_exit_indicators(bars: pl.DataFrame) -> pl.DataFrame:
    """Add the moving averages and ATR the exit rules need, per symbol.

    Unlike the entry indicators in `turtlex.research.qullamaggie.add_indicators`, these are
    computed on the *current* close rather than shift-1. An entry filter must not see the bar
    it fires on; an exit rule acts on a close that has already printed, which is how
    `EMAExitStrategy` and `ATRExitStrategy` are written.

    Args:
        bars: Adjusted bar frame from `qullamaggie.load_bars`

    Returns:
        The frame with ema20, ma_sma50, ma_sma200 and atr14 added.
    """
    df = bars.sort(["symbol", "date"])
    prev_close = pl.col("adj_close").shift(1).over("symbol")
    true_range = pl.max_horizontal(
        pl.col("adj_high") - pl.col("adj_low"),
        (pl.col("adj_high") - prev_close).abs(),
        (pl.col("adj_low") - prev_close).abs(),
    )
    return df.with_columns(
        pl.col("adj_close").ewm_mean(span=20, adjust=False).over("symbol").alias("ema20"),
        pl.col("adj_close").rolling_mean(50, min_samples=50).over("symbol").alias("ma_sma50"),
        pl.col("adj_close").rolling_mean(200, min_samples=200).over("symbol").alias("ma_sma200"),
        # Wilder smoothing, matching ATRExitStrategy
        true_range.ewm_mean(alpha=1.0 / 14, adjust=False).over("symbol").alias("atr14"),
    )


def bootstrap_win_rate(base_ret: np.ndarray, var_ret: np.ndarray) -> tuple[float, float]:
    """Fraction of block-bootstrap resamples in which the variant beats the baseline.

    A stationary block bootstrap over the *paired* daily return series — both curves are
    resampled on the same day indices, so the comparison holds the market path fixed and only
    the sampling of it varies. Blocks preserve the short-horizon autocorrelation that makes a
    naive i.i.d. bootstrap overstate significance.

    Args:
        base_ret: Baseline daily portfolio returns
        var_ret: Variant daily portfolio returns, same length and dates

    Returns:
        (CAGR win rate, Sortino win rate), each in 0..1.
    """
    rng = np.random.default_rng(BOOT_SEED)
    n = len(base_ret)
    n_blocks = int(np.ceil(n / BOOT_BLOCK))
    offsets = np.arange(BOOT_BLOCK)
    wins_cagr = 0
    wins_sortino = 0
    for _ in range(BOOT_RESAMPLES):
        starts = rng.integers(0, n, size=n_blocks)
        idx = ((starts[:, None] + offsets[None, :]).ravel()[:n]) % n
        base_sample, var_sample = base_ret[idx], var_ret[idx]
        if compute_daily_cagr(var_sample) > compute_daily_cagr(base_sample):
            wins_cagr += 1
        base_s, var_s = compute_daily_sortino(base_sample), compute_daily_sortino(var_sample)
        if math.isfinite(base_s) and math.isfinite(var_s) and var_s > base_s:
            wins_sortino += 1
    return wins_cagr / BOOT_RESAMPLES, wins_sortino / BOOT_RESAMPLES


@dataclass(frozen=True)
class MarketData:
    """Bar-derived state for one evaluation window, shared by every config in that window.

    Only `signals_by_entry` varies between the s20/s16/s12 configs, so the expensive part —
    loading bars and unpacking them into per-symbol arrays — is built once per period.
    """

    cal: list[date]
    cal_int: list[int]
    cal_pos: dict[int, int]
    regime_streak: list[int]
    sym_dates: dict[str, np.ndarray]
    sym_close: dict[str, np.ndarray]
    sym_atr: dict[str, np.ndarray]
    sym_ma: dict[str, dict[str, np.ndarray]]

    def idx_on(self, symbol: str, dint: int) -> int:
        """Index of the symbol's last bar on or before `dint`, or -1 if it has none."""
        arr = self.sym_dates.get(symbol)
        if arr is None:
            return -1
        return int(np.searchsorted(arr, dint, side="right")) - 1

    def price_on(self, symbol: str, dint: int) -> float:
        """The symbol's adjusted close on or before `dint`, or 0.0 if it has no bar yet."""
        i = self.idx_on(symbol, dint)
        return float(self.sym_close[symbol][i]) if i >= 0 else 0.0


def build_market(bars: pl.DataFrame, bull_dates: set[date], cal: list[date]) -> MarketData:
    """Unpack an adjusted bar frame into the per-symbol arrays the daily loop indexes into.

    Args:
        bars: Adjusted bar frame carrying the exit indicators from `add_exit_indicators`
        bull_dates: Dates on which SPY closed above its 200d SMA
        cal: The window's trading days, from `qm.load_trading_days`

    Returns:
        MarketData for the window.
    """
    sym_dates: dict[str, np.ndarray] = {}
    sym_close: dict[str, np.ndarray] = {}
    sym_atr: dict[str, np.ndarray] = {}
    sym_ma: dict[str, dict[str, np.ndarray]] = {}
    for (symbol,), grp in bars.group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        name = str(symbol)
        sym_dates[name] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_close[name] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_atr[name] = g["atr14"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_ma[name] = {
            "ema20": g["ema20"].cast(pl.Float64).to_numpy(allow_copy=True),
            "sma50": g["ma_sma50"].cast(pl.Float64).to_numpy(allow_copy=True),
            "sma200": g["ma_sma200"].cast(pl.Float64).to_numpy(allow_copy=True),
        }

    # Master trading calendar = SPY days, as in portfolio-sim: the union of universe bar dates
    # would add the market holidays a few symbols carry bars on, as flat trading days.
    cal_int = [(d - _EPOCH).days for d in cal]

    # Consecutive trading days on which SPY has closed below its 200d SMA, as of each cal day.
    regime_streak: list[int] = []
    streak = 0
    for day in cal:
        streak = 0 if day in bull_dates else streak + 1
        regime_streak.append(streak)

    return MarketData(
        cal=cal,
        cal_int=cal_int,
        cal_pos={dint: i for i, dint in enumerate(cal_int)},
        regime_streak=regime_streak,
        sym_dates=sym_dates,
        sym_close=sym_close,
        sym_atr=sym_atr,
        sym_ma=sym_ma,
    )


def build_signals(
    ind: pl.DataFrame, bars: pl.DataFrame, bull_dates: set[date], start: date, sma_thresh: float, market: MarketData
) -> tuple[dict[int, list[Signal]], int, int]:
    """Generate, rank-gate and entry-resolve the signals for one config, keyed by entry day.

    The ranking gate mirrors the portfolio runner's `--min-signal-ranking` default. For s20 it
    is a no-op, but it binds for the looser s16/s12 thresholds, so it is applied throughout to
    keep the entry set identical to the production path.

    Args:
        ind: Indicator frame from `qullamaggie.add_indicators`
        bars: Adjusted bar frame, for resolving the next-bar entry
        bull_dates: Dates passing the SPY regime gate
        start: First date a signal may be emitted for
        sma_thresh: Minimum fraction above the 50d SMA (0.12 = s12)
        market: Window whose calendar the entry day must land on

    Returns:
        (signals keyed by entry date-int, count dropped by the ranking gate,
        count with no entry bar inside the window).
    """
    sig = qm.resolve_entries(qm.get_signals(ind, bull_dates, start, sma_thresh=sma_thresh), bars)
    sig = qm.add_ranking(sig)
    signals_by_entry: dict[int, list[Signal]] = {}
    n_below_rank = n_no_cal = 0
    for row in sig.iter_rows(named=True):
        if row["ranking"] < qm.MIN_RANKING:
            n_below_rank += 1
            continue
        entry_dint = (row["entry_date"] - _EPOCH).days
        if entry_dint not in market.cal_pos:
            n_no_cal += 1
            continue
        signals_by_entry.setdefault(entry_dint, []).append(
            Signal(symbol=row["symbol"], entry_dint=entry_dint, entry_price=float(row["entry_price"]), ranking=row["ranking"])
        )
    # Same-day signals compete for cash, so the funding order decides which trades exist.
    # portfolio-sim funds the best-ranked first (its RANK_FUNDING); match it, or the baseline
    # cannot reconcile. The sort is stable, so ties keep arrival order as they do there.
    for day_signals in signals_by_entry.values():
        day_signals.sort(key=lambda s: s.ranking, reverse=True)
    return signals_by_entry, n_below_rank, n_no_cal


def closed_trade(p: Position, dint: int, px: float, reason: str) -> ClosedTrade:
    """Record a position closed (or marked to market) at `px` on day `dint`.

    Args:
        p: The position being closed
        dint: Date-int of the exit
        px: Adjusted close the position exits at
        reason: The rule that closed it, or "open" for a period-end mark

    Returns:
        The round trip as a ClosedTrade.
    """
    return ClosedTrade(
        symbol=p.symbol,
        entry_date=_EPOCH + timedelta(days=p.entry_dint),
        exit_date=_EPOCH + timedelta(days=dint),
        entry_px=p.entry_px,
        exit_px=px,
        ret_pct=(px / p.entry_px - 1.0) * 100.0,
        hold_days=float(dint - p.entry_dint),
        reason=reason,
    )


@dataclass
class _Run:
    """One exit rule's simulation in progress: the open book and what it has recorded so far."""

    market: MarketData
    rule: ExitRule
    cash: float = INIT_EQUITY
    positions: list[Position] = field(default_factory=list)
    trades: list[ClosedTrade] = field(default_factory=list)
    exit_counts: Counter[str] = field(default_factory=Counter)
    taken: int = 0
    skipped: int = 0

    def marked_value(self, dint: int) -> float:
        """Cash plus the open positions at today's close; a symbol with no bar yet counts as 0."""
        return self.cash + sum(p.shares * self.market.price_on(p.symbol, dint) for p in self.positions)

    def exit_reason(self, p: Position, px: float, i: int, day_i: int) -> str | None:
        """Name the rule that closes `p` today, or None to keep holding.

        Precedence is pinned so every exit is attributable to exactly one rule: the checks run in
        order and the first that fires wins.

        Args:
            p: The position, with its peak and trend count already updated for today
            px: Today's adjusted close
            i: Index of today's bar in the symbol's arrays
            day_i: Index of today in the window's calendar

        Returns:
            "time", "regime", "stop", "trail", "trend" or "dead", or None.
        """
        rule, dint = self.rule, self.market.cal_int[day_i]
        ret = px / p.entry_px - 1.0
        if dint >= p.exit_int:
            return "time"
        if (
            rule.regime_days is not None
            and self.market.regime_streak[day_i] >= rule.regime_days
            and (not rule.regime_losers_only or ret < 0)
        ):
            return "regime"
        if rule.stop_atr is not None and px <= p.entry_px - rule.stop_atr * p.entry_atr:
            return "stop"
        if rule.stop_pct is not None and px <= p.entry_px * (1.0 - rule.stop_pct):
            return "stop"
        trail_armed = rule.trail_arm_pct is None or p.peak / p.entry_px - 1.0 >= rule.trail_arm_pct
        if rule.trail_pct is not None and trail_armed and px <= p.peak * (1.0 - rule.trail_pct):
            return "trail"
        if rule.trend_ma is not None and p.trend_cnt >= rule.trend_days:
            return "trend"
        if rule.dead_days is not None and i - p.entry_idx >= rule.dead_days and ret < rule.dead_min_ret:
            return "dead"
        if rule.dead_cal_days is not None and dint - p.entry_dint >= rule.dead_cal_days and ret < rule.dead_min_ret:
            return "dead"
        return None

    def step(self, p: Position, day_i: int) -> tuple[str, float] | None:
        """Advance one position by a day: update its peak and trend count, then test the exits.

        Args:
            p: The position, updated in place
            day_i: Index of today in the window's calendar

        Returns:
            (exit reason, exit price) if a rule fires, else None. A symbol with no bar yet is
            carried untouched.
        """
        i = self.market.idx_on(p.symbol, self.market.cal_int[day_i])
        if i < 0:
            return None
        px = float(self.market.sym_close[p.symbol][i])
        p.peak = max(p.peak, px)
        if self.rule.trend_ma is not None:
            ma_val = self.market.sym_ma[p.symbol][self.rule.trend_ma][i]
            p.trend_cnt = p.trend_cnt + 1 if (not np.isnan(ma_val) and px < ma_val) else 0
        reason = self.exit_reason(p, px, i, day_i)
        return (reason, px) if reason is not None else None

    def close_exits(self, day_i: int) -> None:
        """Run one day's exit pass over the open positions.

        Proceeds are added to cash one exit at a time, in the same order as
        `turtlex.research.portfolio_sim`, so the float sums match it exactly.

        Args:
            day_i: Index of today in the window's calendar
        """
        dint = self.market.cal_int[day_i]
        still_open: list[Position] = []
        for p in self.positions:
            hit = self.step(p, day_i)
            if hit is None:
                still_open.append(p)
                continue
            reason, px = hit
            self.cash += p.shares * px
            self.exit_counts[reason] += 1
            self.trades.append(closed_trade(p, dint, px, reason))
        self.positions = still_open

    def open_position(self, s: Signal, dint: int, target: float) -> Position:
        """Open a position in `s` worth `target` dollars on day `dint`.

        Args:
            s: The signal being funded
            dint: Entry date-int
            target: Dollars to invest

        Returns:
            The new Position.
        """
        entry_idx = self.market.idx_on(s.symbol, dint)
        atr = float(self.market.sym_atr[s.symbol][entry_idx]) if entry_idx >= 0 else float("nan")
        return Position(
            symbol=s.symbol,
            shares=target / s.entry_price,
            entry_px=s.entry_price,
            entry_dint=dint,
            entry_idx=entry_idx,
            exit_int=dint + self.rule.hold_cal,
            # A missing ATR would otherwise stop the trade out instantly; fall back
            # to the entry price, which puts the stop at or below zero (inactive).
            entry_atr=atr if not math.isnan(atr) else s.entry_price,
            peak=s.entry_price,
        )

    def fund(self, dint: int, signals: list[Signal]) -> None:
        """Fund today's signals in order, each at POS_FRACTION of the value marked after today's exits.

        Args:
            dint: Today's date-int
            signals: Today's signals, best-ranked first
        """
        target = POS_FRACTION * self.marked_value(dint)
        for s in signals:
            if self.cash + 1e-9 < target:
                self.skipped += 1
                continue
            self.cash -= target
            self.positions.append(self.open_position(s, dint, target))
            self.taken += 1


def run_sim(market: MarketData, signals_by_entry: dict[int, list[Signal]], rule: ExitRule) -> SimResult:
    """Simulate the portfolio over one window under one exit rule.

    The daily loop matches `turtlex.research.portfolio_sim.run_sim` (what
    `scripts/qullamaggie-portfolio-sim.py` runs), and the CAGR/MaxDD/Calmar/Sortino come from the
    same `equity_curve_metrics`, so results are directly comparable to the committed baseline.

    Args:
        market: Window state from `build_market`
        signals_by_entry: Signals keyed by the date-int they are funded on
        rule: The exit configuration to apply

    Returns:
        SimResult with the equity curve, trade log and exit attribution.
    """
    run = _Run(market, rule)
    equity_curve: list[float] = []
    cash_curve: list[float] = []
    for day_i, dint in enumerate(market.cal_int):
        run.close_exits(day_i)
        run.fund(dint, signals_by_entry.get(dint, []))
        equity_curve.append(run.marked_value(dint))
        cash_curve.append(run.cash)

    # Open at period end — marked to market, not force-closed.
    last_dint = market.cal_int[-1]
    marks = ((p, market.price_on(p.symbol, last_dint)) for p in run.positions)
    run.trades.extend(closed_trade(p, last_dint, px, "open") for p, px in marks if px > 0)

    eq = np.array(equity_curve)
    cash_arr = np.array(cash_curve)
    return SimResult(
        rule=rule,
        **equity_curve_metrics(eq),
        avg_uninv_pct=float(np.mean(cash_arr / eq) * 100),
        taken=run.taken,
        skipped=run.skipped,
        eq=eq,
        daily_ret=eq[1:] / eq[:-1] - 1.0,
        trades=run.trades,
        exit_counts=run.exit_counts,
    )


def load_window(bars_history: DailyBarsQueryRepository, start: date, end: date) -> tuple[MarketData, pl.DataFrame, pl.DataFrame, set[date]]:
    """Load and prepare everything one evaluation window needs.

    Args:
        bars_history: Repository for bar reads
        start: First day of the evaluation window
        end: Last day of the evaluation window

    Returns:
        (market state, indicator frame, adjusted bar frame with exit indicators, bull dates).
    """
    print(f"  loading {start} – {end} …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, start, end)
    cal = qm.load_trading_days(bars_history, start, end)
    bars = qm.load_bars(bars_history, start, end)
    ind = qm.add_indicators(bars)
    bars = add_exit_indicators(bars)
    return build_market(bars, bull_dates, cal), ind, bars, bull_dates


def dd_floor(base: SimResult) -> float:
    """The deepest MaxDD a variant may reach: the baseline's, worsened by MAXDD_GUARD_PP."""
    return base.max_dd - MAXDD_GUARD_PP / 100.0


def beats(res: SimResult, base: SimResult) -> bool:
    """The pass bar: higher CAGR and Sortino than `base`, with MaxDD no more than MAXDD_GUARD_PP worse.

    Args:
        res: The variant
        base: The baseline run on the same signals

    Returns:
        True if `res` clears the bar.
    """
    return res.cagr > base.cagr and res.sortino > base.sortino and res.max_dd > dd_floor(base)


def report_label(res: SimResult, base: SimResult) -> str:
    """The row label for `res`: the baseline's fixed name, or the rule's.

    Args:
        res: The result being labelled
        base: The baseline result

    Returns:
        The label.
    """
    return "baseline (366d only)" if res is base else res.rule.name


def pick_finalists(candidates: list[SimResult], base: SimResult) -> list[SimResult]:
    """The candidates that clear the pass bar, each rule once, ordered by Sortino.

    Args:
        candidates: Every sweep, control and composed result
        base: The baseline they are scored against

    Returns:
        The passing results, best Sortino first.
    """
    seen: set[ExitRule] = set()
    finalists = []
    for r in candidates:  # the sma200 control is also a cell in idea 4 — report it once
        if beats(r, base) and r.rule not in seen:
            seen.add(r.rule)
            finalists.append(r)
    finalists.sort(key=lambda r: r.sortino, reverse=True)
    return finalists


def trade_metric_rows(base: SimResult, shortlist: list[SimResult]) -> list[str]:
    """Trade metrics and exit attribution, one row for the baseline and each shortlisted result.

    Args:
        base: The baseline
        shortlist: The results to report after it

    Returns:
        Table rows; a result with no trades is left out.
    """
    rows: list[str] = []
    for res in [base, *shortlist]:
        metrics = compute_trade_metrics([t.ret_pct for t in res.trades], [t.hold_days for t in res.trades])
        if metrics is None:
            continue
        breakdown = ", ".join(f"{k}={v}" for k, v in sorted(res.exit_counts.items())) or "—"
        rows.append(
            f"{report_label(res, base):<26.26} {metrics.n:>4} {metrics.win_pct:>6.1f} {metrics.mean_pct:>+8.2f} "
            f"{metrics.median_pct:>+8.2f} {metrics.profit_factor:>6.2f} {metrics.cvar95_pct:>+8.2f} "
            f"{metrics.sortino:>9.3f}  {breakdown}"
        )
    return rows


def year_return_rows(cal: list[date], base: SimResult, shortlist: list[SimResult]) -> tuple[list[int], list[str]]:
    """Calendar-year returns of the baseline and each shortlisted result.

    Args:
        cal: The window's trading days, which index every equity curve
        base: The baseline
        shortlist: The results to report after it

    Returns:
        (the years, one table row per result).
    """
    years = sorted({d.year for d in cal})
    year_index = {y: [i for i, d in enumerate(cal) if d.year == y] for y in years}

    def year_return(res: SimResult, y: int) -> float:
        idxs = year_index[y]
        start_eq = res.eq[idxs[0] - 1] if idxs[0] > 0 else INIT_EQUITY
        return float(res.eq[idxs[-1]] / start_eq - 1.0) * 100

    rows = [f"{report_label(res, base):<26.26} " + " ".join(f"{year_return(res, y):>+8.1f}" for y in years) for res in [base, *shortlist]]
    return years, rows


def robustness_matrix(bars_history: DailyBarsQueryRepository) -> tuple[list[str], int]:
    """Re-run WINNER against the baseline in every VALIDATION_PERIODS x VALIDATION_CONFIGS cell.

    Args:
        bars_history: Repository for bar reads

    Returns:
        (one table row per cell, number of cells that pass).
    """
    rows: list[str] = []
    n_pass = 0
    for start, end in VALIDATION_PERIODS:
        print(f"Validating period {start} – {end} …", flush=True)
        v_market, v_ind, v_bars, v_bull = load_window(bars_history, start, end)
        for cfg_name, cfg_thresh in VALIDATION_CONFIGS:
            v_signals, _, _ = build_signals(v_ind, v_bars, v_bull, start, cfg_thresh, v_market)
            v_base = run_sim(v_market, v_signals, BASELINE)
            v_rule = run_sim(v_market, v_signals, WINNER)
            cell_pass = beats(v_rule, v_base)
            n_pass += int(cell_pass)
            rows.append(
                f"{f'{start.year}-{end.year}':<12} {cfg_name:<4} {v_base.taken:>4} | "
                f"{v_base.cagr * 100:>+9.2f} {v_rule.cagr * 100:>+9.2f} {(v_rule.cagr - v_base.cagr) * 100:>+7.2f} | "
                f"{v_base.sortino:>8.3f} {v_rule.sortino:>8.3f} {v_rule.sortino - v_base.sortino:>+7.3f} | "
                f"{v_base.max_dd * 100:>8.2f} {v_rule.max_dd * 100:>8.2f} | "
                f"{'PASS' if cell_pass else 'fail':>5}"
            )
        del v_market, v_ind, v_bars  # release the window's bars before loading the next
    return rows, n_pass


def main() -> None:
    if qm.MIN_RANKING != REF_MIN_RANKING:
        raise ValueError(
            f"qm.MIN_RANKING is {qm.MIN_RANKING} but the REF_* baseline was run at R>={REF_MIN_RANKING}; "
            "refresh the baseline block from portfolio-v4.md before running the sweep"
        )
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Preparing sweep window …", flush=True)
    market, ind, bars, bull_dates = load_window(bars_history, EVAL_START, EVAL_END)
    signals_by_entry, n_below_rank, n_no_cal = build_signals(ind, bars, bull_dates, EVAL_START, SMA_THRESH, market)
    n_signals = sum(len(v) for v in signals_by_entry.values())
    print(f"  {n_signals} signals ({n_below_rank} below ranking {qm.MIN_RANKING}, {n_no_cal} with no entry bar)", flush=True)

    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    def table(hdr: str, rows: list[str]) -> None:
        out("")
        out("```text")
        out(hdr)
        out("-" * len(hdr))
        for row in rows:
            out(row)
        out("```")

    print("Running baseline …", flush=True)
    base = run_sim(market, signals_by_entry, BASELINE)

    def verdict(res: SimResult) -> str:
        return "PASS" if beats(res, base) else "fail"

    def result_row(label: str, res: SimResult) -> str:
        return (
            f"{label:<26.26} {res.final:>10,.0f} {res.cagr * 100:>+7.2f} {res.max_dd * 100:>8.2f} "
            f"{res.calmar:>7.3f} {res.sortino:>8.3f} {res.taken:>6} {res.skipped:>6} {verdict(res):>5}"
        )

    row_hdr = f"{'variant':<26} {'Final$':>10} {'CAGR%':>7} {'MaxDD%':>8} {'Calmar':>7} {'Sortino':>8} {'taken':>6} {'skip':>6} {'':>5}"

    out("# Qullamaggie Exit-Strategy Sweep")
    out("")
    out(f"Run date: {run_timestamp()}")
    out("")
    out(
        f"Config: `bk50d_s12_v2.0` | {EVAL_START} – {EVAL_END} | initial ${INIT_EQUITY:,.0f} | "
        f"sizing {POS_FRACTION:.0%} of portfolio value | ranking >= {qm.MIN_RANKING} | "
        f"time-cap backstop {qm.HOLD_CAL}d"
    )
    out("")
    out(
        f"{n_signals} signals entered the simulation ({n_below_rank} dropped below the ranking gate, "
        f"{n_no_cal} with no entry bar in the window). Exits fill at the day's adjusted close."
    )

    out("")
    out("## Baseline reconciliation")
    out("")
    out(
        "Signals here and in `qullamaggie-portfolio-sim.py` both come from `turtlex.research.qullamaggie`, "
        "and both fund same-day signals best-ranked first, so on the same day's data the two baselines "
        "should agree. A divergence means either the harness no longer reproduces portfolio-sim, which "
        "would invalidate every comparison below, or the data has moved since the REF_* run: re-run "
        "portfolio-sim on the same data before reading it as the former."
    )
    rec_hdr = f"{'source':<26} {'Final$':>10} {'CAGR%':>7} {'MaxDD%':>8} {'Sortino':>8}"
    table(
        rec_hdr,
        [
            f"{f'portfolio-sim ({REF_RUN_DATE})':<26} {REF_FINAL:>10,.0f} {REF_CAGR_PCT:>+7.2f} {REF_MAXDD_PCT:>8.2f} {REF_SORTINO:>8.3f}",
            f"{'this harness':<26} {base.final:>10,.0f} {base.cagr * 100:>+7.2f} {base.max_dd * 100:>8.2f} {base.sortino:>8.3f}",
        ],
    )
    drift = abs(base.cagr * 100 - REF_CAGR_PCT)
    out("")
    if drift <= RECONCILE_TOL_PP:
        out(f"CAGR divergence: {drift:.2f}pp (within the {RECONCILE_TOL_PP:.1f}pp tolerance).")
    else:
        out(
            f"CAGR divergence: {drift:.2f}pp, ABOVE the {RECONCILE_TOL_PP:.1f}pp tolerance. The REF_* row is from "
            f"{REF_RUN_DATE}; if the data has been refreshed since, re-run portfolio-sim on the same data before "
            "treating this as a harness fault."
        )
    out("")
    out(f"Pass bar: CAGR > {base.cagr * 100:+.2f}%, Sortino > {base.sortino:.3f}, MaxDD > {dd_floor(base) * 100:.2f}%.")

    all_results: list[SimResult] = []
    best_by_idea: dict[str, SimResult] = {}

    for idea, rules in IDEAS.items():
        print(f"Sweeping {idea} …", flush=True)
        results = [run_sim(market, signals_by_entry, r) for r in rules]
        all_results.extend(results)
        best_by_idea[idea] = max(results, key=lambda r: r.sortino)
        out("")
        out(f"## {idea}")
        table(
            row_hdr,
            [result_row(r.rule.name, r) for r in results] + ["-" * len(row_hdr), result_row("baseline (366d only)", base)],
        )

    print("Running controls …", flush=True)
    control_results = [run_sim(market, signals_by_entry, r) for r in CONTROLS]
    out("")
    out("## Controls")
    out("")
    out(
        "The four exit modes `qullamaggie-portfolio-sim.py` carried but never selected "
        "(`stop30`, `trail25`, `sma200x5`, `dead120`), at the constants it used for them. They were "
        "removed from it on 2026-11-15 and are measured only here."
    )
    table(
        row_hdr,
        [result_row(r.rule.name, r) for r in control_results] + ["-" * len(row_hdr), result_row("baseline (366d only)", base)],
    )

    # One composed run: the two best-scoring ideas whose mechanisms don't overlap. Chosen by
    # rank rather than named in advance, but still a single extra run — not a second sweep.
    ranked_ideas = sorted(best_by_idea.values(), key=lambda r: r.sortino, reverse=True)
    first = ranked_ideas[0]
    partner = next((r for r in ranked_ideas[1:] if not (mechanisms(r.rule) & mechanisms(first.rule))), None)
    composed_res = run_sim(market, signals_by_entry, compose(first.rule, partner.rule)) if partner is not None else None
    out("")
    out("## Composed rule")
    out("")
    out("The two best-scoring ideas with non-overlapping mechanisms, run together.")
    if composed_res is not None:
        out("")
        out(f"Rule: `{composed_res.rule.name}` (name truncated in the table below).")
    table(
        row_hdr,
        ([result_row(composed_res.rule.name, composed_res)] if composed_res is not None else ["(no disjoint pair)"])
        + ["-" * len(row_hdr), result_row("baseline (366d only)", base)],
    )

    out("")
    out("## Verdict by idea")
    out("")
    out("Deltas are the idea's best-by-Sortino variant against the baseline.")
    verdict_hdr = f"{'idea':<38} {'cells':>6} {'pass':>5} {'best variant':<24} {'dCAGR':>7} {'dSortino':>9} {'dMaxDD':>8}"
    verdict_rows: list[str] = []
    for idea, rules in IDEAS.items():
        results = [r for r in all_results if r.rule in rules]
        best = best_by_idea[idea]
        verdict_rows.append(
            f"{idea:<38.38} {len(results):>6} {sum(1 for r in results if verdict(r) == 'PASS'):>5} "
            f"{best.rule.name:<24.24} {(best.cagr - base.cagr) * 100:>+7.2f} {best.sortino - base.sortino:>+9.3f} "
            f"{(best.max_dd - base.max_dd) * 100:>+8.2f}"
        )
    table(verdict_hdr, verdict_rows)

    candidates = [*all_results, *control_results] + ([composed_res] if composed_res is not None else [])
    finalists = pick_finalists(candidates, base)
    shortlist = finalists or sorted(best_by_idea.values(), key=lambda r: r.sortino, reverse=True)

    out("")
    out("## Finalists — trade metrics and exit attribution")
    out("")
    if finalists:
        out(f"{len(finalists)} variant(s) cleared the bar, ordered by Sortino.")
    else:
        out("**No variant cleared the bar.** Showing the best variant of each idea instead, for diagnosis.")
    trade_hdr = f"{'variant':<26} {'N':>4} {'Win%':>6} {'Mean%':>8} {'Med%':>8} {'PF':>6} {'CVaR95%':>8} {'tSortino':>9}  exits by rule"
    table(trade_hdr, trade_metric_rows(base, shortlist))

    out("")
    out("## Finalists — per-year decomposition")
    out("")
    out("An edge concentrated in one year is regime-contingent, not a general improvement.")
    years, year_rows = year_return_rows(market.cal, base, shortlist)
    table(f"{'variant':<26} " + " ".join(f"{y:>8}" for y in years), year_rows)

    out("")
    out("## Finalists — bootstrap win rate vs baseline")
    out("")
    out(
        f"Stationary block bootstrap, {BOOT_RESAMPLES:,} resamples of {BOOT_BLOCK}-day blocks, paired on "
        "day indices. The figure is the fraction of resampled paths on which the variant beats the "
        "baseline — near 50% means the difference is indistinguishable from noise."
    )
    boot_hdr = f"{'variant':<26} {'CAGR win%':>10} {'Sortino win%':>13}"
    boot_rows: list[str] = []
    for res in shortlist:
        print(f"Bootstrapping {res.rule.name} …", flush=True)
        win_cagr, win_sortino = bootstrap_win_rate(base.daily_ret, res.daily_ret)
        boot_rows.append(f"{res.rule.name:<26.26} {win_cagr * 100:>10.1f} {win_sortino * 100:>13.1f}")
    table(boot_hdr, boot_rows)

    out("")
    out(f"## Robustness matrix — `{WINNER.name}` across configs and periods")
    out("")
    out(
        f"The winning rule's parameters were chosen on **s12 / {EVAL_START}–{EVAL_END}**. Every other "
        "cell below varies the entry threshold, the period, or both, and none of them informed that "
        "choice. Each cell re-runs the baseline and the rule on identical signals, so the difference "
        "is the exit and nothing else."
    )
    matrix_hdr = (
        f"{'period':<12} {'cfg':<4} {'N':>4} | {'base CAGR':>9} {'rule CAGR':>9} {'d':>7} | "
        f"{'base Srt':>8} {'rule Srt':>8} {'d':>7} | {'base DD':>8} {'rule DD':>8} | {'':>5}"
    )
    matrix_rows, n_pass = robustness_matrix(bars_history)
    table(matrix_hdr, matrix_rows)
    out("")
    out(f"**{n_pass} of {len(matrix_rows)} cells pass**, on the same bar used for the sweep.")
    out("")
    out(
        "`N` is the baseline trade count, which doubles as a read on how capital-constrained each "
        "cell is: the rule's second mechanism is recycling capital into signals that would "
        "otherwise go unfunded, so it has less to work with where cash was already idle."
    )

    out("")
    out("## Audit sample — first 10 rule-driven exits of the top finalist")
    out("")
    out(
        "Every field below is checkable against `turtle.daily_bars`: `exit $` is that symbol's "
        "split/dividend-adjusted close on `exit date`, and the rule that fired is named."
    )
    top = shortlist[0]
    audit_hdr = f"{'symbol':<10} {'entry date':<12} {'exit date':<12} {'entry $':>9} {'exit $':>9} {'ret%':>8} {'calD':>5}  rule"
    audit_rows = [
        f"{t.symbol:<10} {str(t.entry_date):<12} {str(t.exit_date):<12} {t.entry_px:>9.2f} "
        f"{t.exit_px:>9.2f} {t.ret_pct:>+8.2f} {t.hold_days:>5.0f}  {t.reason}"
        for t in [t for t in top.trades if t.reason not in ("time", "open")][:10]
    ]
    out(f"Rule: {top.rule.name}")
    table(audit_hdr, audit_rows)

    out("")
    out("## Limitations")
    out("")
    out(
        "- Single evaluation window; parameters are scored on the same data they were chosen on. "
        "The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it."
    )
    out(
        "- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees "
        "companies that are large today. This survivorship bias inflates every absolute figure here, baseline "
        "included; relative comparisons are unaffected."
    )
    out("- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.")

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
