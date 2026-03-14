"""Exit strategies package."""

from .atr import ATRExitStrategy
from .base import ExitStrategy
from .buy_and_hold import BuyAndHoldExitStrategy
from .ema import EMAExitStrategy
from .macd import MACDExitStrategy
from .profit_loss import ProfitLossExitStrategy

__all__ = [
    "ExitStrategy",
    "BuyAndHoldExitStrategy",
    "ProfitLossExitStrategy",
    "EMAExitStrategy",
    "MACDExitStrategy",
    "ATRExitStrategy",
]
