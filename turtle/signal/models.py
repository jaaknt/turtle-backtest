from dataclasses import dataclass
from datetime import date


@dataclass
class Signal:
    """Ticker signals

    Attributes:
        ticker (str): Stock symbol code
        date (date): Date when the signal was generated
        ranking (int): Ranking score of the signal (1-100)
    """

    ticker: str
    date: date
    ranking: int
