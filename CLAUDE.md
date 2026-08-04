# CLAUDE.md

Python-based financial trading strategy backtesting library for US stocks. Supports multiple strategies (Qullamaggie, Darvas Box, Mars, Momentum), portfolio management, and market data via EODHD API. Data stored in PostgreSQL.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Refactor Etiquette

- Do NOT remove docstrings or comments when refactoring unless explicitly asked.
- Before large refactors, propose a brief plan (especially scope boundaries) and wait for confirmation.

## 6. Standard Workflow

- After non-trivial changes, run pytest and mypy before proposing a commit. Run mypy with no arguments (`uv run mypy`) — scanned paths are defined in `pyproject.toml` `[tool.mypy] files`.
- Polars for all new code. Pandas is intentionally retained in `turtlex/portfolio/analytics.py`, plus indirectly via `quantstats`. Don't introduce pandas elsewhere; flag any new pandas import in code review.
- **Always run `scripts/*.py` studies under a memory cap** (see [Running Research Studies](#running-research-studies)). They load millions of rows; an uncapped runaway takes the whole WSL distro down, not just the script.

## Quick Start & Common Commands

### Most Common Operations

Full CLI reference — every flag and worked examples — is in [docs/scripts.md](docs/scripts.md).

| Task | Command | Use When |
| ------ | --------- | ---------- |
| **Generate signals** | `uv run signal-runner --start-date 2024-06-01 --end-date 2024-06-01` | Analyze trading opportunities |
| **Portfolio backtest** | `uv run portfolio-runner --start-date 2024-01-01 --end-date 2024-12-31` | Test multi-position strategy |
| **Single backtest** | `uv run backtest-runner --tickers AAPL --start-date 2024-01-01 --end-date 2024-01-01` | Test specific ticker |
| **Download data** | `uv run download-eodhd-data` | Bulk historical/reference data from EODHD |
| **Snapshot fundamentals** | `uv run snapshot-company` | Refresh the `company` table |
| **Import Lightyear trades** | `uv run lightyear-import` | Load real Buy/Sell executions from statement CSVs |
| **Install deps** | `uv sync --extra lint` | First setup, or after a dependency change |
| **Start database** | `docker-compose up -d` | Before any data operations |
| **Apply migrations** | `uv run alembic upgrade head` | After pulling schema changes |
| **Run tests** | `uv run pytest` | Verify code changes |
| **Test coverage** | `uv run pytest --cov=turtlex --cov-report=term-missing` | Find untested code paths |
| **Lint markdown docs** | `npx markdownlint-cli2` | Check README/CLAUDE.md/docs before committing (`--fix` to auto-fix) |
| **Run Bruno API smoke tests** | `uv run pytest -m bruno` | Verify live EODHD endpoints still match expectations (requires `npm install -g @usebruno/cli` + real `EODHD_API_KEY` in `bruno/eodhd/.env`) |

### Running Research Studies

The `scripts/*.py` studies load the whole qualified universe of daily bars (~7M rows for the
widest one). Run them under a cgroup memory cap so a runaway dies alone:

```bash
systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 uv run scripts/<name>.py
```

Why this matters on WSL: every user process — your shell, Claude Code, MCP servers, the
script — shares one unbounded `/init.scope` cgroup, and `systemd-oomd` is not installed. An
uncapped OOM therefore kills the terminal and can wedge the VM entirely (`Wsl/Service/E_UNEXPECTED`)
rather than just failing the script. `MemorySwapMax=0` is the important half: it prevents the
swap-thrash that makes the OOM kill unreapable.

A capped run that dies exits **137** — that is the OOM killer, not a bug in the study. Raise the
cap or narrow the input; don't re-run unchanged. Reference peaks: the relax sweep, the widest
study, peaks at ~3.5 GB.

### Baseline Algorithm

**`bk50d_s12_v2.0` gated at `MIN_RANKING >= 40` is the reference algorithm.** Use it whenever a
comparison or example needs one — new studies, ad-hoc queries, docs and explanations — so numbers
quoted in different places stay comparable. It is a 50-day-high breakout sitting more than 12%
above the 50-day SMA, entered at the next trading day's split/dividend-adjusted open and held 366
calendar days, with the `QullamaggieRanking` score gated at 40 (the `--min-signal-ranking`
default). Note the gate is `>= 40`, not `> 40` — a signal scoring exactly 40 is kept.

The `s16` and `s20` variants differ only in that SMA-distance threshold and stay in the standard
sweep set; report them alongside s12 rather than in place of it. Full definition and naming
convention: `docs/research/qullamaggie-backtest-v4.md` (Step 1).

## Tool Preferences

- For GitHub queries (PRs, issues, Actions, workflow runs), ALWAYS use the GitHub MCP server first. Only fall back to `gh` CLI or Bash if MCP lacks the needed tool.
- For Postgres queries, use the `mcp__postgres__query` tool with parameter name `sql` (not `query`).
- For library/framework documentation lookups, use context7 MCP rather than guessing or web search.
- For code analysis — locating a symbol, understanding how a class/function is used, tracing call paths, or assessing the blast radius of a change — use the `codegraph_explore` MCP tool (or the `codegraph explore` / `codegraph node` CLI if MCP isn't available) before grep/find or reading files one by one.

## Git Workflow

Trunk-based development — commit directly to `main`, no pull requests or feature branches.

## Architecture Overview

### Package Rules

- **`turtlex/model.py`** holds every shared domain dataclass (`Signal`, `Trade`, `Benchmark`, …).
  Do not create per-package `models.py` files.
- **`turtlex/repository/`** is the only place SQL lives. `query/` does sync `Engine` analytical
  reads; `ingest/` does writes, with the session type following the caller — async
  `AsyncSession` for the EODHD download path, sync `Engine` for the Lightyear statement
  importer. Note the two read shapes on `DailyBarsQueryRepository`: `get_bars_pl` (one ticker —
  the per-ticker runner) and `get_qualified_universe_bars_pl` (whole universe in one query —
  `turtlex/research/`).
- **`turtlex/strategy/factory.py`** holds the `TRADING_STRATEGIES` / `EXIT_STRATEGIES` /
  `RANKING_STRATEGIES` registries — the canonical string → class mapping. CLIs derive their
  argparse `choices` from the registry keys; never hardcode strategy name lists in scripts.
- **`turtlex/research/qullamaggie.py`** mirrors `QullamaggieStrategy` in bulk form: production
  loads one ticker per query because the runner walks the universe ticker by ticker, research
  loads everything at once so sweeps can re-filter in memory. Parity is enforced by
  `tests/research/test_qullamaggie_parity.py` — keep both, and keep them identical.
- **`turtlex/schema/`** is Pydantic, and only for external (EODHD) API responses that need field
  aliasing. Everything internal is a dataclass.
- **`turtlex/backtest/metrics.py`** is the single source of the shared trade/daily metrics
  (`compute_trade_metrics`, `compute_daily_sortino`). Don't recompute Sortino, CVaR or profit
  factor locally in a study — see [docs/scripts.md](docs/scripts.md) on the two Sortino regimes.
- **Strategy/exit/ranking implementations** live under `turtlex/strategy/{trading,exit,ranking}/`,
  each behind the ABC in its `base.py`. See [docs/strategy.md](docs/strategy.md) for what each one
  does and when to use it.

### Database

- **Schema**: `turtle` (PostgreSQL)

## Core Systems Overview

The portfolio trio — `PortfolioManager`, `PortfolioSignalSelector`, `PortfolioAnalytics` — is
described in [docs/service.md](docs/service.md).

## Database Migrations

Alembic standalone mode with raw SQL (the usual `current` / `history` / `upgrade head` /
`downgrade -1` / `revision -m` commands apply). Migrations live in `db/migrations/versions/`, the
version table is `public.alembic_version`, and the target database is selected via `DB_ENV`
(`local` default, `hetzner` for the VPS).

## Development Workflows

Adding a new trading strategy: see the `add-trading-strategy` skill.

Committing and pushing to `main`: see the `commit-push` skill.

## Design Patterns & Principles

### Configuration (Factory Method)

`Settings.from_toml()` is the single entry point for all config. It loads TOML, validates required env vars (raises `ValueError` if missing — never falls back to TOML values for secrets), builds nested config objects, and creates the connection pool. See `turtlex/config/settings.py`.

### Async Boundary

Async is used only in the data-download path; analytical queries are always sync:

- **Async (downloads/writes)**: external API clients (`turtlex/client/eodhd.py`, `httpx.AsyncClient`), download-orchestration services (e.g. `turtlex/service/eodhd_service.py`, concurrent requests via `asyncio.gather`), and the EODHD download write repositories in `turtlex/repository/ingest/` (`AsyncSession`). Scripts may use `asyncio.run()` as the async entry point. Write repositories follow their caller, so a sync CLI with no I/O to overlap gets a sync one — `ingest/lightyear.py` is `Engine`-based end to end.
- **Sync (analytical reads)**: query repositories (`turtlex/repository/query/`) use a sync `Engine`; strategy, backtesting, and portfolio logic is synchronous. Do not make query repositories or backtest logic async.

### Naming Conventions

Folders and packages are **singular** snake_case: `turtlex/service/`, `turtlex/repository/` — not
`services/` or `repositories/`. Everything else follows PEP 8.

### Docstrings

All public methods (no leading underscore) must have a docstring explaining the purpose of the method and each parameter. Private methods (`_name`) do not require docstrings unless the logic is non-obvious.

### Logging

One module-level logger per file via `logging.getLogger(__name__)`. Use `DEBUG` for decision points and data values; `WARNING`/`ERROR` for anomalies and failures. Never log secrets or API keys.

Every CLI configures logging exactly once: `setup_logging(args.verbose)` from `turtlex/config/logging.py`, called in `main()` immediately after parsing arguments and before `Settings.from_toml()`, so the database-connection banner it logs at INFO is visible. The `--verbose/-v` flag comes from `add_logging_args()` in `turtlex/cli/common.py` (already included via `build_common_analysis_parser()`). Never add a second logging bootstrap: no `logging.basicConfig`, no `dictConfig`, and no handler mutation from library code. `setup_logging` attaches `ApiTokenFilter` to the stdout handler, so `api_token` redaction is always on; third-party loggers are pinned in `_THIRD_PARTY_LEVELS` and stay pinned under `--verbose`.

### Error Handling

Validate preconditions early and return `bool` (for data-collection methods) or raise `ValueError` with a descriptive message. No bare `except` clauses. No swallowed exceptions. Properties validate their preconditions before computing.

## Testing

Tests mirror the source tree under `tests/` — a change in `turtlex/strategy/exit/atr.py` belongs in
`tests/strategy/exit/test_atr_exit_strategy.py`. Shared fixtures live in `tests/conftest.py`;
file-specific fixtures stay in the individual test file.

Two tests guard invariants rather than a single unit, and are worth knowing before changing the
things they cover:

- `research/test_qullamaggie_parity.py` — asserts `turtlex/research/qullamaggie.py` (bulk) and
  `QullamaggieStrategy` (per-ticker) emit identical `(symbol, signal_date, entry_date, entry_price)`
  tuples, and that their filter constants have not drifted apart.
- `scripts/test_metric_conventions.py` — keeps the `scripts/` studies on the shared metric helpers.

Run with `uv run pytest` or `uv run pytest tests/strategy/trading/test_darvas_box.py`.
`-m bruno` tests hit the live EODHD API and are deselected by default.
