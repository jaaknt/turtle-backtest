# Job-run logging

## Context

The scheduled jobs in `deploy/` (systemd user timers running `download-eodhd-data`,
`snapshot-company`, plus a bash-only `pg_dump` backup) leave no durable trace. The only record that
a run happened is journald on whichever host ran it — so "did Tuesday's history download actually
finish?", "how long has the weekly full refresh been taking?" and "which commit produced this data?"
all require SSH plus `journalctl` archaeology, and the answer disappears when the journal rotates.

There is no run-tracking of any kind in the codebase today: no `job_run`, `run_log`,
`execution_log` or audit table. Run history is currently kept by hand as Markdown under `docs/`.

The outcome: one row per CLI invocation in a new `turtle.job_runs` table, carrying name, timing,
the full parameter set as `jsonb`, the code version, and the error if it failed — switchable on and
off, so the VPS records runs while local development does not.

> **Note on the config mechanism.** §3 has been updated to the `ACTIVE_PROFILE` profile scheme that
> replaced the original per-environment switch. See *Configuration (Factory Method)* in `CLAUDE.md`.

## Decisions already made

| Decision | Choice |
| --- | --- |
| Scope | All **6** console-script entry points, not just the two in `deploy/`. The bash-only `turtle-backup.service` is out of scope. |
| Crash safety | Two-phase write: `INSERT` at start with `status='running'`, `UPDATE` at end. A hard-killed run (OOM/SIGKILL) leaves a visible orphan `running` row. |
| `version` | Package version plus git SHA, e.g. `1.0.0+fd66f3b`. |
| `error` | Exceptions **and** the last `ERROR`-level log message — 5 of 6 CLIs fail via `logger.error(); return 1` rather than by raising, so exception-only capture would leave most real failures blank. |
| Defaults | Superseded — now a flat `[job_runs] enabled`, off in the base file and on via the `hetzner` profile (see the note above). A missing config section still means **disabled**, never a crash. |
| `parameters` shape | Nested: `{"cli": {...}, "strategy": {...}}`. The `cli` section is `vars(args)`; the `strategy` section is the resolved `describe_parameters()` of the trading strategy, so a run records the thresholds that were actually in effect, not just the flags that were typed. Only the 3 analysis runners have a `strategy` section. |
| `duration` type | `INTERVAL`, generated. Charting needs `EXTRACT(EPOCH FROM duration)`; readability at the psql prompt won. |
| `scripts/` studies | Out of scope. The 6 console-script entry points only — even though the `scripts/*.py` studies are the ones that actually get OOM-killed, they don't share the CLI bootstrap and would need individual wiring. |

## 1. Migration — `db/migrations/versions/2026_08_15_000001_create_job_runs_table.py`

`revision = "e2f3a4b5c6d7"`, `down_revision = "d1e2f3a4b5c6"` — the current head
(`2026_08_03_000001_create_lightyear_transaction_table.py`).

Follow the house style exactly: pure `op.execute` raw SQL (never `op.create_table`),
`op.execute("SET search_path TO turtle, public")` as the first statement, fully-qualified
`turtle.job_runs`, one-line docstrings on `upgrade`/`downgrade`, a `COMMENT ON` for the table and
every column, and a `downgrade()` that does `DROP TABLE IF EXISTS turtle.job_runs CASCADE`.

```sql
CREATE TABLE turtle.job_runs (
    id         BIGINT      GENERATED ALWAYS AS IDENTITY,
    name       TEXT        NOT NULL,
    status     TEXT        NOT NULL DEFAULT 'running',
    start_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_at     TIMESTAMPTZ,
    duration   INTERVAL    GENERATED ALWAYS AS (end_at - start_at) STORED,
    parameters JSONB       NOT NULL,
    version    TEXT        NOT NULL,
    exit_code  INTEGER,
    error      TEXT,
    hostname   TEXT        NOT NULL,
    CONSTRAINT pk_job_runs PRIMARY KEY (id),
    CONSTRAINT job_runs_status_check CHECK (status IN ('running', 'success', 'failed')),
    CONSTRAINT job_runs_finished_check CHECK ((status = 'running') = (end_at IS NULL))
);

CREATE INDEX idx_job_runs_name_start_at ON turtle.job_runs (name, start_at DESC);
CREATE INDEX idx_job_runs_unfinished ON turtle.job_runs (start_at DESC) WHERE status = 'running';
```

Three deliberate deviations from the table template, each worth noting in review:

- **`duration` is a generated column**, not a value the application writes. `timestamptz - timestamptz`
  is immutable (`pg_proc.provolatile = 'i'` for `timestamptz_mi`, verified on the PostgreSQL 17.10
  server), so `STORED` is legal. It is `NULL` exactly while the run is in flight, and it can never
  drift out of sync with `start_at`/`end_at`. This is why the recorder never computes an elapsed time.
- **No `created_at` / `modified_at` and no `job_runs_modified_at` trigger**, unlike every other table
  here. They would duplicate `start_at` and `end_at` exactly.
- **No `GRANT`.** `docs/specs/lightyear-data-import.md` records that the `GRANT INSERT` in the
  `company_history` migration is redundant, and this was re-confirmed live: `pg_default_acl` shows
  `alembic` granting `app_user=arwd` on tables and `rwU` on sequences in schema `turtle`. `arwd`
  covers the INSERT **and** the UPDATE the two-phase write needs, and an IDENTITY column needs no
  separate sequence grant. Reads are covered too: the same default ACL grants `claude=r`, which is
  what the Postgres MCP tool connects as. (`trading_ro` holds no privileges on *any* `turtle` table
  — a pre-existing condition of the schema, not something this table introduces.)

`job_runs_finished_check` is the invariant that keeps the two-phase write honest: a row is
`running` if and only if it has no `end_at`.

The `COMMENT ON COLUMN turtle.job_runs.parameters` should state the shape, since it is not obvious
from the type: `{"cli": {...}, "strategy": {...}}`, where `strategy` is absent for the three
standalone utilities and for any run killed before it resolved a strategy. No GIN index on
`parameters` — at a few hundred rows a year, a sequential scan is free.

> Naming note: every other table here is singular (`company`, `ticker`, `lightyear_transaction`);
> `job_runs` is plural as explicitly requested.

## 2. Table definition — `turtlex/repository/tables.py`

Add the `Table` alongside the existing ones (shared `metadata`, `schema="turtle"`). This introduces
the **first `JSONB` column in the schema**, so it needs a new import:

```python
from sqlalchemy.dialects.postgresql import ENUM, JSONB
```

Omit `duration` from the `Table` — it is database-generated and must never appear in an INSERT or
UPDATE payload, exactly as `created_at`/`modified_at` are omitted from the other tables.

`id` **is** defined on the `Table` (`primary_key=True`), because `start_run` needs it for
`RETURNING` and `finish_run` needs it in the `WHERE`. It must never be supplied as a value:
`GENERATED ALWAYS AS IDENTITY` (as opposed to `BY DEFAULT`) rejects an explicit insert outright.

## 3. Config switch — `turtlex/config/model.py`, `turtlex/config/settings.py`, `config/settings.toml`

A flat `[job_runs]` table, off in the base file and switched on by the profile the VPS runs under:

```toml
# config/settings.toml
[job_runs]
enabled = false

# config/settings-hetzner.toml
[job_runs]
enabled = true
```

`turtlex/config/model.py` — a plain dataclass, matching the existing no-pydantic style:

```python
@dataclass
class JobRunsConfig:
    """Job-run logging configuration"""

    enabled: bool = False
```

`turtlex/config/settings.py` — read from the merged configuration, after the profile overlay has
been applied:

```python
job_runs_config = JobRunsConfig(enabled=bool(data.get("job_runs", {}).get("enabled", False)))
```

The `.get()` defaults are what deliver "missing section = disabled, no crash": an old
`config/settings.toml` on the VPS silently records nothing instead of breaking every CLI. This is
deliberately **more lenient** than the `[database]` read, which raises on a malformed section —
telemetry config must never be able to take a job down.

Add `job_runs: JobRunsConfig = field(default_factory=JobRunsConfig)` as the **last** field of
`Settings`, with a default, so existing positional constructions in tests keep working.

## 4. Version resolution — `turtlex/common/version.py` (new)

```python
@cache
def resolve_version() -> str:
    """Return the running code version as "<package>+<git-sha>", e.g. "1.0.0+fd66f3b"."""
```

- Package half from `turtlex.__version__`. `turtlex/__init__.py` and `pyproject.toml` now agree on
  `1.0.0` (aligned in `124bd6e`), so either source works; use `__version__` because it is always
  importable and needs no `importlib.metadata` lookup. The git SHA is the half that actually
  identifies deployed code, since the VPS updates by `git pull`.
- SHA via `subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=<repo root>, ...)` with
  `check=False`, a short timeout, and captured output. Repo root from
  `Path(__file__).resolve().parents[2]` — do not rely on cwd. On `FileNotFoundError` (no git binary)
  or a non-zero return (installed wheel, no `.git`), return the bare package version.
- `@cache` so the subprocess runs at most once per process.

## 5. Write repository — `turtlex/repository/ingest/job_run.py` (new)

Copy the shape of `turtlex/repository/ingest/lightyear.py`: module-level logger, class docstring
"Sync Engine-based repository for job-run writes.", `__init__(self, engine: Engine)` storing
`self._engine`, SQLAlchemy Core statements, `with self._engine.begin() as conn:`, Google-style
docstrings whose `Returns:` names the type.

```python
class JobRunRepository:
    def start_run(self, name: str, parameters: dict[str, object], version: str, hostname: str) -> int:
        """Insert a 'running' row and return its id."""  # INSERT ... RETURNING id

    def finish_run(self, run_id: int, status: str, exit_code: int, error: str | None, parameters: dict[str, object]) -> None:
        """Close out a run, setting end_at (which populates the generated duration column)."""
```

`finish_run` sets `end_at=func.current_timestamp()` so `duration` is computed server-side from two
timestamps taken by the same clock. Export both from `turtlex/repository/ingest/__init__.py`
alongside the existing repositories.

`finish_run` rewrites `parameters` as well, because the `strategy` section does not exist yet at
INSERT time — see §6. An orphaned `running` row therefore carries only its `cli` section, which is
the correct outcome: a run killed before resolving its strategy never had one.

## 6. Recorder — `turtlex/service/job_run_service.py` (new)

Holds four things: the last-ERROR log capture, the parameter buffer, parameter serialization, and
the enabled/disabled no-op behaviour.

```python
class _LastErrorCapture(logging.Handler):
    """Keeps the most recent ERROR-level message emitted during a run."""


class JobRunRecorder:
    """Records one CLI invocation into turtle.job_runs; a no-op when repository is None."""

    def __init__(self, repository: JobRunRepository | None, name: str, parameters: Mapping[str, object]) -> None: ...
    def start(self) -> None: ...
    def add_parameters(self, section: str, values: Mapping[str, object]) -> None: ...
    def finish(self, exit_code: int) -> None: ...
```

- **`add_parameters`** is what makes the `strategy` section possible. The resolved parameters only
  exist *after* `resolve_trading_strategy()` runs, which happens inside `body()` — by which time the
  `running` row is already inserted. Rather than a third write, `add_parameters` buffers the section
  in memory and `finish()` writes the merged dict in the UPDATE it was already making. The
  constructor seeds the buffer as `{"cli": vars(args)}`.

- **Disabled path**: `repository=None` → `start`, `add_parameters` and `finish` all return
  immediately. No engine work, no serialization, no subprocess. `body()` still receives a real
  recorder object, so callers never branch on whether logging is on.
- **Error capture**: `start()` attaches `_LastErrorCapture` (level `ERROR`) to the root logger;
  `finish()` removes it in a `finally` so it can never leak across runs or accumulate under pytest.
  `finish()` writes `status='success'` when `exit_code == 0`, else `'failed'` with the captured
  message. Because `run_cli` already logs `f"Analysis failed with error: {e}"` before returning 1,
  raised exceptions are captured by the same mechanism — no separate exception plumbing needed.
- **Failure isolation** (the one deliberate swallow): both `start()` and `finish()` wrap their DB
  call in `except SQLAlchemyError` → `logger.warning(...)`, never re-raising. A narrow, named
  exception class, not a bare `except`, with a comment stating the rule: *telemetry must never fail
  the job it is measuring* — a Postgres hiccup must not turn a successful `download-eodhd-data` into
  exit 1. If `start()` failed, `self._run_id` stays `None` and `finish()` skips its UPDATE.
- **Serialization**: a module-private `_jsonable(value)` recursing over `list`/`tuple`/`dict`, mapping
  `date`/`datetime` → `isoformat()`, `Path` → `str`, passing `None`/`bool`/`int`/`float`/`str`
  through, and falling back to `str(value)` for anything else. This is required, not optional:
  `vars(args)` contains `datetime.date` (from `iso_date_type`), `pathlib.Path` (`--folder`), and
  `list[tuple[str, str]]` (from `key_value_type`, used by `--trading-param`/`--exit-param`) — none of
  which `json` accepts. No CLI argument carries a secret (dates, strategy names, paths and integer
  limits only); secrets live solely in env vars, so no redaction is needed.

## 7. CLI wiring — `turtlex/cli/common.py` and all 6 entry points

Add one helper next to the existing `run_cli`, which stays **unchanged** (as do its four tests):

```python
def run_job(name: str, args: argparse.Namespace, settings: Settings, body: Callable[[JobRunRecorder], int]) -> int:
    """Run `body` under run_cli, recording the invocation in turtle.job_runs."""
    recorder = JobRunRecorder(JobRunRepository(settings.engine) if settings.job_runs.enabled else None, name, vars(args))
    recorder.start()
    exit_code = 1
    try:
        exit_code = run_cli(args, functools.partial(body, recorder))
    finally:
        recorder.finish(exit_code)
    return exit_code
```

Wrapping rather than replacing `run_cli` is what keeps this small: `run_cli` already maps
`KeyboardInterrupt`/`Exception` to a logged error plus exit code 1, and the recorder reads the
outcome off the return value and the captured log. `functools.partial` adapts the recorder-taking
body to the `Callable[[], int]` that `run_cli` expects, so `run_cli` itself needs no change. The
`try/finally` covers the `BaseException` cases `run_cli` deliberately lets through (e.g.
`SystemExit`), defaulting to a failed row.

`body` takes the recorder so it can report the resolved strategy parameters. This is dependency
injection rather than a module-level or contextvar singleton, per CLAUDE.md's no-globals rule. The
three Pattern B bodies accept the argument and ignore it.

**Pattern A** — `signal_runner.py`, `portfolio_runner.py`, `backtest_runner.py`: the `body()`
closure gains a parameter and one `add_parameters` call, and the call site changes:

```diff
-    def body() -> int:
+    def body(recorder: JobRunRecorder) -> int:
         try:
             trading_strategy, _bars_history = resolve_trading_strategy(args, settings)
         except ValueError as e:
             logger.error(str(e))
             return 1
+        recorder.add_parameters("strategy", trading_strategy.describe_parameters())
...
-    return run_cli(args, body)
+    return run_job("signal-runner", args, settings, body)
```

`resolve_trading_strategy` stays **inside** `body()`. Hoisting it above `run_job` would make the
resolved parameters available at INSERT time, but a bad `--trading-param` would then fail before any
row existed — losing exactly the failure record that motivated capturing `error` in the first place.

`backtest_runner.py` and `portfolio_runner.py` resolve an exit strategy in the same `try` block;
they add `recorder.add_parameters("exit_strategy", exit_strategy_kwargs)` alongside. Note this is a
weaker record than the trading section — `resolve_exit_strategy_kwargs` returns only the explicit
`--exit-param` overrides, not the strategy's full effective parameter set.

**Pattern B** — the three standalone CLIs need their work extracted so `run_job` has a `body` to
call. Mechanical, but not one-line:

All three take the `recorder` argument and ignore it — none has a strategy to describe.

- `snapshot_company.py` — move the snapshot work into a nested `body(recorder) -> int`, then
  `return run_job("snapshot-company", args, settings, body)`. Behaviour change worth noting: an
  unexpected exception now becomes a logged error and exit 1 instead of an uncaught traceback.
- `import_lightyear.py` — **keep the `args.folder.is_dir()` check and its comment before
  `Settings.from_toml()`**; extract the body into a module-level
  `_import_statements(args, settings, recorder) -> int` and pass
  `functools.partial(_import_statements, args, settings)`, leaving `run_job` to supply the recorder.
- `download_eodhd_data.py` — the only structural change. `Settings.from_toml()` currently lives
  *inside* the async `download()` coroutine, but the recorder needs `settings.engine` in `main()`.
  Move it up, add a `settings` parameter to `download()` and document it in the existing docstring,
  and replace `main()`'s own `try/except Exception: return 1` with the `run_job` call:

```diff
     setup_logging(args.verbose)
+    settings = Settings.from_toml()
+
+    def body(recorder: JobRunRecorder) -> int:
+        asyncio.run(download(settings, data=args.data, start_date=args.start_date,
+                             end_date=args.end_date, ticker_limit=args.ticker_limit))
+        return 0
+
+    return run_job("download-eodhd-data", args, settings, body)
```

  `download()` keeps its own `try/except/finally` (it must still `await eodhd_service.close()`), so a
  failure there logs twice — once with `exc_info=True` from `download()`, once from `run_cli`.
  Acceptable; the alternative is editing shared error handling.

### Known gap, by design

`import_lightyear`'s missing-folder check returns 1 *before* settings exist, so that one failure mode
records no row. Loading config just to log a config-independent failure would defeat the comment
already in the code.

## 8. Tests

Mirror the source tree. The established pattern for repository tests is a `MagicMock` engine plus
compiling the statement against the postgres dialect — no live DB (see
`tests/repository/ingest/test_lightyear.py`).

| File | Asserts |
| --- | --- |
| `tests/repository/ingest/test_job_run.py` | `start_run` compiles to an INSERT with `RETURNING job_runs.id` and returns the id; `finish_run` targets `WHERE id = :id` and rewrites `parameters`; `duration` and `id` never appear in either payload. |
| `tests/service/test_job_run_service.py` | No-op when `repository is None` (engine never touched); `_jsonable` handles `date`, `Path`, `list[tuple[str, str]]` and falls back to `str`; a `SQLAlchemyError` from `start_run`/`finish_run` does **not** propagate and logs a warning; a failed `start()` makes `finish()` skip; last-ERROR capture fills `error`; the handler is detached from the root logger after `finish()`; `add_parameters` merges under its section and is a safe no-op when disabled. |
| `tests/cli/test_common.py` (extend) | `run_job` returns the body's exit code; records `success` for 0 and `failed` for non-zero; a raising body still produces a finished row; the recorder reaches `body` so `add_parameters` from inside it lands in the finished row. |
| `tests/config/test_settings.py` (extend) | Missing `[job_runs]` → `enabled is False`; the flat `[job_runs] enabled = true` → `enabled is True`. |
| `tests/common/test_version.py` (new) | Format is `<version>+<sha>`; degrades to the bare version when `git` is missing or fails. |

## 9. Verification

```bash
docker-compose up -d
uv run alembic upgrade head && uv run alembic current   # expect e2f3a4b5c6d7
```

Temporarily flip `[job_runs] enabled = true` in `config/settings.toml`, then exercise a success, a failure, and the
jsonb serialization edge cases:

```bash
uv run snapshot-company                                             # success, exit 0
# date + list[tuple] params. --trading-strategy qullamaggie is required: sma_thresh belongs to
# qullamaggie, and the default darvas_box rejects it with "not an overridable parameter".
uv run signal-runner --start-date 2024-06-01 --end-date 2024-06-01 \
    --trading-strategy qullamaggie --trading-param sma_thresh=0.20
uv run signal-runner --start-date 2024-06-01 --end-date 2024-06-01 \
    --trading-param nonsense=1                                      # failure -> error populated
```

```sql
SELECT id, name, status, start_at, duration, exit_code, version, parameters, error
FROM turtle.job_runs ORDER BY start_at DESC LIMIT 10;
```

Check that `duration` is non-null and plausible; `version` looks like `1.0.0+<sha>`; and the failing
run has `status='failed'`, `exit_code=1` and a non-null `error`. Confirm both jsonb sections, and
that the resolved `strategy` section carries thresholds never typed on the command line:

```sql
SELECT name,
       parameters->'cli'->>'trading_strategy'  AS cli_strategy,
       parameters->'strategy'->>'sma_thresh'   AS effective_sma_thresh,
       parameters->'strategy'                  AS strategy_section
FROM turtle.job_runs ORDER BY start_at DESC LIMIT 5;
```

The `snapshot-company` row should have a `cli` section and **no** `strategy` key at all — that
asymmetry between the analysis runners and the standalone utilities is expected, not a bug.

Then confirm the disabled path and the crash path:

```bash
# flip enabled back to false -> run again -> no new row
# crash safety: start a long run, SIGKILL it, then run the orphan query below
```

```sql
-- the run just killed: still 'running', no end_at, NULL duration
SELECT id, name, start_at, end_at, duration, exit_code
FROM turtle.job_runs WHERE status = 'running' ORDER BY start_at DESC;
```

The same query with `AND start_at < now() - interval '1 day'` is the operational form — the one
worth putting in `docs/implementation.md` to find orphans left by past crashes rather than the one
just created.

Gate before commit:

```bash
uv run pytest && uv run mypy && npx markdownlint-cli2
```

On the VPS: `uv run alembic upgrade head` (its Postgres is localhost), then
`systemctl --user start snapshot_company.service` and re-run the query against that database.

## 10. Docs to update

- **`CLAUDE.md`** — note `turtle.job_runs` under *Database*, and the `[job_runs]` switch under
  *Configuration*.
- **`docs/implementation.md`** — add the migration and the `hetzner` profile to the VPS
  deploy phases; mention that a killed job leaves a `running` row, and give the query that finds
  orphans.
- **`docs/scripts.md`** — one line noting that every CLI records its invocation when enabled.

No reaper job for orphaned `running` rows — that is speculative until the orphans prove annoying.
