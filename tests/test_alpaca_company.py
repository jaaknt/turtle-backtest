from turtle.data.alpaca_company import AlpacaCompanyRepo

from pytest_mock import MockerFixture


def test_map_yahoo_company_data(mocker: MockerFixture) -> None:
    repo = AlpacaCompanyRepo(engine=mocker.Mock())

    data = {
        "shortName": "Apple Inc.",
        "country": "USA",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "fullTimeEmployees": 164000,
        "dividendRate": 0.96,
        "trailingPE": 28.5,
        "forwardPE": 25.0,
        "averageDailyVolume10Day": 60000000,
        "fiftyDayAverage": 175.0,
        "marketCap": 2800000000000,
        "enterpriseValue": 2750000000000,
        "beta": 1.2,
        "floatShares": 15000000000,
        "shortRatio": 0.8,
        "pegRatio": 2.5,
        "recommendationMean": 1.8,
        "numberOfAnalystOpinions": 40,
        "returnOnAssets": 0.28,
        "returnOnEquity": 1.47,
    }

    result = repo.map_yahoo_company_data("AAPL", data)

    assert result["symbol"] == "AAPL"
    assert result["short_name"] == "Apple Inc."
    assert result["country"] == "USA"
    assert result["industry_code"] == "Consumer Electronics"
    assert result["sector_code"] == "Technology"
    assert result["employees_count"] == 164000
    assert result["dividend_rate"] == 0.96
    assert result["trailing_pe_ratio"] == 28.5
    assert result["forward_pe_ratio"] == 25.0
    assert result["market_cap"] == 2800000000000
    assert result["source"] == "yahoo"


def test_map_yahoo_company_data_infinity_pe(mocker: MockerFixture) -> None:
    repo = AlpacaCompanyRepo(engine=mocker.Mock())

    data = {
        "shortName": "Some Corp",
        "trailingPE": "Infinity",
        "forwardPE": "Infinity",
    }

    result = repo.map_yahoo_company_data("XYZ", data)

    assert result["trailing_pe_ratio"] is None
    assert result["forward_pe_ratio"] is None


def test_fetch_company_data_returns_none_on_bad_data(mocker: MockerFixture) -> None:
    repo = AlpacaCompanyRepo(engine=mocker.Mock())

    mock_ticker = mocker.Mock()
    mock_ticker.info = {}
    mocker.patch("turtle.data.alpaca_company.yf.Ticker", return_value=mock_ticker)

    result = repo.fetch_company_data("INVALID")

    assert result is None
