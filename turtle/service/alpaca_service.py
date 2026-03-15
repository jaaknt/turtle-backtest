import logging
from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.config.model import AppConfig
from turtle.data.bars_history import BarsHistoryRepo
from turtle.data.company import CompanyRepo
from turtle.data.models import Symbol, SymbolGroup
from turtle.data.symbol import SymbolRepo
from turtle.data.symbol_group import SymbolGroupRepo

import pandas as pd
from sqlalchemy import Engine

logger = logging.getLogger(__name__)


class DataUpdateService:
    def __init__(
        self,
        engine: Engine,
        app_config: AppConfig,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 300,
    ) -> None:
        self.engine = engine
        self.time_frame_unit = time_frame_unit
        self.warmup_period = warmup_period

        self.symbol_repo = SymbolRepo(self.engine, app_config.eodhd["api_key"])
        self.symbol_group_repo = SymbolGroupRepo(self.engine)
        self.company_repo = CompanyRepo(self.engine)
        self.bars_history = BarsHistoryRepo(
            self.engine,
            app_config.alpaca["api_key"],
            app_config.alpaca["secret_key"],
        )

    def update_symbol_list(self) -> None:
        self.symbol_repo.update_symbol_list()

    def update_company_list(self, batch_size: int = 100) -> None:
        symbol_list: list[Symbol] = self.symbol_repo.get_symbol_list("USA")
        batch: list[dict] = []
        for symbol_rec in symbol_list:
            values = self.company_repo.fetch_company_data(symbol_rec.symbol)
            if values:
                logger.info(f"Fetched: {symbol_rec.symbol}")
                batch.append(values)
            if len(batch) >= batch_size:
                self.company_repo.save_company_list_bulk(batch)
                logger.info(f"Saved batch of {len(batch)} companies")
                batch.clear()
        if batch:
            self.company_repo.save_company_list_bulk(batch)
            logger.info(f"Saved final batch of {len(batch)} companies")

    def update_bars_history(self, start_date: datetime, end_date: datetime | None) -> None:
        symbol_list = self.symbol_repo.get_symbol_list("USA")
        for symbol_rec in symbol_list:
            self.bars_history.update_bars_history(symbol_rec.symbol, start_date, end_date)

    def get_company_list(self, symbol_list: list[str]) -> pd.DataFrame:
        self.company_repo.get_company_list(symbol_list)
        df = self.company_repo.convert_df()
        return df

    def get_symbol_group_list(self, symbol_group: str) -> list[SymbolGroup]:
        return self.symbol_group_repo.get_symbol_group_list(symbol_group)
