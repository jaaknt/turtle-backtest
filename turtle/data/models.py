from dataclasses import dataclass


@dataclass
class Symbol:
    symbol: str
    name: str
    exchange: str
    country: str
