import streamlit as st
import pandas as pd
import psycopg
from datetime import datetime

from turtle.strategy import momentum

conn = psycopg.connect(
    "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"
)

start_date = datetime(year=2024, month=8, day=19).date()
momentum_stock_list = momentum.momentum_stocks(conn, start_date)

data = {"Symbol": momentum_stock_list}

df = pd.DataFrame(data)

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
