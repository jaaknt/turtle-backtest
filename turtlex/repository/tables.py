"""
SQLAlchemy Core table definitions for database operations.

This module contains Table objects used for all database operations
in the repository layer.
"""

from sqlalchemy import BigInteger, Column, Date, DateTime, Float, Integer, MetaData, Numeric, SmallInteger, Table, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB

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

# lightyear_transaction table definition (created_at/modified_at are owned by the DB)
lightyear_transaction_table = Table(
    "lightyear_transaction",
    metadata,
    Column("reference", Text, primary_key=True),
    Column("transacted_at", DateTime),
    Column("ticker_code", Text),
    Column("isin", Text),
    Column("transaction_type", Text),
    Column("quantity", Numeric(20, 9)),
    Column("currency", Text),
    Column("price", Numeric(20, 9)),
    Column("gross_amount", Numeric(20, 2)),
    Column("fee", Numeric(20, 2)),
    Column("tax", Numeric(20, 2)),
    Column("net_amount", Numeric(20, 2)),
    Column("source_file", Text),
    schema="turtle",
)

# job_runs table definition. `duration` is deliberately absent: it is a generated column computed
# from end_at - start_at, so it must never appear in an INSERT or UPDATE payload. `id` is present
# because the start insert returns it and the finish update filters on it, but it is
# GENERATED ALWAYS AS IDENTITY and must never be supplied as a value.
job_runs_table = Table(
    "job_runs",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", Text),
    Column("status", Text),
    Column("start_at", DateTime(timezone=True)),
    Column("end_at", DateTime(timezone=True)),
    Column("parameters", JSONB),
    Column("version", Text),
    Column("exit_code", Integer),
    Column("error", Text),
    Column("hostname", Text),
    schema="turtle",
)

# signal table definition. `id` is GENERATED ALWAYS AS IDENTITY and must never be supplied as a
# value; created_at/modified_at are owned by the DB.
signal_table = Table(
    "signal",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("trading_strategy", Text),
    Column("ranking_strategy", Text),
    Column("symbol", Text),
    Column("signal_date", Date),
    Column("ranking", SmallInteger),
    Column("signal_close", Float),
    Column("parameters", JSONB),
    schema="turtle",
)

# Reference values for ticker-table contents, shared by query and ingest repos
US_EXCHANGES = ["NASDAQ", "NYSE", "NYSE ARCA", "NYSE MKT"]
COMMON_STOCK_TYPE = "Common Stock"
