from datetime import datetime
from turtle.data.alpaca_bars_history import AlpacaBarsHistoryRepo
from turtle.data.models import Bar

from pytest_mock import MockerFixture


def test_get_bars_history(mocker: MockerFixture) -> None:
    mock_data = [
        (str(datetime(2023, 8, 1)), 100.0, 105.0, 95.0, 102.0, 1000000, 10000),
        (str(datetime(2023, 8, 2)), 102.0, 110.0, 100.0, 108.0, 1200000, 12000),
    ]

    mock_get_bars_history_db = mocker.patch.object(
        AlpacaBarsHistoryRepo, "_get_bars_history_db", return_value=mock_data
    )

    repo = AlpacaBarsHistoryRepo(
        engine=mocker.Mock(),
        alpaca_api_key="dummy_key",
        alpaca_api_secret="dummy_secret",
    )

    symbol = "META"
    start_date = datetime(2023, 8, 1)
    end_date = datetime(2023, 8, 2)
    bars = repo.get_bars_history(symbol, start_date, end_date)

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

    assert bars == expected_bars
    mock_get_bars_history_db.assert_called_once_with(symbol, start_date, end_date)


def test_get_bars_history_empty(mocker: MockerFixture) -> None:
    mock_get_bars_history_db = mocker.patch.object(
        AlpacaBarsHistoryRepo, "_get_bars_history_db", return_value=[]
    )

    repo = AlpacaBarsHistoryRepo(
        engine=mocker.Mock(),
        alpaca_api_key="dummy_key",
        alpaca_api_secret="dummy_secret",
    )

    bars = repo.get_bars_history("AAPL", datetime(2023, 8, 1), datetime(2023, 8, 2))

    assert bars == []
    mock_get_bars_history_db.assert_called_once()
