from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


@dataclass
class Symbol:
    """Stock exchange symbol details

    Attributes:
    symbol (str): symbol code in stock exchange
    name (str): stock/etf/... name
    exchange (str): exchange code
    country (str): exchange country (can be different from company country)
    """

    symbol: str
    name: str
    exchange: str
    country: str


@dataclass
class Company:
    """Company data

    Attributes:
    symbol (str): symbol code in stock exchange
    short_name (str): stock/etf/... name
    country (str): company country
    industry_code (str):
    sector_code (str):
    employees_count (int):
    dividend_rate (float):
    market_cap (float):
    enterprice_value (float):
    beta (float):
    shares_float (float):
    short_ratio: (float):
    recommodation_mean (float):
    """



    symbol: str
    short_name: str
    country: str
    industry_code: str
    sector_code: str
    employees_count: int
    dividend_rate: float
    market_cap: float
    enterprice_value: float
    beta: float
    shares_float: float
    short_ratio: float
    recommodation_mean: float


@dataclass
class Bar:
    """Bar data

    Attributes:
    """

    hdate: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int


@dataclass
class SymbolGroup:
    """Stock symbol groups

    Attributes:
    symbol (str): symbol code in stock exchange
    symbol_group (str): group (NAS100, ...) where the symbol belongs
    rate (float): rate of the symbol in the group
    """

    symbol_group: str
    symbol: str
    rate: float


class Exchange(BaseModel):
    """Represents a stock exchange from EODHD."""

    name: str = Field(..., alias='Name')
    code: str = Field(..., alias='Code')
    country: str = Field(..., alias='Country')
    currency: str = Field(..., alias='Currency')
    country_iso3: str | None = Field(default=None, alias='CountryISO3')


class Ticker(BaseModel):
    """Represents a stock ticker from EODHD."""

    code: str = Field(..., alias='Code')
    name: str = Field(..., alias='Name')
    country: str = Field(..., alias='Country')
    exchange: str = Field(..., alias='Exchange')
    currency: str = Field(..., alias='Currency')
    type: str = Field(..., alias='Type')
    isin: str | None = Field(default=None, alias='Isin')


class PriceHistory(BaseModel):
    """Represents one historical price data point (EOD) from EODHD."""

    ticker: str
    date: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int


class TickerExtended(BaseModel):
    """Represents extended ticker information from EODHD US quote delayed API."""

    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    type: str | None = Field(default=None, alias='type')
    name: str | None = Field(default=None, alias='name')
    sector: str | None = Field(default=None, alias='sector')
    industry: str | None = Field(default=None, alias='industry')
    average_volume: int | None = Field(default=None, alias='averageVolume')
    fifty_day_average_price: float | None = Field(default=None, alias='fiftyDayAveragePrice')
    dividend_yield: float | None = Field(default=None, alias='dividendYield')
    market_cap: int | None = Field(default=None, alias='marketCap')
    pe: float | None = Field(default=None, alias='pe')
    forward_pe: float | None = Field(default=None, alias='forwardPE')
