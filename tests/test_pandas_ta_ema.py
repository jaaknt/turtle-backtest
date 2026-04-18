"""Test pandas-ta EMA calculations for accuracy."""

import numpy as np
import pandas as pd
import pandas_ta


def calculate_ema_sma_seeded(prices: list[float], period: int) -> list[float]:
    """
    Calculate EMA using SMA as the initial seed (matches pandas-ta implementation).

    pandas-ta seeds EMA with the SMA of the first `period` values, then applies:
    EMA[t] = price[t] * alpha + EMA[t-1] * (1 - alpha)
    where alpha = 2 / (period + 1).

    Args:
        prices: List of price values
        period: EMA period (e.g., 10 for EMA-10)

    Returns:
        List of EMA values with NaN for initial warmup period
    """
    alpha = 2 / (period + 1)
    result = [float("nan")] * len(prices)
    if len(prices) < period:
        return result
    result[period - 1] = sum(prices[:period]) / period
    for i in range(period, len(prices)):
        result[i] = prices[i] * alpha + result[i - 1] * (1 - alpha)
    return result


def test_ema_10_matches_pandas_ewm() -> None:
    """Test that pandas-ta EMA-10 matches the SMA-seeded EMA calculation."""
    test_prices = [
        100.0,
        101.5,
        99.8,
        102.3,
        104.1,
        103.7,
        105.2,
        106.8,
        105.9,
        107.1,
        108.3,
        107.5,
        109.2,
        110.8,
        109.4,
        111.2,
        112.6,
        111.8,
        113.4,
        114.9,
        113.7,
        115.3,
        116.8,
        115.2,
        117.1,
        118.4,
        117.6,
        119.2,
        120.5,
        119.8,
    ]

    pandas_ta_ema = pandas_ta.ema(pd.Series(test_prices), length=10)
    expected_ema = calculate_ema_sma_seeded(test_prices, 10)

    tolerance = 1e-10
    for i, (ta_val, expected_val) in enumerate(zip(pandas_ta_ema, expected_ema, strict=True)):
        if not np.isnan(expected_val):
            assert not np.isnan(ta_val), f"pandas-ta returned NaN at index {i}"
            assert abs(ta_val - expected_val) < tolerance, (
                f"EMA mismatch at index {i}: pandas-ta={ta_val:.10f}, expected={expected_val:.10f}, diff={abs(ta_val - expected_val):.2e}"
            )


def test_ema_10_with_minimal_data() -> None:
    """Test EMA-10 calculation with exactly 10 data points."""
    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]

    result = pandas_ta.ema(pd.Series(prices), length=10)

    # Should have exactly one valid EMA value (at index 9)
    valid_count = result.notna().sum()
    assert valid_count == 1, f"Should have exactly one valid EMA value, got {valid_count}"

    # First 9 should be NaN
    assert all(np.isnan(result.iloc[i]) for i in range(9)), "First 9 values should be NaN"
    assert not np.isnan(result.iloc[9]), "Last value should be valid"


def test_ema_10_with_insufficient_data() -> None:
    """Test EMA-10 behavior with less than 10 data points."""
    prices = [100.0, 101.0, 102.0, 103.0, 104.0]  # Only 5 prices

    result = pandas_ta.ema(pd.Series(prices), length=10)

    # pandas-ta returns None when there is insufficient data to compute the indicator
    assert result is None, "pandas-ta returns None when data length < period"


def test_ema_10_edge_cases() -> None:
    """Test EMA-10 with constant prices and large price jumps."""
    # Test with constant prices - EMA should equal the constant
    constant_prices = [100.0] * 15
    result_constant = pandas_ta.ema(pd.Series(constant_prices), length=10)

    valid_values = result_constant.dropna()
    assert len(valid_values) > 0, "Should have valid EMA values"
    assert all(abs(val - 100.0) < 1e-10 for val in valid_values), "EMA of constant prices should equal the constant"

    # Test with price jump - EMA should trend toward new level
    jump_prices = [100.0] * 10 + [200.0] * 10
    result_jump = pandas_ta.ema(pd.Series(jump_prices), length=10)

    assert result_jump.iloc[9] < result_jump.iloc[19], "EMA should increase after price jump"
    assert result_jump.iloc[19] < 200.0, "EMA should lag behind sudden price increase"
    assert result_jump.iloc[19] > 100.0, "EMA should move toward new price level"


def test_ema_10_integration_with_pandas() -> None:
    """Test EMA-10 calculation within a pandas DataFrame context similar to strategy usage."""
    close_prices = [
        100.0,
        101.5,
        99.8,
        102.3,
        104.1,
        103.7,
        105.2,
        106.8,
        105.9,
        107.1,
        108.3,
        107.5,
        109.2,
        110.8,
        109.4,
        111.2,
        112.6,
        111.8,
        113.4,
        114.9,
    ]
    df = pd.DataFrame({"close": close_prices, "volume": [1000] * 20})

    # Calculate EMA the same way as in strategies
    df["ema_10"] = pandas_ta.ema(df["close"], length=10)

    # First 9 values should be NaN
    assert df["ema_10"].iloc[:9].isna().all(), "First 9 EMA values should be NaN"

    # Remaining values should be valid floats
    valid = df["ema_10"].iloc[9:]
    assert valid.notna().all(), "EMA values from index 9 onward should be valid"
    assert (valid > 0).all(), "All valid EMA values should be positive"
