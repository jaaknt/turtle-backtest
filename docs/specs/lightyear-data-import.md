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
| `Tax Amt.` | Stored in its own `tax` column, empty cell → `0` |
| Symbols traded but not in the group | Skipped, and named in a `WARNING` |
| `docs/specs/lightyear-example.csv` | Committed **anonymised** — scrambled references, rounded amounts |

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

The same mistake in miniature is a *single* symbol missing from the group: you buy something new,
forget to seed it, and the buy is silently dropped by filter 3. §6 names those symbols in a
`WARNING` rather than letting the ledger go quietly incomplete.

### Why the `CCY = 'USD'` rule matters

Verified against the live DB: 13 of the 14 Buy/Sell symbols in the full statement match
`ticker_group('active')` once `.US` is appended — measured against `active` because it is the only
group that exists today; the argument holds for `lightyear`, which will be a subset of the same
`TICKER.US` keys. **ASML is a false match.** The CSV row is the
Amsterdam listing (ISIN `NL0010273215`, EUR 1385.60); `ASML.US` in `turtle.ticker` is the NASDAQ ADR
(ISIN `USN070592100`). Without the currency rule, a EUR sale of the AMS line would be recorded as a
sale of a US ADR that was never held.

ISIN cross-checking was rejected as the guard because EODHD ISIN data is unreliable —
`turtle.ticker` reports `SN.US` as ISIN `US7997OY1051`, while the statement (correctly) says
`KYG8068L1086`. A strict ISIN check would silently drop a genuine buy.

## The CSV format

Verified against `docs/specs/lightyear-example.csv`. The header, in order:

```text
 "Date","Reference","Ticker","ISIN","Type","Quantity","CCY","Price/share","Gross Amount","FX Rate","Fee","Net Amt.","Tax Amt."
```

Four properties of this header will each break a naive parser:

- **The line starts with a literal space**, before the opening quote of `"Date"`. With
  `csv.DictReader`'s default dialect that space makes the first field unquoted, so the column is
  named `' "Date"'` — quotes included — and `row["Date"]` raises `KeyError`. **`skipinitialspace=True`
  is mandatory**, not cosmetic.
- **Trailing periods**: `Net Amt.` and `Tax Amt.`, unlike `Gross Amount`.
- **`Price/share`** carries a slash; **`FX Rate`** exists and is unused by this importer.
- Every cell is a quoted string; `""` means N/A, and numerics keep trailing zeros (`"8.000000000"`).

Row shapes, by `Type`:

| `Type` | `Ticker` | `ISIN` | `Quantity` / `Price/share` | `Fee` | `Tax Amt.` |
| --- | --- | --- | --- | --- | --- |
| `Buy` / `Sell` | symbol | populated | populated | populated | empty in the sample |
| `Dividend` | symbol | populated | empty | empty | populated |
| `Conversion` | a currency code | empty | empty | one leg only | empty |

Only `Buy`/`Sell` is imported, so the empty `Quantity`/`Price/share`/`ISIN` cells never reach the
`NOT NULL` columns. `Fee` and `Tax Amt.` are the exceptions: both are `NOT NULL` in the table and
both can be empty, so **an empty `Fee` or `Tax Amt.` cell parses to `Decimal("0")`**.

`Gross Amount` means different things per side — for a Buy it is cost **plus** fee; for a Sell it is
proceeds **before** fee. Verified on all three sample buys:

```text
DUOL   8 × 131.50 = 1052.00 = Net Amt.     Net + Fee 1.00 = 1053.00 = Gross Amount
PRGS  25 × 41.17  = 1029.25 = Net Amt.     Net + Fee 1.00 = 1030.25 = Gross Amount
GENI 150 × 7.215  = 1082.25 = Net Amt.     Net + Fee 1.00 = 1083.25 = Gross Amount
```

Store all four money columns verbatim; never derive one from the others.

Dates are **day-first**: `%d/%m/%Y %H:%M:%S`. `31/07/2026` in the sample proves it.

Reference prefixes seen: `OR-` (order), `DD-` (dividend), `CN-` (conversion). **`CN-` references
appear twice**, once per FX leg — so non-unique references demonstrably occur in this format, and
`OR-` being unique is an assumption worth surfacing rather than trusting. See §6.

## Implementation

### 1. Migration — `db/migrations/versions/2026_08_03_000001_create_lightyear_transaction_table.py`

Copy the shape of `db/migrations/versions/2026_03_20_000001_create_ticker_group_table.py`:
`op.execute("SET search_path TO turtle, public")` first, fully schema-qualified raw SQL, a
`COMMENT ON` per column, a `<table>_modified_at` trigger calling `turtle.update_modified_at_column()`,
and a `downgrade()` that drops the trigger then the table.

- `revision = "d1e2f3a4b5c6"`, `down_revision = "c7d8e9f0a1b2"` — confirmed head via
  `uv run alembic current`.
- **No `GRANT` statement needed.** Confirmed via `pg_default_acl`: role `alembic` in schema `turtle`
  already grants `app_user=arwd` and `claude=r` on every relation it creates. The `GRANT INSERT`
  line in the `company_history` migration is redundant; do not copy it.
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
    tax              NUMERIC(20, 2) NOT NULL,
    net_amount       NUMERIC(20, 2) NOT NULL,
    source_file      TEXT           NOT NULL,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at      TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lightyear_transaction PRIMARY KEY (reference),
    CONSTRAINT lightyear_transaction_type_check CHECK (transaction_type IN ('buy', 'sell'))
)
```

**The database owns both timestamp columns**, exactly as it does for every other table in the
schema — nothing in Python ever writes them:

- On `INSERT`, `created_at` and `modified_at` are both filled by their
  `DEFAULT CURRENT_TIMESTAMP`.
- On `UPDATE`, the `lightyear_transaction_modified_at` trigger overwrites `modified_at` via
  `turtle.update_modified_at_column()`. That function sets `NEW.modified_at` only; `created_at` is
  never touched after insert.

So the trigger is `BEFORE UPDATE` (not `BEFORE INSERT OR UPDATE`), matching `ticker_group`,
`daily_bars` and the rest. This is why §2 omits both columns from the `Table` definition and §5
omits them from the insert payload.

Three column choices that deviate from repo habit, deliberately:

- **`transacted_at` is `TIMESTAMP`, not `TIMESTAMPTZ`.** The statement's timezone is not documented
  and the sample is self-contradictory (`13:30:00` on a US buy reads as UTC market open;
  `18:05:48` on an Amsterdam sell is after that market closes in UTC). Storing the printed value
  verbatim is lossless; converting under a guessed zone is not. Say so in the `COMMENT ON COLUMN`.
- **Money columns are `NUMERIC`, and the Python side uses `Decimal`.** `turtlex/model.py` uses
  `float` throughout, but those are strategy-domain values; this is a financial ledger where float
  drift on summed amounts is a real defect.
- **`tax` is stored even though it is empty on every sampled Buy.** The column exists in the
  statement and is populated on Dividend rows; the sample contains no USD Sell, so a withholding tax
  on a sale is untested territory. Storing it keeps `gross_amount`, `fee`, `tax` and `net_amount`
  mutually reconcilable, and avoids a retroactive migration the first time a taxed sale arrives.

### 2. `turtlex/repository/tables.py`

Add `lightyear_transaction_table` following the existing pattern — **omit `created_at` and
`modified_at`**, which the DB defaults and the trigger own (see §1), `schema="turtle"`.
`Numeric(20, 9)` for `quantity` and `price`, `Numeric(20, 2)` for the four money columns,
`DateTime` for `transacted_at`.

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

`LightyearTransaction` with the 13 payload fields, matching the existing plain-`@dataclass` style
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

The `values(...)` payload carries the 13 dataclass fields only — never `created_at` or `modified_at`.
Both are supplied by the DB (see §1), and `LightyearTransaction` has no field for either.

Because conflicts do nothing, a reference already stored from an earlier file keeps its original
`source_file` — first-seen wins. Intended, and worth a line in the docstring so it is not later read
as a bug.

Also update `turtlex/repository/ingest/__init__.py`: export `LightyearRepository` in `__all__` and
widen the module docstring, which currently claims the package is async-only.

### 6. `turtlex/service/lightyear_service.py` — parse, filter, insert

Two result dataclasses live in this module rather than `turtlex/model.py`. They are computed results
sitting next to their producer, following `TradeMetrics` in `turtlex/backtest/metrics.py`; CLAUDE.md's
rule targets shared *domain* dataclasses and per-package `models.py` files, neither of which this is.

```python
@dataclass
class FileImportSummary:
    file_name: str
    rows: int  # data rows read
    buy_sell: int  # passed filter 1
    matched: int  # passed filters 2 and 3
    inserted: int  # rows the DB actually accepted
    skipped_currency: int
    skipped_not_in_group: int
    unseeded_symbols: set[str]  # USD buy/sell tickers absent from the group


@dataclass
class ImportSummary:
    files: list[FileImportSummary]
    # properties for the run totals: rows, buy_sell, matched, inserted, unseeded_symbols
```

`LightyearService(repository, ticker_repo)` with one public method:

```python
def import_folder(self, folder: Path, group_code: str) -> ImportSummary:
```

Parsing notes that will otherwise cause bugs — see [The CSV format](#the-csv-format) for the
evidence behind each:

- **`csv.DictReader(f, skipinitialspace=True)`.** Without the flag the first column is named
  `' "Date"'` and every `row["Date"]` raises `KeyError`. The repo has no CSV *reader* today (only a
  `csv.DictWriter` in `portfolio_service.py`); Polars is a poor fit here given empty-string cells in
  typed columns.
- **Date format is `%d/%m/%Y %H:%M:%S` — day-first, not US.**
- **Empty `Fee` or `Tax Amt.` → `Decimal("0")`.** Both columns are `NOT NULL` in the table and both
  can arrive empty.
- **Store `Gross Amount`, `Fee`, `Tax Amt.` and `Net Amt.` verbatim.** Gross is cost *plus* fee on a
  Buy and proceeds *before* fee on a Sell; deriving one from another silently breaks on one side.
- **Store `transaction_type` lowercased.** The CSV says `Buy`/`Sell`; the DB accepts only `buy`/`sell`
  (CHECK constraint above). Do the `.lower()` once, in the service, when building the dataclass —
  never in SQL and never at read time, so every consumer can compare against a lowercase literal.
- `FX Rate` is ignored.

Filter chain per row, counting each rejection reason for the summary:

1. `Type` not in `{"Buy", "Sell"}` → skip
2. `CCY != "USD"` → skip, `skipped_currency += 1`
3. `f"{Ticker}.US"` not in the group set → skip, `skipped_not_in_group += 1` and record the symbol
   in `unseeded_symbols`
4. otherwise → insert candidate with `transaction_type = Type.lower()`

Before inserting, check for duplicate `reference` values *within the file* and log a `WARNING`
naming them. Per file, not per run: overlapping statements repeat references across files by design,
so a per-run check would fire on every correct re-import. `ON CONFLICT DO NOTHING` would otherwise
silently discard the second row of a partially-filled order that reused its order reference.

Fetch the group set once per run, not per file — and **fail loudly if it comes back empty**. Since
the group is populated by hand, an empty set means it was never seeded or the code was misspelled,
not that nothing matched. Raise `ValueError` naming the group code rather than parsing files that
can only produce zero inserts.

### 7. `turtlex/cli/import_lightyear.py` + `pyproject.toml`

Follow `turtlex/cli/snapshot_company.py` — it is the closest existing CLI:
module docstring with a `Usage:` block → `create_argument_parser()` ending in `add_logging_args(parser)`
→ `main() -> int` doing `parse_args()`, then `setup_logging(args.verbose)`, then `Settings.from_toml()`
→ `if __name__ == "__main__": sys.exit(main())`. Fully sync, no `asyncio.run`.

`snapshot_company.py` talks to `settings.engine` directly; this CLI needs the service, so wire it the
way `signal_runner.py` does:

```python
service = LightyearService(
    repository=LightyearRepository(settings.engine),
    ticker_repo=TickerQueryRepository(settings.engine),
)
```

Flags: `--folder` (default `data/lightyear`), `--ticker-group` (default `lightyear`), `--verbose`.

Register in `[project.scripts]`: `lightyear-import = "turtlex.cli.import_lightyear:main"`.

Log one INFO summary line per file and one for the run, e.g.
`statement-2026-07.csv: 51 rows, 14 buy/sell, 12 matched, 3 inserted, 9 already stored`.

When `unseeded_symbols` is non-empty, add a `WARNING` naming them:
`skipped 2 USD buy/sell rows for symbols not in group 'lightyear': AMD, NVDA — seed them if held`.

Return `1` (with a logged error) if the folder does not exist, or if the ticker group is empty —
catch the `ValueError` from §6 and log it, telling the operator to seed `turtle.ticker_group`.
Return `0` when the folder exists but holds no CSVs, logging a warning — an empty drop folder is a
normal state, not a failure.

### 8. `.gitignore`

Statements are personal financial records and must never be committed:

```gitignore
data/lightyear/
```

No `.gitkeep`, and therefore no negation rule. Git cannot track an empty directory, so keeping the
drop folder in version control would need a placeholder file plus the `data/lightyear/*` +
`!data/lightyear/.gitkeep` pair — and it would buy nothing. The folder is never used empty: dropping
a statement into it is a manual prerequisite (see Context), and that step creates the directory. On
a fresh clone the tool reports the §7 "folder does not exist" error, which names the path and the
fix.

Setup is therefore one command, already part of the verification steps below:

```bash
mkdir -p data/lightyear
```

### 9. `docs/specs/lightyear-example.csv`

Committed as the format fixture, **anonymised**: scramble the reference suffixes and round the
amounts. Preserve exactly:

- the header **byte for byte, including the leading space** — this is what the regression test in
  §10 pins
- day-first dates
- the duplicate `CN-` reference pair (one row per FX leg)
- `qty × price = Net Amt.` and `Net Amt. + Fee = Gross Amount` on every Buy
- one `Dividend` row, to keep a populated `Tax Amt.` and an empty `Fee` in the fixture

Add one **EUR `Sell`** row. The current sample has neither a Sell nor a non-USD Buy/Sell, so filter 2
and the Sell path have no fixture row at all.

### 10. Tests

Mirror the source tree, mock the engine (there are zero DB-integration tests in this repo).
Note neither `tests/cli/` nor `tests/service/` has an `__init__.py`, unlike `tests/repository/*` —
match the local convention.

- `tests/repository/ingest/test_lightyear.py` — mock `Engine` via the `_make_engine_mock` helper
  style in `tests/repository/query/test_ticker.py`; assert the conflict clause and the empty-list guard.
- `tests/repository/query/test_ticker.py` — extend with `get_group_ticker_codes` cases.
- `tests/service/test_lightyear_service.py` — the core of the suite. Feed `tmp_path` CSVs modelled on
  the example and assert: day-first date parsing, all three rejection reasons, `Decimal` precision
  preserved, empty `Fee`/`Tax Amt.` → `0`, `transaction_type` lowercased to `buy`/`sell`, the
  in-file duplicate-reference warning, the empty-group `ValueError`, `unseeded_symbols` populated,
  and multi-file folder scanning.
  Plus **one test that parses the committed `docs/specs/lightyear-example.csv` directly** and asserts
  the expected candidates. This is the only test that catches the leading-space header regression — a
  hand-built `tmp_path` fixture would encode whatever header the test author assumed.
- `tests/cli/test_import_lightyear.py` — follow `tests/cli/test_signal_runner.py`, patching
  `turtlex.cli.import_lightyear.Settings` / `.setup_logging` / the repository classes.

### 11. Docs

- `docs/scripts.md` — new `## lightyear-import` section using the file's bolded-label template
  (intro, `**Usage:**` bash fence, `**Options:**` bullets), matching `## snapshot-company`.
- `CLAUDE.md` — one row in the "Most Common Operations" table.

## Verification

```bash
# 1. Migration round-trips cleanly
uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head

# 2. Unit tests and types
uv run pytest
uv run mypy

# 3. Seed the watchlist by hand, then confirm it is non-empty
psql -c "INSERT INTO turtle.ticker_group (code, ticker_code)
         VALUES ('lightyear','DUOL.US'),('lightyear','PRGS.US'),('lightyear','GENI.US')
         ON CONFLICT DO NOTHING;"
psql -c "SELECT COUNT(*) FROM turtle.ticker_group WHERE code = 'lightyear'"

# 4. End-to-end against the committed example
mkdir -p data/lightyear && cp docs/specs/lightyear-example.csv data/lightyear/
uv run lightyear-import --verbose

# 5. Idempotency — must report 0 inserted
uv run lightyear-import
```

Expected on `docs/specs/lightyear-example.csv` with those three symbols seeded: **3 rows inserted**
(DUOL, PRGS, GENI). The `Dividend` row and the four `Conversion` rows are dropped on type; the added
EUR `Sell` is dropped on the currency rule. A second run inserts 0.

Against a **full** downloaded statement — which is not in the repo — expect **12 rows inserted**, the
12 USD buys (DUOL, PRGS, GENI, BULL, SN, HNI, GDDY, GTLB, AVTR, MRVL, NIO, VRT), assuming all 12 are
in the `lightyear` group. ASML and SEC0 are skipped on the currency rule. Any of the 12 missing from
the group is skipped on filter 3 and named in the unseeded-symbols warning — check that warning
before concluding the parser dropped something.

The full statement contains **no USD sell**, so the Sell path is exercised only by unit tests and the
synthetic EUR sell in the example — worth a manual check against a later statement that includes one.

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
