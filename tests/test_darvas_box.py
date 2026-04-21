import warnings
from datetime import date, datetime, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.momentum import MomentumRanking
from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
from unittest.mock import MagicMock

import pandas as pd
import polars as pl

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")


def test_check_local_max() -> None:
    series = pd.Series([1, 2, 3, 10, 3, 2, 1])
    assert DarvasBoxStrategy.check_local_max(0, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(1, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(2, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(3, series, 3, 3) is True
    assert DarvasBoxStrategy.check_local_max(4, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(5, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(6, series, 3, 3) is False


def test_check_local_min() -> None:
    series = pd.Series([10, 9, 8, 7, 1, 7, 8, 9, 10])
    assert DarvasBoxStrategy.check_local_min(0, series, 2) is False
    assert DarvasBoxStrategy.check_local_min(1, series, 2) is False
    assert DarvasBoxStrategy.check_local_min(2, series, 2) is False
    assert DarvasBoxStrategy.check_local_min(3, series, 2) is False
    assert DarvasBoxStrategy.check_local_min(4, series, 2) is True
    assert DarvasBoxStrategy.check_local_min(5, series, 2) is True
    assert DarvasBoxStrategy.check_local_min(6, series, 2) is True
    assert DarvasBoxStrategy.check_local_min(7, series, 2) is False
    assert DarvasBoxStrategy.check_local_min(8, series, 2) is False


def test_collect() -> None:
    bars_history_mock = MagicMock(spec=OhlcvAnalyticsRepository)
    ranking_strategy_mock = MagicMock(spec=MomentumRanking)
    strategy = DarvasBoxStrategy(bars_history_mock, ranking_strategy_mock, warmup_period=3, min_bars=3)

    bars_history_mock.get_bars_pl.return_value = pl.DataFrame(
        {
            "date": [date.today()] * 10,
            "close": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "open": [0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "volume": [0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 15.0],
        }
    )

    assert strategy.collect_data("AAPL", date.today(), date.today()) is True
    assert not strategy.pl_df.is_empty()

    # Test with insufficient data
    bars_history_mock.get_bars_pl.return_value = pl.DataFrame(
        {"date": [date.today(), date.today()], "close": [1.0, 2.0]}
    )
    assert strategy.collect_data("GOOG", date.today(), date.today()) is False


def test_calculate_indicators() -> None:
    bars_history_mock = MagicMock(spec=OhlcvAnalyticsRepository)
    ranking_strategy_mock = MagicMock(spec=MomentumRanking)
    strategy = DarvasBoxStrategy(bars_history_mock, ranking_strategy_mock, warmup_period=3, min_bars=3)

    n = 35
    base_date = date(2024, 1, 1)
    strategy.pl_df = pl.DataFrame(
        {
            "date": [base_date + timedelta(days=i) for i in range(n)],
            "close": [float(i) for i in range(1, n + 1)],
            "open": [0.0] + [float(i) for i in range(1, n)],
            "high": [float(i) for i in range(2, n + 2)],
            "low": [0.0] + [float(i) for i in range(1, n)],
            "volume": [1.0] * (n - 1) + [15.0],
        }
    )
    strategy.calculate_indicators_pl()

    expected_columns = [
        "max_close_20",
        "ema_10",
        "ema_20",
        "ema_50",
        "ema_200",
        "ema_volume_10",
    ]
    for column in expected_columns:
        assert column in strategy.pl_df.columns
    assert strategy.pl_df["ema_10"][-1] is not None
    assert strategy.pl_df["max_close_20"][-1] is not None


def test_is_local_max_valid() -> None:
    df = pd.DataFrame(
        {
            "high": [1, 2, 3, 10, 3, 2, 1, 5, 6, 7, 8, 9, 10],
            "is_local_min": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
            ],
        }
    )

    # Test when local max is valid
    assert DarvasBoxStrategy.is_local_max_valid(df, 10, 3) is True

    # Test when local max is invalid due to a higher high in the following rows
    df_invalid = df.copy()
    df_invalid.loc[8, "high"] = 11
    assert DarvasBoxStrategy.is_local_max_valid(df_invalid, 10, 3) is False

    # Test when local max is valid due to no local min within the following count
    df_no_min = df.copy()
    df_no_min["is_local_min"] = False
    assert DarvasBoxStrategy.is_local_max_valid(df_no_min, 10, 3) is True

    # Test when local max is valid with different following count
    assert DarvasBoxStrategy.is_local_max_valid(df, 10, 5) is True


def test_price_to_ranking() -> None:
    """Test the price to ranking conversion logic."""
    ranking_strategy = MomentumRanking()

    # Test each price range
    assert ranking_strategy._price_to_ranking(5.0) == 20  # $0-10 range
    assert ranking_strategy._price_to_ranking(10.0) == 20  # Boundary: exactly $10
    assert ranking_strategy._price_to_ranking(15.0) == 16  # $10-20 range
    assert ranking_strategy._price_to_ranking(20.0) == 16  # Boundary: exactly $20
    assert ranking_strategy._price_to_ranking(40.0) == 12  # $20-60 range
    assert ranking_strategy._price_to_ranking(60.0) == 12  # Boundary: exactly $60
    assert ranking_strategy._price_to_ranking(150.0) == 8  # $60-240 range
    assert ranking_strategy._price_to_ranking(240.0) == 8  # Boundary: exactly $240
    assert ranking_strategy._price_to_ranking(500.0) == 4  # $240-1000 range
    assert ranking_strategy._price_to_ranking(1000.0) == 4  # Boundary: exactly $1000
    assert ranking_strategy._price_to_ranking(1500.0) == 1  # >$1000 range

    # Test edge cases
    assert ranking_strategy._price_to_ranking(0.0) == 1  # Zero price
    assert ranking_strategy._price_to_ranking(-10.0) == 1  # Negative price


def test_ranking() -> None:
    """Test the ranking method with mock data."""
    test_date = datetime(2024, 1, 15)

    # Test case 1: Stock with $50 price (should return rank 12 for price component only)
    mock_df = pl.DataFrame(
        {
            "date": [test_date.date()],
            "close": [50.0],
            "open": [49.0],
            "high": [51.0],
            "low": [48.0],
            "volume": [1000000],
            "ema_10": [50.0],
            "ema_20": [50.0],
            "ema_50": [50.0],
            "ema_200": [50.0],
        }
    )

    ranking_strategy = MomentumRanking()
    ranking = ranking_strategy.ranking(mock_df, test_date)
    assert ranking == 12  # Only price ranking since no historical data for EMA trends

    # Test case 2: High-priced stock (should return rank 1)
    mock_df_expensive = pl.DataFrame(
        {
            "date": [test_date.date()],
            "close": [1500.0],
            "open": [1480.0],
            "high": [1520.0],
            "low": [1470.0],
            "volume": [500000],
            "ema_10": [1500.0],
            "ema_20": [1500.0],
            "ema_50": [1500.0],
            "ema_200": [1500.0],
        }
    )

    ranking_strategy = MomentumRanking()
    ranking = ranking_strategy.ranking(mock_df_expensive, test_date)
    assert ranking == 1

    # Test case 3: Low-priced stock (should return rank 20 for price component)
    mock_df_cheap = pl.DataFrame(
        {
            "date": [test_date.date()],
            "close": [8.50],
            "open": [8.20],
            "high": [8.80],
            "low": [8.10],
            "volume": [2000000],
            "ema_10": [8.50],
            "ema_20": [8.50],
            "ema_50": [8.50],
            "ema_200": [8.50],
        }
    )

    ranking_strategy = MomentumRanking()
    ranking = ranking_strategy.ranking(mock_df_cheap, test_date)
    assert ranking == 20


def test_get_polars_signals_returns_empty_on_downtrend() -> None:
    """_get_polars_signals returns [] when prices are declining (no buy conditions met)."""
    n = 100
    base = 100.0
    closes = [base - i * 0.5 for i in range(n)]
    opens = [c * 1.01 for c in closes]  # bearish bodies
    highs = [c * 1.02 for c in closes]
    lows = [c * 0.98 for c in closes]
    start = date(2020, 1, 2)
    pl_df = pl.DataFrame({
        "date": [start + timedelta(days=i) for i in range(n)],
        "open": opens, "high": highs, "low": lows, "close": closes,
        "volume": [1_000_000.0] * n,
    })

    mock_repo = MagicMock(spec=OhlcvAnalyticsRepository)
    mock_repo.get_bars_pl.return_value = pl_df
    mock_ranking = MagicMock(spec=MomentumRanking)

    strategy = DarvasBoxStrategy(
        mock_repo, mock_ranking,
        time_frame_unit=TimeFrameUnit.WEEK,
        warmup_period=10, min_bars=10,
    )
    last_date = pl_df["date"][-1]
    assert strategy.get_signals("TEST", last_date, last_date) == []


def test_get_polars_signals_produces_signal() -> None:
    """_get_polars_signals produces at least one signal on consistently uptrending data."""
    n = 150
    base, growth = 100.0, 1.006
    closes = [base * (growth**i) for i in range(n)]
    opens = [c * 0.99 for c in closes]    # 1% bullish body → (close-open)/close ≈ 1% > 0.8% ✓
    highs = [c * 1.01 for c in closes]
    lows = [c * 0.98 for c in closes]
    volumes = [1_000_000.0] * n
    volumes[-1] = 1_600_000.0             # last bar: 1.6× EMA ≥ 1.1× ✓
    start = date(2020, 1, 2)
    pl_df = pl.DataFrame({
        "date": [start + timedelta(days=i) for i in range(n)],
        "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes,
    })

    mock_repo = MagicMock(spec=OhlcvAnalyticsRepository)
    mock_repo.get_bars_pl.return_value = pl_df
    mock_ranking = MagicMock(spec=MomentumRanking)
    mock_ranking.ranking.return_value = 8

    strategy = DarvasBoxStrategy(
        mock_repo, mock_ranking,
        time_frame_unit=TimeFrameUnit.WEEK,  # skip EMA-200 condition
        warmup_period=100, min_bars=100,
    )
    last_date = pl_df["date"][-1]
    signals = strategy.get_signals("TEST", last_date, last_date)
    assert len(signals) >= 1
