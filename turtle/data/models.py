from dataclasses import dataclass


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
