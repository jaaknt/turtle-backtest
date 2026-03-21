from dataclasses import dataclass


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
