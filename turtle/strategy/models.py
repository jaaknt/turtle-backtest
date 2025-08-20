from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    """Ticker signals
     
    Attributes:
        ticker (str): Stock symbol code
        date (datetime): Date when the signal was generated
    """

    ticker: str
    date: datetime