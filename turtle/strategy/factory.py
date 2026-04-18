"""Strategy factory functions shared across CLI scripts.

Use these factories when instantiating strategies by name from CLI arguments
(e.g. ``--trading-strategy darvas_box``). They own the canonical string →
class mapping and raise ``ValueError`` with a descriptive message for unknown
names. Do not duplicate these mappings in individual scripts.

For programmatic use where the concrete class is already known, instantiate
the strategy directly instead of going through the factory.
"""

from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.exit.atr import ATRExitStrategy
from turtle.strategy.exit.base import ExitStrategy
from turtle.strategy.exit.buy_and_hold import BuyAndHoldExitStrategy
from turtle.strategy.exit.ema import EMAExitStrategy
from turtle.strategy.exit.macd import MACDExitStrategy
from turtle.strategy.exit.profit_loss import ProfitLossExitStrategy
from turtle.strategy.exit.trailing_percentage_loss import TrailingPercentageLossExitStrategy
from turtle.strategy.ranking.base import RankingStrategy
from turtle.strategy.ranking.breakout_quality import BreakoutQualityRanking
from turtle.strategy.ranking.momentum import MomentumRanking
from turtle.strategy.ranking.volume_momentum import VolumeMomentumRanking
from turtle.strategy.trading.base import TradingStrategy
from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
from turtle.strategy.trading.mars import MarsStrategy
from turtle.strategy.trading.momentum import MomentumStrategy


def get_trading_strategy(strategy_name: str, ranking_strategy: RankingStrategy, bars_history: OhlcvAnalyticsRepository) -> TradingStrategy:
    """Create a trading strategy instance by name."""
    strategy_classes: dict[str, type[TradingStrategy]] = {
        "darvas_box": DarvasBoxStrategy,
        "mars": MarsStrategy,
        "momentum": MomentumStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown trading strategy '{strategy_name}'. Available strategies: {available}")

    return strategy_class(
        bars_history=bars_history,
        ranking_strategy=ranking_strategy,
        time_frame_unit=TimeFrameUnit.DAY,
    )


def get_exit_strategy(strategy_name: str, bars_history: OhlcvAnalyticsRepository) -> ExitStrategy:
    """Create an exit strategy instance by name."""
    strategy_classes: dict[str, type[ExitStrategy]] = {
        "buy_and_hold": BuyAndHoldExitStrategy,
        "profit_loss": ProfitLossExitStrategy,
        "ema": EMAExitStrategy,
        "macd": MACDExitStrategy,
        "atr": ATRExitStrategy,
        "trailing_percentage_loss": TrailingPercentageLossExitStrategy,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown exit strategy '{strategy_name}'. Available strategies: {available}")

    return strategy_class(bars_history=bars_history)


def get_ranking_strategy(strategy_name: str) -> RankingStrategy:
    """Create a ranking strategy instance by name."""
    strategy_classes: dict[str, type[RankingStrategy]] = {
        "momentum": MomentumRanking,
        "volume_momentum": VolumeMomentumRanking,
        "breakout_quality": BreakoutQualityRanking,
    }

    strategy_class = strategy_classes.get(strategy_name.lower())
    if strategy_class is None:
        available = ", ".join(strategy_classes.keys())
        raise ValueError(f"Unknown ranking strategy '{strategy_name}'. Available strategies: {available}")

    return strategy_class()
