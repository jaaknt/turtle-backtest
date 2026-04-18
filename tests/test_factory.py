from turtle.strategy.factory import get_trading_strategy
from turtle.strategy.trading.momentum import MomentumStrategy
from unittest.mock import MagicMock


def test_factory_momentum_uses_polars() -> None:
    mock_repo = MagicMock()
    mock_ranking = MagicMock()
    strategy = get_trading_strategy("momentum", mock_ranking, mock_repo)
    assert isinstance(strategy, MomentumStrategy)
    assert strategy.use_polars is True
