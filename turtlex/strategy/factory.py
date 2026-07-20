"""Strategy factory functions shared across CLI scripts.

Use these factories when instantiating strategies by name from CLI arguments
(e.g. ``--trading-strategy darvas_box``). The module-level registries
(``TRADING_STRATEGIES``, ``EXIT_STRATEGIES``, ``RANKING_STRATEGIES``) own the
canonical string → class mapping; CLIs derive their argparse ``choices`` from
the registry keys. The ``get_*`` functions raise ``ValueError`` with a
descriptive message for unknown names. Do not duplicate these mappings in
individual scripts.

For programmatic use where the concrete class is already known, instantiate
the strategy directly instead of going through the factory.
"""

import inspect
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
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking
from turtlex.strategy.ranking.volume_momentum import VolumeMomentumRanking
from turtlex.strategy.trading.base import TradingStrategy
from turtlex.strategy.trading.darvas_box import DarvasBoxStrategy
from turtlex.strategy.trading.mars import MarsStrategy
from turtlex.strategy.trading.momentum import MomentumStrategy
from turtlex.strategy.trading.qullamaggie import QullamaggieStrategy

# Canonical name → class registries. Constructors within each category share a
# uniform signature, so CLIs derive argparse choices from the registry keys.
TRADING_STRATEGIES: dict[str, Callable[[DailyBarsQueryRepository, RankingStrategy], TradingStrategy]] = {
    "darvas_box": DarvasBoxStrategy,
    "mars": MarsStrategy,
    "momentum": MomentumStrategy,
    "qullamaggie": QullamaggieStrategy,
}

EXIT_STRATEGIES: dict[str, Callable[[DailyBarsQueryRepository], ExitStrategy]] = {
    "buy_and_hold": BuyAndHoldExitStrategy,
    "profit_loss": ProfitLossExitStrategy,
    "ema": EMAExitStrategy,
    "macd": MACDExitStrategy,
    "atr": ATRExitStrategy,
    "trailing_percentage_loss": TrailingPercentageLossExitStrategy,
}

RANKING_STRATEGIES: dict[str, Callable[[], RankingStrategy]] = {
    "momentum": MomentumRanking,
    "volume_momentum": VolumeMomentumRanking,
    "breakout_quality": BreakoutQualityRanking,
    "qullamaggie": QullamaggieRanking,
}


def get_trading_strategy(strategy_name: str, ranking_strategy: RankingStrategy, bars_history: DailyBarsQueryRepository) -> TradingStrategy:
    """Create a trading strategy instance by name."""
    strategy_class = TRADING_STRATEGIES.get(strategy_name.lower())
    if strategy_class is None:
        available = ", ".join(TRADING_STRATEGIES.keys())
        raise ValueError(f"Unknown trading strategy '{strategy_name}'. Available strategies: {available}")

    return strategy_class(bars_history, ranking_strategy)


def get_exit_strategy(strategy_name: str, bars_history: DailyBarsQueryRepository) -> ExitStrategy:
    """Create an exit strategy instance by name."""
    strategy_class = EXIT_STRATEGIES.get(strategy_name.lower())
    if strategy_class is None:
        available = ", ".join(EXIT_STRATEGIES.keys())
        raise ValueError(f"Unknown exit strategy '{strategy_name}'. Available strategies: {available}")

    return strategy_class(bars_history)


def resolve_exit_strategy_kwargs(exit_strategy: ExitStrategy, exit_params: list[tuple[str, str]]) -> dict[str, int | float | str]:
    """Coerce ``--exit-param key=value`` CLI pairs into kwargs for `exit_strategy.initialize()`.

    Each value is cast to the type annotation of the matching `initialize()` parameter
    (int/float/str). Parameters left unspecified are omitted so the strategy's own
    defaults apply.

    Args:
        exit_strategy: The concrete exit strategy instance to resolve parameters against.
        exit_params: (key, raw_value) pairs, typically from a repeatable CLI flag.

    Returns:
        Keyword arguments ready to forward to `exit_strategy.initialize(...)`.

    Raises:
        ValueError: If a key isn't a parameter of this exit strategy's `initialize()`,
            or a value can't be coerced to its annotated type.
    """
    params = {
        name: param
        for name, param in inspect.signature(exit_strategy.initialize).parameters.items()
        if name not in ("ticker", "start_date", "end_date")
    }
    kwargs: dict[str, int | float | str] = {}
    for key, raw_value in exit_params:
        param = params.get(key)
        if param is None:
            available = ", ".join(sorted(params)) or "(none)"
            raise ValueError(f"Unknown parameter '{key}' for {type(exit_strategy).__name__}. Available: {available}")
        try:
            kwargs[key] = param.annotation(raw_value) if param.annotation in (int, float, str) else raw_value
        except ValueError as e:
            raise ValueError(f"Invalid value for '{key}': {raw_value!r} ({e})") from e
    return kwargs


def get_ranking_strategy(strategy_name: str) -> RankingStrategy:
    """Create a ranking strategy instance by name."""
    strategy_class = RANKING_STRATEGIES.get(strategy_name.lower())
    if strategy_class is None:
        available = ", ".join(RANKING_STRATEGIES.keys())
        raise ValueError(f"Unknown ranking strategy '{strategy_name}'. Available strategies: {available}")

    return strategy_class()
