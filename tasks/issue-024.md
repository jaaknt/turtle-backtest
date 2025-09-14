# Refactor @turtle/strategy/darvas_box.py 

> **Note**: This document references the original package structure. As of recent refactoring:
> - `turtle/strategy/` has been renamed to `turtle/signal/`
> - `trading_strategy.py` has been renamed to `base.py`
> - Exit strategies have been moved from `turtle/backtest/exit_strategy.py` to separate files in `turtle/exit/`
The goal is to refactor existing ranking calculation to 
separate folder @turtle/ranking.

new file @ranking_strategy.py
class RankingStrategy(ABC):
    """
    Abstract base class for ranking strategies.

    This interface defines ranking calculation
    """
    def ranking(self, signal: Signal) -> int:

new file @momentum.py
class MomentumRanking(RankingStrategy)
   def __init__(
        self,
        bars_history: BarsHistoryRepo, # OHLCV for calculation
    ): 
move all @turtle/strategy/darvas_box.py ranking calculations to this implementation
call ranking calculation from @turtle/strategy/darvas_box.py

## Implementation Plan

### 1. Create Ranking Module Structure
- Create `turtle/ranking/` directory
- Add `__init__.py` for proper module structure
- Create `ranking_strategy.py` with abstract base class
- Create `momentum.py` with MomentumRanking implementation

### 2. Extract Ranking Logic from DarvasBoxStrategy
Current ranking methods in darvas_box.py to extract:
- `_price_to_ranking(price: float) -> int`
- `_ranking_ema200_1month() -> int`
- `_ranking_ema200_3month() -> int`
- `_ranking_ema200_6month() -> int`
- `_ranking_period_high() -> int`
- `ranking(ticker: str, date_to_check: datetime) -> int`

### 3. Update Method Signatures
- Change ranking method signature from `ranking(ticker: str, date_to_check: datetime) -> int`
  to `ranking(signal: Signal) -> int` as specified in the abstract class
- Ensure the new implementation can handle the Signal object properly

### 4. Integration
- Update DarvasBoxStrategy to use MomentumRanking instance
- Maintain backward compatibility
- Ensure all existing functionality works correctly

### 5. Code Quality
- Add proper type hints and documentation
- Follow existing code conventions
- Run linting and fix any issues 
