import os
import psycopg
import json
import logging.config
import logging.handlers
import pathlib
from contextlib import contextmanager
from datetime import datetime
from dotenv import load_dotenv
from typing import List

from turtle.strategy.momentum import MomentumStrategy
from turtle.data.symbol import SymbolRepo
from turtle.data.company import CompanyRepo
from turtle.data.bars_history import BarsHistoryRepo

from turtle.data.models import Symbol

logger = logging.getLogger("__name__")
DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"


def setup_logging():
    config_file = pathlib.Path("config/stdout.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)


@contextmanager
def get_db_connection(dsn):
    connection = psycopg.connect(dsn)
    try:
        yield connection
    finally:
        connection.close()


def update_symbol_list() -> None:
    with get_db_connection(DSN) as connection:
        symbol_repo = SymbolRepo(connection, str(os.getenv("EODHD_API_KEY")))
        symbol_repo.update_exchange_symbol_list()


def update_company_list() -> None:
    with get_db_connection(DSN) as connection:
        company_repo = CompanyRepo(connection)
        symbol_repo = SymbolRepo(connection, str(os.getenv("EODHD_API_KEY")))
        symbol_list: List[Symbol] = symbol_repo.get_symbol_list("USA")
        for symbol_rec in symbol_list:
            company_repo.update_company_info(symbol_rec.symbol)


def update_bars_history(start_date: datetime, end_date: datetime) -> None:
    with get_db_connection(DSN) as connection:
        symbol_repo = SymbolRepo(connection, str(os.getenv("EODHD_API_KEY")))
        symbol_list = symbol_repo.get_symbol_list("USA")
        bars_history = BarsHistoryRepo(
            connection,
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )
        for symbol_rec in symbol_list:
            bars_history.update_bars_history(
                symbol_rec.symbol,
                start_date,
                end_date,
            )
    logger.info(f"Stocks update: {start_date} - {end_date}")


def momentum_stocks(end_date: datetime) -> None:
    with get_db_connection(DSN) as connection:
        momentum_strategy = MomentumStrategy(
            connection,
            str(os.getenv("EODHD_API_KEY")),
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )
        momentum_stock_list = momentum_strategy.momentum_stocks(end_date)
        logger.info(momentum_stock_list)


def get_company_data(symbol_list: List[str]) -> None:
    with get_db_connection(DSN) as connection:
        company_repo = CompanyRepo(connection)
        company_repo.get_company_data(symbol_list)
        _ = company_repo.convert_df()
        # logger.info(company_repo.company_list)
        # logger.info(df)


def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index
    setup_logging()
    # Load environment variables from the .env file (if present)
    load_dotenv()

    # update_ticker_list()
    # update_company_list()
    # update_bars_history(
    #    datetime(year=2024, month=8, day=22), datetime(year=2024, month=8, day=23)
    # )
    momentum_stocks(datetime(year=2024, month=8, day=25))
    # get_company_data(["AMZN", "TSLA"])

    """
    Receive NYSE/NASDAQ symbol list from EODHD
    update_ticker_list()
    """
    """
    Get company data from YAHOO
    with get_db_connection(dsn) as connection:
        company = Company(connection, str(os.getenv("EODHD_API_KEY")))
        company.update_company_list()
    
    !! Run database updates after that to update ticker.status values
    """
    # company.update_company_list(conn)

    """
    Update daily OHLC stocks history from Alpaca
    update_stocks_history(conn, datetime(year=2024, month=8, day=5).date(),  datetime(year=2024, month=8, day=17).date())

    """

    """
    Calculate momentum strategy 
    for ticker in ["SPY", "QQQ"]:
        bars_history.update_ssssticker_history(
            conn,
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            ticker,
            datetime(year=2016, month=1, day=1).date(),
            datetime(year=2024, month=8, day=12).date(),
        )

    with get_db_connection(dsn) as connection:
        end_date = datetime(year=2024, month=8, day=25)
        momentum_strategy = MomentumStrategy(
            connection, str(os.getenv("EODHD_API_KEY"))
        )
        momentum_stock_list = momentum_strategy.momentum_stocks(end_date)
        logger.info(momentum_stock_list)

    logger.info(momentum.weekly_momentum(conn, "PLTR", end_date))
    """
    # with get_db_connection(dsn) as connection:
    #     end_date = datetime(year=2024, month=8, day=25).date()
    #     momentum_strategy = MomentumStrategy(connection)
    #     momentum_stock_list = momentum_strategy.momentum_stocks(end_date)
    #     logger.info(momentum_stock_list)

    # momentum_stocks(conn, start_date)
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
