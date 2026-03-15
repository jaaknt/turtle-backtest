import logging
from turtle.data.alpaca_tables import alpaca_symbol_table
from turtle.data.models import Symbol
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.trading.models import Asset
from alpaca.trading.requests import GetAssetsRequest
from sqlalchemy import Engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


class AlpacaSymbolRepo:
    def __init__(self, engine: Engine, alpaca_api_key: str, alpaca_secret_key: str):
        self.engine = engine
        self.trading_client = TradingClient(alpaca_api_key, alpaca_secret_key)

    def map_alpaca_asset(self, asset: Asset) -> dict[str, Any]:
        return {
            "symbol": asset.symbol,
            "name": asset.name,
            "exchange": asset.exchange.value if asset.exchange else None,
            "country": "USA",
            "currency": "USD",
            "isin": None,
            "symbol_type": "stock",
            "source": "alpaca",
            "status": "ACTIVE" if asset.status == AssetStatus.ACTIVE else "INACTIVE",
        }

    def _get_symbol_list_db(self, country: str) -> list[Any]:
        table = alpaca_symbol_table
        stmt = (
            select(table.c.symbol, table.c.name, table.c.exchange, table.c.country)
            .where(table.c.country == country)
            .where(table.c.status == "ACTIVE")
            .order_by(table.c.symbol)
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return list(result.fetchall())

    def get_symbol_list(self, country: str, symbol: str = "") -> list[Symbol]:
        result = self._get_symbol_list_db(country)
        symbol_list = [Symbol(*row) for row in result]
        if symbol:
            symbol_list = [s for s in symbol_list if s.symbol >= symbol]
        logger.debug(f"{len(symbol_list)} symbols returned from database")
        return symbol_list

    def save_symbol_list(self, values: dict[str, Any]) -> None:
        self.save_symbol_list_bulk([values])

    def save_symbol_list_bulk(self, values_list: list[dict[str, Any]]) -> None:
        if not values_list:
            return
        table = alpaca_symbol_table
        stmt = pg_insert(table).values(values_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "name": stmt.excluded.name,
                "exchange": stmt.excluded.exchange,
                "country": stmt.excluded.country,
                "currency": stmt.excluded.currency,
                "isin": stmt.excluded.isin,
                "symbol_type": stmt.excluded.symbol_type,
                "source": stmt.excluded.source,
                "status": stmt.excluded.status,
                "modified_at": func.current_timestamp(),
            },
        )
        with self.engine.begin() as conn:
            logger.debug(f"Bulk inserting {len(values_list)} symbols into database")
            conn.execute(stmt)

    def get_alpaca_asset_list(self) -> list[Asset]:
        request = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
        )
        assets: list[Asset] = self.trading_client.get_all_assets(request)  # type: ignore[assignment]
        logger.debug(f"Fetched {len(assets)} assets from Alpaca")
        return assets

    def update_symbol_list(self) -> None:
        assets = self.get_alpaca_asset_list()
        values_list = [self.map_alpaca_asset(asset) for asset in assets if "-" not in asset.symbol]
        self.save_symbol_list_bulk(values_list)
