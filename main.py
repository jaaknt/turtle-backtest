# import pandas as pd
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
    active_assets = client.list_assets(status="active")
    # nasdaq100_companies = client.index_constituents('NDX')

    # index = yf.Ticker("^NDX")
    # print(index.info)
    # companies = index.info

    # Return the list of companies
    return active_assets


def main():
    # Make a request to the Alpha Vantage API to get a list of companies in the Nasdaq 100 index
    data = get_nasdaq_100_companies()
    print(data)


if __name__ == "__main__":
    main()
