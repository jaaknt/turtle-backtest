# import pandas as pd
import collections
import base64
import uuid
import yfinance as yf
import alpaca_trade_api as alpaca

# yf.pdr_override()
# from pandas_datareader import data
import requests

# Replace YOUR_API_KEY with your actual API key
vantage_api_key = "1ZTMVZX0N4RZEBTF"

alpaca_api_key = "AKI8X4PEAZE996RQWLJC"
alpaca_secret_key = "pNB8qPfGkFhwYuBiFRrFDr0u9RT5cCAKlSSwDaaC"


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


def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index
    data = get_nasdaq_100_companies()
    print(data)

    # Example usage
    # uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    # base64_string = generate_base64_from_uuid(uuid_str)
    # print(base64_string)


if __name__ == "__main__":
    main()
