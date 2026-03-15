import logging
from turtle.data.alpaca_symbol import AlpacaSymbolRepo
from turtle.data.models import Symbol
from unittest.mock import MagicMock

import pytest
from alpaca.trading.enums import AssetExchange, AssetStatus
from alpaca.trading.models import Asset
from pytest_mock import MockerFixture

mocked_data = [
    ("AMZN", "Amazon.com Inc.", "NASDAQ", "USA"),
    ("TSLA", "Tesla Inc.", "NASDAQ", "USA"),
]


def _make_asset(symbol: str, name: str, exchange: AssetExchange, status: AssetStatus = AssetStatus.ACTIVE) -> MagicMock:
    asset = MagicMock(spec=Asset)
    asset.symbol = symbol
    asset.name = name
    asset.exchange = exchange
    asset.status = status
    return asset


def test_get_symbol_list(mocker: MockerFixture) -> None:
    mocker.patch("turtle.data.alpaca_symbol.TradingClient")
    mock_get_symbol_list_db = mocker.patch.object(
        AlpacaSymbolRepo, "_get_symbol_list_db", return_value=mocked_data
    )

    repo = AlpacaSymbolRepo(engine=mocker.Mock(), alpaca_api_key="dummy_key", alpaca_secret_key="dummy_secret")
    symbols = repo.get_symbol_list(country="USA")

    expected_symbols = [
        Symbol(symbol="AMZN", name="Amazon.com Inc.", exchange="NASDAQ", country="USA"),
        Symbol(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", country="USA"),
    ]

    assert symbols == expected_symbols
    mock_get_symbol_list_db.assert_called_once_with("USA")


def test_get_symbol_list_empty(mocker: MockerFixture) -> None:
    mocker.patch("turtle.data.alpaca_symbol.TradingClient")
    mock_get_symbol_list_db = mocker.patch.object(
        AlpacaSymbolRepo, "_get_symbol_list_db", return_value=[]
    )

    repo = AlpacaSymbolRepo(engine=mocker.Mock(), alpaca_api_key="dummy_key", alpaca_secret_key="dummy_secret")
    symbols = repo.get_symbol_list(country="USA")

    assert symbols == []
    mock_get_symbol_list_db.assert_called_once_with("USA")


def test_get_alpaca_asset_list_returns_data(mocker: MockerFixture) -> None:
    mock_trading_client = mocker.patch("turtle.data.alpaca_symbol.TradingClient").return_value
    assets = [
        _make_asset("AAPL", "Apple Inc.", AssetExchange.NASDAQ),
        _make_asset("MSFT", "Microsoft Corporation", AssetExchange.NASDAQ),
    ]
    mock_trading_client.get_all_assets.return_value = assets

    repo = AlpacaSymbolRepo(engine=mocker.Mock(), alpaca_api_key="test_key", alpaca_secret_key="test_secret")
    result = repo.get_alpaca_asset_list()

    assert result == assets
    mock_trading_client.get_all_assets.assert_called_once()


def test_get_alpaca_asset_list_api_key_not_in_log(mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
    mock_trading_client = mocker.patch("turtle.data.alpaca_symbol.TradingClient").return_value
    mock_trading_client.get_all_assets.return_value = []

    repo = AlpacaSymbolRepo(engine=mocker.Mock(), alpaca_api_key="super_secret_key", alpaca_secret_key="super_secret_secret")
    with caplog.at_level(logging.DEBUG, logger="turtle.data.alpaca_symbol"):
        repo.get_alpaca_asset_list()

    assert "super_secret_key" not in caplog.text
    assert "super_secret_secret" not in caplog.text


def test_map_alpaca_asset(mocker: MockerFixture) -> None:
    mocker.patch("turtle.data.alpaca_symbol.TradingClient")
    repo = AlpacaSymbolRepo(engine=mocker.Mock(), alpaca_api_key="k", alpaca_secret_key="s")

    asset = _make_asset("AAPL", "Apple Inc.", AssetExchange.NASDAQ)
    result = repo.map_alpaca_asset(asset)

    assert result["symbol"] == "AAPL"
    assert result["name"] == "Apple Inc."
    assert result["exchange"] == "NASDAQ"
    assert result["country"] == "USA"
    assert result["currency"] == "USD"
    assert result["source"] == "alpaca"
    assert result["status"] == "ACTIVE"
    assert result["isin"] is None


def test_map_alpaca_asset_inactive(mocker: MockerFixture) -> None:
    mocker.patch("turtle.data.alpaca_symbol.TradingClient")
    repo = AlpacaSymbolRepo(engine=mocker.Mock(), alpaca_api_key="k", alpaca_secret_key="s")

    asset = _make_asset("DEAD", "Dead Corp.", AssetExchange.NYSE, status=AssetStatus.INACTIVE)
    result = repo.map_alpaca_asset(asset)

    assert result["status"] == "INACTIVE"
