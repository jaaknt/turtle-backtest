from pydantic import BaseModel, Field


class Ticker(BaseModel):
    """Represents a stock ticker from EODHD."""

    code: str = Field(..., alias="Code")
    name: str = Field(..., alias="Name")
    country: str = Field(..., alias="Country")
    exchange: str = Field(..., alias="Exchange")
    currency: str = Field(..., alias="Currency")
    type: str = Field(..., alias="Type")
    isin: str | None = Field(default=None, alias="Isin")
