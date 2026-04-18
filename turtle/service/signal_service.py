# from typing import List, Tuple
import logging
from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.repository.eodhd import TickerQueryRepository

# from turtle.strategy.trading.momentum import MomentumStrategy
# from turtle.strategy.trading.darvas_box import DarvasBoxStrategy
# from turtle.strategy.trading.mars import MarsStrategy
from turtle.strategy.trading.base import TradingStrategy
from turtle.strategy.trading.market import MarketData
from turtle.strategy.trading.models import Signal

from sqlalchemy import Engine

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
        self.symbol_repo = TickerQueryRepository(self.engine)
        self.bars_history = OhlcvAnalyticsRepository(self.engine)
        self.market_data = MarketData(self.bars_history)

    def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
        """Wrapper function for TradingStrategy.get_signals."""
        return self.trading_strategy.get_signals(ticker, start_date, end_date)

    def get_symbol_list(self, symbol_filter: str = "USA", max_symbols: int = 10_000) -> list[str]:
        """
        Get list of symbols to test.

        Args:
            symbol_filter: Filter for symbol selection
            max_symbols: Optional limit on number of symbols

        Returns:
            List of symbol strings
        """
        return self.symbol_repo.get_symbol_list(symbol_filter, limit=max_symbols)
