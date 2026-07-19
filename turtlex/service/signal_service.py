# from typing import List, Tuple
import logging
from datetime import date

from sqlalchemy import Engine

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Signal
from turtlex.repository.daily_bars_query import DailyBarsQueryRepository

# from turtlex.strategy.trading.momentum import MomentumStrategy
# from turtlex.strategy.trading.darvas_box import DarvasBoxStrategy
# from turtlex.strategy.trading.mars import MarsStrategy
from turtlex.strategy.trading.base import TradingStrategy

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(
        self,
        engine: Engine,
        trading_strategy: TradingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
    ) -> None:
        self.trading_strategy = trading_strategy
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.engine = engine
        self.bars_history = DailyBarsQueryRepository(self.engine)

    def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
        """Wrapper function for TradingStrategy.get_signals."""
        return self.trading_strategy.get_signals(ticker, start_date, end_date)
