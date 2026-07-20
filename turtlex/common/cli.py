"""CLI argument type helpers."""

import argparse
from datetime import date


def iso_date_type(date_string: str) -> date:
    """Custom argparse type for ISO date validation (YYYY-MM-DD)."""
    try:
        return date.fromisoformat(date_string)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Expected ISO format (YYYY-MM-DD)") from err


def key_value_type(value: str) -> tuple[str, str]:
    """Custom argparse type for a single 'KEY=VALUE' token (e.g. --exit-param profit_target=15)."""
    key, sep, val = value.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError(f"Expected KEY=VALUE, got '{value}'")
    return key, val
