import os
import streamlit as st
import pandas as pd
import psycopg
from contextlib import contextmanager
from datetime import datetime
from typing import List

from turtle.data.company import CompanyRepo
from turtle.strategy.momentum import MomentumStrategy

DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"


@contextmanager
def get_db_connection(dsn):
    connection = psycopg.connect(dsn)
    try:
        yield connection
    finally:
        connection.close()


def momentum_stocks(end_date: datetime) -> List[str]:
    with get_db_connection(DSN) as connection:
        momentum_strategy = MomentumStrategy(
            connection,
            str(os.getenv("EODHD_API_KEY")),
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )
        return momentum_strategy.momentum_stocks(end_date)


def get_company_data(symbol_list: List[str]) -> pd.DataFrame:
    with get_db_connection(DSN) as connection:
        company_repo = CompanyRepo(connection)
        company_repo.get_company_data(symbol_list)
    return company_repo.convert_df()


end_date = datetime(year=2024, month=8, day=25)
# momentum_stock_list = momentum.momentum_stocks(conn, start_date)
# data = {"Symbol": momentum_stock_list}

# df = get_company_data(["AMZN", "TSLA"])
df = get_company_data(momentum_stocks(end_date))

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
