# Design: `turtle-web` — a read-only website over the turtle database

> **Status:** draft for review. No implementation has started.

## Context

`turtle-backtest` produces everything through CLIs that print to stdout and drop a
quantstats HTML blob into `reports/`. To see today's signals or what you are holding, you
run a script and read a fixed-width table in a terminal. There is no way to look at a price
chart with your own entries marked on it.

This document designs a **separate, read-only website** on the Hetzner VPS, private to
Tailscale, with three pages: signals for the last 3 months, current portfolio state, and
stock price charts. The overriding constraint is **minimum self-written code** — the design
leans on TradingView Lightweight Charts, a classless CSS framework, and SQL, and writes as
little application code as possible.

### Decisions already made

| Decision | Choice |
| --- | --- |
| Deployment | Hetzner VPS, Tailscale-only, no TLS/auth needed |
| Access | Strictly read-only (SELECT only) |
| Repo | New standalone repo; does **not** import `turtlex` |
| Charts | TradingView **Lightweight Charts v5.2** (Apache-2.0, vendored, no npm) |
| Chart scope | Any of the 5,627 symbols in `daily_bars` |
| Portfolio | **Real** Lightyear positions, not the simulated backtest portfolio |
| Signals | Persisted nightly into a new `turtle.signal` table by `turtle-backtest` |

## The blocking finding

**The database holds market data only.** Verified against the live Hetzner DB — the `turtle`
schema has exactly 7 tables:

| Table | Rows | Note |
| --- | --- | --- |
| `daily_bars` | 20,049,330 (4.4 GB) | PK `(symbol, date)` — **the only index**. 5,627 symbols, 2000-01-02 → 2026-08-09 |
| `ticker` | 53,717 | PK `code` (`AAPL.US`) |
| `company` | 6,607 | sector, industry, market_cap, pe |
| `company_history` | 18,923 | monthly point-in-time snapshots |
| `ticker_group` | 2,589 | `active` = 2,580 (strategy universe), `lightyear` = 9 (really held) |
| `exchange` | 73 | |
| `lightyear_transaction` | **9** | real executed buys/sells |

There is **no signal, trade, or position table**. `signal-runner` computes signals in memory
and `print()`s them (`turtlex/cli/signal_runner.py:41`); nothing writes them. `PortfolioState`
(`turtlex/model.py:275`) is an in-memory object that vanishes at process exit, and
`PortfolioManager` has no repository injected at all.

So the work splits into **two repos**. Workstream 1 lands in `turtle-backtest` and is a
precondition for the signals page.

## Recommended architecture

**FastAPI + Jinja2 server-rendered pages + Lightweight Charts. No HTMX, no npm, no build step.**

```text
Browser ──HTTP──> uvicorn/FastAPI ──SELECT──> PostgreSQL (turtle schema)
   │                    │
   │                    ├── Jinja2 renders tables directly into HTML
   │                    └── /api/* returns JSON only for the charts
   │
   └── vendored lightweight-charts.standalone.production.js (~50 KB) draws candles
```

Tables are the bulk of this UI, and a Jinja `{% for %}` loop renders one in ~10 lines. The
only genuinely interactive surface is the chart, and Lightweight Charts is self-contained —
it needs no frontend framework around it. No npm, no bundler, no `dist/`; deploy is
`git pull && systemctl --user restart`, matching the existing EODHD timer pattern exactly.

### Options considered

All three assume a Python backend and Lightweight Charts on the frontend; they differ in how
much structure they impose between the two.

| | **A. FastAPI + Jinja2** ✅ | **B. FastAPI JSON + vanilla ESM** | **C. FastAPI JSON + React/Vite** |
| --- | --- | --- | --- |
| Self-written LOC | **~550** | ~800–900 | ~1,200–1,400 |
| JS LOC | ~90 | ~300 | ~500 |
| Runtime deps | 6 | 5 | 5 + ~250 npm |
| Build step | **none** | none (TS would add one) | Vite + tsc |
| Deploy | 1 systemd unit | 1 systemd unit | build, then serve `dist/` |
| Tables come from | Jinja loops (free) | hand-written DOM code | TanStack Table |

The two table pages contain **zero JavaScript** under option A. The chart page contains one
`<script>` that parses a JSON blob already on the page.

**Why not B:** the API boundary is cleaner, but you hand-write ~180 lines of
`innerHTML`/`createElement` table rendering that Jinja gives you free, and number formatting
gets written twice. It costs +250 LOC to remove one dependency. TypeScript would reintroduce
the build step.

**Why not C:** best ceiling if this grows, and TanStack Table gives sorting/filtering free —
but it is a second toolchain (node on the VPS, or a committed `dist/`) plus an npm supply
chain, for a page only you can reach. Lightweight Charts in React also needs
`useRef`/`useEffect` with a `chart.remove()` cleanup, and StrictMode's double-invoked effects
produce two overlaid charts — the most commonly reported LWC-in-React bug.

**HTMX was considered and rejected.** Swapping a container that holds a live chart does not
reliably re-run its `<script>`, so you must hook `htmx:afterSwap` and re-`createChart` —
and call `chart.remove()` on the old instance or leak a canvas and a `ResizeObserver` per
swap. For three pages and one user, a full page reload costs ~30 ms of server time. HTMX
buys nothing here and adds a second mental model plus that trap.

Client-side table sorting is the one thing given up. Solve it with `ORDER BY` query params
(`/signals?sort=ranking`) — about six lines of Python with a whitelist dict, no JS.

## Workstream 1 — `turtle-backtest` changes (precondition)

Small and additive. Four changes, no touch to `Signal` or any strategy.

### 1.1 New table

`Signal` (`turtlex/model.py:8-20`) carries exactly three fields — `ticker`, `date`, `ranking`.
**Persist only those, plus the strategy name.** Everything display-related (entry date/price,
current price, change %, %above SMA50, ADR%) is derived in SQL on the read side.

Rationale — and note this is *not* the obvious one. Widening `Signal` would **not** break
`tests/research/test_qullamaggie_parity.py`: that test builds `set[tuple]` of exactly
`(symbol, signal_date, entry_date, entry_price)` (see its docstring and the
`for symbol, _, _, _ in entries` unpacking), so extra dataclass fields are invisible to it.

The real risk is the opposite and worse: new fields would be **uncovered** by parity, so the
bulk path (`turtlex/research/qullamaggie.py`) and the production path (`QullamaggieStrategy`)
could silently disagree on `adr_pct`/`pct_vs_sma50` forever with a green suite. CLAUDE.md's
"keep both, and keep them identical" would quietly stop holding for half the payload.
Widening the table pressures you to widen the parity tuple too — real work in this repo.

Keeping it narrow also stays fast: the derived SQL below runs in **92 ms for 250 signals**,
and a 3-month window realistically holds tens, not hundreds.

The escape hatch is clean — the migration is additive, so if the derived SQL drifts or gets
slow, add columns later and the view collapses to a plain SELECT.

> ⚠️ **Documented caveat, not a thing to engineer around.** `pct_vs_sma50` is re-derived from
> `adjusted_close`, which EODHD rewrites retroactively on every dividend. If the 50-day
> window straddles a later ex-date, the displayed value drifts from what it was when the
> signal fired — roughly `(dividend/price) × (fraction of window before ex-date)`, well under
> 0.25% for a typical quarterly dividend. Splits cancel entirely; `adr_pct` is immune. So the
> persisted `ranking` will very occasionally be one point off what the displayed inputs
> imply. Fine for a display; not fine for research, which is why research keeps using Polars.

New alembic migration in `db/migrations/versions/`, raw SQL via `op.execute` per house style:

Follow the shape of `2026_08_03_000001_create_lightyear_transaction_table.py` exactly — raw
SQL, `SET search_path`, a `COMMENT` on every column, and the `modified_at` trigger.

```sql
CREATE TABLE turtle.signal (
    strategy     TEXT     NOT NULL,
    symbol       TEXT     NOT NULL,
    signal_date  DATE     NOT NULL,
    ranking      SMALLINT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_signal PRIMARY KEY (strategy, symbol, signal_date),
    CONSTRAINT signal_ranking_check CHECK (ranking BETWEEN 0 AND 100)
);
CREATE INDEX ix_signal_signal_date ON turtle.signal (signal_date DESC);

CREATE TRIGGER signal_modified_at
    BEFORE UPDATE ON turtle.signal
    FOR EACH ROW EXECUTE FUNCTION turtle.update_modified_at_column();
```

Two design calls worth stating explicitly in the migration comments:

1. **`strategy` holds the full variant label** (`bk50d_s12_v2.0`), not the registry key
   (`qullamaggie`). The CLI takes `--trading-strategy qullamaggie --trading-param
   sma_thresh=0.16`, so without a label column s12 and s16 **collide on the primary key**.
   Add a `--persist-label` flag defaulting to `args.trading_strategy`.
2. **Persist ungated.** Write every signal the strategy emits and let readers apply
   `ranking >= :min_ranking`. This mirrors `qullamaggie-signals-v4.py`, which deliberately
   computes cohorts on the ungated pool and shows a held position's sub-gate score rather
   than `--` (`:250-255`). Gating at write time destroys information you cannot recover.

Add the matching `Table` to `turtlex/repository/tables.py`.

### 1.2 Write repository

`turtlex/repository/ingest/signal.py` — sync `Engine` (the CLI has no I/O to overlap, so it
follows the caller per the package rules), `INSERT ... ON CONFLICT (strategy, symbol,
signal_date) DO UPDATE SET ranking = EXCLUDED.ranking, modified_at = now()`. Model it on
`turtlex/repository/ingest/lightyear.py:19-46`.

### 1.3 `--persist` flag on signal-runner

`SignalService.scan()` already returns `list[Signal]` (`turtlex/service/signal_service.py:46`).
The change in `run_list` (`turtlex/cli/signal_runner.py:44-49`) is a handful of lines: after
sorting, if `args.persist`, hand the list to the repository. The strategy identifier comes
from the resolved strategy, not a hardcoded string.

### 1.4 Nightly timer

`deploy/signal-persist.{service,timer}`, copied from `deploy/eodhd-download-daily.*` including
the DEPLOY/PREREQUISITES/STATUS/REMOVE header comments. Schedule **07:00 Europe/Tallinn,
Mon–Sat** — a two-hour margin after the 05:00 EODHD download. Keep it a *separate* timer
rather than chaining `Wants=`/`After=` off the download unit, so a download failure produces
one alert instead of a cascade and either can be re-run independently.

systemd does no command substitution, so either add a small `--start-date-days-ago` flag or
wrap the date arithmetic in `/bin/sh -c`:

```bash
uv run signal-runner --persist \
    --trading-strategy qullamaggie --ranking-strategy qullamaggie \
    --persist-label bk50d_s12_v2.0 \
    --start-date "$(date -I -d '7 days ago')" --end-date "$(date -I)"
```

A 7-day window rather than a 1-day one is correct, not merely cheap:
`QullamaggieStrategy._get_polars_signals` runs its cooldown loop over the full fetched warmup
window and only *then* filters to `d >= start_date`
(`turtlex/strategy/trading/qullamaggie.py:262-272`), so a wider window cannot double-emit.

**Cost:** `SignalService.scan` issues one `get_bars_pl` query per universe ticker
(~2,100–2,580 tickers × 730-day warmup); budget 2–5 minutes. A 3-month backfill is the *same
single pass* with a wider date range — not 90× the work.

**Backfill:** one manual run seeds the three months the site needs:

```bash
uv run signal-runner --trading-strategy qullamaggie --ranking-strategy qullamaggie \
    --start-date 2026-05-12 --end-date 2026-08-11 --persist
```

### 1.5 Read-only DB role

Mirror the `claude` role (`db/init.sh:40-47`), plus four role-level settings that role does
not have — it is an MCP client, this one is a network service:

```sql
CREATE USER turtle_web WITH PASSWORD '${DB_WEB_PASSWORD}';
GRANT CONNECT ON DATABASE trading TO turtle_web;
GRANT USAGE   ON SCHEMA turtle    TO turtle_web;
GRANT SELECT  ON ALL TABLES IN SCHEMA turtle TO turtle_web;
-- FOR ROLE alembic: tables created by future migrations (turtle.signal) inherit this
ALTER DEFAULT PRIVILEGES FOR ROLE alembic IN SCHEMA turtle GRANT SELECT ON TABLES TO turtle_web;

ALTER ROLE turtle_web SET default_transaction_read_only       = on;    -- writes fail at the server
ALTER ROLE turtle_web SET statement_timeout                   = '10s'; -- one bad query can't wedge a worker
ALTER ROLE turtle_web SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE turtle_web SET jit                                 = off;   -- see below
```

`default_transaction_read_only = on` is the important one: a `GRANT`-only role still permits
a write if a table's grants are ever widened. This makes it structurally impossible rather
than conventional.

`jit = off` is not cosmetic. Measured on this database, JIT compilation was **352 ms of a
1,472 ms** query and **138 ms of a 2,851 ms** one — row-count misestimates on small results
routinely trip the JIT cost threshold here, and every query in this app returns few rows.

Extend `db/init.sh` for fresh installs and run the equivalent `psql` once on the VPS.

## Workstream 2 — the `turtle-web` repo

### Layout

```text
turtle-web/
├── pyproject.toml                # uv + hatchling; ruff line-length 140; mypy disallow_untyped_defs
├── config/settings.toml          # [database] / [database.pool]
├── .env.example                  # DB_WEB_PASSWORD  (no EODHD_API_KEY)
├── deploy/turtle-web.service
├── turtleweb/
│   ├── config.py                 # mirrors Settings.from_toml() minus the EODHD requirement
│   ├── db.py                     # sync Engine factory
│   ├── sql.py                    # every SQL string, one place — the whole data layer
│   ├── catalog.py                # symbol catalog, loaded once in the lifespan
│   ├── payload.py                # rows -> chart JSON shapes (isoformat, float casts)
│   ├── main.py                   # FastAPI app + 4 routes
│   ├── templates/{base,signals,portfolio,chart}.html
│   └── static/
│       ├── vendor/lightweight-charts.standalone.production.js
│       ├── vendor/pico.min.css
│       └── chart.js
└── tests/{test_queries.py,test_routes.py}
```

`config.py` deliberately does **not** reuse `Settings.from_toml()`: it hard-requires
`EODHD_API_KEY` and hands out an `app_user` read-write engine. Copy the "TOML for structure, env
for secrets" pattern, require only `DB_WEB_PASSWORD`.

### Routes

| Route | Returns | Notes |
| --- | --- | --- |
| `GET /` | 302 → `/signals` | |
| `GET /signals` | HTML | `?days=90&min_ranking=44` |
| `GET /portfolio` | HTML | positions + totals + equity-curve container |
| `GET /chart?symbol=` | HTML | full page load, no HTMX swap |
| `GET /healthz` | JSON | |

There is **no JSON API and no `/api/symbols` endpoint.** Chart data is embedded in the page
it belongs to as `<script type="application/json">`, and symbol autocomplete is a native
`<datalist>` (see §2.4). That removes four routes, a debounce, and a request-race class of
bug.

> ⚠️ **The Jinja→JS handoff is the most likely way this app breaks.** Emit the payload as
> `<script type="application/json">{{ payload|tojson }}</script>` and read it with
> `JSON.parse(el.textContent)` — never interpolate into inline JS, where a company name
> containing an apostrophe breaks the page. `tojson` uses `json.dumps`, which raises on raw
> `datetime.date` and `Decimal`, so call `.isoformat()` on dates and cast money to `float8`
> in SQL.

### Dependencies

`fastapi`, `uvicorn[standard]`, `jinja2`, `sqlalchemy`, `psycopg[binary,pool]`,
`pydantic-settings`. Vendored assets: `lightweight-charts.standalone.production.js` and
`pico.min.css` (classless — the entire stylesheet is one `<link>`, zero CSS written).

Note `fastapi`, **not** `fastapi[standard]`: the extra pulls in the CLI, `email-validator`
and `python-multipart`, none of which a GET-only server-rendered app uses. Deliberately
absent: **polars, pandas, numpy, alembic**. This app does no dataframe work — SQL returns
display-ready rows, which is the point of pushing the derivations into SQL.

Use `pydantic-settings` with `TomlConfigSettingsSource` rather than cloning the parent repo's
60 lines of hand-rolled TOML loading. Order the sources env > `.env` > TOML so a secret can
never be read from a committed file, and give `db_password` no default so a missing
`DB_WEB_PASSWORD` fails at import — matching the parent's "never fall back for secrets" rule.

Skip profiles entirely. `turtle-backtest` has an `ACTIVE_PROFILE` overlay so one checkout can behave
differently on a dev machine and on the VPS; a *server* has exactly one deployment shape, whose host
and password are both per-machine and both belong in `.env`.

## The SQL

All verified with `EXPLAIN ANALYZE` against the live Hetzner database. Put every statement in
one module, `turtleweb/sql.py`, as module-level constants — that module *is* the data layer.
No repository classes, no ORM models, no service layer: five queries and no writes would make
an abstraction over them exactly the "abstractions for single-use code" CLAUDE.md §2 forbids.

Engine-level guards, applied once rather than per query:

```python
sa.create_engine(
    settings.sqlalchemy_url,
    pool_size=2,
    max_overflow=2,
    pool_pre_ping=True,
    connect_args={"options": "-c statement_timeout=10000 -c jit=off"},
)
```

### Price bars — 1 ms

```sql
SELECT date, open, high, low, close, adjusted_close, volume
FROM turtle.daily_bars
WHERE symbol = :symbol AND date >= :start AND date <= :end
ORDER BY date;
```

`Index Scan using pk_daily_bars … Execution Time: 0.983 ms` for AAPL.US over 2.5 years.
Charts are effectively free. Serialize `date` as `YYYY-MM-DD` — Lightweight Charts wants a
date string, and a naive `datetime` cast introduces a timezone offset.

### Symbol catalog — 142 ms, cached at startup

The obvious `SELECT symbol, max(date) FROM daily_bars GROUP BY symbol` is a **full 20M-row
seq scan at 1,472 ms**. Use a loose index scan instead — index-only, no new index needed:

```sql
WITH RECURSIVE syms AS (
    (SELECT min(symbol) AS symbol FROM turtle.daily_bars)
    UNION ALL
    SELECT (SELECT min(b.symbol) FROM turtle.daily_bars b WHERE b.symbol > s.symbol)
    FROM syms s WHERE s.symbol IS NOT NULL
)
SELECT s.symbol, t.name
FROM syms s LEFT JOIN turtle.ticker t ON t.code = s.symbol
WHERE s.symbol IS NOT NULL;
```

`Execution Time: 142.298 ms`, 5,627 rows — **10× faster**. This is a *loose index scan* (skip
scan): PostgreSQL 17 has no native one, so the recursive CTE does 5,627 `min(symbol) WHERE
symbol > ?` index probes instead of reading all 20 million index entries.

**Do not write a search endpoint.** Load the list once in the FastAPI lifespan and serve
autocomplete from a native `<datalist>` — 5,627 symbols plus names is ~178 KB raw, ~60 KB
gzipped. Ship it with the page.

```html
<form method="get" action="/chart">
  <input name="symbol" list="symbols" value="{{ symbol }}" required
         placeholder="AAPL.US" autocomplete="off">
  <datalist id="symbols">
    {% for s in symbols %}<option value="{{ s.symbol }}">{{ s.name }}</option>{% endfor %}
  </datalist>
  <button>Load</button>
</form>
```

Zero JS, zero debounce, zero request races, zero new index. For comparison, `ILIKE` against
`turtle.ticker` is a **69 ms seq scan per keystroke** *and* returns 53,717 rows including
symbols with no bars — worse on every axis.

### Current positions — 70 ms

Reuse the proven netting query at `scripts/qullamaggie-signals-v4.py:207-228` verbatim. Its
documented caveats (`:189-198`) must be repeated in the page footer:

- `avg_price` is **buy-weighted only** — a partial sell leaves the cost basis unmoved.
- Fees and tax are excluded, so P&L reads slightly better than realised.
- `curr_price` is the **raw** close, not adjusted — that is what compares to actual fills.

Optional: adding `AND date >= CURRENT_DATE - INTERVAL '30 days'` to the `latest` CTE cuts it
from 23,643 rows scanned to ~90. At 70 ms for one user this is not urgent, and the guard
would blank out a delisted symbol's last known close.

### Portfolio equity curve

Verified against live data — returns 9 positions on every trading day; latest row is
**market value $10,678.97 vs cost basis $9,598.61**.

```sql
WITH tx AS (
  SELECT ticker_code, transacted_at::date AS d,
         CASE WHEN transaction_type='buy' THEN quantity ELSE -quantity END AS dq,
         CASE WHEN transaction_type='buy' THEN price*quantity ELSE -price*quantity END AS dcost
  FROM turtle.lightyear_transaction
),
cal AS (
  SELECT date FROM turtle.daily_bars
  WHERE symbol='SPY.US' AND date >= (SELECT min(d) FROM tx)
),
pos AS (
  SELECT c.date, t.ticker_code, SUM(t.dq) AS shares, SUM(t.dcost) AS cost
  FROM cal c JOIN tx t ON t.d <= c.date
  GROUP BY c.date, t.ticker_code
)
SELECT p.date,
       SUM(p.shares * px.close) AS market_value,
       SUM(p.cost)              AS cost_basis
FROM pos p
CROSS JOIN LATERAL (            -- last known close on or before p.date
    SELECT b.close FROM turtle.daily_bars b
    WHERE b.symbol = p.ticker_code AND b.date <= p.date
      AND b.date > p.date - 30 AND b.close > 0
    ORDER BY b.date DESC LIMIT 1
) px
WHERE p.shares > 0
GROUP BY p.date ORDER BY p.date;
```

The lateral is defensive, not a fix for a live bug: I compared it against the simpler
`JOIN … ON b.date = p.date` and **they agree exactly on today's data**, since all 9 holdings
are US symbols sharing the SPY calendar. But the plain join silently *understates the whole
day* the first time any holding has no bar — a halt, a delisting, a calendar mismatch — and
that failure is invisible in the output. The lateral costs nothing and cannot do that.

> ⚠️ **This is not a true equity curve, and the page must say so.** The Lightyear importer
> keeps only Buy/Sell rows in USD (`turtlex/service/lightyear_service.py:161-267`) — deposits,
> withdrawals, dividends and FX are never imported, so cash is unknowable. What is plotted is
> **holdings market value vs cumulative cost basis**. Label it that way rather than "equity".

### Signals, last 3 months

Reads the new table and derives every display column. Three laterals: entry bar, latest bar,
and the indicator window.

```sql
SELECT s.symbol, t.name, s.signal_date, s.ranking,
       e.entry_date,
       e.entry_price,                                                -- RAW open: recognisable
       last.close                                   AS curr_price,   -- RAW close: recognisable
       last.date                                    AS curr_date,    -- staleness is visible
       100.0 * (last.adj_close / e.entry_adj - 1.0) AS change_pct,   -- ADJUSTED: split-safe
       100.0 * ind.pct_vs_sma50                     AS pct_vs_sma50,
       100.0 * ind.adr_pct                          AS adr_pct
FROM turtle.signal s
LEFT JOIN turtle.ticker t ON t.code = s.symbol
LEFT JOIN LATERAL (
    SELECT b.date AS entry_date, b.open AS entry_price,
           b.open * b.adjusted_close / b.close AS entry_adj
    FROM turtle.daily_bars b
    WHERE b.symbol = s.symbol
      AND b.date >  s.signal_date
      AND b.date <= s.signal_date + 10             -- bound: next trading day is within 10 days
      AND b.close > 0 AND b.adjusted_close > 0 AND b.volume > 0
    ORDER BY b.date LIMIT 1
) e ON TRUE
LEFT JOIN LATERAL (
    SELECT b.date, b.close, b.adjusted_close AS adj_close
    FROM turtle.daily_bars b
    WHERE b.symbol = s.symbol
      AND b.date > CURRENT_DATE - 400              -- bound: avoids a full backward index scan
      AND b.close > 0 AND b.volume > 0
    ORDER BY b.date DESC LIMIT 1
) last ON TRUE
LEFT JOIN LATERAL (
    SELECT w.adjusted_close / w.sma50 - 1.0 AS pct_vs_sma50, w.adr_pct
    FROM (
        SELECT b.date, b.adjusted_close,
               avg(b.adjusted_close)                   OVER win50 AS sma50,
               count(*)                                OVER win50 AS n50,
               avg((b.high - b.low) / NULLIF(b.low,0)) OVER win20 AS adr_pct,
               count(*)                                OVER win20 AS n20
        FROM turtle.daily_bars b
        WHERE b.symbol = s.symbol
          AND b.date <= s.signal_date
          AND b.date >  s.signal_date - 130        -- ### CRITICAL ### 2851 ms -> 92 ms
          AND b.close > 0 AND b.adjusted_close > 0 AND b.volume > 0
        WINDOW win50 AS (ORDER BY b.date ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING),
               win20 AS (ORDER BY b.date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)
    ) w
    WHERE w.date = s.signal_date AND w.n50 = 50 AND w.n20 = 20
) ind ON TRUE
WHERE s.strategy = :strategy
  AND s.signal_date >= CURRENT_DATE - CAST(:days AS int)
  AND s.ranking >= :min_ranking
ORDER BY s.signal_date DESC, s.ranking DESC;
```

#### The date bound is the whole ballgame

**PostgreSQL cannot push a `LIMIT` through a `WindowAgg`.** Without
`AND b.date > s.signal_date - 130`, each lateral computes the window over the symbol's
*entire* history and discards all but one row. Measured on this database with 250 signals:

| Form | Rows per lateral | Execution |
| --- | --- | --- |
| Unbounded (`date <= signal_date` only) | 3,371 | **2,851 ms** |
| Bounded (`+ date > signal_date - 130`) | 87 | **92 ms** |

A 31× speedup from one WHERE clause, and the difference between a usable page and a timeout.
130 calendar days yields ~89 trading bars, comfortably above the 51 the SMA50 window needs.

#### Conventions that differ from the research script, deliberately

- **`ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING` is exactly Polars `shift(1).rolling_mean(50)`.**
  The `n50 = 50 AND n20 = 20` guard reproduces Polars' `min_samples`; without it a newly
  listed ticker silently shows a 12-bar "SMA50".
- **The adjustment factor cancels out of ADR%.** `turtlex/strategy/trading/qullamaggie.py:184`
  computes `adj_high = high * (adjusted_close/close)`, so
  `(adj_high − adj_low)/adj_low ≡ (high − low)/low`. The cheap raw form is exactly right.
- **Display raw prices, compute the return from adjusted ones.** The research script uses raw
  for all three (`:29-31`) and therefore needs `SUSPICIOUS_DAY_MOVE = 0.50` (`:79`) to
  suppress the split artifacts that convention creates. On a live page holding positions for
  366 days a split is a matter of when, not if. Deriving `change_pct` from
  `adjusted_close / adjusted_open` makes splits and dividends cancel exactly and removes the
  heuristic. Document that it is now a *total* return, dividends reinvested.
- **`CURRENT_DATE - 400` instead of an unbounded backward scan.** The script's
  `DISTINCT ON (symbol) … ORDER BY symbol, date DESC` reads every bar for every symbol; a
  bounded lateral is ~1 ms. Surfacing `curr_date` makes staleness visible rather than silent.

Expected volume is **~30–90 signals per 3 months** for the baseline `bk50d_s12_v2.0` at
`R >= 44` (11.4 gated signals/month per `docs/research/result-qullamaggie-backtest-v4.md`),
so the page never paginates.

## The chart code

This is the whole of `chart.js`, using the confirmed v5.2 API:

```js
const {createChart, CandlestickSeries, HistogramSeries, LineSeries,
       createSeriesMarkers} = LightweightCharts;

const d = JSON.parse(document.getElementById('chart-data').textContent);

const chart   = createChart(el, { autoSize: true });
const candles = chart.addSeries(CandlestickSeries,
                    { upColor: '#26a69a', downColor: '#ef5350', borderVisible: false });
const sma50   = chart.addSeries(LineSeries, { lineWidth: 1, lastValueVisible: false });
const volume  = chart.addSeries(HistogramSeries,
                    { priceFormat: { type: 'volume' } }, 1);   // <- paneIndex, 3rd arg

candles.setData(d.bars);                    // [{time:'2026-08-09',open,high,low,close}]
volume.setData(d.volume);
sma50.setData(d.sma50);
if (d.markers.length) createSeriesMarkers(candles, d.markers);
chart.timeScale().fitContent();
```

`addSeries` takes `paneIndex` as its third argument, so there is no need for a follow-up
`.moveToPane(1)` — that method is for relocating an *existing* series.

Emit `sma50` as `null` where fewer than 50 bars are available; Lightweight Charts renders
`{time, value: null}` as a gap. Note this is a *display* SMA on the raw close, centred on the
current bar — deliberately **not** the strategy's shift-1 adjusted SMA50 from the signals
query. Label the legend "SMA50 (close)" so the two are never compared.

The equity curve is the same library: a `LineSeries` for market value and another for cost
basis. Prefer `LineSeries` over `AreaSeries` here — with only ~30 points an area fill reads
as a placeholder — and overlay a normalized benchmark so the points have something to sit
against.

## Deployment

`deploy/turtle-web.service`, modelled on `deploy/eodhd-download-daily.service` with the same
header-comment convention:

```ini
[Unit]
Description=Turtle Web (read-only dashboard)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/turtle-web
EnvironmentFile=%h/.config/turtle-web/secrets.env
ExecStart=%h/.local/bin/uv run uvicorn turtleweb.main:app --host 100.x.y.z --port 8080
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

Take `BIND_HOST` from the `EnvironmentFile` (`$(tailscale ip -4)`) and add
`After=network-online.target tailscaled.service`.

**Bind to the Tailscale IP, never `0.0.0.0`.** The Hetzner firewall currently allows inbound
SSH from one IP and blocks everything else (`docs/implementation.md`), so port 8080 is
unreachable from the public internet — but binding explicitly means a firewall change can
never accidentally expose it. Requires `loginctl enable-linger`, same as the existing timers.
Note `WantedBy=default.target`, not `timers.target`: this is a persistent service, unlike
every existing `Type=oneshot` unit in `deploy/`.

> **Worth knowing before you conclude the app is slow:** with all inbound UDP blocked,
> Tailscale cannot establish a direct peer connection and falls back to relaying through
> DERP. It works — every measurement in this document was taken over it — but it adds latency
> and caps throughput. Adding an inbound rule for **UDP 41641** to the Hetzner firewall is
> what enables the direct path.

## Verification

### Workstream 1 checks

1. `uv run alembic upgrade head` → `\d turtle.signal` shows the table and `ix_signal_date`.
2. `uv run pytest && uv run mypy` clean.
3. Backfill run above → `SELECT count(*), min(signal_date), max(signal_date) FROM turtle.signal;`
   returns roughly 30–90 rows spanning ~90 days.
4. Re-run the same command → count unchanged (proves the upsert is idempotent).
5. `systemctl --user list-timers signal-persist.timer` shows the next 05:30 firing.

### Known-good anchors

Assert against these; they were measured on 2026-08-12 and move only with fresh bars.

| Check | Expected |
| --- | --- |
| `SYMBOL_LIST` row count | 5,627 (2,580 with `in_universe = true`) |
| `POSITIONS` row count | 9 (all buys, no sells yet) |
| `EQUITY_CURVE` final row | `market_value ≈ 10678.97`, `cost_basis = 9598.61` |
| `cost_basis` if you use `gross_amount` instead | 9,607.61 — the €9 delta is 9 × €1.00 in fees, the cleanest check that you picked the column you meant |
| `BARS` for AAPL.US since 2000-01-02 | 6,690 rows |

### Guard the 31× regression in a test

Correctness tests cannot see it — the unbounded query returns identical rows, just 31× slower.
Assert on the plan shape instead:

```python
def test_signals_query_is_index_bounded(engine: sa.Engine) -> None:
    """The indicator LATERAL must stay date-bounded; without it this query takes ~2.9 s."""
    plan = "\n".join(r[0] for r in engine.connect().execute(sa.text("EXPLAIN " + sql.SIGNALS), PARAMS))
    assert plan.count("Index Cond") >= 3
    assert "Seq Scan on daily_bars" not in plan
```

More generally: every `EXPLAIN` in this app should show `Index Scan using pk_daily_bars` with
an `Index Cond` containing **both** `symbol =` and a `date` bound. A bare `symbol =` with no
date bound is the slow shape.

The other high-value test parses the embedded chart JSON — `date`/`Decimal` leaking into
`|tojson` produces a blank chart and a console error rather than a 500, so nothing else
catches it:

```python
def test_chart_payload_is_valid_json(client):
    html = client.get("/chart?symbol=AAPL.US").text
    blob = re.search(r'<script id="chart-data"[^>]*>(.*?)</script>', html, re.S).group(1)
    data = json.loads(blob)
    assert set(data["bars"][0]) == {"time", "open", "high", "low", "close"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["bars"][0]["time"])
```

### Workstream 2 checks

1. `psql -U turtle_web` → `SELECT 1 FROM turtle.signal LIMIT 1` succeeds; `INSERT` is
   **denied by `default_transaction_read_only`**, not merely ungranted.
2. `curl localhost:8080/healthz` → 200.
3. `/signals` renders rows matching the SQL run directly in psql.
4. `/portfolio` totals match `market_value 10678.97 / cost_basis 9598.61` for 2026-08-09
   (numbers move with fresh bars; the check is that page and SQL agree).
5. `/chart?symbol=AAPL.US` draws candles + volume pane + SMA50. Then load a *held* symbol and
   confirm an entry marker sits on its signal date; then a thin symbol with gaps, to confirm
   nulls don't throw.
6. Typing `AAPL` in the symbol box offers completions with no network request.
7. From a second Tailscale device the site loads; from the public IP,
   `curl --max-time 5 http://<public-ip>:8080/signals` times out or is refused.
8. `systemctl --user restart turtle-web`, then reboot the VPS and confirm it returns without
   an SSH login — this is what actually tests `enable-linger`, the classic silent failure.

## Index recommendations: add nothing to `daily_bars`

Worth stating explicitly, because two queries here *look* like they need an index and neither
does. The only index on `turtle.daily_bars` is `pk_daily_bars` — 955 MB against a 3,471 MB
heap. Every hot path is `symbol = ? AND date <bounded>`, a perfect prefix match.

| Candidate | Verdict |
| --- | --- |
| `daily_bars (date)` | **No.** ~450–600 MB of new index, and it slows the nightly bulk insert. No query here filters by date without a symbol, so it would never be chosen. |
| `daily_bars (symbol) INCLUDE (…)` | **No.** Redundant with the PK's leading column. |
| `ticker (code text_pattern_ops)` or a `pg_trgm` GIN index | **No.** Made moot by the startup symbol cache. |
| `signal (signal_date DESC)` | **Yes** — but it ships with the new table's own DDL. |

Both queries that looked index-hungry were fixed by rewriting instead, and both rewrites beat
any index: the ticker search does 5,627 probes for the *entire* list rather than deduping
13,289 matching rows, and no index helps a window aggregate that has been asked to read 4,630
rows — bounding the range means it reads 87. **So the only migration `turtle-backtest` needs
is the `turtle.signal` table itself.**

## Open items for implementation

1. Confirm the strategy label string to persist (`bk50d_s12_v2.0` is the baseline) and add
   `--persist-label`.
2. Pick the Tailscale IP/hostname for the bind address.
3. Decide `net_amount` vs `gross_amount` for the equity curve's cost basis — the €9 fee delta
   is the verification anchor either way. Keeping `net_amount` stays consistent with the
   `avg_price` basis on the positions page.
