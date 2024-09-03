from turtle.data.symbol import SymbolRepo
from turtle.data.models import Symbol


# Example data returned by the mocked _get_symbol_list_db method
mocked_data = [
    ("AMZN", "Amazon.com Inc.", "NASDAQ", "USA"),
    ("TSLA", "Tesla Inc.", "NASDAQ", "USA"),
]


def test_get_symbol_list(mocker):
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


def test_get_symbol_list_empty(mocker):
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
