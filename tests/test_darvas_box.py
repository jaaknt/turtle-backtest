import pandas as pd
import warnings
from unittest.mock import MagicMock
from datetime import datetime

from turtle.strategy.darvas_box import DarvasBoxStrategy
from turtle.data.bars_history import BarsHistoryRepo

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module="pkg_resources"
    )


def test_check_local_max():
    series = pd.Series([1, 2, 3, 10, 3, 2, 1])
    assert DarvasBoxStrategy.check_local_max(0, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(1, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(2, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(3, series, 3, 3) is True
    assert DarvasBoxStrategy.check_local_max(4, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(5, series, 3, 3) is False
    assert DarvasBoxStrategy.check_local_max(6, series, 3, 3) is False


def test_check_local_min():
    series = pd.Series([10, 9, 8, 1, 8, 9, 10])
    assert DarvasBoxStrategy.check_local_min(0, series, 3) is False
    assert DarvasBoxStrategy.check_local_min(1, series, 3) is False
    assert DarvasBoxStrategy.check_local_min(2, series, 3) is False
    assert DarvasBoxStrategy.check_local_min(3, series, 3) is True
    assert DarvasBoxStrategy.check_local_min(4, series, 3) is False
    assert DarvasBoxStrategy.check_local_min(5, series, 3) is False
    assert DarvasBoxStrategy.check_local_min(6, series, 3) is False


def test_collect():
    bars_history_mock = MagicMock(spec=BarsHistoryRepo)
    strategy = DarvasBoxStrategy(bars_history_mock, period_length=10, min_bars=3)

    # Mock the return value of get_ticker_history
    bars_history_mock.get_ticker_history.return_value = pd.DataFrame(
        {"close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
    )

    assert strategy.collect("AAPL", datetime.now()) is True
    assert not strategy.df.empty
    assert "max_close_20" in strategy.df.columns
    assert "ema_10" in strategy.df.columns
    assert "ema_20" in strategy.df.columns
    assert "ema_50" in strategy.df.columns

    # Test with insufficient data
    bars_history_mock.get_ticker_history.return_value = pd.DataFrame({"close": [1, 2]})
    assert strategy.collect("AAPL", datetime.now()) is False


def test_is_local_max_valid():
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
