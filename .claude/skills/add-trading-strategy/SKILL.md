---
name: add-trading-strategy
description: Steps and template for adding a new trading strategy to turtlex — base class to extend, where tests go, factory registration, and how to smoke-test it. Use when adding or scaffolding a new trading signal strategy.
---

# Adding a New Trading Strategy

1. **Create strategy file**: `turtlex/strategy/trading/my_strategy.py`
2. **Extend TradingStrategy base class**:

   ```python
   from turtlex.model import Signal
   from turtlex.strategy.trading.base import TradingStrategy

   class MyStrategy(TradingStrategy):
       def collect_data(self, ticker: str, start_date: date, end_date: date) -> bool:
           ...

       def calculate_indicators(self) -> None:
           ...

       def get_signals(self, ticker: str, start_date: date, end_date: date) -> list[Signal]:
           # Your logic here
           return signals
   ```

3. **Add tests**: `tests/strategy/trading/test_my_strategy.py` (mirror the source tree)
4. **Register in the factory**: Add your class to the `TRADING_STRATEGIES` registry in `turtlex/strategy/factory.py` — all CLIs derive their `--trading-strategy` choices from it. For programmatic use, instantiate the class directly and pass it to the service constructor.
5. **Test**: `uv run signal-runner --trading-strategy my_strategy --start-date 2024-06-01 --end-date 2024-06-01`
