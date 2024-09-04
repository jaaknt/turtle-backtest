import os
import pandas as pd
from psycopg_pool import ConnectionPool
from datetime import datetime

import logging.config
import logging.handlers
from typing import Optional, List

from turtle.data.symbol import SymbolRepo
from turtle.data.company import CompanyRepo
from turtle.data.bars_history import BarsHistoryRepo

from turtle.data.models import Symbol
from turtle.strategy.market import MarketData
from turtle.strategy.momentum import MomentumStrategy


logger = logging.getLogger(__name__)
DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"


class DataUpdate:
    def __init__(self) -> None:
        self.pool: ConnectionPool = ConnectionPool(
            conninfo=DSN, min_size=5, max_size=10, max_idle=600
        )
        self.symbol_repo = SymbolRepo(self.pool, str(os.getenv("EODHD_API_KEY")))
        self.company_repo = CompanyRepo(self.pool)
        self.bars_history = BarsHistoryRepo(
            self.pool,
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )
        self.market_data = MarketData(self.bars_history)
        self.momentum_strategy = MomentumStrategy(self.bars_history)

    def update_symbol_list(self) -> None:
        self.symbol_repo.update_symbol_list()

    def update_company_list(self) -> None:
        symbol_list: List[Symbol] = self.symbol_repo.get_symbol_list("USA")
        for symbol_rec in symbol_list:
            self.company_repo.update_company_info(symbol_rec.symbol)

    def update_bars_history(
        self, start_date: datetime, end_date: Optional[datetime]
    ) -> None:
        symbol_list = self.symbol_repo.get_symbol_list("USA")
        for symbol_rec in symbol_list:
            self.bars_history.update_bars_history(
                symbol_rec.symbol, start_date, end_date
            )

    def momentum_stocks(self, start_date: datetime) -> List[str]:
        if self.market_data.spy_momentum(start_date):
            symbol_list: List[Symbol] = self.symbol_repo.get_symbol_list("USA")
            momentum_stock_list = []
            for symbol_rec in symbol_list:
                if self.momentum_strategy.weekly_momentum(
                    symbol_rec.symbol, start_date
                ):
                    momentum_stock_list.append(symbol_rec.symbol)
            return momentum_stock_list
        return []

    def get_company_list(self, symbol_list: List[str]) -> pd.DataFrame:
        self.company_repo.get_company_list(symbol_list)
        df = self.company_repo.convert_df()
        return df
