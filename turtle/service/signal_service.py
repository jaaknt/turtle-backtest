# from typing import List, Tuple
import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.service.market import MarketData

# from turtle.strategy.trading.momentum import MomentumStrategy
# from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
# from turtle.strategy.trading.mars import MarsStrategy
from turtle.strategy.trading.base import TradingStrategy

from sqlalchemy import Engine

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(
        self,
        engine: Engine,
        trading_strategy: TradingStrategy,
        market_ticker: str,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
    ) -> None:
        self.trading_strategy = trading_strategy
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.engine = engine
        self.bars_history = OhlcvAnalyticsRepository(self.engine)
        self.market_data = MarketData(self.bars_history, market_ticker)

    def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
        """Wrapper function for TradingStrategy.get_signals."""
        return self.trading_strategy.get_signals(ticker, start_date, end_date)
