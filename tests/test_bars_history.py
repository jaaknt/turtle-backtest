from datetime import datetime
from pytest_mock import MockerFixture

from turtle.data.bars_history import BarsHistoryRepo
from turtle.data.models import Bar


def test_get_bars_history(mocker: MockerFixture) -> None:
    # Mock data for META daily bars
    mock_data = [
        (str(datetime(2023, 8, 1)), 100.0, 105.0, 95.0, 102.0, 1000000, 10000),
        (str(datetime(2023, 8, 2)), 102.0, 110.0, 100.0, 108.0, 1200000, 12000),
    ]

    # Mock the _get_bars_history_db method using mocker
    mock_get_bars_history_db = mocker.patch.object(
        BarsHistoryRepo, "_get_bars_history_db", return_value=mock_data
    )

    # Instantiate BarsHistoryRepo with the mock connection
    repo = BarsHistoryRepo(
        pool=mocker.Mock(),
        alpaca_api_key="dummy_key",
        alpaca_api_secret="dummy_secret",
    )

    # Call the method you want to test
    symbol = "META"
    start_date = datetime(2023, 8, 1)
    end_date = datetime(2023, 8, 2)
    bars = repo.get_bars_history(symbol, start_date, end_date)

    # Expected result as a list of Bar dataclass instances
    expected_bars = [
        Bar(
            hdate=str(datetime(2023, 8, 1)),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
            trade_count=10000,
        ),
        Bar(
            hdate=str(datetime(2023, 8, 2)),
            open=102.0,
            high=110.0,
            low=100.0,
            close=108.0,
            volume=1200000,
            trade_count=12000,
        ),
    ]

    # Assertions
    assert bars == expected_bars
    mock_get_bars_history_db.assert_called_once_with(symbol, start_date, end_date)
