# Design: persisting `signal-runner` output to `turtle.signal`

> **Status:** implemented and verified against local Postgres on 2026-08-23. Every step in
> [Verification](#verification) passed except step 11, which needs `[job_runs] enabled` — off on
> dev machines by design, so it is checkable only on the VPS. The migration has **not** been
> applied to the Hetzner database yet.
>
> Two notes from the run. Step 2 produced **169** rows, not the 208 the step predicts: local
> `daily_bars` ends 2026-08-18 against the VPS's 2026-08-21, so the window is three trading days
> shorter — a data-freshness difference, not a defect. And no `GRANT` was needed after all: the
> `ALTER DEFAULT PRIVILEGES` in `db/init.sh:37` had applied, and `app_user` came out with
> SELECT/INSERT/UPDATE/DELETE on the new table.

## Context

`signal-runner` computes signals in memory and prints them; nothing is stored. Every look at
"what fired last week" means re-running a 2–3 minute universe scan, and the planned read-only
website ([web.md](web.md)) has no table to read from — that spec names this work as
**Workstream 1**, a precondition for its signals page.

This adds an opt-in `--persist` flag that writes each signal to a new `turtle.signal` table. The
signal-date close gets its own `signal_close` column; the remaining per-signal values live in a
`parameters jsonb` column, so a stored row is self-describing and its values are frozen as they
were when the signal fired.

That freezing is the main reason to prefer this over the spec's original narrow table.
[web.md](web.md) proposed storing only `(strategy, symbol, signal_date, ranking)` and
re-deriving every display column in SQL, which carries two costs this avoids:

- a three-lateral query the spec measures at **92 ms**, and **2,851 ms** if anyone drops its
  `date > signal_date - 130` bound (web.md §"Signals, last 3 months");
- a documented correctness caveat (web.md §1.1): `pct_vs_sma50` is re-derived from
  `adjusted_close`, which EODHD rewrites retroactively on every dividend, so the displayed inputs
  drift from the ones the persisted `ranking` was computed from.

## Decisions (settled with the user)

| Question | Decision |
| --- | --- |
| Primary key | Surrogate `id BIGINT GENERATED ALWAYS AS IDENTITY`. |
| Natural key | `UNIQUE (trading_strategy, symbol, signal_date)` — the target the upsert conflicts on. |
| `ranking_strategy` | `NOT NULL`, and **not** part of the unique key: provenance naming the scheme that produced the stored `ranking`. |
| `signal_close` | `NOT NULL`, a real column holding the signal-date raw close. |
| `parameters` jsonb | **Per-signal values**, flat: the `Signal.indicators` keys plus `next_open`. Not run configuration — `turtle.job_runs.parameters` already records CLI arguments per invocation. |
| `trading_strategy` | Holds the full variant label (`bk50d_s12_v2.0`) via a new `--persist-label`, defaulting to `args.trading_strategy`. Without it, s12/s16/s20 collide on the natural key. |

> **Assumption to confirm on review:** the `signal_close` column **replaces** the same-named key
> inside `parameters` rather than duplicating it, so the jsonb carries only the indicators and
> `next_open`. Storing one number in both a column and a jsonb key invites them to disagree.
> `next_open` stays in jsonb; it was not asked for as a column.
>
> ⚠️ **`signal_close NOT NULL` makes `--persist` qullamaggie-only.** Only `QullamaggieStrategy`
> fills `Signal.signal_close`; `darvas_box`, `mars` and `momentum` emit a bare signal
> (`darvas_box.py:71`, `mars.py:144`, `momentum.py:80`). Under this constraint,
> `signal-runner --trading-strategy mars --persist` cannot write. §3 turns that into an early,
> descriptive `ValueError` instead of a raw Postgres constraint violation, and §"Deliberately
> rejected" records that this reverses an earlier position. `ranking_strategy NOT NULL` costs
> nothing by comparison — `--ranking-strategy` always has a value, defaulting to `qullamaggie`.

## Implementation

### 1. Migration — `db/migrations/versions/2026_08_23_000001_create_signal_table.py`

`revision = "a4b5c6d7e8f9"`, `down_revision = "f3a4b5c6d7e8"` (verified current head,
`2026_08_16_000001_fix_job_runs_column_comments.py`), continuing the hand-written hex-word
sequence.

Follow `2026_08_03_000001_create_lightyear_transaction_table.py` exactly: `op.execute` raw SQL
throughout, `SET search_path TO turtle, public` first, fully-qualified `turtle.*` names, a
`COMMENT ON` for **every** column, the `modified_at` trigger, and a `downgrade()` that drops the
trigger before the table.

```sql
CREATE TABLE turtle.signal (
    id                BIGINT      GENERATED ALWAYS AS IDENTITY,
    trading_strategy  TEXT        NOT NULL,
    ranking_strategy  TEXT        NOT NULL,
    symbol            TEXT        NOT NULL,
    signal_date       DATE        NOT NULL,
    ranking           SMALLINT    NOT NULL,
    signal_close      FLOAT8      NOT NULL,
    parameters        JSONB       NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_signal PRIMARY KEY (id),
    CONSTRAINT uq_signal_trading_strategy_symbol_signal_date UNIQUE (trading_strategy, symbol, signal_date),
    CONSTRAINT signal_ranking_check CHECK (ranking BETWEEN 0 AND 100),
    CONSTRAINT signal_close_positive_check CHECK (signal_close > 0 AND signal_close < 'Infinity'),
    CONSTRAINT signal_parameters_object_check CHECK (jsonb_typeof(parameters) = 'object')
);
CREATE INDEX idx_signal_signal_date ON turtle.signal (signal_date DESC);
```

Every element has a precedent here: `BIGINT GENERATED ALWAYS AS IDENTITY` from `job_runs:26`,
`uq_<table>_<cols>` from `ticker:38` (`uq_ticker_symbol_exchange`), `FLOAT8` for prices from
`daily_bars:32`, `idx_<table>_<cols>` from `job_runs:73` — note `idx_`, not the `ix_` in web.md §1.1.

Two points to state in the migration comments:

- **`ranking_strategy` is outside the unique key**, by decision. A re-run under a different scheme
  **overwrites** the row rather than adding one, and the column names whichever scheme won — see
  the hazard note at the end.
- **`signal_parameters_object_check`.** `JSONB NOT NULL` does not stop `'null'::jsonb`, a bare
  scalar, or an array. The column is a contract with a different repository (`turtle-web`) reading
  it months from now; this one line makes "always an object" true rather than merely intended. It
  also catches an accidental `json.dumps` before the write, which would otherwise store a JSON
  *string* that passes `NOT NULL` and only surfaces on the read side weeks later.

Column comments to write (every existing migration avoids apostrophes inside these SQL literals —
keep them out rather than escaping):

- `id` — surrogate key; `GENERATED ALWAYS AS IDENTITY`, never supplied by the writer.
- `trading_strategy` — full variant label from `--persist-label`, e.g. `bk50d_s12_v2.0`, defaulting
  to the `--trading-strategy` registry key. Part of the natural key so s12/s16/s20 do not overwrite
  each other. Nothing validates that the label matches the parameters actually used —
  `turtle.job_runs.parameters` is the authoritative record of those.
- `ranking_strategy` — the ranking scheme that produced `ranking`, e.g. `qullamaggie`. **Not part of
  the unique key**: a later run of the same trading strategy under a different scheme replaces the
  row, and this column names whichever scheme won.
- `ranking` — 0-100 from `ranking_strategy`; the two columns always travel together. **Stored
  ungated**: `--min-signal-ranking` narrows what signal-runner prints, never what it writes, so
  readers apply their own threshold. Thresholds are scheme-relative — read this with
  `ranking_strategy`, never alone.
- `signal_close` — raw (unadjusted) close on `signal_date`, the bar every entry filter was evaluated
  on. Not the entry fill: the backtest enters at the next trading day's adjusted open.
- `parameters` — per-signal values as of `signal_date`: the strategy's reported indicators
  (`pct_vs_sma50`, `adr_pct`, `adr_pct_change`, `vol_dry_up_ratio`, `rsi14`, `tight_range_ratio`,
  `roc_252d` for qullamaggie) plus `next_open`, the next bar's raw open. A key is **absent, never
  null**, when not reported — `next_open` is missing until a bar after `signal_date` has been
  loaded. Per-signal payload only — the run configuration is in `turtle.job_runs.parameters`.

The `ranking` comment is where the spec's ungated rule earns its keep: it puts the rule where an
analyst finds it with no code in front of them.

**Probably no `GRANT` — but verify rather than assume.** `db/init.sh:37` does
`ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user`,
so an alembic-created table should already be writable by `app_user`. That only holds if the target
database was initialised after that line was added, which I could not confirm for the live Hetzner
database — and `2026_06_24_000001_create_company_history_table.py:48` carries an explicit
`GRANT INSERT ... TO app_user`, suggesting it has not always held. After migrating, run
`\dp turtle.signal`; if `app_user` is absent, add
`op.execute("GRANT SELECT, INSERT, UPDATE ON turtle.signal TO app_user")`.

### 2. `turtlex/repository/tables.py`

Append after `job_runs_table`; add `SmallInteger` to the existing `sqlalchemy` import (`Float`,
`Date`, `Text`, `BigInteger` and `JSONB` are already there).

```python
# signal table definition. `id` is GENERATED ALWAYS AS IDENTITY and must never be supplied as a
# value; created_at/modified_at are owned by the DB.
signal_table = Table(
    "signal",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("trading_strategy", Text),
    Column("ranking_strategy", Text),
    Column("symbol", Text),
    Column("signal_date", Date),
    Column("ranking", SmallInteger),
    Column("signal_close", Float),
    Column("parameters", JSONB),
    schema="turtle",
)
```

The `id`-present-but-never-written shape and its comment mirror `job_runs_table` exactly.

### 3. `turtlex/repository/ingest/signal.py` — new

Sync `Engine`, per the package rule that a write repository follows its caller and this CLI has no
I/O to overlap. Shape from `ingest/lightyear.py`, upsert form from `ingest/daily_bars.py:34-49`.

```python
class SignalRepository:
    """Sync Engine-based repository for strategy-signal writes."""

    def __init__(self, engine: Engine) -> None: ...

    def upsert_signals(self, signals: list[Signal], *, trading_strategy: str, ranking_strategy: str) -> int:
        """Store signals under `trading_strategy`, overwriting any already stored for the same key.

        Args:
            signals: Signals to store, ungated -- the caller must not have applied a ranking filter
            trading_strategy: Variant label written to the trading_strategy column, e.g. bk50d_s12_v2.0
            ranking_strategy: Name of the scheme that produced each ranking

        Returns:
            int: Number of signals sent to the database

        Raises:
            ValueError: If any signal carries no signal_close, which turtle.signal requires
        """
```

**Validate the `NOT NULL` precondition here, not at the database.** CLAUDE.md asks for early
validation with a descriptive message, and the raw alternative is
`null value in column "signal_close" violates not-null constraint` — true, but it names neither the
strategy nor the reason:

```python
missing = [s for s in signals if s.signal_close is None]
if missing:
    raise ValueError(
        f"{len(missing)} of {len(signals)} signals carry no signal_close (first: {missing[0].ticker} "
        f"{missing[0].date}); turtle.signal requires it, so --persist needs a strategy that reports "
        "the signal-date close -- currently only qullamaggie"
    )
```

Conflict target is the **unique constraint**, not the primary key — `id` is a surrogate and never
matches an existing row:

```python
stmt = pg_insert(signal_table).values(values)
on_conflict_stmt = stmt.on_conflict_do_update(
    index_elements=[signal_table.c.trading_strategy, signal_table.c.symbol, signal_table.c.signal_date],
    set_={
        # ranking_strategy is updated with ranking, never without it: the column names the scheme
        # that produced the stored score, so leaving it behind would make the row lie about itself.
        "ranking_strategy": stmt.excluded.ranking_strategy,
        "ranking": stmt.excluded.ranking,
        "signal_close": stmt.excluded.signal_close,
        # incoming is authoritative for every key EXCEPT next_open, which falls back to the
        # stored value. A plain assignment here DELETES a next_open an earlier, wider run
        # backfilled; a blanket `existing || incoming` fixes that but strands every indicator
        # the current run stopped reporting. jsonb_strip_nulls drops the key when neither has one.
        "parameters": func.jsonb_strip_nulls(
            stmt.excluded.parameters.op("||")(
                func.jsonb_build_object(
                    "next_open",
                    func.coalesce(stmt.excluded.parameters["next_open"], signal_table.c.parameters["next_open"]),
                )
            )
        ),
    },
)
```

That `ranking_strategy` line is the direct consequence of keeping it out of the unique key. A run
under a different scheme replaces the row; if the update omitted the column, the row would keep the
old scheme's name against the new scheme's score — the one genuinely corrupt state this schema can
reach.

**`DO UPDATE`, not `DO NOTHING`.** Two values legitimately change on a re-run: `next_open` arrives
once a later bar is loaded, and `ranking` itself can move, because `pct_vs_sma50` derives from
`adjusted_close`, which EODHD rewrites retroactively on every dividend (web.md §1.1). `DO
NOTHING` would freeze the first, emptier payload forever.

Return `len(values)`, as `daily_bars.py:49` does — `DO UPDATE` writes every row, so the count *is*
the input length. `lightyear.py` uses `RETURNING` only because `DO NOTHING` makes both `rowcount`
and the input length meaningless. Put that reasoning in a comment, or the next reader will "fix" it
to match lightyear.

Payload helper, module-level:

```python
def _parameters(signal: Signal) -> dict[str, float]:
    """Per-signal jsonb payload: the reported indicators plus next_open.

    None is omitted rather than stored as JSON null, matching Signal.indicators, which already
    drops an indicator whose signal-date value is missing. An absent key therefore always means
    "not reported". The signal-date close is excluded on purpose -- it has a column of its own.
    """
    params = dict(signal.indicators)
    if signal.next_open is not None:
        params["next_open"] = signal.next_open
    return params
```

No serialisation helper is needed: every value is already JSON-native (`float`, `dict[str, float]`),
so `job_run_service._jsonable` — a private helper of another module — must not be reached for. JSONB
takes the plain dict; no `json.dumps` (`ingest/job_run.py:41` is the precedent).

One `VALUES` for the whole list, as `lightyear.py` does — a 3-month s12 run is ~208 rows, so no
batching. This is safe from Postgres's *"ON CONFLICT DO UPDATE command cannot affect row a second
time"*, which fires when one statement carries two rows sharing a conflict key:
`_get_polars_signals` appends each accepted date once per ticker after the cooldown loop
(`qullamaggie.py:294`) and `SignalService.scan` visits each ticker once, so `(symbol, signal_date)`
is unique within a scan.

Register in `turtlex/repository/ingest/__init__.py` (alphabetised import + `__all__`), and extend
its module docstring — it currently reads "the Lightyear statement importer is sync (Engine)",
naming the one sync repository, which stops being true.

*(The module name does not shadow the stdlib `signal`: Python 3 uses absolute imports and this is a
package submodule. Worth a comment so nobody "fixes" it.)*

### 4. `turtlex/cli/signal_runner.py`

Two flags on `create_argument_parser()` — on **this** parser, not `build_common_analysis_parser()`,
so backtest-runner and portfolio-runner do not grow a flag they do not implement:

- `--persist` (`store_true`) — off by default; the CLI stays read-only unless asked. Its help must
  say it requires a strategy reporting the signal-date close, i.e. `qullamaggie` today.
- `--persist-label` (`str`, `default=None`, `metavar="LABEL"`).

**Normalise the label in `main()` immediately after `parse_args()`**, before `log_parameters` and
`run_job`:

```python
if not args.persist_label:
    args.persist_label = args.trading_strategy
```

Placement matters. `run_job` records `vars(args)` into `turtle.job_runs.parameters.cli`, so
normalising first means the *effective* label is what gets logged and recorded. Resolving lazily at
the call site would work but would record `persist_label: null` in the one table that exists to
answer "what did that run actually do".

**The ordering trap, and why it is structural.** [web.md](web.md) §1.1 requires persisting
*ungated* — "Gating at write time destroys information you cannot recover." But `run_list` today
**rebinds** the name:

```python
signals = service.scan(...)
if args.min_signal_ranking > 0:
    kept = [...]
    signals = kept  # <- the ungated list is now unreachable under any name
```

After that line the ungated list does not exist, so persistence added "at the end" is *forced* to
be gated. The fix is to stop rebinding, which makes the correct behaviour independent of statement
order:

```python
signals = service.scan(...)  # ungated, and stays that way
if signal_repo is not None:
    # Ahead of the ranking gate on purpose: --min-signal-ranking narrows what is printed, never
    # what is written. A gated write destroys rows no reader can recover without a full rescan.
    written = signal_repo.upsert_signals(signals, trading_strategy=args.persist_label, ranking_strategy=args.ranking_strategy)
    logger.info(f"Persisted {written} signals as '{args.persist_label}' ranked by {args.ranking_strategy}")

listed = signals
if args.min_signal_ranking > 0:
    listed = [s for s in signals if s.ranking >= args.min_signal_ranking]
    logger.info(f"Ranking gate >= {args.min_signal_ranking}: kept {len(listed)} of {len(signals)} signals")
print(format_signal_table(sorted(listed, key=lambda s: (s.date, s.ticker)), service.ticker_repo.get_sectors()))
```

Persist **before** printing: if the write fails the run should fail loudly and print nothing, rather
than print a table that reads as success and then raise. Do not wrap it in `try/except` — CLAUDE.md
forbids swallowed exceptions, and `run_job` records the failure in `job_runs` on hosts where
job-run logging is enabled — off on dev machines, where stderr and the exit code are the whole
signal. (Contrast the
`JobRunRecorder`, which *is* guarded: that is telemetry *about* the run; this is the run's output.)

Signature: `run_list(service, args, signal_repo: SignalRepository | None = None)`. A trailing
defaulted parameter leaves the three existing `TestHandlers` tests untouched. `main()` passes
`SignalRepository(settings.engine) if args.persist else None` — the same conditional-repository
shape `run_job` already uses for `JobRunRepository`, and it keeps a write repository out of the
read-only path entirely.

### 5. Docs

- `docs/scripts.md` — both flags in the signal-runner option list, one worked example, the sentence
  that matters (`--persist` writes **before** the `--min-signal-ranking` gate, so the gate never
  affects what is stored), and the qullamaggie-only restriction.
- `docs/signal_runner.md` — a `SignalRepository` node in the component diagram and an
  `H->>SR: upsert_signals(ungated)` arrow placed before the gate step.
- `CLAUDE.md` §Database — a `turtle.signal` bullet beside the `turtle.job_runs` one.
- [web.md](web.md) §1.1–1.3 — amend to match: surrogate key, the `trading_strategy` /
  `ranking_strategy` split, `signal_close`, `parameters`, and the `--min-signal-ranking`
  interaction, all of which postdate that section.
- `npx markdownlint-cli2` after any markdown edit.

## Not in scope

- **The nightly systemd timer** ([web.md](web.md) §1.4). Its example command in §1.4 is now
  over-specified — since `c1ae107`, `--trading-strategy qullamaggie` and `--ranking-strategy
  qullamaggie` are the defaults. See the `next_open` note in Verification before writing it.
- **The 3-month backfill run** (web.md §1.4) — operational, and blocked on the same
  local-database prerequisite as verification.
- **The `turtle_web` read-only role** (web.md §1.5) — belongs with the website.

## Tests

Mirroring the source tree, per CLAUDE.md.

`tests/repository/ingest/test_signal.py` (new) — MagicMock-engine pattern from
`tests/repository/ingest/test_lightyear.py:13-26`, asserting on compiled SQL:

- empty list → `0`, `engine.begin` never called; non-empty → `len(signals)`
- compiled SQL contains `ON CONFLICT (trading_strategy, symbol, signal_date) DO UPDATE SET`
- **the update sets `ranking_strategy`, `ranking`, `signal_close` and `parameters`** — omitting
  `ranking_strategy` is the corrupt-row bug above; omitting `parameters` is the `next_open` backfill
  bug. A `set_={"ranking": ...}`-only upsert passes every other assertion in this file.
- `id`, `created_at` and `modified_at` are absent from the insert payload
- payload for a qullamaggie-shaped `Signal`: the close lands on the `signal_close` column, and the
  jsonb has exactly 8 keys (7 indicators + `next_open`) with **no `signal_close` key of its own**
- `next_open` omitted from the jsonb when it is `None` — the newest-bar case
- **a `Signal` with `signal_close is None` raises `ValueError`, and the engine is never touched** —
  pins the precondition check rather than letting Postgres reject it
- `trading_strategy` and `ranking_strategy` come from the arguments, not from the `Signal`

`tests/cli/test_signal_runner.py` (extend):

- **`test_persist_writes_ungated_while_table_is_gated`** — the regression test for this whole design:
  `--persist --min-signal-ranking 44` with signals scoring 34 and 44; assert the repository received
  **both** and the printed table shows only the 44. If the rebinding is reintroduced, this fails.
- repository not called without `--persist`
- `--persist-label bk50d_s12_v2.0` reaches `upsert_signals`' `trading_strategy` argument, and
  `args.ranking_strategy` reaches its `ranking_strategy` argument
- `test_defaults`: `args.persist is False`, `args.persist_label is None`
- `TestMain`: with `--persist`, `SignalRepository` constructed once with `settings.engine`; without
  it, not constructed; and `--trading-strategy mars --persist` normalises `persist_label` to `"mars"`

No migration test — the repo has none, and `upgrade`/`downgrade` are checked by hand.

## Verification

```bash
uv run alembic upgrade head
uv run alembic downgrade -1 && uv run alembic upgrade head   # trigger + table drop cleanly
uv run pytest && uv run mypy && uv run ruff check turtlex/ scripts/ && uv run ruff format --check turtlex/ scripts/
npx markdownlint-cli2
```

Then, against localhost Postgres:

1. `\d turtle.signal` — `pk_signal` on `id`, `uq_signal_trading_strategy_symbol_signal_date`, all three
   CHECKs, `idx_signal_signal_date`, and the `signal_modified_at` trigger.
2. `uv run signal-runner --start-date 2026-06-01 --end-date 2026-08-22 --persist --persist-label bk50d_s12_v2.0`
   → expect **208** rows (the ungated s12 count measured this session).
3. `SELECT symbol, signal_date, ranking_strategy, ranking, signal_close, jsonb_pretty(parameters) FROM turtle.signal LIMIT 3;`
   — `ranking_strategy = 'qullamaggie'`, the `signal_close` column populated, and 8 jsonb keys with
   no `signal_close` among them.
4. **Ungated proof** (the acceptance test for the spec rule): re-run with `--min-signal-ranking 44`,
   then `SELECT min(ranking) FROM turtle.signal WHERE trading_strategy = 'bk50d_s12_v2.0';` must still
   be **below 44**. If it rises to 44, persistence is behind the gate.
5. **Idempotency:** re-run identically → `count(*)` unchanged. Assert on the count, *not* on
   `modified_at` or the payload: `DO UPDATE` rewrites every row by design, so the trigger bumps
   `modified_at` on every run.
6. **`next_open` backfill:** run with `--end-date D`, confirm `parameters ? 'next_open'` is false for
   signals dated D; re-run with `--end-date D+5` and confirm it flips true. Note the direction —
   re-running the *same* `--end-date` never fills it, because the window ends there and the last bar
   still has no successor (`qullamaggie.py:297-299`). Only a later `--end-date` backfills. **This is
   why the eventual §1.4 timer needs a rolling multi-day window, not a single day.**
7. **Variant separation:** `--trading-param sma_thresh=0.16 --persist-label bk50d_s16_v2.0` → both
   labels coexist for a symbol/date both variants emit, with different `id`s.
8. **Ranking-scheme overwrite** (the consequence of keeping `ranking_strategy` out of the key):
   re-run step 2 with `--ranking-strategy momentum`. `count(*)` must be **unchanged**, and
   `SELECT DISTINCT ranking_strategy FROM turtle.signal WHERE trading_strategy = 'bk50d_s12_v2.0';`
   must return only `momentum` — proving the column tracked the score rather than going stale.
9. **The NOT NULL restriction, surfaced properly:** `--trading-strategy mars --persist` must fail
   with the `ValueError` message from §3, not a Postgres constraint violation, and must leave
   `count(*)` unmoved.
10. **Off by default:** a run with no `--persist` leaves `count(*)` unmoved.
11. `SELECT parameters->'cli'->>'persist_label' FROM turtle.job_runs WHERE name = 'signal-runner' ORDER BY start_at DESC LIMIT 1;`
    — the effective label, not null.

> ⚠️ **Where you can run this.** Test `--persist` against the local Docker Postgres, never against
> the Hetzner VPS. This used to be enforced: `ACTIVE_PROFILE=hetzner-db` connected as the SELECT-only
> `claude` role, so a write under that profile failed with a clear Postgres error. Since 2026-08-29
> the profile connects as `app_user`, which **can** write, so a `--persist` run under `hetzner-db`
> now inserts into production instead of failing. Check the `Database connection:` banner the CLI
> logs at INFO before passing `--persist`.

## Deliberately rejected

- **A `SignalPersistService`** — one call site, one method; CLAUDE.md §2 forbids abstractions for
  single-use code. `SignalService` is a scan orchestrator; giving it a write repository would couple
  the read path to a write path only one CLI wants.
- **Promoting the indicators to real columns.** Note web.md §1.1's parity argument does **not**
  transfer: it was made about widening `Signal` with newly *computed* fields, whereas these floats
  are already computed on both paths, and the parity tuple is
  `(symbol, signal_date, entry_date, entry_price)` — it covers them under neither design. Two
  reasons that do hold: the key set is strategy-specific and expected to move — `vol_dry_up_ratio`
  was retired *as an entry filter* on 2026-08-01 and is still reported, and `tight_range_ratio` has
  always been reported-only, so which values are worth keeping is under active revision; and absent-means-not-reported maps cleanly onto a missing
  key but badly onto a nullable column, where NULL conflates "this strategy does not report it"
  with "reported as nothing". Separately, the parity gap web.md names is real and already open —
  that is an argument for widening the parity tuple, not against columns.
- **A `job_run_id` column** — tempting for provenance, but a re-run overwrites the row, so after the
  second run the recorded id names a run that did not produce the current values.
- **Widening `Signal` or touching any strategy** — nothing here requires it. In particular, do not
  make `darvas_box`/`mars`/`momentum` populate `signal_close` just to let them persist; that is a
  change to three strategies in service of a table none of them has a reason to write to yet.

**Reversed by `signal_close NOT NULL`:** an earlier draft kept `--persist` strategy-agnostic, on the
grounds that `(trading_strategy, symbol, signal_date, ranking)` is a useful row on its own. The
`NOT NULL` decision settles it the other way — `--persist` now requires a strategy that reports the
signal-date close. The §3 precondition check is what keeps that a clear message rather than a
constraint violation 3 minutes into a universe scan.

**Known, accepted hazards.**

- Re-running one label with a different `sma_thresh` silently overwrites another variant's values —
  the label is the only thing separating variants and nothing validates it.
- Re-running under a different `--ranking-strategy` replaces the previous scheme's score rather than
  storing both, by decision. `ranking_strategy` names the winner, so no row lies, but the earlier
  score is gone.
- `--persist --max-tickers 500` writes a partial universe indistinguishable from a full one — and
  `get_qullamaggie_qualified_symbols` applies the limit in Python after an `ORDER BY code`, so it is
  the alphabetically-first N, not a sample.
- A re-run whose window or universe is not a superset of the previous one leaves a **mixture** under
  one label: run A over Jun-Aug under `qullamaggie` then run B over Aug only under `momentum`, and
  `WHERE trading_strategy = ? AND ranking >= 44` silently spans two incomparable score
  distributions. Every row is honest; the label is not. Group by `(trading_strategy,
  ranking_strategy)` rather than filtering on the label alone. Verification step 8 re-runs an
  identical window and so does not exercise this.

In all four, `turtle.job_runs.parameters.cli` is where the truth is — which is what the
`trading_strategy` column comment points at.
