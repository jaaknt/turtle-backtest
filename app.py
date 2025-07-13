import streamlit as st
import pandas as pd

from datetime import datetime
from typing import List

from turtle.service.strategy_runner import StrategyRunner

end_date = datetime(year=2024, month=8, day=30)
# momentum_stock_list = momentum.momentum_stocks(conn, start_date)
# data = {"Symbol": momentum_stock_list}

# df = get_company_data(["AMZN", "TSLA"])
strategy_runner = StrategyRunner()
# Use DarvasBoxStrategy as the default trading strategy
symbol_list: List[str] = strategy_runner.momentum_stocks(end_date, strategy_runner.darvas_box_strategy)
df: pd.DataFrame = strategy_runner.get_company_list(symbol_list)

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
