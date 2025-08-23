import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

from datetime import datetime
from typing import cast

from turtle.service.strategy_runner_service import StrategyRunnerService
from turtle.strategy.darvas_box import DarvasBoxStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from psycopg_pool import ConnectionPool
from psycopg import Connection
from psycopg.rows import TupleRow

# Type alias for better clarity
DatabasePool = ConnectionPool[Connection[TupleRow]]

# Load environment variables
load_dotenv()

end_date = datetime(year=2025, month=8, day=12)

# Create database connection and bars_history for strategy
pool = cast(
    DatabasePool,
    ConnectionPool(
        conninfo="host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres", min_size=5, max_size=50, max_idle=600
    ),
)
bars_history = BarsHistoryRepo(
    pool,
    str(os.getenv("ALPACA_API_KEY")),
    str(os.getenv("ALPACA_SECRET_KEY")),
)

# Create DarvasBoxStrategy instance
darvas_strategy = DarvasBoxStrategy(
    bars_history=bars_history,
    time_frame_unit=TimeFrameUnit.DAY,
    warmup_period=730,
)

# Create strategy runner with the trading strategy
strategy_runner = StrategyRunnerService(trading_strategy=darvas_strategy)

# Get ticker list (now with correct method signature)
for ticker in strategy_runner.get_symbol_list():
    signals = strategy_runner.get_trading_signals(ticker, end_date, end_date)


# Extract just the symbol names for get_company_list
symbol_names = [ticker.ticker for ticker in signals]
df: pd.DataFrame = strategy_runner.get_company_list(symbol_names)

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
