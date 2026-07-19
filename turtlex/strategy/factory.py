"""Strategy factory functions shared across CLI scripts.

Use these factories when instantiating strategies by name from CLI arguments
(e.g. ``--trading-strategy darvas_box``). They own the canonical string →
class mapping and raise ``ValueError`` with a descriptive message for unknown
names. Do not duplicate these mappings in individual scripts.

For programmatic use where the concrete class is already known, instantiate
the strategy directly instead of going through the factory.
"""

from collections.abc import Callable

from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.strategy.exit.atr import ATRExitStrategy
from turtlex.strategy.exit.base import ExitStrategy
from turtlex.strategy.exit.buy_and_hold import BuyAndHoldExitStrategy
from turtlex.strategy.exit.ema import EMAExitStrategy
from turtlex.strategy.exit.macd import MACDExitStrategy
from turtlex.strategy.exit.profit_loss import ProfitLossExitStrategy
from turtlex.strategy.exit.trailing_percentage_loss import TrailingPercentageLossExitStrategy
from turtlex.strategy.ranking.base import RankingStrategy
from turtlex.strategy.ranking.breakout_quality import BreakoutQualityRanking
from turtlex.strategy.ranking.momentum import MomentumRanking
from turtlex.strategy.ranking.volume_momentum import VolumeMomentumRanking
from turtlex.strategy.trading.base import TradingStrategy
from turtlex.strategy.trading.darvas_box import DarvasBoxStrategy
from turtlex.strategy.trading.mars import MarsStrategy
from turtlex.strategy.trading.momentum import MomentumStrategy
from turtlex.strategy.trading.qullamaggie import QullamaggieStrategy


def get_trading_strategy(strategy_name: str, ranking_strategy: RankingStrategy, bars_history: DailyBarsQueryRepository) -> TradingStrategy:
    """Create a trading strategy instance by name."""
    strategies: dict[str, Callable[[], TradingStrategy]] = {
        "darvas_box": lambda: DarvasBoxStrategy(bars_history, ranking_strategy),
        "mars": lambda: MarsStrategy(bars_history, ranking_strategy),
        "momentum": lambda: MomentumStrategy(bars_history, ranking_strategy),
        "qullamaggie": lambda: QullamaggieStrategy(bars_history, ranking_strategy),
    }

    factory = strategies.get(strategy_name.lower())
    if factory is None:
        available = ", ".join(strategies.keys())
        raise ValueError(f"Unknown trading strategy '{strategy_name}'. Available strategies: {available}")

    return factory()


def get_exit_strategy(strategy_name: str, bars_history: DailyBarsQueryRepository) -> ExitStrategy:
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
