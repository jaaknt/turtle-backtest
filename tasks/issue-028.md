# Refactor EODHD vs ALPACA downloaded data tables
Currently there are 2 different approaches to get company/historical data old Alpaca approach
@daily_eod_update.py and new EODHD approach @download_eodhd_data.py.
As different data is downloaded the current solution does not suite well anymore

The goal is to separate these processes outcomes to different schemas to be saved
- Alpaca data to tables in alpaca schema (does not exist currently)
- EODHD data to tables in turtle schema (current approach)

The steps to be involved
- create new schema alpaca using alembic
- create new tables in alpaca schema for data downloading
- @daily_eod_update.py saves data only to alpaca schema tables
- @alpaca_service.py saves data only in alpaca schema tables
- lower layer processing must be also in different files eodhd vs alpaca

Migration is not in the scope

## Implementation Plan

### Context
All data currently lands in the `turtle` PostgreSQL schema regardless of source. The EODHD
download workflow (`download_eodhd_data.py` / `eodhd_service.py`) already correctly targets
`turtle.*` tables. The Alpaca workflow (`daily_eod_update.py` / `alpaca_service.py`) is
redirected to a new `alpaca` schema so the two pipelines are cleanly isolated at the DB
and code layer.

**Scope decision:**
- Write side only: only `alpaca_service.py` (and its new repos) changes target schema.
- Backtest/signal services that READ from `turtle.bars_history` are left unchanged.
- Migration of existing data is out of scope.

---

### Files Created

#### Alembic migrations
- `db/migrations/versions/2026_03_15_0001-a1b2c3d4e5f6_create_alpaca_schema.py`
  - `upgrade()`: `CREATE SCHEMA alpaca`
  - `downgrade()`: `DROP SCHEMA alpaca CASCADE`
  - `down_revision`: `"d5a4fcae22c8"`

- `db/migrations/versions/2026_03_15_0002-b2c3d4e5f6a1_create_alpaca_tables.py`
  - `upgrade()`: creates three tables:
    - `alpaca.symbol` — same columns as `turtle.ticker`
    - `alpaca.bars_history` — same columns as `turtle.bars_history` + index on (symbol, hdate)
    - `alpaca.company` — same columns as `turtle.company`
  - `downgrade()`: drops all three tables

#### Data layer
- `turtle/data/alpaca_tables.py` — SQLAlchemy Core table definitions with `schema="alpaca"`
  - `alpaca_symbol_table`, `alpaca_bars_history_table`, `alpaca_company_table`

- `turtle/data/alpaca_symbol.py` — `AlpacaSymbolRepo`
  - Targets `alpaca.symbol`; same public API as `SymbolRepo`

- `turtle/data/alpaca_bars_history.py` — `AlpacaBarsHistoryRepo`
  - Targets `alpaca.bars_history`; same public API as `BarsHistoryRepo`

- `turtle/data/alpaca_company.py` — `AlpacaCompanyRepo`
  - Targets `alpaca.company`; same public API as `CompanyRepo`

#### Tests
- `tests/test_alpaca_symbol.py`
- `tests/test_alpaca_bars_history.py`
- `tests/test_alpaca_company.py`

---

### Files Modified

#### `turtle/services/alpaca_service.py`
Replaced repo imports and instantiations:
```python
# Before
from turtle.data.bars_history import BarsHistoryRepo
from turtle.data.company import CompanyRepo
from turtle.data.symbol import SymbolRepo

# After
from turtle.data.alpaca_bars_history import AlpacaBarsHistoryRepo
from turtle.data.alpaca_company import AlpacaCompanyRepo
from turtle.data.alpaca_symbol import AlpacaSymbolRepo
```
Attribute names (`symbol_repo`, `bars_history`, `company_repo`) preserved so
`daily_eod_update.py` needs no changes.

---

### Verification
```bash
uv run alembic upgrade head   # apply migrations (requires running DB)
uv run pytest                  # 105 tests pass
uv run ruff check .            # no lint errors
```
