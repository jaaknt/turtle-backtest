"""Sync Engine-based repositories for analytical reads."""

from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.repository.query.ticker import TickerQueryRepository

__all__ = ["DailyBarsQueryRepository", "TickerQueryRepository"]
