from pydantic import BaseModel, Field


class Exchange(BaseModel):
    """Represents a stock exchange from EODHD."""

    name: str = Field(..., alias="Name")
    code: str = Field(..., alias="Code")
    country: str = Field(..., alias="Country")
    currency: str = Field(..., alias="Currency")
    country_iso3: str | None = Field(default=None, alias="CountryISO3")
