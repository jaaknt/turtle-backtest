import streamlit as st
import pandas as pd

from datetime import datetime
from typing import List

from turtle.service.strategy_runner import StrategyRunner
from turtle.strategy.darvas_box import DarvasBoxStrategy

end_date = datetime(year=2024, month=8, day=30)
# momentum_stock_list = momentum.momentum_stocks(conn, start_date)
# data = {"Symbol": momentum_stock_list}

# df = get_company_data(["AMZN", "TSLA"])
strategy_runner = StrategyRunner()
# Create DarvasBoxStrategy instance
darvas_strategy = DarvasBoxStrategy(strategy_runner.bars_history)
symbol_list: List[str] = strategy_runner.get_tickers_list(end_date, darvas_strategy)
df: pd.DataFrame = strategy_runner.get_company_list(symbol_list)

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
