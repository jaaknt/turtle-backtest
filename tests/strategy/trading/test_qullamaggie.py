"""Polars path signal tests for QullamaggieStrategy."""
from datetime import date, timedelta
from turtle.strategy.trading.qullamaggie import QullamaggieStrategy
from unittest.mock import MagicMock

import numpy as np
import polars as pl

N = 320  # > min_bars=300, > 253 bars needed for roc_252d
QUIET = 30  # last QUIET bars: low volume (dry-up) and contracted range (ADR change)


def _build_ohlcv(
    n: int = N,
    breakouts: dict[int, float] | None = None,
    early_close_scale: float = 1.0,
    last_volume: float | None = None,
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
    """
    closes = np.array([100.0 + (i % 2) for i in range(n)])
    if early_close_scale != 1.0:
        closes[: n - 252] *= early_close_scale
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


def _make_strategy(ticker_df: pl.DataFrame, spy_df: pl.DataFrame) -> QullamaggieStrategy:
    mock_repo = MagicMock()
    mock_repo.get_bars_pl.side_effect = lambda ticker, start, end, tf: spy_df if ticker == "SPY.US" else ticker_df
    mock_ranking = MagicMock()
    mock_ranking.ranking.return_value = 50
    return QullamaggieStrategy(bars_history=mock_repo, ranking_strategy=mock_ranking)


def test_breakout_produces_signal() -> None:
    ohlcv = _build_ohlcv(breakouts={N - 1: 120.0})
    last_date = ohlcv["date"][-1]
    strategy = _make_strategy(ohlcv, _build_spy(last_date))
    signals = strategy.get_signals("TEST.US", last_date, last_date)
    assert len(signals) == 1
    assert signals[0].ticker == "TEST.US"
    assert signals[0].date == last_date
    assert signals[0].ranking == 50


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


def test_universe_uses_qualified_symbols() -> None:
    ohlcv = _build_ohlcv()
    strategy = _make_strategy(ohlcv, _build_spy(ohlcv["date"][-1]))
    mock_ticker_repo = MagicMock()
    mock_ticker_repo.get_qualified_symbols.return_value = ["AAA.US", "BBB.US"]
    assert strategy.get_universe(mock_ticker_repo, limit=100) == ["AAA.US", "BBB.US"]
    mock_ticker_repo.get_qualified_symbols.assert_called_once_with(limit=100)
