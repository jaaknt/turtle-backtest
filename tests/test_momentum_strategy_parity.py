"""Parity test: MomentumStrategy pandas path vs polars path must produce identical signals."""
from datetime import date, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.strategy.trading.momentum import MomentumStrategy
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import polars as pl
import pytest


def _build_ohlcv(n: int = 150) -> tuple[pd.DataFrame, pl.DataFrame]:
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

    dates_dt = pd.date_range(start="2020-01-02", periods=n, freq="B")  # business days
    dates_d = [d.date() for d in dates_dt]

    pd_df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "adjusted_close": closes, "volume": volumes},
        index=pd.DatetimeIndex(dates_dt, name="date"),
    )

    pl_df = pl.DataFrame(
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

    return pd_df, pl_df


def _make_strategy(pd_df: pd.DataFrame, pl_df: pl.DataFrame, use_polars: bool) -> MomentumStrategy:
    mock_repo = MagicMock()
    mock_repo.get_ticker_history.return_value = pd_df
    mock_repo.get_bars_pl.return_value = pl_df

    mock_ranking = MagicMock()
    mock_ranking.ranking.return_value = 50

    return MomentumStrategy(
        bars_history=mock_repo,
        ranking_strategy=mock_ranking,
        time_frame_unit=TimeFrameUnit.WEEK,  # skips EMA200 condition, simpler to satisfy
        warmup_period=100,
        min_bars=100,
        use_polars=use_polars,
    )


@pytest.fixture
def ohlcv() -> tuple[pd.DataFrame, pl.DataFrame]:
    return _build_ohlcv(n=150)


def test_pandas_path_produces_signals(ohlcv: tuple[pd.DataFrame, pl.DataFrame]) -> None:
    pd_df, pl_df = ohlcv
    strategy = _make_strategy(pd_df, pl_df, use_polars=False)
    last_date = pd_df.index[-1].date()
    signals = strategy.get_signals("TEST", last_date, last_date)
    assert len(signals) >= 1, "Pandas path should produce at least one signal on the last bar"


def test_polars_path_produces_signals(ohlcv: tuple[pd.DataFrame, pl.DataFrame]) -> None:
    pd_df, pl_df = ohlcv
    strategy = _make_strategy(pd_df, pl_df, use_polars=True)
    last_date = pl_df["date"][-1]
    signals = strategy.get_signals("TEST", last_date, last_date)
    assert len(signals) >= 1, "Polars path should produce at least one signal on the last bar"


def test_both_paths_return_identical_signal_dates(ohlcv: tuple[pd.DataFrame, pl.DataFrame]) -> None:
    """Core parity check: both paths must agree on every signal date."""
    pd_df, pl_df = ohlcv
    last_date = pl_df["date"][-1]
    # Use a wider window so multiple candidate dates are evaluated
    start_date = last_date - timedelta(days=30)

    pd_signals = _make_strategy(pd_df, pl_df, use_polars=False).get_signals("TEST", start_date, last_date)
    pl_signals = _make_strategy(pd_df, pl_df, use_polars=True).get_signals("TEST", start_date, last_date)

    pd_dates = sorted(s.date for s in pd_signals)
    pl_dates = sorted(s.date for s in pl_signals)

    assert pd_dates == pl_dates, f"Signal dates differ: pandas={pd_dates}, polars={pl_dates}"


def test_signal_ticker_and_ranking_preserved(ohlcv: tuple[pd.DataFrame, pl.DataFrame]) -> None:
    pd_df, pl_df = ohlcv
    last_date = pl_df["date"][-1]

    for use_polars in (False, True):
        strategy = _make_strategy(pd_df, pl_df, use_polars=use_polars)
        signals = strategy.get_signals("AAPL", last_date, last_date)
        for s in signals:
            assert s.ticker == "AAPL"
            assert s.ranking == 50
