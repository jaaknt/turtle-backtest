from dataclasses import dataclass
# from typing import Optional


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
    symbol_group (str): group (NASDAQ100, NASQAQ, ...) where the symbol belongs
    rate (float): rate of the symbol in the group
    """

    symbol_group: str
    symbol: str
    rate: float
