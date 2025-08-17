import json
import logging.config
import logging.handlers
import pathlib
from datetime import datetime
from dotenv import load_dotenv

from turtle.service.data_update_service import DataUpdateService
from turtle.service.strategy_runner_service import StrategyRunnerService
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)
DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"


def setup_logging() -> None:
    config_file = pathlib.Path("config/stdout.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)


def init_db() -> None:
    """Initialize the database with the required tables and data."""
    data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
    start_date: datetime = datetime(year=2017, month=1, day=1)
    end_date: datetime = datetime(year=2025, month=6, day=27)

    data_updater.update_symbol_list()
    data_updater.update_company_list()
    data_updater.update_bars_history(start_date, end_date)


def main() -> None:
    # Setup logging configuration
    setup_logging()
    # Load environment variables from the .env file (if present)
    load_dotenv()
    # Initialize the database
    # init_db()
    # return

    data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)
    start_date: datetime = datetime(year=2024, month=6, day=25)  # noqa: F841
    end_date: datetime = datetime(year=2025, month=6, day=27)  # noqa: F841

    # data_updater = DataUpdateService(time_frame_unit=TimeFrameUnit.WEEK)

    # ticker = "TSLA"
    # start_date: datetime = datetime(year=2022, month=1, day=1)  # noqa: F841
    # end_date: datetime = datetime(year=2023, month=12, day=31)  # noqa: F841

    # strategy_runner = StrategyRunnerService(time_frame_unit=TimeFrameUnit.DAY)
    # strategy_runner.mars_strategy.calculate_entries(
    #    ticker,
    #    start_date,
    #    end_date,
    # )

    # data_updater.update_symbol_list()
    # data_updater.update_company_list()
    # data_updater.update_bars_history(start_date, end_date)

    # strategy_runner = StrategyRunnerService(time_frame_unit=TimeFrameUnit.DAY)
    # from turtle.strategy.darvas_box import DarvasBoxStrategy
    # darvas_strategy = DarvasBoxStrategy(strategy_runner.bars_history)
    # symbol_list = strategy_runner.get_tickers_list(end_date, darvas_strategy)
    # logger.info(symbol_list)

    # strategy_runner.get_tickers_count(start_date, end_date, darvas_strategy)

    # df = strategy_runner.get_company_list(symbol_list)
    # logger.info(df)

    # data_updater.update_bars_history(
    #    datetime(year=2016, month=1, day=1), datetime(year=2024, month=10, day=25)
    # )

    # update_ticker_list()
    # update_company_list()
    # update_bars_history(
    #    datetime(year=2024, month=8, day=22), datetime(year=2024, month=8, day=23)
    # )
    # momentum_stocks(datetime(year=2024, month=8, day=25))
    # get_company_list(["AMZN", "TSLA"])

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
        bars_history.update_ticker_history(
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
