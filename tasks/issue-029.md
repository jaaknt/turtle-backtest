# Remove all ALPACA and  YFinance related code
Make code base smaller by removing all
- alpaca/yfinance related tables in alembic migrations
- alpaca related files @turtle/data folder
- alpace related servies in @turtle/service folder
- scripts/daily_eod_update.py and all dependencies
- update tests accordingly
- update documentation by removing alpaca related documentation from *.md files
- change version to 1.0.0 in @pyproject.toml

## Implementation Plan
 Context

 The codebase historically used Alpaca (for market data) and Yahoo Finance (for company fundamentals) alongside EODHD. All data now flows through EODHD. This removes the dead
 Alpaca/YFinance code to simplify the codebase and bump the version to 1.0.0.

 ---
 Files to DELETE

 ┌────────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
 │                File                │                              Reason                               │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ turtle/data/alpaca_bars_history.py │ Alpaca-specific bars history repo (never used in production path) │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ turtle/data/alpaca_company.py      │ Alpaca/YFinance company repo                                      │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ turtle/data/alpaca_symbol.py       │ Alpaca symbol repo                                                │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ turtle/data/alpaca_tables.py       │ Table defs for non-existent alpaca schema                         │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ turtle/service/alpaca_service.py   │ DataUpdateService wrapping all alpaca repos                       │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ scripts/daily_eod_update.py        │ Only entry point for Alpaca/YFinance updates                      │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ tests/test_alpaca_bars_history.py  │ Tests for deleted repo                                            │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ tests/test_alpaca_company.py       │ Tests for deleted repo                                            │
 ├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
 │ tests/test_alpaca_symbol.py        │ Tests for deleted repo                                            │
 └────────────────────────────────────┴───────────────────────────────────────────────────────────────────┘

 ---
 Files to MODIFY

 turtle/data/bars_history.py

 - Remove all alpaca.* imports
 - Remove alpaca_api_key / alpaca_api_secret params from __init__; keep only engine
 - Remove StockHistoricalDataClient initialization
 - Remove map_alpaca_bars_history(), update_bars_history(), _map_timeframe_unit()
 - Remove save_bars_history() and save_bars_history_bulk() — only called internally by the removed update_bars_history
 - Keep: _get_bars_history_db(), get_bars_history(), convert_df(), get_ticker_history()

 turtle/data/company.py

 - Remove yfinance import
 - Remove map_yahoo_company_data(), fetch_company_data(), update_company_info()
 - Keep: save_company_list(), save_company_list_bulk(), _get_company_list_db(), get_company_list(), convert_df()

 turtle/config/model.py

 - Remove alpaca field from AppConfig dataclass

 turtle/config/settings.py

 - Remove ALPACA_API_KEY and ALPACA_SECRET_KEY from required_env_vars
 - Remove lines that load alpaca keys into data["app"]["alpaca"]

 config/settings.toml

 - Remove alpaca.api_key and alpaca.secret_key lines

 scripts/backtest.py

 - Change BarsHistoryRepo(engine=settings.engine, alpaca_api_key=..., alpaca_api_secret=...) → BarsHistoryRepo(engine=settings.engine)

 scripts/portfolio_runner.py

 - Same change as backtest.py for BarsHistoryRepo constructor

 scripts/signal_runner.py

 - Remove AppConfig import if unused after change
 - Change BarsHistoryRepo(engine, alpaca_api_key=..., alpaca_api_secret=...) → BarsHistoryRepo(engine)

 app.py

 - Change BarsHistoryRepo(engine, settings.app.alpaca["api_key"], settings.app.alpaca["secret_key"]) → BarsHistoryRepo(engine)

 tests/conftest.py

 - Remove ALPACA_API_KEY and ALPACA_SECRET_KEY from required_env_vars fixture

 tests/test_settings.py

 - Remove alpaca assertions from TestAppConfig
 - Remove ALPACA vars from TestSettingsFromToml tests (env var lists, assertions)

 pyproject.toml

 - Remove alpaca-py>=0.43.2
 - Remove yfinance>=1.2.0
 - Bump version from 0.3.0 to 1.0.0

 CLAUDE.md

 - Remove alpaca-py from Core Libraries list
 - Remove daily_eod_update.py from Scripts Quick Reference table
 - Remove DataUpdateService from Service Layer table
 - Remove Alpaca from Data Sources section
 - Update any troubleshooting items that reference Alpaca

 README.md

 - Remove references to Alpaca and Yahoo Finance
 - Remove examples/docs for daily_eod_update.py and DataUpdateService

 ---
 What NOT to change

 - Alembic migrations: The data_source_type ENUM includes 'alpaca' and 'yahoo' — these are already applied to the DB and altering PostgreSQL ENUMs is complex. Leave migrations and
 tables.py ENUM definition untouched.
 - turtle/data/company.py read/save methods — still useful for EODHD company data flow
 - turtle/data/tables.py — ENUM definition stays as-is (maps to existing DB type)

 ---
 Verification

 # Run all tests — should pass with no alpaca-related failures
 uv run pytest

 # Check for any remaining alpaca/yfinance imports
 grep -r "alpaca\|yfinance" turtle/ scripts/ tests/ --include="*.py" -l

 # Lint check
 uv run ruff check .
