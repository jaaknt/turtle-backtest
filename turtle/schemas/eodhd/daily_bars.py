from datetime import date

from pydantic import BaseModel


class DailyBars(BaseModel):
    """Represents one EOD daily bar from EODHD."""

    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
