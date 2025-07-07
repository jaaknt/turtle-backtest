import os
import pandas as pd
from psycopg_pool import ConnectionPool
from datetime import datetime

import logging.config
import logging.handlers
from typing import Optional, List

from turtle.data.symbol import SymbolRepo
from turtle.data.symbol_group import SymbolGroupRepo
from turtle.data.company import CompanyRepo
from turtle.data.bars_history import BarsHistoryRepo

from turtle.data.models import Symbol, SymbolGroup
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)
DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres"


class DataUpdate:
    def __init__(
        self,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 300,
    ) -> None:
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.pool: ConnectionPool = ConnectionPool(
            conninfo=DSN, min_size=5, max_size=10, max_idle=600
        )
        self.symbol_repo = SymbolRepo(self.pool, str(os.getenv("EODHD_API_KEY")))
        self.symbol_group_repo = SymbolGroupRepo(self.pool)
        self.company_repo = CompanyRepo(self.pool)
        self.bars_history = BarsHistoryRepo(
            self.pool,
            str(os.getenv("ALPACA_API_KEY")),
            str(os.getenv("ALPACA_SECRET_KEY")),
        )

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


    def get_company_list(self, symbol_list: List[str]) -> pd.DataFrame:
        self.company_repo.get_company_list(symbol_list)
        df = self.company_repo.convert_df()
        return df

    def get_symbol_group_list(self, symbol_group: str) -> List[SymbolGroup]:
        return self.symbol_group_repo.get_symbol_group_list(symbol_group)
