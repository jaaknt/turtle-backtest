from pydantic import BaseModel


class PriceHistory(BaseModel):
    """Represents one historical price data point (EOD) from EODHD."""

    ticker: str
    date: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
