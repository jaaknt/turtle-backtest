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
    Column("symbol", Text, primary_key=True),
    Column("name", Text),
    Column("exchange", Text),
    Column("country", Text),
    Column("currency", Text),
    Column("isin", Text),
    Column("symbol_type", Text),
    Column("source", Text),
    Column("status", Text),
    Column("modified_at", DateTime, server_default=func.now()),
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
