# import pandas as pd
# import collections
# import base64
# import uuid
# import math
import yfinance as yf

# import alpaca_trade_api as alpaca
from dotenv import load_dotenv
import os

# yf.pdr_override()
# from pandas_datareader import data
import requests
import psycopg

from datetime import datetime

from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient

conn = psycopg.connect(
    "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"
)


def map_alpaca_bar_history(row) -> dict:
    place_holders = {}
    place_holders["symbol"] = row[0][0]
    place_holders["hdate"] = row[0][1].to_pydatetime().date()
    place_holders["open"] = row[1]
    place_holders["high"] = row[2]
    place_holders["low"] = row[3]
    place_holders["close"] = row[4]
    place_holders["volume"] = row[5]
    place_holders["trade_count"] = row[6]
    place_holders["source"] = "alpaca"

    return place_holders


def map_eodhd_symbol_list(ticker: dict) -> dict:
    place_holders = {}
    place_holders["symbol"] = ticker["Code"]
    place_holders["name"] = ticker["Name"]
    place_holders["exchange"] = ticker["Exchange"]
    place_holders["country"] = ticker["Country"]
    place_holders["currency"] = ticker["Currency"]
    place_holders["isin"] = ticker["Isin"]
    place_holders["symbol_type"] = "stock"
    place_holders["source"] = "eodhd"

    return place_holders


def map_yahoo_company_data(symbol: str, data: dict) -> dict:
    place_holders = {}
    place_holders["symbol"] = symbol
    place_holders["short_name"] = data.get("shortName")
    place_holders["country"] = data.get("country")
    place_holders["industry_code"] = data.get("industryKey")
    place_holders["sector_code"] = data.get("sectorKey")
    place_holders["employees_count"] = data.get("fullTimeEmployees")
    place_holders["dividend_rate"] = data.get("dividendRate")
    place_holders["trailing_pe_ratio"] = (
        None if data.get("trailingPE") == "Infinity" else data.get("trailingPE")
    )
    place_holders["forward_pe_ratio"] = (
        None if data.get("forwardPE") == "Infinity" else data.get("forwardPE")
    )
    place_holders["avg_volume"] = data.get("averageDailyVolume10Day")
    place_holders["market_cap"] = data.get("marketCap")
    place_holders["enterprice_value"] = data.get("enterpriseValue")
    place_holders["short_ratio"] = data.get("shortRatio")
    place_holders["peg_ratio"] = data.get("pegRatio")
    place_holders["recommodation_mean"] = data.get("recommendationMean")
    place_holders["number_of_analysyst"] = data.get("numberOfAnalystOpinions")
    place_holders["roa_value"] = data.get("returnOnAssets")
    place_holders["roe_value"] = data.get("returnOnEquity")
    place_holders["source"] = "yahoo"

    return place_holders


def save_bars_history(place_holders: dict) -> None:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute(
        """
           INSERT INTO turtle.bars_history
           (symbol, hdate, open, high, low, close, volume, trade_count, source)
           VALUES(%(symbol)s, %(hdate)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(trade_count)s, %(source)s) 
           ON CONFLICT (symbol, hdate) DO NOTHING                
                   """,
        place_holders,
    )
    conn.commit()


def get_symbol_list(country: str) -> None:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute("""
           SELECT symbol
             FROM turtle.ticker
            WHERE country = 'USA'
            ORDER BY symbol       
                   """)
    result = cursor.fetchall()
    return list(map(" ".join, result))


def save_symbol_list(place_holders: dict) -> None:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute(
        """
           INSERT INTO turtle.ticker
           (symbol, "name", exchange, country, currency, isin, symbol_type, source)
           VALUES(%(symbol)s, %(name)s, %(exchange)s, %(country)s, %(currency)s, %(isin)s, %(symbol_type)s, %(source)s)         
                   """,
        place_holders,
    )
    conn.commit()


def save_company_list(place_holders: dict) -> None:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    print(place_holders)
    cursor.execute(
        """
           INSERT INTO turtle.company
           (symbol, short_name, country, industry_code, sector_code, employees_count, dividend_rate, trailing_pe_ratio, 
            forward_pe_ratio, avg_volume, market_cap, enterprice_value, short_ratio, peg_ratio, recommodation_mean, 
            number_of_analysyst, roa_value, roe_value, "source")
           VALUES(%(symbol)s, %(short_name)s, %(country)s, %(industry_code)s, %(sector_code)s, %(employees_count)s, %(dividend_rate)s, %(trailing_pe_ratio)s,
                  %(forward_pe_ratio)s, %(avg_volume)s, %(market_cap)s, %(enterprice_value)s, %(short_ratio)s, %(peg_ratio)s, %(recommodation_mean)s,
                  %(number_of_analysyst)s, %(roa_value)s, %(roa_value)s, 'yahoo')   
           ON CONFLICT (symbol) DO UPDATE SET              
           (short_name, country, industry_code, sector_code, employees_count, dividend_rate, trailing_pe_ratio, 
            forward_pe_ratio, avg_volume, market_cap, enterprice_value, short_ratio, peg_ratio, recommodation_mean, 
            number_of_analysyst, roa_value, roe_value, "source", modified_at) = 
           (EXCLUDED.short_name, EXCLUDED.country, EXCLUDED.industry_code, EXCLUDED.sector_code, EXCLUDED.employees_count, EXCLUDED.dividend_rate, EXCLUDED.trailing_pe_ratio, 
            EXCLUDED.forward_pe_ratio, EXCLUDED.avg_volume, EXCLUDED.market_cap, EXCLUDED.enterprice_value, EXCLUDED.short_ratio, EXCLUDED.peg_ratio, EXCLUDED.recommodation_mean, 
            EXCLUDED.number_of_analysyst, EXCLUDED.roa_value, EXCLUDED.roe_value, EXCLUDED."source", CURRENT_TIMESTAMP) 
                   """,
        place_holders,
    )
    conn.commit()


def get_eodhd_exchange_symbol_list(exchange_code: str) -> list[dict]:
    url = f'https://eodhd.com/api/exchange-symbol-list/{exchange_code}?api_token={os.getenv('EODHD_API_KEY')}&fmt=json&type=stock'
    data = requests.get(url).json()
    print(data)
    # print(type(data))
    # print(type(data[0]))
    return data


def update_historal_data(starting_symbol: str) -> None:
    stock_data_client = StockHistoricalDataClient(
        api_key=os.getenv("ALPACA_API_KEY"), secret_key=os.getenv("ALPACA_SECRET_KEY")
    )
    symbol_list = get_symbol_list("USA")
    for symbol in symbol_list:
        if symbol >= starting_symbol:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                start=datetime(year=2016, month=1, day=1).date(),
                end=datetime(year=2024, month=7, day=19).date(),
                limit=10000,
                timeframe=TimeFrame.Day,
                feed=DataFeed.SIP,
            )
            data = stock_data_client.get_stock_bars(request_params=request)
            if data.df.empty:
                print(f"{datetime.now():%c} Unknown symbol: {symbol}")
            else:
                print(f"{datetime.now():%c} Saving: {symbol}")
                for row in data.df.itertuples(index=True):
                    place_holders = map_alpaca_bar_history(row)
                    save_bars_history(place_holders)
                    # print(row[0][0], row[0][1].to_pydatetime(), row[1], type(row[0][1].to_pydatetime()))
        else:
            print(f"{datetime.now():%c} Symbol: {symbol} already exists")


def update_exchange_symbol_list() -> None:
    data = get_eodhd_exchange_symbol_list("NYSE")
    for ticker in data:
        if "-" not in ticker["Code"]:
            place_holders = map_eodhd_symbol_list(ticker)
            save_symbol_list(place_holders)
    data = get_eodhd_exchange_symbol_list("NASDAQ")
    for ticker in data:
        if "-" not in ticker["Code"]:
            place_holders = map_eodhd_symbol_list(ticker)
            save_symbol_list(place_holders)


def update_company_list() -> None:
    # data = get_eodhd_exchange_symbol_list('NYSE')
    symbol_list = get_symbol_list("USA")
    for symbol in symbol_list:
        ticker = yf.Ticker(symbol)
        data = ticker.info
        place_holders = map_yahoo_company_data(symbol, data)
        save_company_list(place_holders)


def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index

    # Load environment variables from the .env file (if present)
    load_dotenv()
    # print(f'SECRET_KEY: {os.getenv('ALPACA_API_KEY')}')
    # update_exchange_symbol_list()
    # update_historal_data('LGHLW')
    # get_symbol_list('USA')
    update_company_list()

    # place_holders={'symbol': 'XYZZZ', 'name': 'Test', 'exchange': 'NASDAQ', 'country': 'US', 'currency': 'USD', 'isin': 'XYZ'}
    # save_symbol_list(place_holders)
    # data = get_nasdaq_100_companies()
    # print(data)

    # Example usage
    # uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    # base64_string = generate_base64_from_uuid(uuid_str)
    # print(base64_string)


if __name__ == "__main__":
    main()
