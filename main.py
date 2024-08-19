from datetime import datetime
# import pandas as pd
# import collections
# import base64
# import uuid
# import math

from dotenv import load_dotenv
import os

# yf.pdr_override()
# from pandas_datareader import data
# import requests
import psycopg

import json
import logging.config
import logging.handlers
import pathlib

# from datetime import datetime

# from alpaca.data.enums import DataFeed
# from alpaca.data.timeframe import TimeFrame
# from alpaca.data.requests import StockBarsRequest
# from alpaca.data.historical import StockHistoricalDataClient

from turtle.data import symbol, company, bars_history
from turtle.strategy import market, momentum

conn = psycopg.connect(
    "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"
)

logger = logging.getLogger("__name__")


def setup_logging():
    config_file = pathlib.Path("config/stdout.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)


def update_stocks_history(
    conn: psycopg.connection, start_date: datetime, end_date: datetime
) -> None:
    symbol_list = symbol.get_symbol_list(conn, "USA")
    for ticker in symbol_list:
        bars_history.update_ticker_history(
            conn,
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            ticker,
            start_date,
            end_date,
        )
    logger.info(f"Stocks update: {start_date} - {end_date}")


def momentum_stocks(conn: psycopg.connection, start_date: datetime) -> None:
    momentum_stock_list = momentum.momentum_stocks(conn, start_date)
    logger.info(f"Momentum stocks {start_date}: {momentum_stock_list}")


def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index
    setup_logging()
    # Load environment variables from the .env file (if present)
    load_dotenv()

    """
    Receive NYSE/NASDAQ symbol list from EODHD
    symbol.update_exchange_symbol_list(conn, os.getenv("EODHD_API_KEY"))

    """
    # symbol.update_exchange_symbol_list(conn, os.getenv("EODHD_API_KEY"))

    """
    Get company data from YAHOO
    company.update_company_list(conn)    
    
    !! Run database updates after that to update ticker.status values
    """
    # company.update_company_list(conn)

    """
    Update daily OHLC stocks history from Alpaca
    update_stocks_history(conn, datetime(year=2024, month=8, day=5).date(),  datetime(year=2024, month=8, day=17).date())

    """
    # update_stocks_history(
    #    conn,
    #    datetime(year=2017, month=1, day=1).date(),
    #    datetime(year=2024, month=8, day=17).date(),
    # )

    """
    Calculate momentum strategy 
    for ticker in ["SPY", "QQQ"]:
        bars_history.update_ticker_history(
            conn,
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            ticker,
            datetime(year=2016, month=1, day=1).date(),
            datetime(year=2024, month=8, day=12).date(),
        )
    start_date = datetime(year=2024, month=8, day=19).date()
    momentum_stocks(start_date)
    """
    start_date = datetime(year=2024, month=8, day=19).date()
    momentum_stocks(conn, start_date)
    # momentum.weekly_momentum(conn, "PLTR", start_date)

    # update_stocks_history(
    #    conn,
    #    datetime(year=2024, month=8, day=5).date(),
    #    datetime(year=2024, month=8, day=17).date(),
    # )
    # symbol.get_symbol_list(conn, "USA")

    # print(f'SECRET_KEY: {os.getenv('ALPACA_API_KEY')}')
    # symbol.update_exchange_symbol_list(conn, os.getenv("EODHD_API_KEY"))
    # company.update_company_list(conn)
    # bars_history.update_historal_data(
    #    conn, os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), "A"
    # )

    # bars_history.get_ticker_history(
    #    conn,
    #    "AMZN",
    #    datetime(year=2023, month=2, day=1).date(),
    #    datetime(year=2024, month=1, day=28).date(),
    #    "week",
    # )

    # logger.info(market.spy_momentum(conn, datetime(year=2024, month=1, day=28).date()))
    # logger.info(momentum.weekly_momentum( conn, "AMZN", datetime(year=2024, month=1, day=28).date()))
    # get_symbol_list('USA')
    # start_date = datetime(year=2024, month=8, day=11).date()
    # momentum_stocks(start_date)
    # momentum.weekly_momentum(conn, "PLTR", start_date)

    # place_holders={'symbol': 'XYZZZ', 'name': 'Test', 'exchange': 'NASDAQ', 'country': 'US', 'currency': 'USD', 'isin': 'XYZ'}
    # save_symbol_list(place_holders)
    # data = get_nasdaq_100_companies()
    # print(data)


if __name__ == "__main__":
    main()
