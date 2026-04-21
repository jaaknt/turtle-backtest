"""Strategy factory functions shared across CLI scripts.

Use these factories when instantiating strategies by name from CLI arguments
(e.g. ``--trading-strategy darvas_box``). They own the canonical string →
class mapping and raise ``ValueError`` with a descriptive message for unknown
names. Do not duplicate these mappings in individual scripts.

For programmatic use where the concrete class is already known, instantiate
the strategy directly instead of going through the factory.
"""

from collections.abc import Callable
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
    strategies: dict[str, Callable[[], TradingStrategy]] = {
        "darvas_box": lambda: DarvasBoxStrategy(bars_history, ranking_strategy),
        "mars": lambda: MarsStrategy(bars_history, ranking_strategy),
        "momentum": lambda: MomentumStrategy(bars_history, ranking_strategy),
    }

    factory = strategies.get(strategy_name.lower())
    if factory is None:
        available = ", ".join(strategies.keys())
        raise ValueError(f"Unknown trading strategy '{strategy_name}'. Available strategies: {available}")

    return factory()


def get_exit_strategy(strategy_name: str, bars_history: OhlcvAnalyticsRepository) -> ExitStrategy:
    """Create an exit strategy instance by name."""
    strategies: dict[str, Callable[[], ExitStrategy]] = {
        "buy_and_hold": lambda: BuyAndHoldExitStrategy(bars_history),
        "profit_loss": lambda: ProfitLossExitStrategy(bars_history),
        "ema": lambda: EMAExitStrategy(bars_history),
        "macd": lambda: MACDExitStrategy(bars_history),
        "atr": lambda: ATRExitStrategy(bars_history),
        "trailing_percentage_loss": lambda: TrailingPercentageLossExitStrategy(bars_history),
    }

    factory = strategies.get(strategy_name.lower())
    if factory is None:
        available = ", ".join(strategies.keys())
        raise ValueError(f"Unknown exit strategy '{strategy_name}'. Available strategies: {available}")

    return factory()


def get_ranking_strategy(strategy_name: str) -> RankingStrategy:
    """Create a ranking strategy instance by name."""
    strategies: dict[str, Callable[[], RankingStrategy]] = {
        "momentum": lambda: MomentumRanking(),
        "volume_momentum": lambda: VolumeMomentumRanking(),
        "breakout_quality": lambda: BreakoutQualityRanking(),
    }

    factory = strategies.get(strategy_name.lower())
    if factory is None:
        available = ", ".join(strategies.keys())
        raise ValueError(f"Unknown ranking strategy '{strategy_name}'. Available strategies: {available}")

    return factory()
