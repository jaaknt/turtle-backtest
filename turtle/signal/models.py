from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    """Ticker signals

    Attributes:
        ticker (str): Stock symbol code
        date (datetime): Date when the signal was generated
        ranking (int): Ranking score of the signal (1-100)
    """

    ticker: str
    date: datetime
    ranking: int
