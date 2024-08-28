import pytest

from turtle.data.models import Symbol


def test_symbol_dataclass():
    symbol_rec = Symbol("AAPL", "Apple", "NASDAQ", "USA")
    assert symbol_rec.symbol == "AAPL"
    assert symbol_rec.name == "Apple"
    assert symbol_rec.exchange == "NASDAQ"
    assert symbol_rec.country == "USA"
