# import pandas as pd
import collections
import base64
import uuid
import yfinance as yf

# import alpaca_trade_api as alpaca
from dotenv import load_dotenv
import os

# yf.pdr_override()
# from pandas_datareader import data
import requests


# function returns a list of companies in the Nasdaq 100 index
def get_nasdaq_100_companies() -> dict:
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index
    # response = requests.get(
    #    f"https://www.alphavantage.co/query?function=INDEX_SP500&apikey={vantage_api_key}"
    # )

    # The API returns a JSON object, which can be easily converted into a Python dictionary
    # data = response.json()

    # The list of companies is stored in the 'Members' key of the dictionary
    # companies = data["Members"]
    client = alpaca.REST(alpaca_api_key, alpaca_secret_key)
    active_assets = client.list_assets(status="active", asset_class="us_equity")
    # count = collections.Counter([d["exchange"] for d in active_assets])
    # print(count)
    print(type(active_assets))
    nasdaq_companies = [
        asset
        for asset in active_assets
        if asset.tradable and asset.exchange == "NASDAQ"
    ]

    # index = yf.Ticker("^NDX")
    # print(index.info)
    # companies = index.info

    # Return the list of companies

    return nasdaq_companies


def generate_base64_from_uuid(uuid_str):
    # Convert UUID string to bytes
    uuid_bytes = uuid.UUID(uuid_str).bytes

    # Encode bytes using base64
    base64_string = base64.urlsafe_b64encode(uuid_bytes).decode("utf-8")

    return base64_string

def get_exchange_symbol_list(exchange_code):
    url = f'https://eodhd.com/api/exchange-symbol-list/{exchange_code}?api_token={os.getenv('EODHD_API_KEY')}&fmt=json&type=stock'
    data = requests.get(url).json()
    print(data)

def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index
    
    # Load environment variables from the .env file (if present)
    load_dotenv()
    # print(f'SECRET_KEY: {os.getenv('ALPACA_API_KEY')}')
    get_exchange_symbol_list('NYSE');

    # data = get_nasdaq_100_companies()
    # print(data)

    # Example usage
    # uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    # base64_string = generate_base64_from_uuid(uuid_str)
    # print(base64_string)


if __name__ == "__main__":
    main()
