# Pandas → Polars Migration Plan

## Context

The codebase is partially migrated: exit strategies are already polars-native, `momentum.py` has a polars-first path, and the repository has a `get_bars_pl()` method. The goal is to complete the migration so all internal modules accept and return `pl.DataFrame` only — removing the pandas dual-path complexity and ultimately eliminating the `pandas-ta` dependency.

**Hard exception:** `turtle/portfolio/analytics.py` uses the `quantstats` library which requires `pd.Series`. It stays pandas and explicitly calls `get_bars_pd()`. This is a reporting layer, not an internal pipeline module.

---

## No-Change Files

These are already polars-native — zero changes needed:
- `turtle/strategy/exit/*.py` (all 6 strategies)
- `turtle/service/market.py`

---

## Execution Order

Steps must be done in this order — each step has no unresolved dependencies on later steps.

---

### Phase 1 — Ranking Layer (easiest, isolated)

**Files:** `turtle/strategy/ranking/base.py`, `momentum.py`, `breakout_quality.py`, `volume_momentum.py`

All three concrete strategies already do all computation in polars internally; the only pandas code is the `_to_polars(df)` call at the top of `ranking()` and the union type hints.

**Step 1 — `turtle/strategy/ranking/base.py`**
- Remove `import pandas as pd`
- Remove `use_polars` param from `__init__` and `self.use_polars` attribute
- Remove `_to_pandas()` and `_to_polars()` static methods entirely
- Change `ranking()` signature: `df: pd.DataFrame | pl.DataFrame` → `df: pl.DataFrame`

**Step 2 — Each of `ranking/momentum.py`, `ranking/breakout_quality.py`, `ranking/volume_momentum.py`** (same changes on all three)
- Remove `import pandas as pd`
- Remove `use_polars` from `__init__` and `super()` call
- Change `ranking()` signature to `df: pl.DataFrame`
- Replace the `pl_df = self._to_polars(df)` opener with direct polars operations on `df`

**Verify:** `uv run pytest tests/test_momentum_ranking.py tests/test_breakout_quality_ranking.py tests/test_volume_momentum_ranking.py` — the test fixtures in these files already pass `pl.DataFrame`, so all tests should pass.

---

### Phase 2 — Trading Strategies (hard work)

The three strategies must have working polars paths before the base class pandas branch is removed.

**Step 3 — `turtle/strategy/trading/momentum.py`** (simplest: polars path already complete)
- Remove `import pandas as pd`
- Remove `from pandas_ta.momentum import macd as ta_macd`
- Remove `from pandas_ta.overlap import ema as ta_ema`
- Remove `calculate_indicators()` (the full pandas method body)
- Remove `_get_pandas_signals()` entirely
- Remove `use_polars: bool = True` from `__init__` and from `super().__init__()` call

**Step 4 — `turtle/strategy/trading/darvas_box.py`** (no polars path yet — must add)

Add `import polars as pl`.

Add `calculate_indicators_pl()` — replicating the same indicator set currently calculated via `pandas_ta` in `calculate_indicators()`:

```python
def calculate_indicators_pl(self) -> None:
    self.pl_df = self.pl_df.with_columns(
        pl.col("close").rolling_max(20).alias("max_close_20"),
        pl.col("high").rolling_max(20).alias("max_high_20"),
        pl.col("close").shift(70).alias("close_70"),
        pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
        pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
        pl.col("close").ewm_mean(span=50, adjust=False).alias("ema_50"),
        pl.col("close").ewm_mean(span=200, adjust=False).alias("ema_200"),
        pl.col("volume").ewm_mean(span=10, adjust=False).alias("ema_volume_10"),
        (pl.col("close").ewm_mean(span=12, adjust=False)
         - pl.col("close").ewm_mean(span=26, adjust=False)).alias("macd"),
    ).with_columns(
        pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal"),
    )
```

Add `_get_polars_signals()` — vectorized polars equivalent of `_get_pandas_signals()`:

```python
def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
    self.calculate_indicators_pl()
    filtered = self.pl_df.filter(pl.col("date") >= start_date)
    if filtered.is_empty():
        return []
    buy_mask = (
        (pl.col("close") >= pl.col("max_close_20"))
        & (pl.col("close") >= pl.col("ema_10"))
        & (pl.col("close") >= pl.col("ema_20"))
        & (pl.col("ema_10") >= pl.col("ema_20"))
        & (pl.col("close") >= pl.col("ema_50"))
        & (pl.col("volume") >= pl.col("ema_volume_10") * 1.10)
        & (pl.col("macd") > pl.col("macd_signal"))
        & ((pl.col("close") - pl.col("open")) / pl.col("close") >= 0.008)
    )
    if self.time_frame_unit == TimeFrameUnit.DAY:
        buy_mask = buy_mask & (pl.col("close") >= pl.col("ema_200")) & (pl.col("ema_50") >= pl.col("ema_200"))
    signal_dates = filtered.filter(buy_mask)["date"].to_list()
    return [
        Signal(ticker=ticker, date=d, ranking=self.ranking_strategy.ranking(self.pl_df, date=d))
        for d in signal_dates
    ]
```

Remove: `calculate_indicators()` (pandas version), `_get_pandas_signals()`, `import numpy as np`, `import pandas as pd`, `from pandas_ta import ...`. Remove `use_polars=False` from `__init__`.

**Keep temporarily:** The four static methods `check_local_max()`, `check_local_min()`, `is_local_max_valid()`, `darvas_box_breakout()` still reference `pd.Series`/`pd.DataFrame`. They are dead code in the signal path but have unit tests. Keep `import pandas as pd` and `import numpy as np` only for these. See Phase 5 for full cleanup.

**EMA note:** `pandas_ta.ema()` uses SMA seeding; polars `ewm_mean(span=N, adjust=False)` starts from bar 0. With a 730-day warmup they converge long before `start_date`, so signal dates are equivalent.

**Step 5 — `turtle/strategy/trading/mars.py`** (no polars path — must add)

Add `import polars as pl`.

Add `calculate_indicators_pl()`:
```python
def calculate_indicators_pl(self) -> None:
    self.pl_df = self.pl_df.with_columns(
        pl.max_horizontal(
            pl.col("open").shift(1).rolling_max(4),
            pl.col("close").shift(1).rolling_max(4),
        ).alias("max_box_4"),
        pl.min_horizontal(
            pl.col("open").shift(1).rolling_min(4),
            pl.col("close").shift(1).rolling_min(4),
        ).alias("min_box_4"),
        pl.col("close").rolling_max(10).alias("max_close_10"),
        pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
        pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
        (pl.col("close").ewm_mean(span=12, adjust=False)
         - pl.col("close").ewm_mean(span=26, adjust=False)).alias("macd"),
        pl.col("volume").shift(1).rolling_mean(4).alias("ema_volume_4"),
    ).with_columns(
        pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal"),
        (pl.col("macd").ewm_mean(span=9, adjust=False) - pl.col("macd")).alias("macd_histogram"),
        ((pl.col("max_box_4") - pl.col("min_box_4")) / pl.col("close")).alias("consolidation_change"),
        ((pl.col("max_box_4") + pl.col("min_box_4")) / 2 - 0.02).alias("hard_stoploss"),
        (pl.col("volume") / pl.col("volume").shift(1).rolling_mean(4)).alias("volume_change"),
    )
```

Update `is_buy_signal()` signature from `row: pd.Series` to `row: dict`. Replace `pd.isna(row["macd"])` with `row["macd"] is None` (polars uses `None` for nulls, not `NaN`).

Add `_get_polars_signals()`:
```python
def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
    self.calculate_indicators_pl()
    filtered = self.pl_df.filter(pl.col("date") >= start_date)
    if filtered.is_empty():
        return []
    signals = []
    for row in filtered.iter_rows(named=True):
        if self.is_buy_signal(ticker, row):
            signals.append(Signal(
                ticker=ticker, date=row["date"],
                ranking=self.ranking_strategy.ranking(self.pl_df, date=row["date"])
            ))
    return signals
```

Rewrite `ranking()` to use `self.pl_df` instead of `self.df`:
```python
def ranking(self, ticker: str, date_to_check: date) -> int:
    if not self.collect_data(ticker, date_to_check, date_to_check):
        return 0
    target = self.pl_df.filter(pl.col("date") == date_to_check)
    if target.is_empty():
        return 0
    return self._price_to_ranking(float(target["close"][-1]))
```

Remove: `calculate_indicators()`, `_get_pandas_signals()`, `calculate_entries()`, `self.df_orig`, `import pandas as pd`, `from pandas_ta import ...`, `use_polars=False` from `__init__`.

**Step 6 — `turtle/strategy/trading/base.py`** (now that all subclasses have `_get_polars_signals`)
- Remove `import pandas as pd`
- Remove `self.df = pd.DataFrame()` and `self.use_polars` attribute
- Remove `use_polars` parameter from `__init__`
- Remove pandas branch from `collect_data()` — always uses `get_bars_pl()`
- Remove pandas branch from `get_signals()` — always calls `_get_polars_signals()`
- Change `_get_polars_signals()` from default-raise to `@abstractmethod`
- Remove `_get_pandas_signals()` abstract method
- Remove abstract `calculate_indicators()` — it was the pandas entrypoint; no longer needed

**Verify:** `uv run pytest tests/test_darvas_box.py tests/test_signal_processor.py` — some tests will need updating (see Phase 4).

---

### Phase 3 — Backtest / Service Layer

**Step 7 — `turtle/backtest/benchmark_utils.py`**

Switch `calculate_benchmark_list()` to call `get_bars_pl()`. Since `get_bars_pl()` accepts only `date` (not `datetime`), apply `.date()` coercion before calling.

Rewrite `calculate_benchmark()` to accept `pl.DataFrame` (no date index — date is a column):
```python
def calculate_benchmark(df: pl.DataFrame, ticker, entry_date, exit_date) -> Benchmark | None:
    if df.is_empty(): return None
    entry_d = entry_date.date() if isinstance(entry_date, datetime) else entry_date
    exit_d  = exit_date.date()  if isinstance(exit_date, datetime) else exit_date
    entry_data = df.filter(pl.col("date") >= entry_d)
    if entry_data.is_empty(): return None
    exit_data = df.filter(pl.col("date") <= exit_d)
    if exit_data.is_empty(): return None
    entry_price = float(entry_data["open"][0])
    exit_price  = float(exit_data["close"][-1])
    if entry_price <= 0: return None
    return Benchmark(ticker=ticker, return_pct=((exit_price - entry_price) / entry_price) * 100.0,
                     entry_date=entry_date, exit_date=exit_date)
```

Remove `import pandas as pd`.

**Step 8 — `turtle/backtest/processor.py`**

Three `get_ticker_history()` calls to replace with `get_bars_pl()`:

1. `calculate_entry_data()` (line 134): date column replaces index.
   ```python
   df = self.bars_history.get_bars_pl(signal.ticker, search_start, search_end, self.time_frame_unit)
   if df.is_empty(): return None
   row = df.row(0, named=True)
   entry_date = datetime.combine(row["date"], datetime.min.time())
   entry_price = float(row["open"])
   if entry_price <= 0: raise ValueError(...)
   ```

2. `calculate_exit_data()` (line 173): only used for the `.empty` guard — exit strategies fetch their own data.
   ```python
   df = self.bars_history.get_bars_pl(signal.ticker, entry_date.date(), ...)
   if df.is_empty(): raise ValueError(...)
   ```

3. `evaluate_exit_conditions()` (line 287): Same pattern — replace `.empty` check.

Remove `import pandas as pd`.

**Step 9 — `turtle/backtest/portfolio_processor.py`**

Two `get_ticker_history()` calls (lines 200, 295). Replace with `get_bars_pl()`. Convert `.empty` → `.is_empty()`, `.iloc[0]["col"]` → `df["col"][0]`.

**Step 10 — `turtle/service/portfolio_service.py`**

One `get_ticker_history()` call (line 254). Replace with `get_bars_pl()`. Replace `safe_float_conversion(df.iloc[0]["close"])` with `float(df["close"][0])`.

**Step 11 — `turtle/repository/analytics.py`** — delete `get_ticker_history()`

No internal callers remain after Steps 7–10. Delete the `get_ticker_history()` method entirely. Keep `get_bars_pd()` — `portfolio/analytics.py` still uses it.

**Verify:** `uv run pytest` — full test suite must pass.

---

### Phase 4 — Test Updates

**Step 12 — `tests/test_darvas_box.py`**
- `test_collect()`: mock `get_bars_pl` returning `pl.DataFrame` instead of `get_ticker_history` returning `pd.DataFrame`
- `test_calculate_indicators()`: set `strategy.pl_df = pl.DataFrame(...)` and call `strategy.calculate_indicators_pl()`; assert expected columns in `strategy.pl_df.columns`
- `check_local_max/min` static method tests: keep unchanged until Phase 5 cleanup
- Any test that passes `pd.DataFrame` to `ranking()`: rebuild fixture as `pl.DataFrame`

**Step 13 — `tests/test_momentum_strategy_parity.py`**
- Delete all `_pandas_*` test functions and parity tests (`test_both_paths_return_identical_signal_dates`, etc.)
- `_build_ohlcv()`: return only `pl.DataFrame`; delete the pandas half
- Remove `mock_repo.get_ticker_history` mock lines; use `get_bars_pl`
- Remove `use_polars=True/False` from `_make_strategy()` helper
- Remove `import pandas as pd`

**Step 14 — `tests/test_volume_momentum_ranking.py`**
- `create_test_data()`: return `pl.DataFrame` directly (list comprehension instead of `pd.date_range()`)
- `_make_constant_df()` and `_make_alternating_df()`: build `pl.DataFrame` directly instead of pandas-then-convert
- Remove remaining `pl.from_pandas()` calls and `import pandas as pd`

**Step 15 — `tests/test_signal_processor.py`**
- Replace all `mock_bars_history.get_ticker_history` with `get_bars_pl`
- Rebuild `sample_ticker_data` / `sample_spy_data` fixtures as `pl.DataFrame` with `date` column (not DatetimeIndex)
- `test_calculate_entry_data_success()`: `entry.date == datetime(2024, 1, 16)` (not `pd.Timestamp`)
- Remove `import pandas as pd`

**Step 16 — `tests/test_ohlcv_analytics_repository.py`**
- Remove tests for `get_ticker_history()` — method is gone
- Keep tests for `get_bars_pd()` and `get_bars_pl()`

**Step 17 — Delete `tests/test_pandas_ta_ema.py`**

Entire file tests `pandas_ta.ema()` accuracy — no longer part of production code.

---

### Phase 5 — Final Cleanup

**Step 18 — `turtle/strategy/trading/darvas_box.py`** — remove remaining pandas static methods

Rewrite `check_local_max(series: pd.Series)`, `check_local_min(series: pd.Series)`, `is_local_max_valid(df: pd.DataFrame)`, and `darvas_box_breakout()` to accept polars types or plain Python lists. Update corresponding tests in `test_darvas_box.py`. After this, remove `import pandas as pd` and `import numpy as np` completely.

**Step 19 — `turtle/common/pandas_utils.py`** — remove

`safe_float_conversion` becomes orphaned after Step 10. Delete the file and remove its import from `portfolio_service.py`.

**Step 20 — Remove `pandas-ta` from `pyproject.toml`**

Remove `"pandas-ta>=0.4.71b0"` from `[project] dependencies`. Run `uv lock`.

---

## Critical Files

| File | Change |
|------|--------|
| `turtle/strategy/trading/darvas_box.py` | Add polars path (Steps 4 + 18) |
| `turtle/strategy/trading/mars.py` | Add polars path (Step 5) |
| `turtle/strategy/trading/base.py` | Remove pandas branch (Step 6) |
| `turtle/strategy/trading/momentum.py` | Remove pandas path (Step 3) |
| `turtle/backtest/processor.py` | Switch 3 calls to `get_bars_pl` (Step 8) |
| `turtle/backtest/benchmark_utils.py` | Rewrite for polars DataFrame (Step 7) |
| `turtle/backtest/portfolio_processor.py` | Switch 2 calls (Step 9) |
| `turtle/service/portfolio_service.py` | Switch 1 call (Step 10) |
| `turtle/repository/analytics.py` | Delete `get_ticker_history()` (Step 11) |
| `turtle/strategy/ranking/base.py` | Remove conversion helpers (Step 1) |
| `turtle/strategy/ranking/*.py` | Remove pandas (Step 2) |
| `pyproject.toml` | Remove `pandas-ta` (Step 20) |

## Verification

After each phase: `uv run pytest` must be green before proceeding.

Final audit — should return only `portfolio/analytics.py` and `repository/analytics.py` (`get_bars_pd`):
```
grep -rn "pandas_ta\|get_ticker_history\|self\.df\b\|pd\.DataFrame\|import pandas" turtle/ --include="*.py"
```
