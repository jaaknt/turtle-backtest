import streamlit as st
import pandas as pd

from datetime import datetime
from typing import List

from turtle.service.data_update import DataUpdate

end_date = datetime(year=2024, month=8, day=30)
# momentum_stock_list = momentum.momentum_stocks(conn, start_date)
# data = {"Symbol": momentum_stock_list}

# df = get_company_data(["AMZN", "TSLA"])
data_update = DataUpdate()
symbol_list: List[str] = data_update.momentum_stocks(end_date)
df: pd.DataFrame = data_update.get_company_list(symbol_list)

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
