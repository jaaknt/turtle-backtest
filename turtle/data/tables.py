"""
SQLAlchemy Core table definitions for bulk database operations.

This module contains Table objects used for efficient bulk insert/upsert operations
that require explicit column access (e.g., PostgreSQL INSERT ON CONFLICT).
"""

from sqlalchemy import BigInteger, Column, DateTime, MetaData, Numeric, Table, Text

# Shared metadata instance for all table definitions
metadata = MetaData()

# Exchange table definition
# Used for bulk upsert operations with pg_insert.on_conflict_do_update
exchange_table = Table(
    "exchange",
    metadata,
    Column("code", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("country", Text, nullable=False),
    Column("currency", Text, nullable=False),
    Column("country_iso3", Text, nullable=True),
    schema="turtle",
)

# Ticker table definition
ticker_table = Table(
    "ticker",
    metadata,
    Column("unique_name", Text, primary_key=True),
    Column("code", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("country", Text),
    Column("exchange", Text, nullable=False),
    Column("currency", Text),
    Column("type", Text),
    Column("isin", Text),
    schema="turtle",
)

# Price History table definition
price_history_table = Table(
    "price_history",
    metadata,
    Column("symbol", Text, primary_key=True),
    Column("time", DateTime(timezone=True), primary_key=True),
    Column("open", Numeric(10, 2), nullable=False),
    Column("high", Numeric(10, 2), nullable=False),
    Column("low", Numeric(10, 2), nullable=False),
    Column("close", Numeric(10, 2), nullable=False),
    Column("adjusted_close", Numeric(10, 2), nullable=False),
    Column("volume", BigInteger, nullable=False),
    Column("source", Text, nullable=False), # Using Text for ENUM type
    schema="turtle",
)
