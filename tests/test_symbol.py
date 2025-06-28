from pytest_mock import MockerFixture

from turtle.data.symbol import SymbolRepo
from turtle.data.models import Symbol


# Example data returned by the mocked _get_symbol_list_db method
mocked_data = [
    ("AMZN", "Amazon.com Inc.", "NASDAQ", "USA"),
    ("TSLA", "Tesla Inc.", "NASDAQ", "USA"),
]


def test_get_symbol_list(mocker: MockerFixture) -> None:
    # Mock the _get_symbol_list_db method
    mock_get_symbol_list_db = mocker.patch.object(
        SymbolRepo, "_get_symbol_list_db", return_value=mocked_data
    )

    repo = SymbolRepo(pool=mocker.Mock(), api_key="dummy_key")

    # Call the method you want to test
    symbols = repo.get_symbol_list(country="USA")

    # Expected result
    expected_symbols = [
        Symbol(symbol="AMZN", name="Amazon.com Inc.", exchange="NASDAQ", country="USA"),
        Symbol(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", country="USA"),
    ]

    # Assertions
    assert symbols == expected_symbols
    mock_get_symbol_list_db.assert_called_once_with("USA")


def test_get_symbol_list_empty(mocker: MockerFixture) -> None:
    # Mock the _get_symbol_list_db method to return an empty list
    mock_get_symbol_list_db = mocker.patch.object(
        SymbolRepo, "_get_symbol_list_db", return_value=[]
    )

    # Instantiate SymbolRepo with the mock connection
    repo = SymbolRepo(pool=mocker.Mock(), api_key="dummy_key")

    # Call the method you want to test
    symbols = repo.get_symbol_list(country="USA")

    # Assertions for empty result
    assert symbols == []
    mock_get_symbol_list_db.assert_called_once_with("USA")


def test_get_symbol_list_with_symbol_filter(mocker: MockerFixture) -> None:
    # Extended mock data for testing symbol filtering
    extended_mocked_data = [
        ("AAPL", "Apple Inc.", "NASDAQ", "USA"),
        ("AMZN", "Amazon.com Inc.", "NASDAQ", "USA"),
        ("GOOGL", "Alphabet Inc.", "NASDAQ", "USA"),
        ("MSFT", "Microsoft Corporation", "NASDAQ", "USA"),
        ("TSLA", "Tesla Inc.", "NASDAQ", "USA"),
    ]

    # Mock the _get_symbol_list_db method
    mock_get_symbol_list_db = mocker.patch.object(
        SymbolRepo, "_get_symbol_list_db", return_value=extended_mocked_data
    )

    repo = SymbolRepo(pool=mocker.Mock(), api_key="dummy_key")

    # Test 1: Filter symbols starting with "M" or later alphabetically
    symbols = repo.get_symbol_list(country="USA", symbol="M")
    
    expected_symbols = [
        Symbol(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ", country="USA"),
        Symbol(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", country="USA"),
    ]
    
    assert symbols == expected_symbols
    mock_get_symbol_list_db.assert_called_with("USA")

    # Test 2: Filter with symbol that matches exactly
    symbols = repo.get_symbol_list(country="USA", symbol="GOOGL")
    
    expected_symbols = [
        Symbol(symbol="GOOGL", name="Alphabet Inc.", exchange="NASDAQ", country="USA"),
        Symbol(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ", country="USA"),
        Symbol(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", country="USA"),
    ]
    
    assert symbols == expected_symbols

    # Test 3: Filter with symbol that returns no results (after last symbol)
    symbols = repo.get_symbol_list(country="USA", symbol="Z")
    assert symbols == []

    # Test 4: Empty string should return all symbols (default behavior)
    symbols = repo.get_symbol_list(country="USA", symbol="")
    
    expected_all_symbols = [
        Symbol(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", country="USA"),
        Symbol(symbol="AMZN", name="Amazon.com Inc.", exchange="NASDAQ", country="USA"),
        Symbol(symbol="GOOGL", name="Alphabet Inc.", exchange="NASDAQ", country="USA"),
        Symbol(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ", country="USA"),
        Symbol(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", country="USA"),
    ]
    
    assert symbols == expected_all_symbols
