# import requests
from psycopg import connection
import yfinance as yf

from turtle.data import symbol


def map_yahoo_company_data(symbol: str, data: dict) -> dict:
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
    place_holders["short_ratio"] = data.get("shortRatio")
    place_holders["peg_ratio"] = data.get("pegRatio")
    place_holders["recommodation_mean"] = data.get("recommendationMean")
    place_holders["number_of_analysyst"] = data.get("numberOfAnalystOpinions")
    place_holders["roa_value"] = data.get("returnOnAssets")
    place_holders["roe_value"] = data.get("returnOnEquity")
    place_holders["source"] = "yahoo"

    return place_holders


def save_company_list(conn: connection, place_holders: dict) -> None:
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    print(place_holders)
    cursor.execute(
        """
           INSERT INTO turtle.company
           (symbol, short_name, country, industry_code, sector_code, employees_count, dividend_rate, trailing_pe_ratio, 
            forward_pe_ratio, avg_volume, avg_price, market_cap, enterprice_value, short_ratio, peg_ratio, recommodation_mean, 
            number_of_analysyst, roa_value, roe_value, "source")
           VALUES(%(symbol)s, %(short_name)s, %(country)s, %(industry_code)s, %(sector_code)s, %(employees_count)s, %(dividend_rate)s, %(trailing_pe_ratio)s,
                  %(forward_pe_ratio)s, %(avg_volume)s, %(avg_price)s, %(market_cap)s, %(enterprice_value)s, %(short_ratio)s, %(peg_ratio)s, %(recommodation_mean)s,
                  %(number_of_analysyst)s, %(roa_value)s, %(roa_value)s, 'yahoo')   
           ON CONFLICT (symbol) DO UPDATE SET              
           (short_name, country, industry_code, sector_code, employees_count, dividend_rate, trailing_pe_ratio, 
            forward_pe_ratio, avg_volume, avg_price, market_cap, enterprice_value, short_ratio, peg_ratio, recommodation_mean, 
            number_of_analysyst, roa_value, roe_value, "source", modified_at) = 
           (EXCLUDED.short_name, EXCLUDED.country, EXCLUDED.industry_code, EXCLUDED.sector_code, EXCLUDED.employees_count, EXCLUDED.dividend_rate, EXCLUDED.trailing_pe_ratio, 
            EXCLUDED.forward_pe_ratio, EXCLUDED.avg_volume, EXCLUDED.avg_price, EXCLUDED.market_cap, EXCLUDED.enterprice_value, EXCLUDED.short_ratio, EXCLUDED.peg_ratio, EXCLUDED.recommodation_mean, 
            EXCLUDED.number_of_analysyst, EXCLUDED.roa_value, EXCLUDED.roe_value, EXCLUDED."source", CURRENT_TIMESTAMP) 
                   """,
        place_holders,
    )
    conn.commit()


def update_company_list(conn: connection) -> None:
    # data = get_eodhd_exchange_symbol_list('NYSE')
    # ticker = yf.Ticker("MSFT")
    # data = ticker.info
    # place_holders = map_yahoo_company_data("MSFT", data)
    # print(place_holders)
    # print(ticker.info)
    # return
    symbol_list = symbol.get_symbol_list(conn, "USA")
    for _symbol in symbol_list:
        ticker = yf.Ticker(_symbol)
        data = ticker.info
        place_holders = map_yahoo_company_data(_symbol, data)
        save_company_list(conn, place_holders)
