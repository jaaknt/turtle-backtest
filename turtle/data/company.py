import time
import yfinance as yf  # type: ignore[import-untyped]
import logging
import pandas as pd
from typing import Any
from dataclasses import asdict
from sqlalchemy import Engine, select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from turtle.data.models import Company
from turtle.data.tables import company_table

logger = logging.getLogger(__name__)


class CompanyRepo:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.company_list: list[Company] = []

    def map_yahoo_company_data(self, symbol: str, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "short_name": data.get("shortName"),
            "country": data.get("country"),
            "industry_code": data.get("industry"),
            "sector_code": data.get("sector"),
            "employees_count": data.get("fullTimeEmployees"),
            "dividend_rate": data.get("dividendRate"),
            "trailing_pe_ratio": None if data.get("trailingPE") == "Infinity" else data.get("trailingPE"),
            "forward_pe_ratio": None if data.get("forwardPE") == "Infinity" else data.get("forwardPE"),
            "avg_volume": data.get("averageDailyVolume10Day"),
            "avg_price": data.get("fiftyDayAverage"),
            "market_cap": data.get("marketCap"),
            "enterprice_value": data.get("enterpriseValue"),
            "beta": data.get("beta"),
            "shares_float": data.get("floatShares"),
            "short_ratio": data.get("shortRatio"),
            "peg_ratio": data.get("pegRatio"),
            "recommodation_mean": data.get("recommendationMean"),
            "number_of_analysyst": data.get("numberOfAnalystOpinions"),
            "roa_value": data.get("returnOnAssets"),
            "roe_value": data.get("returnOnEquity"),
            "source": "yahoo",
        }

    def save_company_list(self, values: dict[str, Any]) -> None:
        table = company_table
        stmt = pg_insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "short_name": stmt.excluded.short_name,
                "country": stmt.excluded.country,
                "industry_code": stmt.excluded.industry_code,
                "sector_code": stmt.excluded.sector_code,
                "employees_count": stmt.excluded.employees_count,
                "dividend_rate": stmt.excluded.dividend_rate,
                "trailing_pe_ratio": stmt.excluded.trailing_pe_ratio,
                "forward_pe_ratio": stmt.excluded.forward_pe_ratio,
                "avg_volume": stmt.excluded.avg_volume,
                "avg_price": stmt.excluded.avg_price,
                "market_cap": stmt.excluded.market_cap,
                "enterprice_value": stmt.excluded.enterprice_value,
                "beta": stmt.excluded.beta,
                "shares_float": stmt.excluded.shares_float,
                "short_ratio": stmt.excluded.short_ratio,
                "peg_ratio": stmt.excluded.peg_ratio,
                "recommodation_mean": stmt.excluded.recommodation_mean,
                "number_of_analysyst": stmt.excluded.number_of_analysyst,
                "roa_value": stmt.excluded.roa_value,
                "roe_value": stmt.excluded.roe_value,
                "source": stmt.excluded.source,
                "modified_at": func.current_timestamp(),
            },
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def update_company_info(self, symbol: str) -> None:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.info

            if not data or not isinstance(data, dict):
                logger.warning(f"No valid data received for symbol: {symbol}")
                return

            if "symbol" not in data and "shortName" not in data:
                logger.warning(f"Symbol {symbol} not found in Yahoo Finance")
                return

            logger.info(f"Saving: {symbol}")
            values = self.map_yahoo_company_data(symbol, data)
            self.save_company_list(values)
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error fetching data for symbol {symbol}: {str(e)}")

    def convert_df(self) -> pd.DataFrame:
        dtypes = {
            "symbol": "string",
            "short_name": "string",
            "country": "string",
            "industry_code": "string",
            "sector_code": "string",
            "employees_count": "Int64",
            "dividend_rate": "Float64",
            "market_cap": "Float64",
            "enterprice_value": "Float64",
            "beta": "Float64",
            "shares_float": "Float64",
            "short_ratio": "Float64",
            "recommodation_mean": "Float64",
        }
        company_dicts = [asdict(company) for company in self.company_list]
        df = pd.DataFrame(company_dicts).astype(dtypes)
        df = df.set_index(["symbol"])
        return df

    def _get_company_list_db(self, symbol_list: list[str]) -> list[Any]:
        table = company_table
        stmt = (
            select(
                table.c.symbol,
                table.c.short_name,
                table.c.country,
                table.c.industry_code,
                table.c.sector_code,
                table.c.employees_count,
                table.c.dividend_rate,
                table.c.market_cap,
                table.c.enterprice_value,
                table.c.beta,
                table.c.shares_float,
                table.c.short_ratio,
                table.c.recommodation_mean,
            )
            .where(table.c.symbol.in_(symbol_list))
            .order_by(table.c.symbol)
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.fetchall()

    def get_company_list(self, symbol_list: list[str]) -> list[Company]:
        result = self._get_company_list_db(symbol_list)
        self.company_list = [Company(*row) for row in result]
        logger.debug(f"{len(result)} symbols returned from company table")
        logger.info(f"{__name__} is logger name")
        return self.company_list
