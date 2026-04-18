"""
SQLAlchemy Core table definitions for database operations.

This module contains Table objects used for all database operations
in the repository layer.
"""

from sqlalchemy import BigInteger, Column, Date, Float, MetaData, Numeric, Table, Text
from sqlalchemy.dialects.postgresql import ENUM

# Shared metadata instance for all table definitions
metadata = MetaData()

# PostgreSQL enum types (already created by migrations, create_type=False)
ticker_status_type = ENUM("active", "inactive", name="ticker_status", schema="turtle", create_type=False)
data_source_type = ENUM("eodhd", "alpaca", "yahoo", name="data_source_type", schema="turtle", create_type=False)

# daily_bars table definition
daily_bars_table = Table(
    "daily_bars",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("date", Date, primary_key=True),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("adjusted_close", Float),
    Column("volume", BigInteger),
    Column("source", data_source_type),
    schema="turtle",
)

# ticker table definition
ticker_table = Table(
    "ticker",
    metadata,
    Column("code", Text, primary_key=True),
    Column("exchange_code", Text),
    Column("name", Text),
    Column("country", Text),
    Column("exchange", Text),
    Column("currency", Text),
    Column("type", Text),
    Column("isin", Text),
    Column("status", ticker_status_type),
    Column("source", data_source_type),
    schema="turtle",
)

# company table definition
company_table = Table(
    "company",
    metadata,
    Column("ticker_code", Text, primary_key=True),
    Column("type", Text),
    Column("name", Text),
    Column("sector", Text),
    Column("industry", Text),
    Column("average_volume", BigInteger),
    Column("average_price", Numeric(20, 2)),
    Column("dividend_yield", Numeric(12, 2)),
    Column("market_cap", BigInteger),
    Column("pe", Numeric(12, 2)),
    Column("forward_pe", Numeric(12, 2)),
    schema="turtle",
)

# ticker_group table definition
ticker_group_table = Table(
    "ticker_group",
    metadata,
    Column("code", Text, primary_key=True),
    Column("ticker_code", Text, primary_key=True),
    Column("rate", Numeric),
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
    schema="turtle",
)
