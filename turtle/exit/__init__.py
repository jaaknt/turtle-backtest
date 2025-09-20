"""Exit strategies package."""

from .base import ExitStrategy
from .buy_and_hold import BuyAndHoldExitStrategy
from .profit_loss import ProfitLossExitStrategy
from .ema import EMAExitStrategy
from .macd import MACDExitStrategy
from .atr import ATRExitStrategy

__all__ = [
    "ExitStrategy",
    "BuyAndHoldExitStrategy",
    "ProfitLossExitStrategy",
    "EMAExitStrategy",
    "MACDExitStrategy",
    "ATRExitStrategy",
]
