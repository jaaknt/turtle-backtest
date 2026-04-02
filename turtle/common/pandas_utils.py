"""Pandas type-coercion utilities."""

from typing import Any


def safe_float_conversion(value: Any) -> float:
    """
    Safely convert pandas Series elements or scalar values to float.

    Handles the type ambiguity that Pylance detects when accessing
    pandas DataFrame elements that could return Series[Any] or scalar values.

    Args:
        value: Value from pandas DataFrame that could be scalar or Series

    Returns:
        float: Converted float value

    Raises:
        ValueError: If value cannot be converted to float
    """
    if hasattr(value, "iloc") and hasattr(value, "dtype"):
        return float(value.iloc[0])
    elif hasattr(value, "item") and not isinstance(value, int | float):
        return float(value.item())
    else:
        return float(value)
