"""
SQLAlchemy Core table definitions for bulk database operations.

This module contains Table objects used for efficient bulk insert/upsert operations
that require explicit column access (e.g., PostgreSQL INSERT ON CONFLICT).
"""

from sqlalchemy import Column, MetaData, Table, Text

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
    Column("code", Text, primary_key=True),
    Column("exchange", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("country", Text),
    Column("currency", Text),
    Column("type", Text),
    Column("isin", Text),
    schema="turtle",
)
