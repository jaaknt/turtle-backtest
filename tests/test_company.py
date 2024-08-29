from turtle.data.company import CompanyRepo
from turtle.data.models import Company

def test_get_company_list(mocker):
    # Mock data to return for MSFT and GOOG companies
    mock_data = [
        (
            "MSFT", "Microsoft Corporation", "USA", "1234", "5678", 150000, 1.5, 1.6e12, 1.5e12, 1.2, 10e9, 0.5, 2.0
        ),
        (
            "GOOG", "Alphabet Inc.", "USA", "4321", "8765", 100000, 1.0, 1.8e12, 1.7e12, 1.1, 12e9, 0.3, 1.8
        )
    ]

    # Use mocker.patch to mock the _get_company_list_db method in CompanyRepo
    mock_get_company_list_db = mocker.patch.object(
        CompanyRepo, '_get_company_list_db', return_value=mock_data
    )

    # Create a mock connection object
    mock_connection = mocker.Mock()

    # Instantiate CompanyRepo with the mock connection
    repo = CompanyRepo(connection=mock_connection)

    # Call the method you want to test
    symbols = ["MSFT", "GOOG"]
    companies = repo.get_company_list(symbols)

    # Expected result as a list of Company dataclass instances
    expected_companies = [
        Company(
            symbol="MSFT", short_name="Microsoft Corporation", country="USA", industry_code="1234", sector_code="5678",
            employees_count=150000, dividend_rate=1.5, market_cap=1.6e12, enterprice_value=1.5e12, beta=1.2,
            shares_float=10e9, short_ratio=0.5, recommodation_mean=2.0
        ),
        Company(
            symbol="GOOG", short_name="Alphabet Inc.", country="USA", industry_code="4321", sector_code="8765",
            employees_count=100000, dividend_rate=1.0, market_cap=1.8e12, enterprice_value=1.7e12, beta=1.1,
            shares_float=12e9, short_ratio=0.3, recommodation_mean=1.8
        )
    ]

    # Assertions
    assert companies == expected_companies
    mock_get_company_list_db.assert_called_once_with(symbols)