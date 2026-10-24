---
name: add-trading-strategy
description: Steps and template for adding a new trading strategy to turtlex — base class to extend, where tests go, factory registration, and how to smoke-test it. Use when adding or scaffolding a new trading signal strategy.
---

# Adding a New Trading Strategy

1. **Create strategy file**: `turtlex/strategy/trading/my_strategy.py`
2. **Extend TradingStrategy base class**. The base class already implements `get_signals` and
   `collect_data`: `get_signals` loads bars into `self.pl_df` (with `warmup_period` days of history
   before `start_date`), returns `[]` when fewer than `min_bars` rows come back, and otherwise calls
   `_get_polars_signals` — the one abstract method. Don't override `get_signals`, or the data load
   and minimum-history check are skipped. Override `collect_data` only to post-filter bars (see
   `QullamaggieStrategy`), calling `super().collect_data(...)` first. `MomentumStrategy` is the
   simplest complete example.

   ```python
   import logging
   from datetime import date

   import polars as pl

   from turtlex.common.enums import TimeFrameUnit
   from turtlex.model import Signal
   from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
   from turtlex.strategy.ranking.base import RankingStrategy

   from .base import TradingStrategy

   logger = logging.getLogger(__name__)


   class MyStrategy(TradingStrategy):
       def __init__(
           self,
           bars_history: DailyBarsQueryRepository,
           ranking_strategy: RankingStrategy,
           time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
           warmup_period: int = 365,
           min_bars: int = 100,
       ):
           """
           Initialize the strategy.

           Args:
               bars_history: Repository for accessing historical bar data
               ranking_strategy: Strategy for ranking signals
               time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
               warmup_period: Calendar days of history loaded before start_date for indicators
               min_bars: Minimum number of bars required for analysis
           """
           super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)

       def calculate_indicators_pl(self) -> None:
           """Add indicator columns to self.pl_df."""
           self.pl_df = self.pl_df.with_columns(pl.col("close").rolling_max(20).alias("max_close_20"))

       def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
           self.calculate_indicators_pl()
           filtered = self.pl_df.filter(pl.col("date") >= start_date)
           if filtered.is_empty():
               logger.debug(f"{ticker} - no data after date filtering")
               return []
           signal_dates = filtered.filter(pl.col("close") >= pl.col("max_close_20"))["date"].to_list()
           return [Signal(ticker=ticker, date=d, ranking=self.ranking_strategy.ranking(self.pl_df, date=d)) for d in signal_dates]
   ```

   Constructor rules, enforced by the factory: the first two parameters must be `bars_history` and
   `ranking_strategy`, and every other parameter needs a default. Parameters annotated `int`,
   `float` or `str` become overridable with `--trading-param KEY=VALUE`. Extend
   `describe_parameters()` if the strategy carries its own thresholds. Fill `Signal.signal_close`
   if the strategy should support `signal-runner --persist`.

3. **Add tests**: `tests/strategy/trading/test_my_strategy.py` (mirror the source tree)
4. **Register in the factory**: Add your class to the `TRADING_STRATEGIES` registry in `turtlex/strategy/factory.py` — all CLIs derive their `--trading-strategy` choices from it. For programmatic use, instantiate the class directly and pass it to the service constructor.
5. **Test**: `uv run signal-runner --trading-strategy my_strategy --start-date 2024-06-03 --end-date 2024-06-03 --max-tickers 50`
   (2024-06-01 is a Saturday; `--max-tickers` keeps the smoke test from scanning the whole universe)
