from unittest.mock import MagicMock

import pytest

from turtlex.strategy.exit.atr import ATRExitStrategy
from turtlex.strategy.exit.base import ExitStrategy
from turtlex.strategy.exit.buy_and_hold import BuyAndHoldExitStrategy
from turtlex.strategy.exit.ema import EMAExitStrategy
from turtlex.strategy.exit.macd import MACDExitStrategy
from turtlex.strategy.exit.profit_loss import ProfitLossExitStrategy
from turtlex.strategy.exit.trailing_percentage_loss import TrailingPercentageLossExitStrategy
from turtlex.strategy.factory import (
    EXIT_STRATEGIES,
    RANKING_STRATEGIES,
    TRADING_STRATEGIES,
    get_exit_strategy,
    get_ranking_strategy,
    get_trading_strategy,
)
from turtlex.strategy.ranking.base import RankingStrategy
from turtlex.strategy.ranking.breakout_quality import BreakoutQualityRanking
from turtlex.strategy.ranking.momentum import MomentumRanking
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking
from turtlex.strategy.ranking.volume_momentum import VolumeMomentumRanking
from turtlex.strategy.trading.darvas_box import DarvasBoxStrategy
from turtlex.strategy.trading.momentum import MomentumStrategy
from turtlex.strategy.trading.qullamaggie import QullamaggieStrategy


def test_factory_creates_momentum_strategy() -> None:
    mock_repo = MagicMock()
    mock_ranking = MagicMock()
    strategy = get_trading_strategy("momentum", mock_ranking, mock_repo)
    assert isinstance(strategy, MomentumStrategy)


def test_factory_creates_qullamaggie_strategy() -> None:
    mock_repo = MagicMock()
    mock_ranking = MagicMock()
    strategy = get_trading_strategy("qullamaggie", mock_ranking, mock_repo)
    assert isinstance(strategy, QullamaggieStrategy)


def test_trading_strategy_name_is_case_insensitive() -> None:
    strategy = get_trading_strategy("DARVAS_BOX", MagicMock(), MagicMock())
    assert isinstance(strategy, DarvasBoxStrategy)


def test_unknown_trading_strategy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown trading strategy 'nope'.*Available"):
        get_trading_strategy("nope", MagicMock(), MagicMock())


@pytest.mark.parametrize(
    ("name", "expected_class"),
    [
        ("buy_and_hold", BuyAndHoldExitStrategy),
        ("profit_loss", ProfitLossExitStrategy),
        ("ema", EMAExitStrategy),
        ("macd", MACDExitStrategy),
        ("atr", ATRExitStrategy),
        ("trailing_percentage_loss", TrailingPercentageLossExitStrategy),
    ],
)
def test_factory_creates_exit_strategy(name: str, expected_class: type[ExitStrategy]) -> None:
    strategy = get_exit_strategy(name, MagicMock())
    assert isinstance(strategy, expected_class)


def test_unknown_exit_strategy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown exit strategy 'nope'.*Available"):
        get_exit_strategy("nope", MagicMock())


@pytest.mark.parametrize(
    ("name", "expected_class"),
    [
        ("momentum", MomentumRanking),
        ("volume_momentum", VolumeMomentumRanking),
        ("breakout_quality", BreakoutQualityRanking),
        ("qullamaggie", QullamaggieRanking),
    ],
)
def test_factory_creates_ranking_strategy(name: str, expected_class: type[RankingStrategy]) -> None:
    strategy = get_ranking_strategy(name)
    assert isinstance(strategy, expected_class)


def test_unknown_ranking_strategy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown ranking strategy 'nope'.*Available"):
        get_ranking_strategy("nope")


def test_every_registry_name_constructs() -> None:
    """Every registry key must be constructible through its factory function."""
    for name in TRADING_STRATEGIES:
        get_trading_strategy(name, MagicMock(), MagicMock())
    for name in EXIT_STRATEGIES:
        get_exit_strategy(name, MagicMock())
    for name in RANKING_STRATEGIES:
        get_ranking_strategy(name)
