from turtle.strategy.factory import get_trading_strategy
from turtle.strategy.trading.momentum import MomentumStrategy
from unittest.mock import MagicMock


def test_factory_creates_momentum_strategy() -> None:
    mock_repo = MagicMock()
    mock_ranking = MagicMock()
    strategy = get_trading_strategy("momentum", mock_ranking, mock_repo)
    assert isinstance(strategy, MomentumStrategy)
