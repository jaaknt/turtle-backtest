#!/usr/bin/env python3
"""
Ranking-hypothesis lab: cache the signal universe once, then judge candidate rankings cheaply.

`QullamaggieRanking` orders 366d outcomes non-monotonically where it matters most — 5/9
non-decreasing decile steps out of sample and at s20, against 8/9 in-sample at s12. Fixing that
needs many small hypotheses tested under one protocol, which is only affordable if each test is
seconds rather than minutes. This script is that affordance:

  --build-cache   loads 2010-2026 bars in chunks, raises signals for s12/s16/s20, attaches each
                  one's 366d forward return, and writes the lot to .cache/ranking-lab/ (once)
  --eval SPEC     scores one candidate spec against the fixed walk-forward protocol and the
                  portfolio replay, prints the scorecard and appends a ledger row
  --screen FEAT   checks whether a candidate feature's effect keeps its sign across sub-periods
                  and folds, the gate a Stage-B feature must pass before it may enter a spec

The protocol, the acceptance rule and the loop that drives this are in
docs/specs/qullamaggie-ranking-loop.md. The machinery — transforms, PAVA isotonic, Spearman,
decile tables, folds — is in turtlex/research/ranking_lab.py, so it is unit-testable and
mypy-checked; this file is argument parsing, data loading and reporting.

Three traps this measures around, inherited from scripts/qullamaggie-ranking-weights.py because
they produce false positives in exactly the same way here:

1. A score threshold is not a fixed filter. A fixed gate keeps a different fraction of signals
   under each scheme, so comparing two schemes at one gate compares selectivity, not skill.
   Everything below is compared at matched keep-%.
2. Taking fewer positions changes returns on its own, so every portfolio cell is reported
   against random subsets of the same size — a candidate demonstrates skill only by beating
   its own null.
3. Coarse tables leave hundreds of signals tied, and cutting top-K inside a tie group by date
   silently selects the earliest. Ties are broken at random and redrawn.

Data source: the cache needs bars back to 2010, and the local Docker Postgres is a five-year
mirror (scripts/update-local-db.sh), so --build-cache must run against the VPS via the
`hetzner-db` profile. Built from the local mirror instead, the early folds are simply empty and
the full-period reference table will not match the committed cohort studies -- which is exactly
what that table is there to reveal.

Memory: --build-cache loads the qualified universe in 3-year chunks precisely so it does not
scale with the 16-year window. Run it under the standard cap anyway (CLAUDE.md):

    ACTIVE_PROFILE=hetzner-db DB_APP_PASSWORD="$DB_CLAUDE_PASSWORD" \
      systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 \
      uv run scripts/qullamaggie-ranking-lab.py --build-cache

--eval and --screen read the parquet cache and need no database at all, so they run unqualified
on any machine once the cache exists.
"""

import argparse
import re
import statistics
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.research import ranking_lab as rl
from turtlex.research.portfolio_replay import Market, run_sim, top_k

_EPOCH = date(1970, 1, 1)

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = rl.CACHE_DIR
CANDIDATE_DIR = REPO_ROOT / "docs" / "research" / "ranking-lab" / "candidates"
LEDGER_PATH = REPO_ROOT / "docs" / "research" / "result-qullamaggie-ranking-lab.md"
LEDGER_START = "<!-- lab:ledger:start -->"
LEDGER_END = "<!-- lab:ledger:end -->"

CHUNK_YEARS = 3
# Each chunk's bars run this far past its last signal date so every signal in the chunk has a
# bar at entry + 366 to exit against. 400 > HOLD_CAL with room for the next trading day.
FORWARD_PAD_DAYS = 400

# Portfolio confirmation. The calendar stops at the holdout boundary so the loop can never
# read the frozen slice, and the sub-period split is that window's midpoint — the same
# "an edge that exists in one half only is not an edge" check qullamaggie-ranking-weights.py
# makes, re-centred on this window rather than on that script's 2021-2026 one.
PORTFOLIO_CONFIG = "s12"  # the live reference algorithm (CLAUDE.md)
PORTFOLIO_START = rl.EVAL_START
PORTFOLIO_END = rl.HOLDOUT_START - timedelta(days=1)
PORTFOLIO_SPLIT = date(2020, 1, 1)
# The one-time holdout run stops here; positions short of their 366-day exit are marked to
# market on the last bar at or before it.
HOLDOUT_END = date(2026, 8, 19)
HOLD_LABEL = rl.HOLD_CAL
KEEP_PCTS = [35, 25, 15]
CONFIRM_KEEP_PCT = 25  # the cell the acceptance rule reads
N_TIE = 10  # tie-break redraws per cell
N_NULL = 30  # random subsets per cell
MIN_NULL_BEATS = 27
MAX_CAGR_GIVEBACK = 1.0  # percentage points a candidate may trail the baseline by
SEED = 20260820
HOLDOUT_GATES = [0, 40, 44, 47, 49, 55, 59, 68]


# ── Cache build ──────────────────────────────────────────────────────────────────────────


def _chunks() -> list[tuple[date, date]]:
    """Signal windows the cache is built in, each loaded with its own warmup and forward pad."""
    out: list[tuple[date, date]] = []
    start = rl.CACHE_START
    while start <= rl.CACHE_END:
        end = min(date(start.year + CHUNK_YEARS, 1, 1) - timedelta(days=1), rl.CACHE_END)
        out.append((start, end))
        start = end + timedelta(days=1)
    return out


def _load_spy_closes(repo: DailyBarsQueryRepository, start: date, end: date) -> pl.DataFrame:
    """Adjusted SPY closes over the window, for the relative-strength features."""
    fetch_start = start - timedelta(days=qm.WARMUP_DAYS)
    spy = repo.get_bars_pl(qm.MARKET_TICKER, fetch_start, end)
    if spy.is_empty():
        raise ValueError(f"No {qm.MARKET_TICKER} bars for {fetch_start}..{end}; relative strength would be null everywhere")
    return spy.sort("date").select("date", pl.col("adjusted_close").alias("adj_close"))


def _forward_returns(signals: pl.DataFrame, bars: pl.DataFrame) -> pl.DataFrame:
    """Attach each signal's fixed 366-calendar-day return, entered at its adjusted open.

    Mirrors `run_trades` in scripts/qullamaggie-cohorts-ranking.py exactly — entry at
    `entry_price` (the next day's adjusted open), exit at the adjusted close of the first bar
    at or after entry + 366 calendar days — so the lab's decile tables are comparable with the
    committed cohort results rather than being a second, subtly different convention.

    Signals whose symbol has no bar that far forward are dropped, as they are there.

    Args:
        signals: Signal frame from `qm.resolve_entries`
        bars: Adjusted bars covering the signal window and its forward pad

    Returns:
        The signals with a `ret` column, unfillable ones removed.
    """
    if signals.is_empty():
        return signals.with_columns(pl.Series("ret", [], dtype=pl.Float64))

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in bars.group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[str(sym)] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_closes[str(sym)] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    keep: list[bool] = []
    rets: list[float] = []
    for sym, entry_date, entry_px in zip(
        signals["symbol"].to_list(), signals["entry_date"].to_list(), signals["entry_price"].to_list(), strict=True
    ):
        dates, closes = sym_dates.get(str(sym)), sym_closes.get(str(sym))
        entry_int = (entry_date - _EPOCH).days
        if dates is None or closes is None or dates[-1] < entry_int + rl.HOLD_CAL:
            keep.append(False)
            rets.append(float("nan"))
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + rl.HOLD_CAL))
        if idx_exit >= len(dates):
            keep.append(False)
            rets.append(float("nan"))
            continue
        keep.append(True)
        rets.append(float((closes[idx_exit] - float(entry_px)) / float(entry_px)))
    return signals.with_columns(pl.Series("ret", rets)).filter(pl.Series(keep))


def build_cache() -> None:
    """Rebuild .cache/ranking-lab/ from the database.

    Chunked on purpose. One 2010-2026 load of the qualified universe is roughly 1.4x the widest
    committed study, which peaks at ~3.5 GB — over the 4 GB cap that keeps an OOM from taking
    the whole WSL distro down. Three-year chunks hold the peak near a third of that, and cost
    only the 730-day warmup being re-read per chunk.

    Chunk boundaries are safe for the 30-day cooldown because `qm.get_signals` runs its cooldown
    chain over the warmup rows too, so a trigger just before a chunk starts still suppresses an
    early in-chunk signal. The s12 signal count is checked against the committed cohort study
    afterwards, which is what would catch a boundary effect if one crept in.
    """
    settings = Settings.from_toml()
    repo = DailyBarsQueryRepository(engine=settings.engine)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    per_config: dict[str, list[pl.DataFrame]] = {name: [] for name, _ in rl.CONFIGS}
    price_parts: list[pl.DataFrame] = []
    calendar: set[date] = set()

    for chunk_start, chunk_end in _chunks():
        load_end = min(chunk_end + timedelta(days=FORWARD_PAD_DAYS), rl.CACHE_END)
        print(f"Chunk {chunk_start} – {chunk_end} (bars to {load_end}) …", flush=True)

        bars = qm.load_bars(repo, chunk_start, load_end)
        if bars.is_empty():
            raise ValueError(
                f"No bars for {chunk_start}..{load_end}, so the cache would silently be missing that period "
                "and every fold trained on it would be skipped. Is ACTIVE_PROFILE=hetzner-db set? "
                "The local Docker mirror only holds ~5 years."
            )
        spy = _load_spy_closes(repo, chunk_start, load_end)
        bull = qm.load_spy_regime(repo, chunk_start, load_end)
        ind = rl.add_lab_features(qm.add_indicators(bars), spy)

        chunk_symbols: set[str] = set()
        for name, thresh in rl.CONFIGS:
            sig = qm.resolve_entries(qm.get_signals(ind, bull, chunk_start, sma_thresh=thresh), bars)
            sig = sig.filter((pl.col("date") >= chunk_start) & (pl.col("date") <= chunk_end))
            sig = _forward_returns(sig, bars)
            print(f"  {name}: {len(sig)} signals with a 366d exit", flush=True)
            if not sig.is_empty():
                per_config[name].append(sig)
                chunk_symbols.update(str(s) for s in sig["symbol"].to_list())

        calendar.update(d for d in bars["date"].to_list() if rl.EVAL_START <= d <= rl.EVAL_END)
        if chunk_symbols:
            price_parts.append(
                bars.filter(pl.col("symbol").is_in(sorted(chunk_symbols)) & (pl.col("date") >= chunk_start)).select(
                    "symbol", "date", "adj_close"
                )
            )
        del bars, ind, spy

    for name in per_config:
        frames = per_config[name]
        if not frames:
            raise ValueError(f"No signals cached for {name}; the cache would be unusable")
        # Realized returns carry the level of the market they were earned in. Subtracting each
        # entry year's mean leaves only the cross-sectional separation, which is the thing a
        # ranking is supposed to supply — the same demeaning the 2026-07-29 weight scan used.
        sig = pl.concat(frames, how="vertical_relaxed").sort(["date", "symbol"])
        sig = sig.with_columns((pl.col("ret") - pl.col("ret").mean().over(pl.col("entry_date").dt.year())).alias("ret_demeaned"))
        sig.write_parquet(CACHE_DIR / f"signals-{name}.parquet")
        print(f"{name}: {len(sig)} signals cached", flush=True)

    prices = pl.concat(price_parts, how="vertical_relaxed").unique(subset=["symbol", "date"]).sort(["symbol", "date"])
    prices.write_parquet(CACHE_DIR / "prices.parquet")
    pl.DataFrame({"date": sorted(calendar)}).write_parquet(CACHE_DIR / "calendar.parquet")
    print(f"prices: {len(prices)} rows, calendar: {len(calendar)} days -> {CACHE_DIR}", flush=True)


# ── Portfolio confirmation ───────────────────────────────────────────────────────────────


def _replay_rows(sig: pl.DataFrame, scores: np.ndarray, cal_set: set[int], *, allow_holdout: bool = False) -> list[dict]:
    """Signal rows the replay can trade, carrying their candidate score.

    Entries on or after the holdout boundary are dropped here rather than filtered upstream,
    so there is exactly one place the frozen slice can leak into a loop iteration. Opening it
    takes an explicit `allow_holdout=True`, which only `cmd_holdout` passes.

    Args:
        sig: Signal frame, in the same row order as `scores`
        scores: Candidate score per signal
        cal_set: Trading days, as days since the epoch, the replay will visit
        allow_holdout: Include entries on or after `HOLDOUT_START`. Only for the one-time
            holdout run; never for a loop iteration.
    """
    rows: list[dict] = []
    holdout_int = (rl.HOLDOUT_START - _EPOCH).days
    for i, r in enumerate(sig.iter_rows(named=True)):
        entry_dint = (r["entry_date"] - _EPOCH).days
        if entry_dint not in cal_set or (not allow_holdout and entry_dint >= holdout_int):
            continue
        rows.append({"symbol": r["symbol"], "entry_dint": entry_dint, "entry_px": float(r["entry_price"]), "score": float(scores[i])})
    return rows


def portfolio_confirm(sig: pl.DataFrame, scores: np.ndarray, market: Market, calendar: list[date], rng: np.random.Generator) -> dict:
    """Replay the candidate's ordering at matched selectivity against a same-size random null.

    Args:
        sig: Signal frame for `PORTFOLIO_CONFIG`
        scores: Candidate score per signal, in the frame's row order
        market: Price arrays for the replay
        calendar: Trading days inside the non-holdout window
        rng: Source of tie-break jitter and null subsets

    Returns:
        Per-keep-% cells with cagr, sortino, max_dd, the null mean and how often the candidate
        beat it, plus each cell's two sub-period CAGRs.
    """
    rows = _replay_rows(sig, scores, {(d - _EPOCH).days for d in calendar})
    halves = [d for d in calendar if d < PORTFOLIO_SPLIT], [d for d in calendar if d >= PORTFOLIO_SPLIT]
    cells: dict[int, dict] = {}
    for pct in KEEP_PCTS:
        n_keep = max(10, round(len(rows) * pct / 100))
        res = [run_sim(market, calendar, top_k(rows, "score", n_keep, rng), "score") for _ in range(N_TIE)]
        null = [
            run_sim(market, calendar, [rows[i] for i in rng.choice(len(rows), size=n_keep, replace=False)], "score")["cagr"]
            for _ in range(N_NULL)
        ]
        cagrs = [r["cagr"] for r in res]
        # A half the cache does not cover scores nan, never a number. cmd_eval turns that into
        # a rejection: an unconfirmable sub-period is not a passed sub-period.
        sub = [
            statistics.fmean([run_sim(market, half, top_k(rows, "score", n_keep, rng), "score")["cagr"] for _ in range(max(2, N_TIE // 2))])
            if half
            else float("nan")
            for half in halves
        ]
        cells[pct] = {
            "cagr": statistics.fmean(cagrs),
            "cagr_sd": statistics.stdev(cagrs) if len(cagrs) > 1 else 0.0,
            "sortino": statistics.fmean([r["sortino"] for r in res]),
            "max_dd": statistics.fmean([r["max_dd"] for r in res]),
            "taken": statistics.fmean([r["taken"] for r in res]),
            "null_cagr": statistics.fmean(null),
            "beats": sum(1 for c in null if statistics.fmean(cagrs) > c),
            "sub": sub,
        }
    return cells


# ── Reporting ────────────────────────────────────────────────────────────────────────────


def _mean_or_nan(values: list[float]) -> float:
    """Mean of the finite values, or nan when there are none.

    A thin fold leaves every decile below `MIN_LOSERS`, so a whole config can report nothing
    at all — which is information, not a crash. It shows up as an em dash in the table.
    """
    finite = [v for v in values if not np.isnan(v)]
    return statistics.fmean(finite) if finite else float("nan")


def _fmt(value: float, width: int, places: int, sign: str = "") -> str:
    """Right-aligned fixed-point cell, rendering nan as an em dash."""
    return f"{'—':>{width}}" if np.isnan(value) else f"{value:>{sign}{width}.{places}f}"


def print_scorecard(card: rl.Scorecard, label: str) -> None:
    """Print one candidate's per-config fold aggregates and its overall numbers."""
    print(f"\n### {label} — {card.spec_id}")
    hdr = f"{'config':<8} {'folds':>6} {'mono_sortino':>13} {'mono_mean':>10} {'spearman':>10} {'spread':>8} {'topD_sortino':>13}"
    print(hdr)
    print("-" * len(hdr))
    for config, _ in rl.CONFIGS:
        cf = [f for f in card.folds if f.config == config]
        if not cf:
            print(f"{config:<8} {0:>6} {'—':>13} {'—':>10} {'—':>10} {'—':>8} {'—':>13}")
            continue
        agg = card.by_config(config)
        mono_mean = _mean_or_nan([f.mono_mean for f in cf])
        top = _mean_or_nan([f.top_decile_sortino for f in cf])
        print(
            f"{config:<8} {len(cf):>6} {_fmt(agg['mono_sortino'], 13, 3)} {_fmt(mono_mean, 10, 3)} "
            f"{_fmt(agg['spearman'], 10, 4, '+')} {_fmt(agg['spread'], 8, 3)} {_fmt(top, 13, 3)}"
        )
    print("-" * len(hdr))
    print(
        f"{'ALL':<8} {len(card.folds):>6} {_fmt(card.mono_sortino, 13, 3)} {'':>10} "
        f"{_fmt(card.spearman, 10, 4, '+')} {_fmt(card.spread, 8, 3)}"
    )


def print_portfolio(cells: dict[int, dict], label: str) -> None:
    """Print the matched-selectivity replay table for one candidate."""
    print(f"\n### Portfolio ({PORTFOLIO_CONFIG}, {PORTFOLIO_START}..{PORTFOLIO_END}) — {label}")
    hdr = (
        f"{'keep':>5} {'CAGR%':>8} {'sd':>5} {'MaxDD%':>8} {'Sortino':>8} {'taken':>6} | "
        f"{'null CAGR%':>11} {'beats':>7} | {'pre-split':>10} {'post-split':>11}"
    )
    print(hdr)
    print("-" * len(hdr))
    for pct, c in cells.items():
        print(
            f"{pct:>4}% {c['cagr']:>+8.2f} {c['cagr_sd']:>5.2f} {c['max_dd']:>8.2f} {c['sortino']:>8.3f} {c['taken']:>6.0f} | "
            f"{c['null_cagr']:>+11.2f} {c['beats']:>4}/{N_NULL} | {_fmt(c['sub'][0], 10, 2, '+')} {_fmt(c['sub'][1], 11, 2, '+')}"
        )


def _full_period_reference(spec: rl.CandidateSpec, signals: dict[str, pl.DataFrame]) -> None:
    """Print full-period population deciles, the calibration check against the committed docs.

    The fold tables above are held-out slices and have no committed counterpart to check
    against. This one does: run `c000-production` and the s12/s16/s20 monotonicity here should
    land on `result-qullamaggie-cohorts-ranking.md`'s population-decile tables. If it does not,
    the judge itself is miscalibrated and no hypothesis result from it means anything.
    """
    print("\n### Full-period population deciles (reference — compare with result-qullamaggie-cohorts-ranking.md)")
    hdr = f"{'config':<8} {'N':>6} {'mono_sortino':>13} {'mono_mean':>10} {'D1 sortino':>11} {'D10 sortino':>12}"
    print(hdr)
    print("-" * len(hdr))
    for config, _ in rl.CONFIGS:
        sig = signals[config].sort(["date", "symbol"])
        sig = sig.filter((pl.col("date") >= rl.EVAL_START) & (pl.col("entry_date") < rl.HOLDOUT_START))
        scores = rl.raw_scores(sig, spec)
        ret = sig["ret"].to_numpy(allow_copy=True).astype(float)
        rng = np.random.default_rng(rl.DECILE_SEED)
        draws = [rl.compute_deciles(scores, ret, rng) for _ in range(rl.N_TIE_DRAWS)]
        if any(len(dec) != rl.N_DECILES for dec in draws):
            raise ValueError(f"{config}: a full-period draw did not resolve {rl.N_DECILES} deciles; D1/D10 would be mislabelled")
        # Print the denominator actually measured. monotone_steps returns (steps, comparable)
        # precisely so a thin decile cannot be reported as "4.0/9" when only five steps could be
        # judged — and this is the table that decides whether the judge itself is calibrated.
        s_pairs = [rl.monotone_steps([d["sortino"] for d in dec]) for dec in draws]
        m_pairs = [rl.monotone_steps([d["mean"] for d in dec]) for dec in draws]
        ms, msn = statistics.fmean([p[0] for p in s_pairs]), statistics.fmean([p[1] for p in s_pairs])
        mm, mmn = statistics.fmean([p[0] for p in m_pairs]), statistics.fmean([p[1] for p in m_pairs])
        d1 = statistics.fmean([dec[0]["sortino"] for dec in draws])
        d10 = statistics.fmean([dec[-1]["sortino"] for dec in draws])
        print(f"{config:<8} {len(sig):>6} {f'{ms:.1f}/{msn:.0f}':>13} {f'{mm:.1f}/{mmn:.0f}':>10} {d1:>11.3f} {d10:>12.3f}")


# ── Ledger ───────────────────────────────────────────────────────────────────────────────


def _first_sentence(text: str) -> str:
    """First sentence of a hypothesis, for the ledger's summary column.

    Splits on a period followed by whitespace, never on a bare period: `split(".")[0]` cut three
    committed rows mid-decimal ("rho -0.", "all 100 points on SMA50 distance and none on ADR or
    price (train rho +0.").

    Args:
        text: The candidate's full hypothesis
    """
    return re.split(r"(?<=\.)\s", text.strip(), maxsplit=1)[0]


def ledger_rows() -> list[str]:
    """Existing ledger rows, or an empty list when the ledger has not been created yet."""
    if not LEDGER_PATH.exists():
        return []
    text = LEDGER_PATH.read_text(encoding="utf-8")
    if LEDGER_START not in text or LEDGER_END not in text:
        raise ValueError(f"{LEDGER_PATH.name} is missing its {LEDGER_START} / {LEDGER_END} markers; refusing to guess where rows go")
    body = text.split(LEDGER_START, 1)[1].split(LEDGER_END, 1)[0]
    return [ln for ln in body.splitlines() if ln.strip().startswith("|") and not ln.strip().startswith("| ---")][1:]


def append_ledger(row: str) -> None:
    """Insert one row immediately before the ledger's end marker.

    Only ever inserts. Everything outside the markers — the current baseline, the hand-written
    reading of what the loop has found — is left untouched, so re-running this can never
    destroy analysis the way a whole-file rewrite would.
    """
    text = LEDGER_PATH.read_text(encoding="utf-8")
    # Validate before writing. The verdict has already been printed by the time this runs, so a
    # malformed ledger would otherwise announce a result and then lose the row that records it --
    # leaving `n_tested` frozen and under-charging the margin for every later candidate.
    for marker in (LEDGER_START, LEDGER_END):
        if text.count(marker) != 1:
            raise ValueError(f"{LEDGER_PATH.name}: expected exactly one {marker}, found {text.count(marker)}")
    if text.index(LEDGER_START) > text.index(LEDGER_END):
        raise ValueError(f"{LEDGER_PATH.name}: {LEDGER_START} appears after {LEDGER_END}")
    head, tail = text.split(LEDGER_END, 1)
    LEDGER_PATH.write_text(f"{head.rstrip()}\n{row}\n{LEDGER_END}{tail}", encoding="utf-8")


# ── Commands ─────────────────────────────────────────────────────────────────────────────


def cmd_eval(spec_path: Path, baseline_path: Path, skip_portfolio: bool) -> None:
    """Judge one candidate against the baseline and record the verdict.

    Args:
        spec_path: Candidate spec to evaluate
        baseline_path: Spec of the reigning baseline, scored under the same protocol
        skip_portfolio: Skip the replay; the verdict is then monotonicity-only and is
            recorded as such rather than being reported as an acceptance
    """
    spec, baseline_spec = rl.load_spec(spec_path), rl.load_spec(baseline_path)
    signals, prices, calendar = rl.load_cache()

    card = rl.evaluate(spec, signals)
    base_card = rl.evaluate(baseline_spec, signals)
    if not card.folds:
        raise ValueError(f"{spec.id} produced no comparable folds; check its feature names against the cache")

    n_tested = len(ledger_rows())
    verdict = rl.judge(card, base_card, n_tested)

    print(f"# Ranking lab — {spec.id}\n\nRun date: {run_timestamp()}\n\n{spec.hypothesis}")
    print(
        f"\nBaseline: {baseline_spec.id} | hypotheses already recorded: {n_tested} | "
        f"required rho margin: {rl.required_margin(n_tested):.4f}"
    )
    print_scorecard(base_card, "Baseline")
    print_scorecard(card, "Candidate")
    _full_period_reference(spec, signals)

    cells: dict[int, dict] = {}
    base_cells: dict[int, dict] = {}
    extra: list[str] = []
    if verdict.accepted and not skip_portfolio:
        rng = np.random.default_rng(SEED)
        cal = [d for d in calendar if PORTFOLIO_START <= d <= PORTFOLIO_END]
        market = Market(prices.filter((pl.col("date") >= PORTFOLIO_START) & (pl.col("date") <= PORTFOLIO_END)))
        sig = signals[PORTFOLIO_CONFIG].sort(["date", "symbol"])
        base_cells = portfolio_confirm(sig, rl.raw_scores(sig, baseline_spec), market, cal, np.random.default_rng(SEED))
        cells = portfolio_confirm(sig, rl.raw_scores(sig, spec), market, cal, rng)
        print_portfolio(base_cells, f"baseline {baseline_spec.id}")
        print_portfolio(cells, f"candidate {spec.id}")

        cell, base_cell = cells[CONFIRM_KEEP_PCT], base_cells[CONFIRM_KEEP_PCT]
        if cell["cagr"] < base_cell["cagr"] - MAX_CAGR_GIVEBACK:
            extra.append(f"portfolio CAGR {cell['cagr']:+.2f} more than {MAX_CAGR_GIVEBACK}pp below baseline {base_cell['cagr']:+.2f}")
        if cell["beats"] < MIN_NULL_BEATS:
            extra.append(f"portfolio beats null only {cell['beats']}/{N_NULL}, needs {MIN_NULL_BEATS}")
        for i, half in enumerate(("pre-split", "post-split")):
            if np.isnan(cell["sub"][i]) or np.isnan(base_cell["sub"][i]):
                extra.append(f"{half} has no trading days in the cache, so the sub-period check cannot confirm this candidate")
            elif cell["sub"][i] < base_cell["sub"][i] - MAX_CAGR_GIVEBACK:
                extra.append(f"{half} CAGR {cell['sub'][i]:+.2f} below baseline {base_cell['sub'][i]:+.2f}")
    elif verdict.accepted and skip_portfolio:
        extra.append("portfolio confirmation skipped (--no-portfolio); monotonicity gates passed")

    # Rebuilt rather than mutated: Verdict is frozen and derives `accepted` from `reasons`, so
    # there is no second copy of the answer to fall out of step with the reasons.
    verdict = rl.Verdict(verdict.reasons + tuple(extra))
    print(f"\n## Verdict: {'ACCEPT' if verdict.accepted else 'REJECT'}")
    for r in verdict.reasons:
        print(f"  - {r}")
    if verdict.accepted:
        print(f"  {spec.id} becomes the new baseline. Update the Current baseline line in {LEDGER_PATH.name}.")

    accepted = verdict.accepted
    reason = "all gates passed" if accepted else "; ".join(verdict.reasons)
    cagr = f"{cells[CONFIRM_KEEP_PCT]['cagr']:+.2f}" if cells else "—"
    append_ledger(
        f"| {len(ledger_rows()) + 1} | `{spec.id}` | {_first_sentence(spec.hypothesis)} | "
        f"{card.mono_sortino:.3f} | {card.spearman:+.4f} | {card.spread:.3f} | {cagr} | "
        f"**{'ACCEPT' if accepted else 'REJECT'}** | {reason} |"
    )
    print(f"\nLedger row appended to {LEDGER_PATH}")


def cmd_screen(feature: str) -> None:
    """Report whether a candidate feature's effect keeps its sign across sub-periods and folds.

    A feature that flips sign between halves is a time effect wearing a cross-sectional
    disguise: it describes when the good trades happened, not which ones they were. This is the
    standard that dropped ADR compression, 12-month ROC and RSI(14) on 2026-07-29 — applied to
    every new feature before it may enter a spec, and to the incumbents too.

    Args:
        feature: Column name to screen, e.g. `rs_126d`
    """
    signals, _, _ = rl.load_cache()
    print(f"# Feature screen — {feature}\n\nRun date: {run_timestamp()}")
    print("\nYear-demeaned Spearman rho against the 366d return, on training slices only.\n")

    verdicts: list[bool] = []
    for config, _ in rl.CONFIGS:
        sig = signals[config].filter(pl.col("entry_date") < rl.HOLDOUT_START).sort(["date", "symbol"])
        if feature not in sig.columns:
            raise ValueError(
                f"No column {feature!r} in the {config} cache; available: {sorted(c for c in sig.columns if not c.startswith('_'))}"
            )
        values = sig[feature].cast(pl.Float64).to_numpy(allow_copy=True).astype(float)
        demeaned = sig["ret_demeaned"].to_numpy(allow_copy=True).astype(float)
        entry = np.array([(d - _EPOCH).days for d in sig["entry_date"].to_list()], dtype=np.int64)

        mid = (rl.EVAL_START - _EPOCH).days + ((rl.HOLDOUT_START - _EPOCH).days - (rl.EVAL_START - _EPOCH).days) // 2
        first, second = entry < mid, entry >= mid
        rho_all = rl.spearman(values, demeaned)
        rho_1, rho_2 = rl.spearman(values[first], demeaned[first]), rl.spearman(values[second], demeaned[second])
        halves_agree = bool(np.sign(rho_1) == np.sign(rho_2) and np.isfinite(rho_1) and np.isfinite(rho_2))

        fold_rhos = []
        for cutoff, _, _ in rl.fold_windows():
            train = entry < (cutoff - _EPOCH).days
            fold_rhos.append(rl.spearman(values[train], demeaned[train]) if train.sum() >= 100 else float("nan"))
        finite = [r for r in fold_rhos if np.isfinite(r)]
        folds_agree = sum(1 for r in finite if np.sign(r) == np.sign(rho_all))
        # "All but one fold" — the same rule at any fold count, matching the spec's 4-of-5.
        folds_ok = len(finite) > 0 and folds_agree >= len(finite) - 1

        passed = halves_agree and folds_ok
        verdicts.append(passed)
        print(f"{config}: N={len(sig)} rho_all={rho_all:+.4f} first_half={rho_1:+.4f} second_half={rho_2:+.4f} halves_agree={halves_agree}")
        print(
            f"  fold rhos: {' '.join(f'{r:+.4f}' for r in fold_rhos)}  -> {folds_agree}/{len(finite)} share rho_all's sign, ok={folds_ok}"
        )
        print(f"  {config} verdict: {'PASS' if passed else 'FAIL'}")

    print(f"\n## Screen: {'PASS' if all(verdicts) else 'FAIL'} — {feature} may {'' if all(verdicts) else 'NOT '}enter a candidate spec")


def cmd_holdout(baseline_path: Path, gates: list[int]) -> None:
    """Open the frozen holdout once and sweep the gate on it.

    Entries from `HOLDOUT_START` onward, replayed to `HOLDOUT_END`. Positions that have not
    reached their 366-day exit by then are still open, and `run_sim` marks them to market on
    the final calendar day — which is what "sell everything on the last bar" means for an
    equity curve.

    Read the result with three limits in mind, all inherent to a window shorter than the hold:

    - Most positions are unrealized. The CAGR is a mark-to-market snapshot, not a settled
      result, and it moves with wherever the market happens to sit on the last bar.
    - Signals raised near the end are held for weeks, not a year, so they dilute toward zero
      rather than expressing the strategy.
    - One 20-month window is one sample. It cannot confirm a gate; it can only fail to.

    This is the promotion check the loop is not allowed to run. It needs the database, so it
    needs `ACTIVE_PROFILE=hetzner-db`.

    Args:
        baseline_path: Spec whose score the gate is applied to
        gates: MIN_RANKING values to sweep
    """
    spec = rl.load_spec(baseline_path)
    settings = Settings.from_toml()
    repo = DailyBarsQueryRepository(engine=settings.engine)

    print(f"Loading holdout bars {rl.HOLDOUT_START} – {HOLDOUT_END} …", flush=True)
    bars = qm.load_bars(repo, rl.HOLDOUT_START, HOLDOUT_END)
    if bars.is_empty():
        raise ValueError(f"No bars for {rl.HOLDOUT_START}..{HOLDOUT_END}; is ACTIVE_PROFILE=hetzner-db set?")
    ind = rl.add_lab_features(qm.add_indicators(bars), _load_spy_closes(repo, rl.HOLDOUT_START, HOLDOUT_END))
    bull = qm.load_spy_regime(repo, rl.HOLDOUT_START, HOLDOUT_END)

    calendar = sorted({d for d in bars["date"].to_list() if rl.HOLDOUT_START <= d <= HOLDOUT_END})
    market = Market(bars.filter(pl.col("date") >= rl.HOLDOUT_START).select("symbol", "date", "adj_close"))
    cal_set = {(d - _EPOCH).days for d in calendar}
    rng = np.random.default_rng(SEED)

    print(f"\n# Holdout — {spec.id}\n\nRun date: {run_timestamp()}")
    print(
        f"\nEntries {rl.HOLDOUT_START} onward, replayed to {calendar[-1]}. Positions short of "
        f"{HOLD_LABEL} days are marked to market on the last bar."
    )

    for config, sma_t in rl.CONFIGS:
        sig = qm.resolve_entries(qm.get_signals(ind, bull, rl.HOLDOUT_START, sma_thresh=sma_t), bars)
        sig = sig.filter(pl.col("date") >= rl.HOLDOUT_START).sort(["date", "symbol"])
        rows = _replay_rows(sig, rl.raw_scores(sig, spec), cal_set, allow_holdout=True)
        if len(rows) < 30:
            print(f"\n{config}: only {len(rows)} tradable signals — too few to sweep")
            continue
        print(f"\n### {config} — {len(rows)} tradable signals")
        hdr = (
            f"{'gate':>5} {'kept':>6} {'keep%':>7} {'CAGR%':>8} {'MaxDD%':>8} {'Sortino':>8} {'taken':>6} | {'null CAGR%':>11} {'beats':>7}"
        )
        print(hdr)
        print("-" * len(hdr))
        for gate in gates:
            kept = [r for r in rows if r["score"] >= gate]
            if len(kept) < 20:
                continue
            res = run_sim(market, calendar, kept, "score")
            # A gate keeping everything has no null: the "random subset" is a permutation of the
            # same signals, so it scores itself and prints a meaningless 0/N. Say n/a instead.
            if len(kept) == len(rows):
                null_txt = f"{'—':>11} {'n/a':>7}"
            else:
                null = [
                    run_sim(market, calendar, [rows[i] for i in rng.choice(len(rows), size=len(kept), replace=False)], "score")["cagr"]
                    for _ in range(N_NULL)
                ]
                beats = sum(1 for c in null if res["cagr"] > c)
                null_txt = f"{statistics.fmean(null):>+11.2f} {beats:>4}/{N_NULL}"
            print(
                f"{gate:>5} {len(kept):>6} {100 * len(kept) / len(rows):>6.1f}% {res['cagr']:>+8.2f} "
                f"{res['max_dd']:>8.2f} {res['sortino']:>8.3f} {res['taken']:>6} | {null_txt}"
            )


def main() -> None:
    """Parse arguments and dispatch to the cache builder, the judge or the feature screen."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-cache", action="store_true", help="rebuild .cache/ranking-lab/ from the database")
    group.add_argument("--eval", metavar="SPEC", type=Path, help="evaluate a candidate spec JSON")
    group.add_argument("--screen", metavar="FEATURE", help="screen a candidate feature for sign stability")
    group.add_argument(
        "--holdout", action="store_true", help="open the frozen 2025+ holdout and sweep the gate (promotion check, needs the database)"
    )
    parser.add_argument(
        "--baseline",
        metavar="SPEC",
        type=Path,
        default=CANDIDATE_DIR / "c000-production.json",
        help="baseline spec to judge against (default: the shipped production bands)",
    )
    parser.add_argument("--no-portfolio", action="store_true", help="skip the portfolio replay; the verdict cannot be an acceptance")
    args = parser.parse_args()

    if args.build_cache:
        build_cache()
    elif args.eval:
        cmd_eval(args.eval, args.baseline, args.no_portfolio)
    elif args.holdout:
        cmd_holdout(args.baseline, HOLDOUT_GATES)
    else:
        cmd_screen(args.screen)


if __name__ == "__main__":
    main()
