# CLAUDE.md

Python backtesting library for US stocks (`turtlex/`): trading strategies (Qullamaggie, Darvas Box,
Mars, Momentum), exit and ranking strategies, portfolio simulation, and research studies in
`scripts/`. Market data comes from the EODHD API and lives in PostgreSQL (schema `turtle`).

## Rules

- **Think first.** State assumptions; if a request has several readings, or something is unclear,
  ask rather than pick silently. Push back when a simpler approach exists.
- **Simplicity and surgical changes.** The minimum code that solves the problem, matching existing
  style. No speculative features, abstractions or config. Don't refactor or reformat code you
  weren't asked to touch; mention unrelated dead code rather than deleting it, but remove orphans
  your own change creates. Never drop docstrings or comments while refactoring.
- **Propose a plan before large refactors** (scope boundaries especially) and wait for confirmation.
- **Polars for all new code.** Pandas stays only in `turtlex/portfolio/analytics.py` (and via
  `quantstats`); flag any new pandas import in review.
- **Verify.** Turn a task into a check (a failing test, a passing run) and loop until it holds.
  After non-trivial changes run pytest and mypy before proposing a commit.

## Commands

Full CLI reference with every flag: [docs/scripts.md](docs/scripts.md).

| Task | Command |
| --- | --- |
| Install deps | `uv sync --extra lint` |
| Lint + types | `bash .githooks/pre-commit` (ruff, ruff format check, and `uv run mypy`, which takes no paths) |
| Tests | `uv run pytest` |
| Run a research study | `systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 uv run scripts/<name>.py` |
| Markdown lint | `npx markdownlint-cli2` (`--fix` to auto-fix) |
| EODHD smoke tests | `uv run pytest -m bruno` (live API; needs `npm i -g @usebruno/cli` and a real key in `bruno/eodhd/.env`) |

**Never run a `scripts/*.py` study uncapped.** Studies load up to ~7M daily bars. On WSL every process shares one
unbounded cgroup and there is no `systemd-oomd`, so an uncapped OOM kills the terminal or wedges the
VM (`Wsl/Service/E_UNEXPECTED`). `MemorySwapMax=0` stops the swap-thrash. Exit **137** is the OOM
killer, not a bug: raise the cap or narrow the input, don't re-run unchanged. The widest study (the
relax sweep) peaks at ~3.5 GB.

## Baseline algorithm

**`bk50d_s12_v2.0`** is the reference for every comparison, example, study and doc, so quoted
numbers stay comparable: a 50-day-high breakout more than 12% above the 50-day SMA, entered at the
next day's adjusted open, held 366 calendar days, `QullamaggieRanking` gated at `MIN_RANKING >= 44`. `s16`/`s20` differ only in the SMA threshold; report them
alongside s12, never instead of it. Definition: `docs/research/qullamaggie-backtest-v4.md` (Step 1).

## Architecture

- **`turtlex/model.py`** holds every shared domain dataclass (`Signal`, `Trade`, …). No per-package
  `models.py`. Pydantic (`turtlex/schema/`) only for EODHD responses that need field aliasing.
- **`turtlex/repository/`** is the only place SQL lives. `query/`: sync `Engine` reads. `ingest/`:
  writes, async `AsyncSession` for EODHD downloads, sync `Engine` for the Lightyear importer (a write repository follows its caller's sync/async shape).
  `DailyBarsQueryRepository` has two read shapes: `get_bars_pl` (one ticker, the runner) and
  `get_qualified_universe_bars_pl` (whole universe, `turtlex/research/`).
- **Async only on the download path** (`turtlex/client/eodhd.py`, `turtlex/service/eodhd_service.py`,
  `repository/ingest/`). Query repositories, strategy, backtest and portfolio logic stay sync.
- **`turtlex/strategy/factory.py`** registries (`TRADING_STRATEGIES`, `EXIT_STRATEGIES`,
  `RANKING_STRATEGIES`) are the name → class mapping; CLIs derive argparse `choices` from them,
  never a hardcoded list. Implementations live in `turtlex/strategy/{trading,exit,ranking}/`
  behind the ABC in each `base.py` ([docs/strategy.md](docs/strategy.md)).
- **`turtlex/research/qullamaggie.py`** is the bulk mirror of `QullamaggieStrategy`; keep both.
  `tests/research/test_qullamaggie_parity.py` keeps their signals and filter constants identical.
- **`turtlex/backtest/metrics.py`** is the single source of trade/daily metrics
  (`compute_trade_metrics`, `compute_daily_sortino`). Don't recompute Sortino, CVaR or profit factor
  in a study; `tests/scripts/test_metric_conventions.py` enforces it. The two Sortino regimes:
  [docs/scripts.md](docs/scripts.md).
- Portfolio trio (`PortfolioManager`, `PortfolioSignalSelector`, `PortfolioAnalytics`):
  [docs/service.md](docs/service.md).
- Packages are **singular** snake_case (`service/`, `repository/`).
- To locate a symbol, trace callers or gauge a change's blast radius, use the `codegraph_explore`
  MCP tool (or the `codegraph explore` CLI) before grep or reading files one by one. For library
  docs use the context7 MCP rather than guessing.

## Database

- `turtle.signal`: one row per signal from `signal-runner --persist`, upserted on
  `(trading_strategy, symbol, signal_date)`, stored **ungated** (`--min-signal-ranking` filters the
  printout only). Per-signal indicators and `next_open` go in `parameters` (jsonb); run configuration
  does not. See [docs/specs/persist-signal.md](docs/specs/persist-signal.md).
- `turtle.job_runs`: one row per CLI invocation, written by `run_job()` in `turtlex/cli/common.py`,
  which every console script routes through.
  See [docs/specs/run_jobs.md](docs/specs/run_jobs.md).
- Queries via the `dbhub` MCP: default `execute_sql_local_ro` (5-year mirror);
  `execute_sql_hetzner_ro` for deeper history. `_rw` only when a write was asked for
  (`hetzner_rw` is production). Never DDL through MCP; schema changes go through Alembic.

## Config and profiles

`Settings.from_toml()` (`turtlex/config/settings.py`) is the only config entry point; missing secret
env vars raise `ValueError`, never fall back to TOML. `ACTIVE_PROFILE=<name>` deep-merges
`config/settings-<name>.toml` over `config/settings.toml`; dev machines leave it unset.
**`hetzner-db` is not read-only**: it connects to the production VPS as `app_user`, so `--persist`
or Alembic under it hits production. Check the `Database connection:` banner. Details:
`.claude/rules/config-profiles.md`.

## Code conventions

- Public methods need a docstring covering purpose and each parameter.
- One `logging.getLogger(__name__)` per file: DEBUG for decisions and values, WARNING/ERROR for
  anomalies; never log secrets. Each CLI calls `setup_logging(args.verbose)`
  (`turtlex/config/logging.py`) once, right after argument parsing (`--verbose` comes from `add_logging_args()`,
  included in `build_common_analysis_parser()`) and before
  `Settings.from_toml()`. No `basicConfig`, `dictConfig` or handler mutation anywhere else.
- Validate early: return `bool` from data-collection methods or raise `ValueError` with a clear
  message. Properties validate their preconditions before computing. No swallowed exceptions.
- Tests mirror the source tree (`turtlex/strategy/exit/atr.py` →
  `tests/strategy/exit/test_atr_exit_strategy.py`); shared fixtures in `tests/conftest.py`,
  file-specific ones in the test file.
  `-m bruno` tests are deselected by default.

## Reviews

`/code-review` and `/simplify` read `git diff`, which leaves out untracked files: `git add -N` new
files first. Check each finding against the code before applying it, and never undo a decision the
user made earlier.

## Git

Trunk-based: commit directly to `main`, no branches or pull requests. Push only when asked; use the
`commit-push` skill. Enable the check-only pre-commit hook once per clone:
`git config core.hooksPath .githooks` (an unexplained green commit means it's off).
