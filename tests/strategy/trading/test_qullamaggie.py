"""Polars path signal tests for QullamaggieStrategy."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import numpy as np
import polars as pl

from turtlex.strategy.trading.qullamaggie import QullamaggieStrategy

N = 320  # > min_bars=300, > 253 bars needed for roc_252d
QUIET = 30  # last QUIET bars: low volume (dry-up) and contracted range (ADR change)


def _build_ohlcv(
    n: int = N,
    breakouts: dict[int, float] | None = None,
    early_close_scale: float = 1.0,
    last_volume: float | None = None,
    pre_breakout_closes: list[float] | None = None,
) -> pl.DataFrame:
    """Build n daily bars that satisfy every filter except the breakout itself.

    Close alternates 100/101 (RSI ~50, 50d max = 101, SMA50 ~100.5); the last
    QUIET bars have 600K volume vs 1M before (volume dry-up, no surge) and a
    3.5% daily range vs 5% before (ADR >= 3% with ADR10/ADR50 < 0.9).

    Args:
        n: Number of bars
        breakouts: Optional {index: close} overrides to create breakout days
        early_close_scale: Scale applied to the first n-252 closes (drives roc_252d up)
        last_volume: Optional volume override for the final bar (volume-surge test)
        pre_breakout_closes: Optional 15 closes for indices n-16..n-2 — exactly the
            values whose 14 diffs form the shift-1 RSI(14) window of the final bar,
            letting a test pin the breakout day's RSI
    """
    closes = np.array([100.0 + (i % 2) for i in range(n)])
    if early_close_scale != 1.0:
        closes[: n - 252] *= early_close_scale
    if pre_breakout_closes is not None:
        closes[n - 16 : n - 1] = pre_breakout_closes
    if breakouts:
        for idx, px in breakouts.items():
            closes[idx] = px
    ranges = np.where(np.arange(n) >= n - QUIET, 0.035, 0.05)
    volumes = np.where(np.arange(n) >= n - QUIET, 600_000.0, 1_000_000.0)
    if last_volume is not None:
        volumes[-1] = last_volume

    start = date(2020, 1, 2)
    return pl.DataFrame(
        {
            "date": [start + timedelta(days=i) for i in range(n)],
            "open": closes,
            "high": closes * (1.0 + ranges),
            "low": closes,
            "close": closes,
            "adjusted_close": closes,
            "volume": volumes,
        }
    )


def _build_spy(last_date: date, n: int = 650, bull: bool = True) -> pl.DataFrame:
    """Build n SPY bars ending on last_date, trending up (bull) or down (bear)."""
    closes = np.linspace(300.0, 400.0, n) if bull else np.linspace(400.0, 300.0, n)
    return pl.DataFrame(
        {
            "date": [last_date - timedelta(days=n - 1 - i) for i in range(n)],
            "close": closes,
        }
    )


def _make_strategy(
    ticker_df: pl.DataFrame, spy_df: pl.DataFrame, sma_thresh: float = QullamaggieStrategy.SMA_THRESH
) -> QullamaggieStrategy:
    mock_repo = MagicMock()
    mock_repo.get_bars_pl.side_effect = lambda ticker, start, end, tf: spy_df if ticker == "SPY.US" else ticker_df
    mock_ranking = MagicMock()
    mock_ranking.ranking.return_value = 50
    return QullamaggieStrategy(bars_history=mock_repo, ranking_strategy=mock_ranking, sma_thresh=sma_thresh)


def test_breakout_produces_signal() -> None:
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0})
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    signals = strategy.get_signals("TEST.US", last_date, last_date)
    assert len(signals) == 1
    assert signals[0].ticker == "TEST.US"
    assert signals[0].date == last_date
    assert signals[0].ranking == 50


def test_higher_sma_thresh_blocks_breakout() -> None:
    # the 120 breakout sits ~19% above the ~100.5 SMA50: a 25% threshold rejects it
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0})
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date), sma_thresh=0.25)
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


def test_lower_sma_thresh_admits_smaller_breakout() -> None:
    # a 105 close clears the 50d max (101) but is only ~4.5% above the SMA50: blocked at
    # the 15% default, accepted at 4%
    ohlcv = _build_ohlcv(breakouts={N - 1: 105.0})
    last_date = ohlcv["date"][-1]
    assert _make_strategy(ohlcv, _build_spy(last_date)).get_signals("TEST.US", last_date, last_date) == []
    signals = _make_strategy(ohlcv, _build_spy(last_date), sma_thresh=0.04).get_signals("TEST.US", last_date, last_date)
    assert [s.date for s in signals] == [last_date]


def test_bear_regime_blocks_signal() -> None:
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0})
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date, bull=False))
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


def test_volume_surge_blocks_signal() -> None:
    # 2.0M > 2x avg_vol_50 (~760K) on the breakout day
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0}, last_volume=2_000_000.0)
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


def test_roc_cap_blocks_signal() -> None:
    # close 252 bars ago is scaled down so the 12-month ROC exceeds 100%
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0}, early_close_scale=0.45)
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


# 14 diffs: 12 gains of +0.5 and 2 losses of 1.0 → avg_gain/avg_loss = 3 → RSI = 75 (>= 70, blocked)
_RSI_75_CLOSES = [100.0, 100.5, 101.0, 101.5, 102.0, 102.5, 103.0, 102.0, 102.5, 103.0, 103.5, 104.0, 104.5, 105.0, 104.0]


def test_rsi_above_70_blocks_signal() -> None:
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0}, pre_breakout_closes=_RSI_75_CLOSES)
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


def test_cooldown_suppresses_second_trigger() -> None:
    # two breakout days 10 calendar days apart: only the first one signals
    ohlcv = _build_ohlcv(breakouts={N - 11: 118.0, N - 1: 120.0})
    first_breakout = ohlcv["date"][N - 11]
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    signals = strategy.get_signals("TEST.US", first_breakout, last_date)
    assert [s.date for s in signals] == [first_breakout]


def test_cooldown_from_warmup_suppresses_in_range_signal() -> None:
    # a trigger 10 days before start_date suppresses the in-range breakout
    ohlcv = _build_ohlcv(breakouts={N - 11: 118.0, N - 1: 120.0})
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


def test_returns_empty_when_insufficient_data() -> None:
    ohlcv = _build_ohlcv(n=200)  # 200 bars < min_bars=300
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    assert strategy.get_signals("TEST.US", last_date, last_date) == []


def test_missing_spy_data_blocks_all_signals() -> None:
    # empty SPY frame (e.g. empty/wrong database): regime filter blocks every signal
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0})
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, pl.DataFrame())
    assert strategy.get_signals("TEST.US", last_date, last_date) == []
    assert strategy._regime_dates == set()


def test_universe_uses_qualified_symbols() -> None:
    ohlcv = _build_ohlcv()
    strategy = _make_strategy(ohlcv, _build_spy(ohlcv["date"][-1]))
    mock_ticker_repo = MagicMock()
    mock_ticker_repo.get_qullamaggie_qualified_symbols.return_value = ["AAA.US", "BBB.US"]
    assert strategy.get_universe(mock_ticker_repo, limit=100) == ["AAA.US", "BBB.US"]
    mock_ticker_repo.get_qullamaggie_qualified_symbols.assert_called_once_with(limit=100)


def test_zero_volume_bars_are_dropped_before_indicators() -> None:
    """Zero-volume bars would skew the rolling volume averages, so they never reach the filters."""
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0})
    with_gaps = ohlcv.with_columns(
        pl.when(pl.col("date").is_in([ohlcv["date"][5], ohlcv["date"][6]])).then(0.0).otherwise(pl.col("volume")).alias("volume")
    )
    last_date = with_gaps["date"][-1]
    strategy = _make_strategy(with_gaps, _build_spy(last_date))

    assert strategy.collect_data("TEST.US", last_date, last_date) is True
    assert strategy.pl_df.shape[0] == N - 2
    assert strategy.pl_df.filter(pl.col("volume") == 0).is_empty()


def test_min_bars_is_applied_after_dropping_unusable_bars() -> None:
    """A ticker whose raw count clears min_bars but whose usable count does not is rejected."""
    ohlcv = _build_ohlcv(n=305)
    zero_dates = ohlcv["date"][:10].to_list()
    with_gaps = ohlcv.with_columns(pl.when(pl.col("date").is_in(zero_dates)).then(0.0).otherwise(pl.col("volume")).alias("volume"))
    last_date = with_gaps["date"][-1]
    strategy = _make_strategy(with_gaps, _build_spy(last_date))

    assert with_gaps.shape[0] >= strategy.min_bars  # raw count would have passed
    assert strategy.collect_data("TEST.US", last_date, last_date) is False
