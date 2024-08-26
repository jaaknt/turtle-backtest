# import requests
import psycopg
import yfinance as yf
import logging
import pandas as pd

from typing import List, Tuple, Union

from turtle.data.symbol import Ticker

logger = logging.getLogger("__name__")


class Company:
    def __init__(self, connection: psycopg.Connection, ticker_api_key: str):
        self.connection: psycopg.Connection = connection
        self.ticker = Ticker(connection, ticker_api_key)
        self.symbol_list: List[str] = []

    def map_yahoo_company_data(self, symbol: str, data: dict) -> dict:
        place_holders = {}
        place_holders["symbol"] = symbol
        place_holders["short_name"] = data.get("shortName")
        place_holders["country"] = data.get("country")
        place_holders["industry_code"] = data.get("industry")
        place_holders["sector_code"] = data.get("sector")
        place_holders["employees_count"] = data.get("fullTimeEmployees")
        place_holders["dividend_rate"] = data.get("dividendRate")
        place_holders["trailing_pe_ratio"] = (
            None if data.get("trailingPE") == "Infinity" else data.get("trailingPE")
        )
        place_holders["forward_pe_ratio"] = (
            None if data.get("forwardPE") == "Infinity" else data.get("forwardPE")
        )
        place_holders["avg_volume"] = data.get("averageDailyVolume10Day")
        place_holders["avg_price"] = data.get("fiftyDayAverage")
        place_holders["market_cap"] = data.get("marketCap")
        place_holders["enterprice_value"] = data.get("enterpriseValue")
        place_holders["beta"] = data.get("beta")
        place_holders["shares_float"] = data.get("floatShares")
        place_holders["short_ratio"] = data.get("shortRatio")
        place_holders["peg_ratio"] = data.get("pegRatio")
        place_holders["recommodation_mean"] = data.get("recommendationMean")
        place_holders["number_of_analysyst"] = data.get("numberOfAnalystOpinions")
        place_holders["roa_value"] = data.get("returnOnAssets")
        place_holders["roe_value"] = data.get("returnOnEquity")
        place_holders["source"] = "yahoo"

        return place_holders

    def save_company_list(self, place_holders: dict) -> None:
        # Creating a cursor object using the cursor() method
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO turtle.company
                (symbol, short_name, country, industry_code, sector_code, employees_count, dividend_rate, trailing_pe_ratio, 
                    forward_pe_ratio, avg_volume, avg_price, market_cap, enterprice_value, beta, shares_float, short_ratio, 
                    peg_ratio, recommodation_mean, number_of_analysyst, roa_value, roe_value, "source")
                VALUES(%(symbol)s, %(short_name)s, %(country)s, %(industry_code)s, %(sector_code)s, %(employees_count)s, %(dividend_rate)s, %(trailing_pe_ratio)s,
                        %(forward_pe_ratio)s, %(avg_volume)s, %(avg_price)s, %(market_cap)s, %(enterprice_value)s, %(beta)s, %(shares_float)s, %(short_ratio)s, 
                        %(peg_ratio)s, %(recommodation_mean)s, %(number_of_analysyst)s, %(roa_value)s, %(roa_value)s, 'yahoo')   
                ON CONFLICT (symbol) DO UPDATE SET              
                (short_name, country, industry_code, sector_code, employees_count, dividend_rate, trailing_pe_ratio, 
                    forward_pe_ratio, avg_volume, avg_price, market_cap, enterprice_value, beta, shares_float, short_ratio,
                    peg_ratio, recommodation_mean, number_of_analysyst, roa_value, roe_value, "source", modified_at) = 
                (EXCLUDED.short_name, EXCLUDED.country, EXCLUDED.industry_code, EXCLUDED.sector_code, EXCLUDED.employees_count, EXCLUDED.dividend_rate, EXCLUDED.trailing_pe_ratio, 
                    EXCLUDED.forward_pe_ratio, EXCLUDED.avg_volume, EXCLUDED.avg_price, EXCLUDED.market_cap, EXCLUDED.enterprice_value, EXCLUDED.beta, EXCLUDED.shares_float, EXCLUDED.short_ratio, 
                    EXCLUDED.peg_ratio, EXCLUDED.recommodation_mean, EXCLUDED.number_of_analysyst, EXCLUDED.roa_value, EXCLUDED.roe_value, EXCLUDED."source", CURRENT_TIMESTAMP) 
                        """,
                place_holders,
            )
            self.connection.commit()

    def update_company_list(self) -> None:
        # data = get_eodhd_exchange_symbol_list('NYSE')
        # ticker = yf.Ticker("MSFT")
        # data = ticker.info
        # place_holders = map_yahoo_company_data("MSFT", data)
        # print(place_holders)
        # print(ticker.info)
        # return
        self.symbol_list = self.ticker.get_symbol_list("USA")
        for _symbol in self.symbol_list:
            ticker = yf.Ticker(_symbol)
            data = ticker.info
            place_holders = self.map_yahoo_company_data(_symbol, data)
            self.save_company_list(place_holders)

    def convert_to_df(self, result: List[Tuple]) -> pd.DataFrame:
        dtypes = {
            "symbol": "string",
            "short_name": "string",
            "country": "string",
            "industry_code": "string",
            "sector_code": "string",
            "employees_count": "Int64",
            "dividend_rate": "Float64",
            "market_cap": "Float64",
            "enterprice_value": "Float64",
            "beta": "Float64",
            "shares_float": "Float64",
            "short_ratio": "Float64",
            "recommodation_mean": "Float64",
        }
        columns = [
            "symbol",
            "short_name",
            "country",
            "industry_code",
            "sector_code",
            "employees_count",
            "dividend_rate",
            "market_cap",
            "enterprice_value",
            "beta",
            "shares_float",
            "short_ratio",
            "recommodation_mean",
        ]

        # Create a pandas DataFrame from the fetched data
        df = pd.DataFrame(result, columns=columns).astype(dtypes)
        df = df.set_index(["symbol"])
        return df

    def get_company_data(
        self, symbol_list: List[str], format: str
    ) -> Union[List[Tuple], pd.DataFrame]:
        logger.info(f"{tuple(symbol_list)} symbols passed to company table")
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, short_name, country, industry_code, sector_code, employees_count, dividend_rate,
                    market_cap, enterprice_value, beta, shares_float, short_ratio, recommodation_mean
                    FROM turtle.company
                    WHERE symbol = ANY(%s)
                    ORDER BY symbol       
                        """,
                [symbol_list],
            )
            result = cursor.fetchall()

        logger.info(f"{len(result)} symbols returned from company table")
        return result if format == "list" else self.convert_to_df(result)
