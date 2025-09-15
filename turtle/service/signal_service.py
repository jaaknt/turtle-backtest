import pandas as pd
from psycopg_pool import ConnectionPool
from datetime import datetime
# from typing import List, Tuple

import logging

from turtle.config.model import AppConfig
from turtle.data.symbol import SymbolRepo
from turtle.data.company import CompanyRepo
from turtle.data.bars_history import BarsHistoryRepo
from turtle.signal.market import MarketData

# from turtle.signal.momentum import MomentumStrategy
# from turtle.signal.darvas_box import DarvasBoxStrategy
# from turtle.signal.mars import MarsStrategy
from turtle.signal.base import TradingStrategy
from turtle.signal.models import Signal
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(
        self,
        pool: ConnectionPool,
        app_config: AppConfig,
        trading_strategy: TradingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
    ) -> None:
        self.trading_strategy = trading_strategy
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.pool = pool
        self.symbol_repo = SymbolRepo(self.pool, app_config.eodhd["api_key"])
        self.company_repo = CompanyRepo(self.pool)
        self.bars_history = BarsHistoryRepo(
            self.pool,
            app_config.alpaca["api_key"],
            app_config.alpaca["secret_key"],
        )
        self.market_data = MarketData(self.bars_history)

    def is_trading_signal(self, ticker: str, date_to_check: datetime) -> bool:
        """Wrapper function for TradingStrategy.has_signal()."""
        return self.trading_strategy.has_signal(ticker, date_to_check)

    def trading_signals_count(self, ticker: str, start_date: datetime, end_date: datetime) -> int:
        """Count trading signals using get_signals()."""
        return len(self.trading_strategy.get_signals(ticker, start_date, end_date))

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

    def get_company_list(self, symbol_names: list[str]) -> pd.DataFrame:
        """
        Get company information for the provided list of symbols.

        Args:
            symbol_names: List of stock symbols to get company data for

        Returns:
            DataFrame containing company information
        """
        self.company_repo.get_company_list(symbol_names)
        return self.company_repo.convert_df()
