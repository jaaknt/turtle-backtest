# Document services in docs/service.md file
The goal is to document existing services
- create new file in docs directory service.md in separate paragraphs
- document these services in this file
  - @service/data_update_service.py
  - @service/strategy_runner_service.py
  - @service/strategy_performance_service.py
- add reference to this file in README.md  

## Plan
Based on analysis of the service files, the three services provide:

1. **DataUpdateService** - Data ingestion and management service that handles downloading and storing market data from multiple APIs (Alpaca, Yahoo Finance, EODHD) into PostgreSQL. Manages symbol lists, company fundamental data, and historical OHLCV data.

2. **StrategyRunnerService** - Strategy execution service that runs trading strategies against historical data. Provides functionality to check trading signals for specific dates/tickers, get lists of tickers with signals, and count trading signals across date ranges.

3. **StrategyPerformanceService** - Comprehensive strategy backtesting service that orchestrates performance testing across multiple symbols and time periods. Calculates detailed performance statistics, supports multiple holding periods, and provides benchmark comparisons against QQQ and SPY.

## Todo List
- [x] Analyze service files to understand functionality  
- [x] Create docs/service.md file documenting all three services
- [x] Add reference to docs/service.md file in README.md
- [ ] Run linting on all changes and fix any errors
