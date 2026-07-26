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
    describe_exit_parameters,
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


@pytest.mark.parametrize("raw_value", ["0.2", "0"])  # "0" must survive: a falsy override is still an override
def test_factory_applies_trading_param_override(raw_value: str) -> None:
    strategy = get_trading_strategy("qullamaggie", MagicMock(), MagicMock(), [("sma_thresh", raw_value)])
    assert isinstance(strategy, QullamaggieStrategy)
    assert strategy.sma_thresh == float(raw_value)


def test_factory_coerces_trading_params_to_their_annotated_types() -> None:
    strategy = get_trading_strategy("qullamaggie", MagicMock(), MagicMock(), [("min_bars", "120"), ("sma_thresh", "0.2")])
    assert strategy.min_bars == 120
    assert isinstance(strategy.min_bars, int)
    assert isinstance(strategy, QullamaggieStrategy)
    assert strategy.sma_thresh == 0.2


def test_factory_defaults_trading_params_when_not_overridden() -> None:
    strategy = get_trading_strategy("qullamaggie", MagicMock(), MagicMock())
    assert isinstance(strategy, QullamaggieStrategy)
    assert strategy.sma_thresh == 0.15


def test_trading_param_unknown_for_the_selected_strategy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown parameter 'sma_thresh' for trading strategy 'darvas_box'.*Available"):
        get_trading_strategy("darvas_box", MagicMock(), MagicMock(), [("sma_thresh", "0.2")])


def test_trading_param_with_uncoercible_value_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Invalid value for 'sma_thresh'"):
        get_trading_strategy("qullamaggie", MagicMock(), MagicMock(), [("sma_thresh", "loose")])


def test_non_scalar_constructor_parameters_are_not_overridable() -> None:
    """time_frame_unit is a TimeFrameUnit, so a raw string must not reach the constructor."""
    with pytest.raises(ValueError, match="Unknown parameter 'time_frame_unit' for trading strategy 'qullamaggie'"):
        get_trading_strategy("qullamaggie", MagicMock(), MagicMock(), [("time_frame_unit", "DAY")])


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


class TestDescribeExitParameters:
    def test_reports_initialize_defaults(self) -> None:
        params = describe_exit_parameters(ProfitLossExitStrategy(MagicMock()), {})

        assert params == {"profit_target": 10.0, "stop_loss": 5.0}

    def test_exit_param_overrides_win_over_defaults(self) -> None:
        params = describe_exit_parameters(ProfitLossExitStrategy(MagicMock()), {"profit_target": 15.0})

        assert params == {"profit_target": 15.0, "stop_loss": 5.0}

    def test_omits_the_per_position_arguments(self) -> None:
        """ticker/start_date/end_date are supplied per position, not configured by the user."""
        params = describe_exit_parameters(BuyAndHoldExitStrategy(MagicMock()), {})

        assert params == {"holding_days": 30}
