# from typing import List, Tuple
import logging
from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.config.model import AppConfig
from turtle.data.symbol import SymbolRepo
from turtle.repositories.analytics import OhlcvAnalyticsRepository

# from turtle.signal.momentum import MomentumStrategy
# from turtle.signal.darvas_box import DarvasBoxStrategy
# from turtle.signal.mars import MarsStrategy
from turtle.signal.base import TradingStrategy
from turtle.signal.market import MarketData
from turtle.signal.models import Signal

from sqlalchemy import Engine

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(
        self,
        engine: Engine,
        app_config: AppConfig,
        trading_strategy: TradingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
    ) -> None:
        self.trading_strategy = trading_strategy
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.engine = engine
        self.symbol_repo = SymbolRepo(self.engine, app_config.eodhd["api_key"])
        self.bars_history = OhlcvAnalyticsRepository(self.engine)
        self.market_data = MarketData(self.bars_history)

    def get_signals(self, ticker: str, start_date: datetime, end_date: datetime) -> list[Signal]:
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
        symbols = self.symbol_repo.get_symbol_list(symbol_filter)
        symbol_list = [symbol.symbol for symbol in symbols][:max_symbols]  # limits list to max symbols
        return symbol_list
