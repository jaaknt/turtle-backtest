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
