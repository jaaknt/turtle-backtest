from dataclasses import dataclass


@dataclass
class SymbolGroup:
    """Stock symbol groups

    Attributes:
    code (str): group (NAS100, ...) where the symbol belongs
    ticker_code (str): symbol code in stock exchange
    rate (float): rate of the symbol in the group
    """

    code: str
    ticker_code: str
    rate: float
