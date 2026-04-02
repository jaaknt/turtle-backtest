# Troubleshooting

Quick reference for common issues. Use `--verbose` on any script for detailed logging and consult logs in `logs/` for additional context.

## Common Issues

| Problem | Quick Fix | Details |
|---------|-----------|---------|
| **Database connection failed** | `docker-compose ps` to verify postgres running, check `.env` credentials | Verify DB exists with `psql -U postgres -l`, test port 5432 access |
| **API rate limiting** | Use `--ticker-limit 10` for testing, verify API keys in `.env` | Check `EODHD_API_KEY` is active, typical limit 20 req/sec |
| **No signals generated** | Verify data exists: `SELECT COUNT(*) FROM turtle.daily_bars WHERE symbol='AAPL'`, enable `--verbose` | Check ticker has sufficient history, validate strategy parameters |
| **Portfolio backtest errors** | Lower `--min-signal-ranking`, verify `initial_capital >= position_max_amount * max_positions` | Ensure signals exist for date range, validate benchmark data (SPY/QQQ) |
| **Slow queries / high memory** | Add indexes: `CREATE INDEX idx_daily_bars_symbol_date ON turtle.daily_bars(symbol, date)`, use `--ticker-limit` | Process data in batches |
| **Migration failures** | `uv run alembic current` to check version, `uv run alembic downgrade -1` to rollback | Review `turtle.alembic_version` table, test upgrade/downgrade paths |

## Diagnostic Commands

```bash
# Verify database is running
docker-compose ps

# Check migration state
uv run alembic current

# Count rows for a symbol
psql -U postgres -d trading -c "SELECT COUNT(*) FROM turtle.daily_bars WHERE symbol='AAPL.US'"

# Run a script with detailed output
uv run python scripts/signal_runner.py --start-date 2024-06-01 --end-date 2024-06-01 --verbose

# Run tests to confirm environment is healthy
uv run pytest
```
