# Lightyear trade import

## Context

Trades are placed manually on the Lightyear broker platform, but the repo has no record of what is
actually held — every position, backtest and study today is hypothetical. The goal is a durable
ledger of real Buy/Sell executions in Postgres, so live holdings can be joined against `daily_bars`,
`company` and signal output using the same `TICKER.US` keys the rest of the codebase uses.

The workflow has two manual steps and one automated one:

1. Download the account statement CSV from Lightyear *(manual)*
2. Drop it into a folder *(manual)*
3. Run one command that parses every CSV in that folder, keeps only the rows matching a watchlist,
   and inserts them idempotently *(automated — this plan)*

Idempotency is the load-bearing requirement: Lightyear statements overlap in date range, so the same
transaction will appear in many downloaded files. Re-running must never double-count.

## Decisions already made

| Decision | Choice |
| --- | --- |
| Rows imported | CSV `Type` of `Buy` and `Sell` only. `Dividend`, `Conversion`, `Deposit` parsed and skipped. |
| Stored `transaction_type` | Lowercased on insert — the only valid DB values are `buy` and `sell`. |
| Symbol filter | Membership in `turtle.ticker_group` under group code `lightyear` — a hand-maintained watchlist, populated and amended by running SQL directly. Nothing in this codebase writes it. |
| Symbol matching | CSV `Ticker` + `.US`, **and** `CCY = 'USD'` |
| Re-import | `reference` is the unique key; `ON CONFLICT DO NOTHING` |
| Scope | Raw transaction ledger only — no derived positions table |
| Input | Scan a folder for `*.csv`; files are left in place |
| Write path | Sync `Engine` repository (not async) |

### The `lightyear` group must be seeded before the first import

`turtle.ticker_group` currently holds exactly one group — `active`, 2580 members. **`lightyear` does
not exist yet.** Create it by hand before the first run; the primary key is `(code, ticker_code)`,
and `rate` is nullable and unused here:

```sql
INSERT INTO turtle.ticker_group (code, ticker_code)
VALUES ('lightyear', 'DUOL.US'), ('lightyear', 'PRGS.US')  -- …one row per held symbol
ON CONFLICT DO NOTHING;
```

Because the group is hand-maintained, an unseeded or misspelled group is the most likely operator
error, and it fails silently: an empty set makes every row miss filter 3, so the run reports "0
inserted" exactly as a correct idempotent re-run does. Guard it — see §6.

### Why the `CCY = 'USD'` rule matters

Verified against the live DB: 13 of the 14 Buy/Sell symbols in the sample statement match
`ticker_group('active')` once `.US` is appended — measured against `active` because it is the only
group that exists today; the argument holds for `lightyear`, which will be a subset of the same
`TICKER.US` keys. **ASML is a false match.** The CSV row is the
Amsterdam listing (ISIN `NL0010273215`, EUR 1385.60); `ASML.US` in `turtle.ticker` is the NASDAQ ADR
(ISIN `USN070592100`). Without the currency rule, a EUR sale of the AMS line would be recorded as a
sale of a US ADR that was never held.

ISIN cross-checking was rejected as the guard because EODHD ISIN data is unreliable —
`turtle.ticker` reports `SN.US` as ISIN `US7997OY1051`, while the statement (correctly) says
`KYG8068L1086`. A strict ISIN check would silently drop a genuine buy.

## Implementation

### 1. Migration — `db/migrations/versions/2026_08_03_000001_create_lightyear_transaction_table.py`

Copy the shape of `db/migrations/versions/2026_03_20_000001_create_ticker_group_table.py`:
`op.execute("SET search_path TO turtle, public")` first, fully schema-qualified raw SQL, a
`COMMENT ON` per column, a `<table>_modified_at` trigger calling `turtle.update_modified_at_column()`,
and a `downgrade()` that drops the trigger then the table.

- `revision = "d1e2f3a4b5c6"`, `down_revision = "c7d8e9f0a1b2"` (current head — verify with
  `uv run alembic current` before writing).
- **No `GRANT` statement needed.** `pg_default_acl` already grants `app_user=arwd` and `claude=r` on
  every table alembic creates. The `GRANT INSERT` line in the `company_history` migration is
  redundant; do not copy it.
- Column name is `modified_at`, **not** `updated_at` (renamed repo-wide in `fb1e3c0`).

```sql
CREATE TABLE turtle.lightyear_transaction (
    reference        TEXT           NOT NULL,
    transacted_at    TIMESTAMP      NOT NULL,
    ticker_code      TEXT           NOT NULL,
    isin             TEXT           NOT NULL,
    transaction_type TEXT           NOT NULL,
    quantity         NUMERIC(20, 9) NOT NULL,
    currency         TEXT           NOT NULL,
    price            NUMERIC(20, 9) NOT NULL,
    gross_amount     NUMERIC(20, 2) NOT NULL,
    fee              NUMERIC(20, 2) NOT NULL,
    net_amount       NUMERIC(20, 2) NOT NULL,
    source_file      TEXT           NOT NULL,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at      TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lightyear_transaction PRIMARY KEY (reference),
    CONSTRAINT lightyear_transaction_type_check CHECK (transaction_type IN ('buy', 'sell'))
)
```

Two column choices that deviate from repo habit, deliberately:

- **`transacted_at` is `TIMESTAMP`, not `TIMESTAMPTZ`.** The statement's timezone is not documented
  and the sample is self-contradictory (`13:30:00` on a US buy reads as UTC market open;
  `18:05:48` on an Amsterdam sell is after that market closes in UTC). Storing the printed value
  verbatim is lossless; converting under a guessed zone is not. Say so in the `COMMENT ON COLUMN`.
- **Money columns are `NUMERIC`, and the Python side uses `Decimal`.** `turtlex/model.py` uses
  `float` throughout, but those are strategy-domain values; this is a financial ledger where float
  drift on summed amounts is a real defect.

### 2. `turtlex/repository/tables.py`

Add `lightyear_transaction_table` following the existing pattern — omit `created_at`/`modified_at`
(DB defaults plus the trigger own them), `schema="turtle"`.

### 3. `turtlex/repository/query/ticker.py` — new read method

```python
def get_group_ticker_codes(self, group_code: str) -> set[str]:
    """Return every ticker code in a ticker_group, unfiltered by exchange or country."""
```

Reuse of the existing `get_symbol_list` was evaluated and rejected: it joins `turtle.ticker` and
filters on `country = 'USA'` and `US_EXCHANGES`, which drops **23 AMEX members** of the `active`
group (`UEC.US`, `BTG.US`, `NG.US`, …) — and would drop the same names from `lightyear`. A
watchlist-membership test must read `ticker_group` alone, or a genuine AMEX purchase would be
silently skipped. Single `select(tg.c.ticker_code).where(tg.c.code == group_code)`
inside `with self._engine.connect()`.

### 4. `turtlex/model.py` — new dataclass

`LightyearTransaction` with the 12 payload fields, matching the existing plain-`@dataclass` style
(not frozen, no slots) with a Google-style `Attributes:` docstring. Per CLAUDE.md this belongs in
`model.py`, not a per-package models file. `datetime` and `Decimal` here, unlike the rest of the file.
`transaction_type` is a `str` holding the already-lowercased `buy`/`sell`; document that in the
`Attributes:` block so callers don't re-normalise.

### 5. `turtlex/repository/ingest/lightyear.py` — new sync repository

```python
class LightyearRepository:
    def __init__(self, engine: Engine) -> None: ...
    def insert_transactions(self, transactions: list[LightyearTransaction]) -> int:
        """Insert transactions, skipping any whose reference is already stored.

        Returns: number of rows actually inserted.
        """
```

`pg_insert(...).values(...).on_conflict_do_nothing(index_elements=[t.c.reference])` executed inside
`with self._engine.begin() as conn:`; return `result.rowcount`. Guard `if not transactions: return 0`
first, per the existing ingest repos.

Also update `turtlex/repository/ingest/__init__.py`: export `LightyearRepository` in `__all__` and
widen the module docstring, which currently claims the package is async-only.

### 6. `turtlex/service/lightyear_service.py` — parse, filter, insert

`LightyearService(repository, ticker_repo)` with one public method:

```python
def import_folder(self, folder: Path, group_code: str) -> ImportSummary:
```

Parsing notes that will otherwise cause bugs:

- **Date format is `%d/%m/%Y %H:%M:%S` — day-first, not US.** `31/07/2026` in the sample proves it.
- Use stdlib `csv.DictReader`. The repo has no CSV *reader* today (only a `csv.DictWriter` in
  `portfolio_service.py`); Polars is a poor fit here given empty-string cells in typed columns.
- Numeric cells arrive as quoted strings with trailing zeros (`"8.000000000"`); `""` means N/A.
- `Gross Amount` means different things per side — for a Buy it is cost **plus** fee
  (`8 × 131.50 = 1052.00` net, gross `1053.00`); for a Sell it is proceeds **before** fee. Store all
  three columns verbatim and do not derive one from the others.
- Header has a trailing-period column name: `Net Amt.` and `Tax Amt.`.
- **Store `transaction_type` lowercased.** The CSV says `Buy`/`Sell`; the DB accepts only `buy`/`sell`
  (CHECK constraint above). Do the `.lower()` once, in the service, when building the dataclass —
  never in SQL and never at read time, so every consumer can compare against a lowercase literal.

Filter chain per row, counting each rejection reason for the summary:

1. `Type` not in `{"Buy", "Sell"}` → skip
2. `CCY != "USD"` → skip
3. `f"{Ticker}.US"` not in the group set → skip
4. otherwise → insert candidate with `transaction_type = Type.lower()`

Before inserting, check for duplicate `reference` values *within* the batch and log a `WARNING`
naming them. `ON CONFLICT DO NOTHING` would otherwise silently discard the second row of a
partially-filled order that reused its order reference. The sample shows `CN-` conversion
references appearing twice (once per FX leg), so non-unique references demonstrably occur in this
format — the `OR-` prefix being unique is an assumption worth surfacing rather than trusting.

Fetch the group set once per run, not per file — and **fail loudly if it comes back empty**. Since
the group is populated by hand, an empty set means it was never seeded or the code was misspelled,
not that nothing matched. Raise `ValueError` naming the group code rather than parsing files that
can only produce zero inserts.

### 7. `turtlex/cli/import_lightyear.py` + `pyproject.toml`

Follow `turtlex/cli/snapshot_company.py` exactly — it is the closest existing CLI:
module docstring with a `Usage:` block → `create_argument_parser()` ending in `add_logging_args(parser)`
→ `main() -> int` doing `parse_args()`, then `setup_logging(args.verbose)`, then `Settings.from_toml()`
→ `if __name__ == "__main__": sys.exit(main())`. Fully sync, no `asyncio.run`.

Flags: `--folder` (default `data/lightyear`), `--ticker-group` (default `lightyear`), `--verbose`.

Register in `[project.scripts]`: `lightyear-import = "turtlex.cli.import_lightyear:main"`.

Log one INFO summary line per file and one for the run, e.g.
`statement-2026-07.csv: 51 rows, 14 buy/sell, 12 matched, 3 inserted, 9 already stored`.

Return `1` (with a logged error) if the folder does not exist, or if the ticker group is empty —
catch the `ValueError` from §6 and log it, telling the operator to seed `turtle.ticker_group`.
Return `0` when the folder exists but holds no CSVs, logging a warning — an empty drop folder is a
normal state, not a failure.

### 8. `.gitignore`

Add `data/lightyear/` — these statements are personal financial records and must never be committed.
Commit a `data/lightyear/.gitkeep` so the drop folder exists after a fresh clone.

### 9. Tests

Mirror the source tree, mock the engine (there are zero DB-integration tests in this repo):

- `tests/repository/ingest/test_lightyear.py` — mock `Engine` via the `_make_engine_mock` helper
  style in `tests/repository/query/test_ticker.py`; assert the conflict clause and the empty-list guard.
- `tests/repository/query/test_ticker.py` — extend with `get_group_ticker_codes` cases.
- `tests/service/test_lightyear_service.py` — the core of the suite. Feed a `tmp_path` CSV built from
  the sample statement and assert: day-first date parsing, all four filter reasons, `Decimal`
  precision preserved, `transaction_type` lowercased to `buy`/`sell`, the in-batch
  duplicate-reference warning, the empty-group `ValueError`, and multi-file folder scanning.
- `tests/cli/test_import_lightyear.py` — follow `tests/cli/test_signal_runner.py`, patching
  `turtlex.cli.import_lightyear.Settings` / `.setup_logging` / the repository classes.

### 10. Docs

- `docs/scripts.md` — new `## lightyear-import` section using the file's bolded-label template
  (intro, `**Usage:**` bash fence, `**Options:**` bullets).
- `CLAUDE.md` — one row in the "Most Common Operations" table.

## Verification

```bash
# 1. Migration round-trips cleanly
uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head

# 2. Unit tests and types
uv run pytest
uv run mypy

# 3. Seed the watchlist by hand (see the seed SQL above), then confirm it is non-empty
psql -c "SELECT COUNT(*) FROM turtle.ticker_group WHERE code = 'lightyear'"

# 4. End-to-end against the sample statement
mkdir -p data/lightyear && cp <statement>.csv data/lightyear/
uv run lightyear-import --verbose

# 5. Idempotency — must report 0 inserted
uv run lightyear-import
```

Expected on the sample statement, assuming all 12 symbols are in the `lightyear` group:
**12 rows inserted** — the 12 USD buys (DUOL, PRGS, GENI, BULL, SN, HNI, GDDY, GTLB, AVTR, MRVL,
NIO, VRT). ASML and SEC0 are skipped on the currency rule; every Dividend, Conversion and Deposit
row is skipped on type. A second run inserts 0. Any of the 12 missing from the group is skipped on
filter 3 — check the per-file "matched" count against the seed list before concluding the parser
dropped something.

Note the sample contains **no USD sell**, so the Sell path is exercised only by unit tests — worth a
manual check against a later statement that includes one.

Then confirm holdings resolve against the rest of the schema:

```sql
SELECT lt.ticker_code,
       SUM(CASE WHEN lt.transaction_type = 'buy' THEN lt.quantity ELSE -lt.quantity END) AS qty,
       c.sector, c.market_cap
FROM turtle.lightyear_transaction lt
LEFT JOIN turtle.company c ON c.ticker_code = lt.ticker_code
GROUP BY lt.ticker_code, c.sector, c.market_cap
HAVING SUM(CASE WHEN lt.transaction_type = 'buy' THEN lt.quantity ELSE -lt.quantity END) > 0
ORDER BY 1;
```
