# import pandas as pd
# import collections
# import base64
# import uuid
# import math
# import yfinance as yf

# import alpaca_trade_api as alpaca
from dotenv import load_dotenv
import os

# yf.pdr_override()
# from pandas_datareader import data
# import requests
import psycopg

# from datetime import datetime

# from alpaca.data.enums import DataFeed
# from alpaca.data.timeframe import TimeFrame
# from alpaca.data.requests import StockBarsRequest
# from alpaca.data.historical import StockHistoricalDataClient

from turtle.data import symbol, company, bars_history

conn = psycopg.connect(
    "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"
)


def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index

    # Load environment variables from the .env file (if present)
    load_dotenv()
    print(symbol.get_symbol_list("USA", conn))

    # print(f'SECRET_KEY: {os.getenv('ALPACA_API_KEY')}')
    # symbol.update_exchange_symbol_list(conn, os.getenv("EODHD_API_KEY"))
    company.update_company_list(conn)
    bars_history.update_historal_data(
        conn, os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), "A"
    )
    # get_symbol_list('USA')

    # place_holders={'symbol': 'XYZZZ', 'name': 'Test', 'exchange': 'NASDAQ', 'country': 'US', 'currency': 'USD', 'isin': 'XYZ'}
    # save_symbol_list(place_holders)
    # data = get_nasdaq_100_companies()
    # print(data)


if __name__ == "__main__":
    main()
