from turtle.data.models import Symbol
from turtle.data.models import Company


def test_symbol_instantiation():
    symbol_rec = Symbol("AAPL", "Apple", "NASDAQ", "USA")
    assert symbol_rec.symbol == "AAPL"
    assert symbol_rec.name == "Apple"
    assert symbol_rec.exchange == "NASDAQ"
    assert symbol_rec.country == "USA"


def test_company_instantiation():
    # Instantiate the Company dataclass
    company = Company(
        symbol="AAPL",
        short_name="Apple Inc.",
        country="USA",
        industry_code="5020",
        sector_code="4500",
        employees_count=147000,
        dividend_rate=0.82,
        market_cap=2.4e12,
        enterprice_value=2.3e12,
        beta=1.20,
        shares_float=16.6e9,
        short_ratio=0.8,
        recommodation_mean=1.5,
    )
    # Assert that the dataclass was instantiated correctly
    assert company.symbol == "AAPL"
    assert company.short_name == "Apple Inc."
    assert company.country == "USA"
    assert company.industry_code == "5020"
    assert company.sector_code == "4500"
    assert company.employees_count == 147000
    assert company.dividend_rate == 0.82
    assert company.market_cap == 2.4e12
    assert company.enterprice_value == 2.3e12
    assert company.beta == 1.20
    assert company.shares_float == 16.6e9
    assert company.short_ratio == 0.8
    assert company.recommodation_mean == 1.5


def test_company_field_types():
    # Instantiate with correct types
    company = Company(
        symbol="AAPL",
        short_name="Apple Inc.",
        country="USA",
        industry_code="5020",
        sector_code="4500",
        employees_count=147000,
        dividend_rate=0.82,
        market_cap=2.4e12,
        enterprice_value=2.3e12,
        beta=1.20,
        shares_float=16.6e9,
        short_ratio=0.8,
        recommodation_mean=1.5,
    )

    # Test that each field is of the correct type
    assert isinstance(company.symbol, str)
    assert isinstance(company.short_name, str)
    assert isinstance(company.country, str)
    assert isinstance(company.industry_code, str)
    assert isinstance(company.sector_code, str)
    assert isinstance(company.employees_count, int)
    assert isinstance(company.dividend_rate, float)
    assert isinstance(company.market_cap, float)
    assert isinstance(company.enterprice_value, float)
    assert isinstance(company.beta, float)
    assert isinstance(company.shares_float, float)
    assert isinstance(company.short_ratio, float)
    assert isinstance(company.recommodation_mean, float)
