"""
SQLAlchemy Core table definitions for database operations.

This module contains Table objects used for all database operations
in the repository layer.
"""

from sqlalchemy import BigInteger, Column, DateTime, MetaData, Numeric, Table, Text, func

# Shared metadata instance for all table definitions
metadata = MetaData()

# bars_history table definition
bars_history_table = Table(
    "bars_history",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("hdate", DateTime(timezone=True), primary_key=True),
    Column("open", Numeric(10, 4)),
    Column("high", Numeric(10, 4)),
    Column("low", Numeric(10, 4)),
    Column("close", Numeric(10, 4)),
    Column("volume", BigInteger),
    Column("trade_count", BigInteger),
    Column("source", Text),
    Column("modified_at", DateTime, server_default=func.now()),
    schema="turtle",
)

# ticker table definition
ticker_table = Table(
    "ticker",
    metadata,
    Column("unique_symbol", Text, primary_key=True),
    Column("exchange_symbol", Text),
    Column("name", Text),
    Column("exchange", Text),
    Column("country", Text),
    Column("currency", Text),
    Column("isin", Text),
    Column("type", Text),
    Column("updated_at", DateTime, server_default=func.now()),
    schema="turtle",
)

# company table definition
company_table = Table(
    "company",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("short_name", Text),
    Column("country", Text),
    Column("industry_code", Text),
    Column("sector_code", Text),
    Column("employees_count", BigInteger),
    Column("dividend_rate", Numeric),
    Column("trailing_pe_ratio", Numeric),
    Column("forward_pe_ratio", Numeric),
    Column("avg_volume", BigInteger),
    Column("avg_price", Numeric),
    Column("market_cap", Numeric),
    Column("enterprice_value", Numeric),
    Column("beta", Numeric),
    Column("shares_float", Numeric),
    Column("short_ratio", Numeric),
    Column("peg_ratio", Numeric),
    Column("recommodation_mean", Numeric),
    Column("number_of_analysyst", BigInteger),
    Column("roa_value", Numeric),
    Column("roe_value", Numeric),
    Column("source", Text),
    Column("modified_at", DateTime, server_default=func.now()),
    schema="turtle",
)

# symbol_group table definition
symbol_group_table = Table(
    "symbol_group",
    metadata,
    Column("symbol_group", Text, primary_key=True),
    Column("symbol", Text, primary_key=True),
    Column("rate", Numeric),
    Column("modified_at", DateTime, server_default=func.now()),
    schema="turtle",
)

# exchange table definition (EODHD)
exchange_table = Table(
    "exchange",
    metadata,
    Column("code", Text, primary_key=True),
    Column("name", Text),
    Column("country", Text),
    Column("currency", Text),
    Column("country_iso3", Text),
    Column("modified_at", DateTime, server_default=func.now()),
    schema="turtle",
)

# price_history table definition (EODHD)
price_history_table = Table(
    "price_history",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("time", DateTime(timezone=True), primary_key=True),
    Column("open", Numeric(10, 4)),
    Column("high", Numeric(10, 4)),
    Column("low", Numeric(10, 4)),
    Column("close", Numeric(10, 4)),
    Column("adjusted_close", Numeric(10, 4)),
    Column("volume", BigInteger),
    Column("source", Text),
    Column("modified_at", DateTime, server_default=func.now()),
    schema="turtle",
)

# ticker_extended table definition (EODHD extended quote data)
ticker_extended_table = Table(
    "ticker_extended",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("type", Text),
    Column("name", Text),
    Column("sector", Text),
    Column("industry", Text),
    Column("average_volume", BigInteger),
    Column("average_price", Numeric),
    Column("dividend_yield", Numeric),
    Column("market_cap", BigInteger),
    Column("pe", Numeric),
    Column("forward_pe", Numeric),
    Column("modified_at", DateTime, server_default=func.now()),
    schema="turtle",
)
