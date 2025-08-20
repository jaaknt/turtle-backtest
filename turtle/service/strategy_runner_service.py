import os
import pandas as pd
from psycopg_pool import ConnectionPool
from datetime import datetime
from typing import List, Tuple

import logging

from turtle.data.symbol import SymbolRepo
from turtle.data.company import CompanyRepo
from turtle.data.bars_history import BarsHistoryRepo
from turtle.data.models import Symbol
from turtle.strategy.market import MarketData

# from turtle.strategy.momentum import MomentumStrategy
# from turtle.strategy.darvas_box import DarvasBoxStrategy
# from turtle.strategy.mars import MarsStrategy
from turtle.strategy.trading_strategy import TradingStrategy
from turtle.strategy.models import Signal
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)
DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"


class StrategyRunnerService:
    def __init__(
        self,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,
    ) -> None:
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.pool: ConnectionPool = ConnectionPool(
            conninfo=DSN, min_size=5, max_size=50, max_idle=600
        )
        self.symbol_repo = SymbolRepo(self.pool, str(os.getenv("EODHD_API_KEY")))
        self.company_repo = CompanyRepo(self.pool)
        self.bars_history = BarsHistoryRepo(
            self.pool,
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )
        self.market_data = MarketData(self.bars_history)

    def get_tickers_list(
        self, date_to_check: datetime, trading_strategy: TradingStrategy
    ) -> List[dict]:
        symbol_list: List[Symbol] = self.symbol_repo.get_symbol_list("USA")
        stock_list: List[dict] = []
        ranking: int = 0
        for symbol_rec in symbol_list:
            if trading_strategy.is_trading_signal(symbol_rec.symbol, date_to_check):
                ranking = trading_strategy.ranking(symbol_rec.symbol, date_to_check)
                stock_list.append({"symbol": symbol_rec.symbol, "ranking": ranking})
        return stock_list

    def is_trading_signal(
        self, ticker: str, date_to_check: datetime, trading_strategy: TradingStrategy
    ) -> bool:
        """Wrapper function for TradingStrategy.is_trading_signal()."""
        return trading_strategy.is_trading_signal(ticker, date_to_check)

    def trading_signals_count(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        trading_strategy: TradingStrategy,
    ) -> int:
        """Wrapper function for TradingStrategy.trading_signals_count()."""
        return trading_strategy.trading_signals_count(ticker, start_date, end_date)

    def get_trading_signals(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        trading_strategy: TradingStrategy,
    ) -> List[Signal]:
        """Wrapper function for TradingStrategy.get_trading_signals."""
        return trading_strategy.get_trading_signals(ticker, start_date, end_date)

    def get_tickers_count(
        self,
        start_date: datetime,
        end_date: datetime,
        trading_strategy: TradingStrategy,
    ) -> List[Tuple]:
        symbol_list: List[Symbol] = self.symbol_repo.get_symbol_list("USA")
        momentum_stock_list = []
        for symbol_rec in symbol_list:
            count = trading_strategy.trading_signals_count(
                symbol_rec.symbol,
                start_date,
                end_date,
            )
            if count > 0:
                momentum_stock_list.append((symbol_rec.symbol, count))
                logger.info(f"Trading signal for {symbol_rec.symbol} - count {count}")

        # top_100 = sorted(self.momentum_stock_list, key=lambda x: x[1], reverse=True)[:100]
        # logger.info(f"Top 100 stocks with trade counts: {top_100}")
        # convert top_20 to list of symbols
        # logger.info(f"Top 100 stocks: {[x[0] for x in top_100]}")

        return momentum_stock_list

    def get_company_list(self, symbol_list: List[str]) -> pd.DataFrame:
        self.company_repo.get_company_list(symbol_list)
        df = self.company_repo.convert_df()
        return df
