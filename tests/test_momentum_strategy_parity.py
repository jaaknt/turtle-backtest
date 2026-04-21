"""Polars path signal tests for MomentumStrategy."""
from datetime import date, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.strategy.trading.momentum import MomentumStrategy
from unittest.mock import MagicMock

import numpy as np
import polars as pl
import pytest


def _build_ohlcv(n: int = 150) -> pl.DataFrame:
    """Build n bars of deterministic uptrending OHLCV data.

    Growth rate is chosen so that:
    - close[n-1] is ~50% above close[n-71] (satisfies the 30% 100-day change)
    - volume on the last bar is 1.5× the EMA, triggering the volume condition
    - all EMA stack conditions hold throughout the trend
    """
    # Exponential uptrend: 0.6% per bar
    base = 100.0
    growth = 1.006
    closes = np.array([base * (growth**i) for i in range(n)])
    opens = closes * 0.99       # 1% bullish body → (close-open)/close ≈ 1% > 0.8% ✓
    highs = closes * 1.01
    lows = closes * 0.98
    volumes = np.full(n, 1_000_000.0)
    volumes[-1] = 1_600_000.0  # last bar: 1.6× EMA ≥ 1.1× ✓

    start = date(2020, 1, 2)
    dates_d = [start + timedelta(days=i) for i in range(n)]

    return pl.DataFrame(
        {
            "date": dates_d,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "adjusted_close": closes,
            "volume": volumes,
        }
    )


def _make_strategy(pl_df: pl.DataFrame, min_bars: int = 100) -> MomentumStrategy:
    mock_repo = MagicMock()
    mock_repo.get_bars_pl.return_value = pl_df
    mock_ranking = MagicMock()
    mock_ranking.ranking.return_value = 50
    return MomentumStrategy(
        bars_history=mock_repo,
        ranking_strategy=mock_ranking,
        time_frame_unit=TimeFrameUnit.WEEK,  # skips EMA200 condition, simpler to satisfy
        warmup_period=100,
        min_bars=min_bars,
    )


def _make_day_strategy(pl_df: pl.DataFrame) -> MomentumStrategy:
    mock_repo = MagicMock()
    mock_repo.get_bars_pl.return_value = pl_df
    mock_ranking = MagicMock()
    mock_ranking.ranking.return_value = 50
    return MomentumStrategy(
        bars_history=mock_repo,
        ranking_strategy=mock_ranking,
        time_frame_unit=TimeFrameUnit.DAY,
        warmup_period=100,
        min_bars=100,
    )


@pytest.fixture
def ohlcv() -> pl.DataFrame:
    return _build_ohlcv(n=150)


def test_polars_path_produces_signals(ohlcv: pl.DataFrame) -> None:
    strategy = _make_strategy(ohlcv)
    last_date = ohlcv["date"][-1]
    signals = strategy.get_signals("TEST", last_date, last_date)
    assert len(signals) >= 1, "Polars path should produce at least one signal on the last bar"


def test_signal_ticker_and_ranking_preserved(ohlcv: pl.DataFrame) -> None:
    last_date = ohlcv["date"][-1]
    signals = _make_strategy(ohlcv).get_signals("AAPL", last_date, last_date)
    for s in signals:
        assert s.ticker == "AAPL"
        assert s.ranking == 50


def test_returns_empty_when_insufficient_data() -> None:
    pl_df = _build_ohlcv(n=50)  # 50 bars < min_bars=100
    strategy = _make_strategy(pl_df, min_bars=100)
    last_date = pl_df["date"][-1]
    assert strategy.get_signals("TEST", last_date, last_date) == []


def test_returns_empty_when_start_date_beyond_data(ohlcv: pl.DataFrame) -> None:
    future_date = date(2099, 1, 1)
    strategy = _make_strategy(ohlcv)
    assert strategy.get_signals("TEST", future_date, future_date) == []


def test_day_timeframe_produces_signals() -> None:
    """EMA-200 branch (DAY timeframe) must produce signals on strongly trending data."""
    pl_df = _build_ohlcv(n=280)
    last_date = pl_df["date"][-1]
    start_date = last_date - timedelta(days=30)
    signals = _make_day_strategy(pl_df).get_signals("TEST", start_date, last_date)
    assert len(signals) >= 1, "DAY timeframe polars path should produce at least one signal"
