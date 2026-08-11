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

**FastAPI + Jinja2 server-rendered pages + Lightweight Charts, no build step.**

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

| | **A. FastAPI + Jinja + HTMX** ✅ | **B. FastAPI JSON + vanilla ESM** | **C. FastAPI JSON + React/Vite** |
| --- | --- | --- | --- |
| Python LOC | ~250 | ~200 | ~200 |
| JS/TS LOC | ~90 | ~300 | ~500 |
| Template LOC | ~120 Jinja | 0 | 0 |
| Runtime deps | 5 | 3 | 3 + ~300 npm |
| Build step | **none** | **none** | Vite + tsc |
| Deploy | 1 systemd unit | 1 systemd unit | build, then serve `dist/` |
| Tables come from | Jinja loops (free) | hand-written DOM code | TanStack Table |

**Why not B:** the API boundary is cleaner, but you hand-write DOM rendering for three
tables — number formatting, sorting, empty states. That is precisely the code Jinja gives
away, and it is where "least code" starts losing. Reasonable if you later want the frontend
to own all rendering.

**Why not C:** best ceiling if this grows into a real product, and TanStack Table gives
sorting/filtering free — but it is a second toolchain (node on the VPS or a committed
`dist/`) for a single private user looking at three pages. Roughly 3× the code for no
benefit at this scale.

**One risk in A, and its mitigation:** HTMX swapping a container that holds a live chart
requires re-initialising the chart on `htmx:afterSwap`, which is a classic source of leaked
chart instances. **Avoid it entirely** — make `/chart` a normal full page load driven by
`?symbol=`, and use HTMX only for the search-suggestions dropdown. This removes the failure
mode and cuts JS further.

## Workstream 1 — `turtle-backtest` changes (precondition)

Small and additive. Four changes, no touch to `Signal` or any strategy.

### 1.1 New table

`Signal` (`turtlex/model.py:8-20`) carries exactly three fields — `ticker`, `date`, `ranking`.
**Persist only those, plus the strategy name.** Everything display-related (entry date/price,
current price, change %, %above SMA50, ADR%) is derived in SQL on the read side.

Rationale: widening `Signal` means touching every strategy that constructs it and risking
`tests/research/test_qullamaggie_parity.py`, to persist values that are presentation
concerns. The escape hatch is clean — the migration below is additive, so if the derived SQL
drifts or gets slow, add columns later and the view collapses to a plain SELECT.

> ⚠️ **Flag for implementation:** SMA50/ADR% recomputed in SQL from `daily_bars` may differ
> slightly from what `QullamaggieStrategy` computed internally (adjusted vs raw close,
> warmup handling). Match the strategy's choice of price column when writing the view, and
> if exact agreement turns out to matter, widen the table instead.

New alembic migration in `db/migrations/versions/`, raw SQL via `op.execute` per house style:

```sql
CREATE TABLE turtle.signal (
    strategy     TEXT     NOT NULL,
    symbol       TEXT     NOT NULL,
    signal_date  DATE     NOT NULL,
    ranking      SMALLINT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    modified_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_signal PRIMARY KEY (strategy, symbol, signal_date)
);
CREATE INDEX ix_signal_date ON turtle.signal (signal_date DESC);
```

`strategy` holds the algorithm identifier, e.g. `bk50d_s12_v2.0`, so the s16/s20 comparison
variants can coexist with the live config. Add the matching `Table` to
`turtlex/repository/tables.py`.

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
the DEPLOY/PREREQUISITES/STATUS/REMOVE header comments. Schedule **05:30 Europe/Tallinn,
Mon–Sat** — after the 05:00 EODHD download lands.

systemd cannot compute dates, so wrap the date arithmetic in a two-line
`deploy/signal-persist.sh` that resolves yesterday and calls:

```bash
uv run signal-runner \
    --trading-strategy qullamaggie --ranking-strategy qullamaggie \
    --start-date "$DAY" --end-date "$DAY" --persist
```

**Cost:** `SignalService.scan` issues one `get_bars_pl` query per universe ticker
(~2,100 tickers × 730-day warmup). That is fine as a nightly batch, and a 3-month backfill
is the *same single pass* with a wider date range — not 90× the work.

**Backfill:** one manual run seeds the three months the site needs:

```bash
uv run signal-runner --trading-strategy qullamaggie --ranking-strategy qullamaggie \
    --start-date 2026-05-12 --end-date 2026-08-11 --persist
```

### 1.5 Read-only DB role

Add a `web_ro` role mirroring the `claude` role (`db/init.sh:40-47`) — `CONNECT`, `USAGE ON
SCHEMA turtle`, `SELECT ON ALL TABLES`, plus `ALTER DEFAULT PRIVILEGES FOR ROLE alembic` so
new tables inherit it. Extend `db/init.sh` for fresh installs and run the equivalent `psql`
once on the VPS for the existing one.

## Workstream 2 — the `turtle-web` repo

### Layout

```text
turtle-web/
├── pyproject.toml                # uv + hatchling; ruff line-length 140; mypy disallow_untyped_defs
├── config/settings.toml          # [database.local] / [database.hetzner] / [database.pool]
├── .env.example                  # DB_ENV, DB_WEB_PASSWORD  (no EODHD_API_KEY)
├── deploy/turtle-web.service
├── turtleweb/
│   ├── config.py                 # mirrors Settings.from_toml() minus the EODHD requirement
│   ├── db.py                     # sync Engine factory
│   ├── queries.py                # every SQL string, one place
│   ├── catalog.py                # symbol catalog, cached in-process
│   ├── main.py                   # FastAPI app + routes
│   ├── templates/{base,signals,portfolio,chart}.html
│   └── static/
│       ├── vendor/lightweight-charts.standalone.production.js
│       ├── vendor/pico.min.css
│       └── chart.js
└── tests/{test_queries.py,test_routes.py}
```

`config.py` deliberately does **not** reuse `Settings.from_toml()`: it hard-requires
`EODHD_API_KEY` (`turtlex/config/settings.py:37-43`) and hands out an `app_user` read-write
engine. Copy the TOML+`DB_ENV` pattern, require only `DB_WEB_PASSWORD`.

### Routes

| Route | Returns | Notes |
| --- | --- | --- |
| `GET /` | 302 → `/signals` | |
| `GET /signals` | HTML | `?days=90&min_ranking=44` |
| `GET /portfolio` | HTML | positions + totals + equity-curve container |
| `GET /chart?symbol=` | HTML | full page load, no HTMX swap |
| `GET /api/bars` | JSON | OHLCV + volume + SMA50 for one symbol |
| `GET /api/markers` | JSON | signal/entry markers for one symbol |
| `GET /api/equity` | JSON | market value vs cost basis series |
| `GET /api/symbols?q=` | JSON | autocomplete, served from the in-process catalog |
| `GET /healthz` | JSON | |

FastAPI's automatic `/docs` gives a free way to eyeball the JSON the chart consumes.

### Dependencies

`fastapi`, `uvicorn[standard]`, `jinja2`, `psycopg[binary]`, `sqlalchemy`. Vendored assets:
`lightweight-charts.standalone.production.js` (~50 KB) and `pico.min.css` (classless — the
entire stylesheet is one `<link>`, zero CSS written).

## The SQL

All verified with `EXPLAIN ANALYZE` against the live Hetzner database.

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

`Execution Time: 142.298 ms`, 5,627 rows — **10× faster**. Load once into a module-level list
in `catalog.py` and filter in Python. Autocomplete then costs zero queries. Filtering
`turtle.ticker` directly is a 69 ms seq scan *and* returns 53,717 rows including symbols with
no bars — worse on both counts.

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
       SUM(p.shares * b.close) AS market_value,
       SUM(p.cost)             AS cost_basis
FROM pos p
JOIN turtle.daily_bars b ON b.symbol = p.ticker_code AND b.date = p.date
WHERE p.shares > 0
GROUP BY p.date ORDER BY p.date;
```

> ⚠️ **This is not a true equity curve, and the page must say so.** The Lightyear importer
> keeps only Buy/Sell rows in USD (`turtlex/service/lightyear_service.py:161-267`) — deposits,
> withdrawals, dividends and FX are never imported, so cash is unknowable. What is plotted is
> **holdings market value vs cumulative cost basis**. Label it that way rather than "equity".

### Signals, last 3 months

Reads the new table and derives display columns. `entry_price` is the split/dividend-adjusted
open of the next trading day, matching the baseline algorithm definition:

```sql
SELECT s.symbol, s.signal_date, s.ranking, e.entry_date, e.entry_price,
       l.curr_price, (l.curr_price / e.entry_price - 1) * 100 AS change_pct
FROM turtle.signal s
LEFT JOIN LATERAL (
    SELECT b.date AS entry_date, b.open * b.adjusted_close / b.close AS entry_price
    FROM turtle.daily_bars b
    WHERE b.symbol = s.symbol AND b.date > s.signal_date
    ORDER BY b.date LIMIT 1
) e ON TRUE
LEFT JOIN LATERAL (
    SELECT b.close AS curr_price FROM turtle.daily_bars b
    WHERE b.symbol = s.symbol ORDER BY b.date DESC LIMIT 1
) l ON TRUE
WHERE s.strategy = :strategy
  AND s.signal_date >= CURRENT_DATE - INTERVAL '90 days'
  AND s.ranking >= :min_ranking
ORDER BY s.signal_date DESC, s.ranking DESC;
```

Both laterals are PK index scans. Expected volume is **~30–90 signals per 3 months** for the
baseline `bk50d_s12_v2.0` at `R >= 44` (11.4 gated signals/month per
`docs/research/result-qullamaggie-backtest-v4.md`), so the page never paginates.

## The chart code

This is the whole of `chart.js`, using the confirmed v5.2 API:

```js
const chart = LightweightCharts.createChart(el, { autoSize: true });
const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {});
const volume  = chart.addSeries(LightweightCharts.HistogramSeries,
                                { priceFormat: { type: 'volume' } });
volume.moveToPane(1);                       // volume in its own pane
const sma = chart.addSeries(LightweightCharts.LineSeries, { lineWidth: 1 });

const d = await (await fetch(`/api/bars?symbol=${symbol}`)).json();
candles.setData(d.bars);                    // [{time:'2026-08-09',open,high,low,close}]
volume.setData(d.volume);
sma.setData(d.sma50);

const m = await (await fetch(`/api/markers?symbol=${symbol}`)).json();
LightweightCharts.createSeriesMarkers(candles, m);   // entry arrows on signal dates
chart.timeScale().fitContent();
```

The equity curve is the same library — one `AreaSeries` for market value plus one
`LineSeries` for cost basis.

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

**Bind to the Tailscale IP, never `0.0.0.0`.** The Hetzner firewall currently allows inbound
SSH from one IP and blocks everything else (`docs/implementation.md`), so port 8080 is
unreachable from the public internet — but binding explicitly means a firewall change can
never accidentally expose it. Requires `loginctl enable-linger`, same as the existing timers.

## Verification

### Workstream 1 checks

1. `uv run alembic upgrade head` → `\d turtle.signal` shows the table and `ix_signal_date`.
2. `uv run pytest && uv run mypy` clean.
3. Backfill run above → `SELECT count(*), min(signal_date), max(signal_date) FROM turtle.signal;`
   returns roughly 30–90 rows spanning ~90 days.
4. Re-run the same command → count unchanged (proves the upsert is idempotent).
5. `systemctl --user list-timers signal-persist.timer` shows the next 05:30 firing.

### Workstream 2 checks

1. `psql -U web_ro` → `SELECT 1 FROM turtle.signal LIMIT 1` succeeds; `INSERT` is **denied**.
2. `curl localhost:8080/healthz` → 200.
3. `/signals` renders rows matching the SQL run directly in psql.
4. `/portfolio` totals match `market_value 10678.97 / cost_basis 9598.61` for 2026-08-09
   (numbers move with fresh bars; the check is that page and SQL agree).
5. `/chart?symbol=AAPL.US` draws candles + volume pane + SMA50, with entry markers on the
   signal dates.
6. `/api/symbols?q=app` returns AAPL.US among its hits in <10 ms (catalog is cached).
7. From a second Tailscale device: the site loads. From the public IP: connection refused.

## Open items for implementation

1. Match the SQL-derived SMA50/ADR% to the strategy's price column (adjusted vs raw) — see
   the flag in §1.1.
2. Confirm which strategy identifier string to persist (`bk50d_s12_v2.0` is the baseline).
3. Pick the Tailscale IP/hostname for the bind address.
