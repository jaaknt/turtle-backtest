#!/usr/bin/env python3
"""
Does the three-feature ranking weighting beat the six-dimension one it replaced?

Background: a per-trade scan of 2010-2020 signals on *year-demeaned* 366d returns found only
three of the six ranking dimensions carried a cross-sectional effect that kept its sign across
both halves of the period -- ADR%(20) (rho +0.121), distance above SMA50 (+0.099) and price
(-0.059). ADR compression, 12-month ROC and RSI(14) were 25-75% time effect and reversed sign.
turtlex/strategy/ranking/qullamaggie.py now weights the three survivors 40/35/25 and drops the
rest. This script is the out-of-sample check of that change, on 2021-2026.

Three traps this measures around, all of which produce false positives if ignored:

1. A score threshold is not a fixed filter. MIN_RANKING=40 keeps a different fraction of
   signals under each weighting, so comparing two schemes "at gate 40" compares selectivity,
   not skill. Schemes are compared at matched keep-% (top K% of signals) instead.
2. Taking fewer positions changes returns on its own. The matched-selectivity and gate tables
   are therefore reported against random subsets of the same size -- a scheme only demonstrates
   skill by beating its own null. (The sub-period table has no null column; read it for the
   direction of the difference between schemes, not as evidence against chance.)
3. Coarse band tables leave hundreds of signals tied on the same score, and cutting the top-K
   inside a tie group by date silently selects the earliest signals. In the matched-selectivity
   and sub-period tables ties are broken at random, redrawn N_TIE times, so no result there
   depends on arbitrary ordering. The gate sweep needs no tie-break -- a threshold takes every
   signal at or above it -- so those rows are single runs.

Signals come from turtlex/research/qullamaggie.py (the bulk counterpart of QullamaggieStrategy,
parity-tested in tests/research/test_qullamaggie_parity.py). The portfolio replay matches
scripts/qullamaggie-portfolio-sim.py: next trading day's adjusted open, position = POS_FRACTION
of portfolio value, skip when cash is short, 366d calendar time exit, still-open positions
marked to market at period end. Two deliberate differences from that script: the MIN_RANKING
gate is not applied up front (sweeping it is the point here), and the master calendar is the
union of universe bar dates rather than SPY's trading days. Both shift CAGR by a few tenths of
a point equally for every scheme, so cross-scheme comparisons hold -- but these numbers are not
directly comparable with result-qullamaggie-portfolio-v4.md.
"""

import statistics
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_daily_sortino
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2021, 1, 1)
EVAL_END = date(2026, 6, 26)
INIT_EQUITY = 30_000.0
POS_FRACTION = 0.04
HOLD_CAL = 366
CONFIGS = [("s20", 0.20), ("s16", 0.16), ("s12", 0.12)]
KEEP_PCTS = [35, 25, 15]
GATES = [0, 20, 30, 40, 42, 44, 46, 50, 60]  # 42-46 bracket the gate that matches the old >=40 selectivity
N_TIE = 20  # tie-break redraws per cell
N_NULL = 30  # random subsets per cell
SPLIT = date(2023, 7, 1)  # sub-period split, to check an edge is not one lucky stretch
SEED = 20260729

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-ranking-weights.md"

# The pre-2026-07-29 production bands, kept here as the baseline to beat. SMA50 carried a
# fixed weight of 50 and the remaining 50 points were split across the other five dimensions
# proportionally to each one's reachable-domain Sortino spread.
LEGACY_BANDS: list[tuple[str, list[tuple[float, int]], int]] = [
    ("adr_pct", [(0.035, 0), (0.04, 0), (0.045, 3), (0.05, 4), (0.08, 8)], 12),
    ("adr_pct_change", [(0.7, 12), (0.8, 0), (0.9, 1)], 0),
    ("pct_vs_sma50", [(0.10, 0), (0.12, 12), (0.15, 22), (0.17, 31), (0.20, 17), (0.30, 44)], 50),
    ("raw_close", [(10.0, 13), (20.0, 4), (50.0, 1), (100.0, 1), (250.0, 0)], 0),
    ("roc_252d", [(-0.20, 10), (0.0, 6), (0.20, 5), (0.40, 8), (0.60, 10), (0.80, 5), (1.00, 0)], 0),
    ("rsi14", [(50.0, 3), (60.0, 2), (70.0, 0)], 0),
]

# The 40/35/25 bands that shipped 2026-07-30 .. 2026-08-07, frozen here so recalibrating the
# live bands does not silently turn this report into new-vs-six-dimension and drop the scheme
# actually being replaced out of the comparison. Same 40/35/25 split as production; what
# differs is the band shapes, fitted to a superseded bk50d_s15_v1.3_roc100 run and anchoring
# each dimension's floor at its worst *reachable* bucket -- which zeroed 49.6% of the s12 pool
# on ADR. Production now anchors that floor outside the entry filter instead.
PREV_BANDS: list[tuple[str, list[tuple[float, int]], int]] = [
    ("adr_pct", [(0.035, 0), (0.04, 0), (0.045, 10), (0.05, 13), (0.08, 27)], 40),
    ("pct_vs_sma50", [(0.10, 0), (0.12, 8), (0.15, 15), (0.17, 22), (0.20, 12), (0.30, 31)], 35),
    ("raw_close", [(10.0, 25), (20.0, 8), (50.0, 2), (100.0, 2), (250.0, 0)], 0),
]

SCHEMES = ("legacy", "prev-bands", "production")


def band_score(value: float | None, bands: list[tuple[float, int]], top: int) -> int:
    """Points of the first band whose upper bound exceeds value; `top` at or above the last.

    Args:
        value: Metric value to score; None or non-finite scores 0
        bands: (upper_bound, points) pairs in ascending bound order
        top: Points for values at or above the last upper bound
    """
    if value is None or not np.isfinite(value):
        return 0
    for upper, points in bands:
        if value < upper:
            return points
    return top


def score_bands(row: dict, scheme: list[tuple[str, list[tuple[float, int]], int]]) -> int:
    """Score a signal with a frozen band table.

    Args:
        row: Signal row carrying the Qullamaggie indicator columns
        scheme: (column, bands, top) triples to sum, e.g. LEGACY_BANDS or PREV_BANDS
    """
    return sum(band_score(row.get(col), bands, top) for col, bands, top in scheme)


class Market:
    """Per-symbol adjusted-close arrays, sorted by date, for the portfolio replay.

    The trading calendar is not held here -- run_sim takes it as a parameter, so the
    sub-period tables replay the same prices over a shorter calendar without copying.
    """

    def __init__(self, bars: pl.DataFrame) -> None:
        self.dates: dict[str, np.ndarray] = {}
        self.closes: dict[str, np.ndarray] = {}
        for (sym,), grp in bars.group_by(["symbol"], maintain_order=False):
            g = grp.sort("date")
            self.dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
            self.closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    def price_on(self, symbol: str, dint: int) -> float:
        """Last adjusted close at or before `dint`.

        Raises rather than returning a sentinel: every caller is pricing a position the
        replay itself opened from this symbol's own bars, so an absent price means the
        market and the signals were built from different frames. Valuing that position at
        zero -- or dropping it without crediting cash -- would show up only as an
        unexplained step down in the equity curve.

        Args:
            symbol: Ticker to price
            dint: Date as days since the epoch
        """
        d = self.dates.get(symbol)
        idx = int(np.searchsorted(d, dint, side="right")) - 1 if d is not None else -1
        if idx < 0:
            raise ValueError(f"No bar for {symbol} at or before {_EPOCH + timedelta(days=dint)}")
        return float(self.closes[symbol][idx])


def run_sim(market: Market, calendar: list[date], signals: list[dict], score_key: str) -> dict:
    """Replay the portfolio over `signals`, funding same-day competitors best-scored first.

    Args:
        market: Per-symbol price arrays
        calendar: Ascending trading days the replay visits
        signals: Signal rows carrying entry_dint, entry_px and the score column
        score_key: Name of the score column deciding funding priority
    """
    by_day: dict[int, list[dict]] = {}
    for s in signals:
        by_day.setdefault(s["entry_dint"], []).append(s)

    cash = INIT_EQUITY
    positions: list[dict] = []
    equity: list[float] = []
    n_taken = 0

    for dint in [(d - _EPOCH).days for d in calendar]:
        still_open = []
        for p in positions:
            if dint >= p["exit_int"]:
                cash += p["shares"] * market.price_on(p["symbol"], dint)
                continue
            still_open.append(p)
        positions = still_open

        mtm = cash + sum(p["shares"] * market.price_on(p["symbol"], dint) for p in positions)
        for s in sorted(by_day.get(dint, []), key=lambda r: r[score_key], reverse=True):
            target = POS_FRACTION * mtm
            if cash + 1e-9 < target:
                continue
            cash -= target
            positions.append({"symbol": s["symbol"], "shares": target / s["entry_px"], "exit_int": dint + HOLD_CAL})
            n_taken += 1

        equity.append(cash + sum(p["shares"] * market.price_on(p["symbol"], dint) for p in positions))

    eq = np.array(equity)
    daily_ret = eq[1:] / eq[:-1] - 1.0
    max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
    n_days = (calendar[-1] - calendar[0]).days
    cagr = float((eq[-1] / eq[0]) ** (365.0 / n_days) - 1.0)
    sortino = compute_daily_sortino(daily_ret)
    return {"cagr": cagr * 100, "max_dd": max_dd * 100, "sortino": sortino, "taken": n_taken}


def top_k(signals: list[dict], score_key: str, n_keep: int, rng: np.random.Generator) -> list[dict]:
    """Top `n_keep` signals by score, with ties broken at random rather than by date.

    Args:
        signals: Signal rows to rank
        score_key: Name of the score column
        n_keep: How many signals to keep
        rng: Source of the tie-break jitter
    """
    jitter = rng.random(len(signals))
    order = sorted(range(len(signals)), key=lambda i: (-signals[i][score_key], jitter[i]))
    return [signals[i] for i in order[:n_keep]]


def main() -> None:
    settings = Settings.from_toml()
    repo = DailyBarsQueryRepository(engine=settings.engine)
    rng = np.random.default_rng(SEED)
    ranker = QullamaggieRanking()

    print(f"Loading bars {EVAL_START} – {EVAL_END} …", flush=True)
    bars = qm.load_bars(repo, EVAL_START, EVAL_END)
    bull = qm.load_spy_regime(repo, EVAL_START, EVAL_END)
    ind = qm.add_indicators(bars)

    calendar = sorted({d for d in bars["date"].to_list() if EVAL_START <= d <= EVAL_END})
    market = Market(bars.filter((pl.col("date") >= EVAL_START) & (pl.col("date") <= EVAL_END)))
    cal_set = {(d - _EPOCH).days for d in calendar}

    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    def table(hdr: str, rows: list[str]) -> None:
        """Emit a fixed-width table as a fenced ```text block, blank-line-padded on both sides."""
        out("")
        out("```text")
        out(hdr)
        out("-" * len(hdr))
        for row in rows:
            out(row)
        out("```")

    out("# Ranking Weights — recalibrated 40/35/25 bands vs the two weightings they replaced")
    out("")
    out(
        f"Period {EVAL_START} .. {EVAL_END}, ${INIT_EQUITY:,.0f} initial equity, "
        f"{POS_FRACTION:.0%} positions, {HOLD_CAL}d calendar hold, next-day-open entries."
    )
    out("")
    out(
        "`production` is the shipped QullamaggieRanking — 40/35/25 with bands re-derived on 2026-08-07 from the "
        "bk50d_s12_v2.0 cohort tables, each dimension's floor anchored outside its entry filter so no qualifying "
        "cohort scores 0. `prev-bands` is the same 40/35/25 split with the superseded bands it replaces (fitted to "
        "an s15_v1.3_roc100 run; ADR < 4.5% scored 0, which was 49.6% of the s12 pool). `legacy` is the "
        "six-dimension weighting dropped on 2026-07-29 (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). "
        f"Ties are broken at random over {N_TIE} redraws; `null` is {N_NULL} random subsets of the same size."
    )

    for name, sma_t in CONFIGS:
        print(f"Signals {name} …", flush=True)
        sig = qm.resolve_entries(qm.get_signals(ind, bull, EVAL_START, sma_thresh=sma_t), bars)
        sig = sig.filter((pl.col("date") >= EVAL_START) & (pl.col("date") <= EVAL_END))

        # Both arms read indicator columns by name, so a rename upstream would silently score
        # that dimension 0 for every signal and hand the comparison to whichever scheme still
        # had all its inputs. Fail here instead.
        required = {col for col, _, _ in (*LEGACY_BANDS, *PREV_BANDS)} | {"raw_close", "adr_pct", "pct_vs_sma50"}
        missing = required - set(sig.columns)
        if missing:
            raise ValueError(f"Signal frame is missing {sorted(missing)}; those dimensions would silently score 0")

        signals: list[dict] = []
        n_no_entry_bar = 0
        for row in sig.iter_rows(named=True):
            r = dict(row)
            entry_dint = (r["entry_date"] - _EPOCH).days
            if entry_dint not in cal_set:  # entry falls past EVAL_END
                n_no_entry_bar += 1
                continue
            r["entry_dint"] = entry_dint
            r["entry_px"] = float(r["entry_price"])
            r["production"] = ranker.ranking(
                pl.DataFrame([{"date": r["date"], "close": r["raw_close"], "adr_pct": r["adr_pct"], "pct_vs_sma50": r["pct_vs_sma50"]}]),
                r["date"],
            )
            r["legacy"] = score_bands(r, LEGACY_BANDS)
            r["prev-bands"] = score_bands(r, PREV_BANDS)
            signals.append(r)

        out("")
        out(
            f"## {name} (%abv_SMA50 > {sma_t:.0%}) — {len(signals)} fillable signals "
            f"({len(sig)} raised, {n_no_entry_bar} with no entry bar inside the period)"
        )

        hdr = f"{'scheme':<11} {'min':>4} {'p25':>4} {'p50':>4} {'p75':>4} {'max':>4} {'mean':>6} {'<40 kept%':>10}"
        rows = []
        for scheme in SCHEMES:
            v = sorted(float(s[scheme]) for s in signals)
            keep40 = 100.0 * sum(1 for x in v if x >= 40) / len(v)
            rows.append(
                f"{scheme:<11} {v[0]:>4.0f} {v[len(v) // 4]:>4.0f} {v[len(v) // 2]:>4.0f} "
                f"{v[3 * len(v) // 4]:>4.0f} {v[-1]:>4.0f} {statistics.fmean(v):>6.1f} {keep40:>9.1f}%"
            )
        out("")
        out("Score distribution — the same gate keeps different fractions under each scheme:")
        table(hdr, rows)

        hdr = (
            f"{'keep':>5} {'scheme':<11} {'CAGR%':>8} {'sd':>5} {'MaxDD%':>8} {'Sortino':>8} {'taken':>6} | "
            f"{'null CAGR%':>11} {'sd':>5} {'beats':>7}"
        )
        rows = []
        for pct in KEEP_PCTS:
            n_keep = max(10, round(len(signals) * pct / 100))
            for scheme in SCHEMES:
                null = [
                    run_sim(market, calendar, [signals[i] for i in rng.choice(len(signals), size=n_keep, replace=False)], scheme)["cagr"]
                    for _ in range(N_NULL)
                ]
                res = [run_sim(market, calendar, top_k(signals, scheme, n_keep, rng), scheme) for _ in range(N_TIE)]
                cagrs = [r["cagr"] for r in res]
                beat = sum(1 for c in null if statistics.fmean(cagrs) > c)
                rows.append(
                    f"{pct:>4}% {scheme:<11} {statistics.fmean(cagrs):>+8.2f} {statistics.stdev(cagrs):>5.2f} "
                    f"{statistics.fmean([r['max_dd'] for r in res]):>8.2f} "
                    f"{statistics.fmean([r['sortino'] for r in res]):>8.3f} "
                    f"{statistics.fmean([r['taken'] for r in res]):>6.0f} | "
                    f"{statistics.fmean(null):>+11.2f} {statistics.stdev(null):>5.2f} {beat:>4}/{N_NULL}"
                )
        out("")
        out(
            "Matched selectivity — top K% by each scheme, so both arms choose from an identical "
            "number of candidates. The `taken` columns still differ: cash runs out on different "
            "days under each ordering, so the executed counts are an outcome, not a control."
        )
        table(hdr, rows)

        halves = {
            f"{EVAL_START:%Y-%m}..{SPLIT:%Y-%m}": [d for d in calendar if d < SPLIT],
            f"{SPLIT:%Y-%m}..{EVAL_END:%Y-%m}": [d for d in calendar if d >= SPLIT],
        }
        hdr = f"{'keep':>5} {'scheme':<11} " + " ".join(f"{h:>20}" for h in halves)
        rows = []
        for pct in KEEP_PCTS:
            n_keep = max(10, round(len(signals) * pct / 100))
            for scheme in SCHEMES:
                cells = []
                for half_cal in halves.values():
                    c = [run_sim(market, half_cal, top_k(signals, scheme, n_keep, rng), scheme)["cagr"] for _ in range(N_TIE // 4)]
                    cells.append(f"{statistics.fmean(c):>+9.2f} (sd {statistics.stdev(c):>4.1f})")
                rows.append(f"{pct:>4}% {scheme:<11} " + " ".join(f"{c:>20}" for c in cells))
        out("")
        out("Sub-period split — an edge that only exists in one half is not an edge:")
        table(hdr, rows)

        hdr = (
            f"{'scheme':<11} {'gate':>5} {'kept':>6} {'keep%':>6} {'CAGR%':>8} {'MaxDD%':>8} {'Sortino':>8} "
            f"{'taken':>6} | {'null CAGR%':>11} {'sd':>5} {'beats':>7}"
        )
        rows = []
        for scheme in SCHEMES:
            for gate in GATES:
                kept = [s for s in signals if s[scheme] >= gate]
                if len(kept) < 20:
                    continue
                gate_res = run_sim(market, calendar, kept, scheme)
                # A gate keeping everything has no null to speak of: the "random subset" is a
                # permutation of the same signals, so it would score itself and print a
                # meaningless 0/30. Say so rather than letting it read as a verdict.
                if len(kept) == len(signals):
                    null_txt = f"{'—':>11} {'—':>5} {'n/a':>7}"
                else:
                    null = [
                        run_sim(market, calendar, [signals[i] for i in rng.choice(len(signals), size=len(kept), replace=False)], scheme)[
                            "cagr"
                        ]
                        for _ in range(N_NULL)
                    ]
                    beat = sum(1 for c in null if gate_res["cagr"] > c)
                    null_txt = f"{statistics.fmean(null):>+11.2f} {statistics.stdev(null):>5.2f} {beat:>4}/{N_NULL}"
                rows.append(
                    f"{scheme:<11} {gate:>5} {len(kept):>6} {100.0 * len(kept) / len(signals):>5.1f}% "
                    f"{gate_res['cagr']:>+8.2f} {gate_res['max_dd']:>8.2f} {gate_res['sortino']:>8.3f} {gate_res['taken']:>6} | "
                    f"{null_txt}"
                )
        out("")
        out("MIN_RANKING gate sweep — each gate against a random gate keeping the same count:")
        table(hdr, rows)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
