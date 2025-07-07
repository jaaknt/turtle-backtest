# Stocks EOD database update

## Task
1. Create new task that updates EOD database every day
2. In first iteration implement local process that must be started manually every day  

## Plan

### Analysis
The system already has a `DataUpdate` class in `turtle/service/data_update.py` that handles data updates via Alpaca API, Yahoo Finance, and EODHD. Currently, `main.py` runs data updates for large date ranges manually. The `update_bars_history` method processes all symbols for a given date range.

### Todo List
1. **Create daily update script** - Create `scripts/daily_eod_update.py` that focuses on getting just the previous trading day's data
2. **Add trading day logic** - Create helper function to determine the previous trading day (accounting for weekends/holidays) 
3. **Add CLI interface** - Create command-line interface with options for date override and dry-run mode
4. **Add error handling** - Implement proper logging, error handling, and retry logic for API failures
5. **Add validation** - Create validation to ensure data was successfully updated and no symbols were missed
6. **Update documentation** - Update `CLAUDE.md` with instructions for running daily updates
7. **Create scripts directory** - Set up proper directory structure for operational scripts
