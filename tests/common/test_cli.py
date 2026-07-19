"""Tests for CLI argument type helpers."""

import argparse
from datetime import date

import pytest

from turtlex.common.cli import iso_date_type


def test_valid_iso_date_is_parsed() -> None:
    assert iso_date_type("2024-06-01") == date(2024, 6, 1)


def test_invalid_date_raises_argument_type_error() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="06/01/2024"):
        iso_date_type("06/01/2024")
