"""Test TA-Lib EMA calculations for accuracy."""

import numpy as np
import pandas as pd
import talib


def calculate_ema_manual(prices: list[float], period: int) -> list[float]:
    """
    Calculate EMA manually using the standard formula.

    EMA formula:
    - Multiplier = 2 / (period + 1)
    - EMA[today] = (Price[today] * Multiplier) + (EMA[yesterday] * (1 - Multiplier))

    Args:
        prices: List of price values
        period: EMA period (e.g., 10 for EMA-10)

    Returns:
        List of EMA values with NaN for initial values where calculation isn't possible
    """
    if len(prices) < period:
        return [np.nan] * len(prices)

    multiplier = 2.0 / (period + 1)
    ema_values = [np.nan] * len(prices)

    # Start with SMA for the first EMA value
    sma_start = sum(prices[:period]) / period
    ema_values[period - 1] = sma_start

    # Calculate subsequent EMA values
    for i in range(period, len(prices)):
        ema_values[i] = (prices[i] * multiplier) + (ema_values[i - 1] * (1 - multiplier))

    return ema_values


def test_ema_10_calculation_accuracy() -> None:
    """Test that TA-Lib EMA-10 calculation matches manual calculation."""
    # Test data - using realistic stock price data
    test_prices = [
        100.0, 101.5, 99.8, 102.3, 104.1, 103.7, 105.2, 106.8, 105.9, 107.1,
        108.3, 107.5, 109.2, 110.8, 109.4, 111.2, 112.6, 111.8, 113.4, 114.9,
        113.7, 115.3, 116.8, 115.2, 117.1, 118.4, 117.6, 119.2, 120.5, 119.8
    ]

    # Calculate EMA using TA-Lib
    talib_ema = talib.EMA(np.array(test_prices, dtype=float), timeperiod=10)

    # Calculate EMA manually
    manual_ema = calculate_ema_manual(test_prices, 10)

    # Compare results (ignoring NaN values)
    tolerance = 1e-10  # Very tight tolerance for numerical precision

    for i, (talib_val, manual_val) in enumerate(zip(talib_ema, manual_ema, strict=True)):
        if not np.isnan(manual_val):  # Only compare valid values
            assert not np.isnan(talib_val), f"TA-Lib returned NaN at index {i}"
            assert abs(talib_val - manual_val) < tolerance, (
                f"EMA mismatch at index {i}: TA-Lib={talib_val:.10f}, "
                f"Manual={manual_val:.10f}, diff={abs(talib_val - manual_val):.2e}"
            )


def test_ema_10_with_minimal_data() -> None:
    """Test EMA-10 calculation with exactly 10 data points."""
    # Minimal test case with exactly 10 prices
    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]

    talib_ema = talib.EMA(np.array(prices, dtype=float), timeperiod=10)
    manual_ema = calculate_ema_manual(prices, 10)

    # Should have exactly one valid EMA value (at index 9)
    assert sum(~np.isnan(talib_ema)) == 1, "Should have exactly one valid EMA value"
    assert sum(not np.isnan(val) for val in manual_ema) == 1, "Manual calculation should match"

    # Compare the single valid value
    valid_idx = 9
    tolerance = 1e-10
    assert abs(talib_ema[valid_idx] - manual_ema[valid_idx]) < tolerance


def test_ema_10_with_insufficient_data() -> None:
    """Test EMA-10 behavior with less than 10 data points."""
    # Test with insufficient data
    prices = [100.0, 101.0, 102.0, 103.0, 104.0]  # Only 5 prices

    talib_ema = talib.EMA(np.array(prices, dtype=float), timeperiod=10)
    manual_ema = calculate_ema_manual(prices, 10)

    # All values should be NaN
    assert all(np.isnan(talib_ema)), "All TA-Lib EMA values should be NaN with insufficient data"
    assert all(np.isnan(val) for val in manual_ema), "All manual EMA values should be NaN with insufficient data"


def test_ema_10_edge_cases() -> None:
    """Test EMA-10 with edge cases like constant prices and large price jumps."""
    # Test with constant prices
    constant_prices = [100.0] * 15
    talib_ema_constant = talib.EMA(np.array(constant_prices, dtype=float), timeperiod=10)

    # After warmup period, EMA should converge to the constant value
    valid_values = talib_ema_constant[~np.isnan(talib_ema_constant)]
    assert all(abs(val - 100.0) < 1e-10 for val in valid_values), "EMA of constant prices should equal the constant"

    # Test with large price jump
    jump_prices = [100.0] * 10 + [200.0] * 10  # Price doubles suddenly
    talib_ema_jump = talib.EMA(np.array(jump_prices, dtype=float), timeperiod=10)

    # EMA should gradually adjust toward new price level
    assert talib_ema_jump[9] < talib_ema_jump[19], "EMA should increase after price jump"
    assert talib_ema_jump[19] < 200.0, "EMA should lag behind sudden price increase"
    assert talib_ema_jump[19] > 100.0, "EMA should move toward new price level"


def test_ema_10_integration_with_pandas() -> None:
    """Test EMA-10 calculation within a pandas DataFrame context similar to strategy usage."""
    # Create test DataFrame similar to strategy usage
    close_prices = [100.0, 101.5, 99.8, 102.3, 104.1, 103.7, 105.2, 106.8, 105.9, 107.1,
                    108.3, 107.5, 109.2, 110.8, 109.4, 111.2, 112.6, 111.8, 113.4, 114.9]
    test_data = {
        'close': close_prices,
        'volume': [1000] * 20
    }
    df = pd.DataFrame(test_data)

    # Calculate EMA the same way as in strategies
    close_values = df["close"].values.astype(float)
    df["ema_10"] = talib.EMA(close_values, timeperiod=10)

    # Verify results
    manual_ema = calculate_ema_manual(close_prices, 10)
    tolerance = 1e-10

    for i, (df_val, manual_val) in enumerate(zip(df["ema_10"], manual_ema, strict=True)):
        if not np.isnan(manual_val):
            assert not np.isnan(df_val), f"DataFrame EMA is NaN at index {i}"
            assert abs(df_val - manual_val) < tolerance, (
                f"DataFrame EMA mismatch at index {i}: DataFrame={df_val:.10f}, "
                f"Manual={manual_val:.10f}"
            )

