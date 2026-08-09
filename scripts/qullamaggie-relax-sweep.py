#!/usr/bin/env python3
"""
Relaxation sweep for bk50d_s20_v2.0 / 366d hold.

Goal: increase signals per month (F/mo) without degrading Sortino and Mean%.
Each variant relaxes exactly ONE dimension of the baseline (all other filters
unchanged); the best 2 and 3 quality-preserving relaxations are then combined.

Indicators and entries come from turtlex.research.qullamaggie, which is parity-tested
against QullamaggieStrategy: baseline filters are roc_12m<100%,
vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250,
avg_vol>=100K, cooldown 30d, mcap>=1.5B excl Comm/RE, tight_range and sma_alignment
disabled. Entry is the next trading bar's adjusted open and every variant — baseline
included — is gated at QullamaggieRanking >= MIN_RANKING, so the sweep measures a
relaxation against the algorithm as actually traded.

The dimensions the shared layer does not parameterise (min price, cooldown,
SMA distance, ADR floor) are re-filtered here from the same indicator frame; the two
universe dimensions (market cap, sector) come from TickerQueryRepository symbol lists.

Variants: cd15 (cooldown 15d), p3 (min price $3), mcap1.0B (mcap floor $1.0B),
sect+CommRE (re-admit Comm Services/Real Estate), p2 (min price $2), sma16/sma12 (SMA
distance 20%->16%/12%), adr2.5 (ADR floor 3.0%->2.5%).

The last three come from the cohort tables rather than from a guess: `p2` because
result-qullamaggie-cohorts-price.md puts the [0-5) band above the $5-$250 aggregate on
every metric at all three SMA thresholds; `sma16` because result-qullamaggie-cohorts-ranking.md
shows the gated s16 pool close to s20 on Sortino (0.13 apart at the R>=44 gate, 2026-08-07 run —
the score's 35-point SMA50 term re-imposes most of what the hard threshold does); `adr2.5` because
result-qullamaggie-cohorts-adr.md's [2.5-3.0) band carries the same Sortino as the whole
population at s20. The `vdu1.0` variant was dropped on 2026-08-01: vol_dry_up is no longer a
production filter, so relaxing it is a no-op against this baseline.

Eval: 2015-01-01 – 2026-06-26 | 366d calendar hold | warmup handled by qm.load_bars
References: docs/research/qullamaggie-backtest-v4.md,
            docs/research/result-qullamaggie-backtest-v4.md,
            docs/research/result-qullamaggie-cohorts-tightrange.md,
            docs/research/result-qullamaggie-cohorts-price.md
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
MIN_AVG_VOL = 100_000
MAX_PRICE = 250.0
MIN_HISTORY = 300
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_CHANGE_CAP = 0.90
MIN_NEG = 10
MIN_RANKING = 44  # QullamaggieRanking gate, matching the portfolio-runner default

# Loosest universe any variant asks for; loaded once, then narrowed per variant.
LOOSEST_MCAP = 1_000_000_000

# The universe query drops a company whose sector is NULL, because `sector NOT IN (...)`
# is NULL for those rows — 21 names above the $1.0B floor. Excluding a sector no company
# has keeps that behaviour wherever no real sector is being excluded: for the bar load,
# and for the sect+CommRE variant, so re-admitting Communication Services and Real Estate
# stays a one-dimension change instead of also pulling in every unknown-sector name.
#
# Note this moved the baseline relative to the pre-migration run of this study, which
# used a symbol-metadata dict that coerced a NULL sector to "" and therefore admitted
# those names into every variant. Excluding them matches the production universe, but
# the baseline row is not comparable with the previous result-qullamaggie-relax-sweep.md.
NO_SUCH_SECTOR = "__no_such_sector__"

LABEL = "bk50d_s20_v2.0"

# Baseline parameter values; each variant overrides exactly one.
BASE_PARAMS = {
    "cooldown": 30,
    "min_price": 5.0,
    "min_mcap": 1.5e9,
    "include_comm_re": False,
    "sma_t": 0.20,
    "adr_min": 0.03,
}

VARIANTS: list[tuple[str, dict]] = [
    ("cd15", {"cooldown": 15}),
    ("p3", {"min_price": 3.0}),
    ("mcap1.0B", {"min_mcap": 1.0e9}),
    ("sect+CommRE", {"include_comm_re": True}),
    ("p2", {"min_price": 2.0}),
    ("sma16", {"sma_t": 0.16}),
    ("sma12", {"sma_t": 0.12}),
    ("adr2.5", {"adr_min": 0.025}),
]

# "Same level" tolerance for the combo-selection quality gate.
QUALITY_TOL = 0.95

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-relax-sweep.md"


def load_loosest_bars(bars_history: DailyBarsQueryRepository) -> pl.DataFrame:
    """Load bars for the LOOSEST universe (mcap >= 1.0B, no real sector excluded);
    per-variant universe constraints are applied later via the symbol lists, so the DB
    is hit only once. Adjustment and unusable-bar handling come from qm.prepare_bars,
    the same path qm.load_bars uses — only the universe predicate is widened here.

    `NO_SUCH_SECTOR` rather than `[]`: an empty list renders an always-true predicate
    that retains NULL-sector names, which `universe()` would then drop anyway. Passing
    the sentinel excludes them here too, so the bar frame and every variant's symbol
    list agree on the universe.

    Bars run past EVAL_END because a 366d hold needs forward data beyond the last
    signal date; `get_signals` bounds the signal window itself.
    """
    fetch_start = EVAL_START - timedelta(days=qm.WARMUP_DAYS)
    df = bars_history.get_qualified_universe_bars_pl(
        fetch_start,
        date.today(),
        min_market_cap=LOOSEST_MCAP,
        excluded_sectors=[NO_SUCH_SECTOR],
    )
    return qm.prepare_bars(df.rename({"close": "raw_close"}))


# ── Ranking ──────────────────────────────────────────────────────────────────

_ranker = QullamaggieRanking()


def compute_ranking(row: dict) -> int:
    """Score one signal 0-100 with the production QullamaggieRanking.

    `raw_close` is mapped onto the `close` column the ranking reads: QullamaggieStrategy
    keeps `close` unadjusted and the price bands are dollar-denominated.
    """
    row_df = pl.DataFrame(
        [{"date": row["date"], "close": row["raw_close"], "adr_pct": row["adr_pct"], "pct_vs_sma50": row["pct_vs_sma50"]}]
    )
    return _ranker.ranking(row_df, row["date"])


def get_signals(df: pl.DataFrame, bull_dates: set[date], allowed_syms: set[str], params: dict) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") <= EVAL_END)
            & pl.col("symbol").is_in(list(allowed_syms))
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & pl.col("adr_pct").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > params["min_price"])
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= params["adr_min"])
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") >= params["sma_t"])
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "raw_close", "adr_pct", "pct_vs_sma50"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    cooldown = params["cooldown"]
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    # Cooldown runs from the warmup window rather than EVAL_START, so a trigger just before
    # the window suppresses an early in-window signal — the ordering qm.get_signals uses.
    # Only accepted triggers on or after EVAL_START are emitted.
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > cooldown:
            last_trigger[sym] = d
            if d >= EVAL_START and compute_ranking(row) >= MIN_RANKING:
                rows_out.append(row)
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


def run_trades(signals: pl.DataFrame, sym_dates: dict[str, np.ndarray], sym_closes: dict[str, np.ndarray]) -> list[dict]:
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        entry_int = (row["entry_date"] - _EPOCH).days
        idx_entry = int(np.searchsorted(dates, entry_int))
        if idx_entry >= len(dates) or dates[idx_entry] != entry_int:
            continue
        if dates[-1] < entry_int + HOLD_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        entry_px = float(row["entry_price"])
        # Seed the drawdown window with the entry fill, so a gap down from the open counts.
        window = np.concatenate(([entry_px], closes[idx_entry : idx_exit + 1]))
        ret = float((closes[idx_exit] - entry_px) / entry_px)
        running_max = np.maximum.accumulate(window)
        mdd = float((1.0 - window / running_max).max())
        records.append({"ret": ret, "mdd": mdd})
    return records


def compute_metrics(records: list[dict]) -> dict:
    a = np.array([r["ret"] for r in records])
    mdds = np.array([r["mdd"] for r in records])
    months = (EVAL_END.year - EVAL_START.year) * 12 + (EVAL_END.month - EVAL_START.month)
    m = compute_trade_metrics(a * 100, HOLD_CAL, trade_drawdowns_pct=mdds * 100, min_losers=MIN_NEG)
    if m is None:  # a variant whose filters admitted nothing
        nan = float("nan")
        return {"n": 0, "freq": 0.0, "win": nan, "mean": nan, "med": nan, "sr": nan, "pf": nan, "mdd": nan}
    return {
        "n": m.n,
        "freq": m.n / max(months, 1),
        "win": m.win_pct,
        "mean": m.mean_pct,
        "med": m.median_pct,
        "sr": m.sortino,
        "pf": m.profit_factor,
        "mdd": m.mean_trade_mdd_pct,
    }


_HDR = f"{'Variant':<36}  {'N':>5}  {'F/mo':>5}  {'Win%':>5}  {'Mean%':>7}  {'Med%':>7}  {'Sortino':>7}  {'PF':>6}  {'MaxDD%':>7}"
_SEP = "─" * len(_HDR)


def fmt_row(label: str, m: dict) -> str:
    pf_str = f"{m['pf']:>6.2f}" if np.isfinite(m["pf"]) else f"{'inf':>6}"
    return (
        f"{label:<36}  {m['n']:>5}  {m['freq']:>5.1f}  {m['win']:>5.1f}  {m['mean']:>+7.2f}  "
        f"{m['med']:>+7.2f}  {m['sr']:>7.3f}  {pf_str}  {m['mdd']:>7.2f}"
    )


def main() -> None:
    settings = Settings.from_toml()

    bars_history = DailyBarsQueryRepository(engine=settings.engine)
    ticker_repo = TickerQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading bars (loosest universe: mcap>=1.0B, all sectors) …", flush=True)
    bars = load_loosest_bars(bars_history)
    valid_syms = set(bars.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"].to_list())
    bars = bars.filter(pl.col("symbol").is_in(list(valid_syms)))
    print(f"  {bars.height:,} bars, {len(valid_syms):,} symbols", flush=True)

    print("Computing indicators …", flush=True)
    # Project down to the columns qm.resolve_entries reads before building the indicator
    # frame, so the full-width bar frame is released rather than held alongside it. This is
    # the widest universe of any study here, so it is also the one most likely to be OOM-killed.
    df = qm.add_indicators(bars)
    bars = bars.select("symbol", "date", "adj_open")

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    # Project to the three columns the trade loop reads before grouping. Grouping the full
    # indicator frame materialised all ~20 columns per group, and the leading sort was a
    # redundant full copy of the widest frame in the study — prepare_bars and add_indicators
    # both already sort by (symbol, date), and each group is re-sorted by date below.
    for (sym,), grp in df.select("symbol", "date", "adj_close").group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)

    universe_cache: dict[tuple[float, bool], set[str]] = {}

    def universe(params: dict) -> set[str]:
        key = (params["min_mcap"], params["include_comm_re"])
        if key not in universe_cache:
            qualified = ticker_repo.get_qullamaggie_qualified_symbols(
                min_market_cap=int(key[0]),
                excluded_sectors=[NO_SUCH_SECTOR] if key[1] else None,
            )
            universe_cache[key] = valid_syms & set(qualified)
        return universe_cache[key]

    def run_variant(label: str, params: dict) -> dict:
        print(f"  {label} …", flush=True)
        signals = qm.resolve_entries(get_signals(df, bull_dates, universe(params), params), bars)
        records = run_trades(signals, sym_dates, sym_closes)
        m = compute_metrics(records)
        print(f"    {fmt_row(label, m)}", flush=True)
        return m

    print("Running baseline + single-dimension variants …", flush=True)
    base_m = run_variant(f"baseline ({LABEL})", BASE_PARAMS)
    single_results: list[tuple[str, dict, dict]] = []  # (label, overrides, metrics)
    for label, overrides in VARIANTS:
        m = run_variant(label, {**BASE_PARAMS, **overrides})
        single_results.append((label, overrides, m))

    # Quality gate: Sortino and Mean% must stay at >= QUALITY_TOL x baseline.
    passing = [
        (label, overrides, m)
        for label, overrides, m in single_results
        if m["sr"] >= QUALITY_TOL * base_m["sr"] and m["mean"] >= QUALITY_TOL * base_m["mean"]
    ]
    passing.sort(key=lambda x: x[2]["freq"], reverse=True)

    # Two combo rankings: raw F/mo gain, and F/mo gain per unit of Sortino given up.
    def cost_ratio(m: dict) -> float:
        return float((m["freq"] - base_m["freq"]) / max(base_m["sr"] - m["sr"], 1e-9))

    by_ratio = sorted(passing, key=lambda x: cost_ratio(x[2]), reverse=True)

    combo_results: list[tuple[str, dict]] = []
    seen_sets: set[frozenset[str]] = set()
    print("Running combos of the best quality-preserving relaxations …", flush=True)
    for ranking in (passing, by_ratio):
        for k in (2, 3):
            if len(ranking) < k:
                continue
            chosen = ranking[:k]
            key = frozenset(lbl for lbl, _, _ in chosen)
            if key in seen_sets:
                continue
            seen_sets.add(key)
            combo_label = "combo(" + "+".join(lbl for lbl, _, _ in chosen) + ")"
            combo_params = dict(BASE_PARAMS)
            for _, overrides, _ in chosen:
                combo_params.update(overrides)
            combo_results.append((combo_label, run_variant(combo_label, combo_params)))

    # ── Assemble report ────────────────────────────────────────────────────────
    table_lines = [_HDR, _SEP, fmt_row(f"baseline ({LABEL})", base_m)]
    for label, _, m in sorted(single_results, key=lambda x: x[2]["sr"], reverse=True):
        table_lines.append(fmt_row(label, m))
    for label, m in combo_results:
        table_lines.append(fmt_row(label, m))
    table = "\n".join(table_lines)

    finding_lines: list[str] = []
    for label, _, m in sorted(
        single_results,
        key=lambda x: (x[2]["freq"] - base_m["freq"]) / max(base_m["sr"] - x[2]["sr"], 1e-9),
        reverse=True,
    ):
        d_freq = m["freq"] - base_m["freq"]
        d_sr = m["sr"] - base_m["sr"]
        d_mean = m["mean"] - base_m["mean"]
        if d_sr >= 0:
            cost = "Sortino cost: none (improved)" if d_sr > 0 else "Sortino cost: none (flat)"
        else:
            cost = f"F/mo gain per unit Sortino lost: {d_freq / -d_sr:.1f}"
        finding_lines.append(f"- `{label}` — ΔF/mo {d_freq:+.1f}, ΔSortino {d_sr:+.3f}, ΔMean% {d_mean:+.2f}pp → {cost}")
    findings = "\n".join(finding_lines)

    print("\n" + table)
    print("\nF/mo gain per unit of Sortino given up (best first):")
    print(findings)

    quality_note = ", ".join(lbl for lbl, _, _ in passing) if passing else "none"

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write(f"# Qullamaggie Relax Sweep — {LABEL} / 366d\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Eval period | {EVAL_START} – {EVAL_END} |\n")
        fh.write(f"| Hold | {HOLD_CAL}d (calendar); entries without {HOLD_CAL}d of forward data skipped |\n")
        fh.write(f"| Baseline | {LABEL}: 50d-high breakout, close >20% above SMA50, next-day adjusted-open entry |\n")
        fh.write(
            "| Baseline fixed filters | roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, "
            "ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=100K, cooldown 30d, "
            "mcap>=1.5B excl Comm/RE |\n"
        )
        fh.write(f"| Ranking gate | QullamaggieRanking >= {MIN_RANKING}, applied to every variant including baseline |\n")
        fh.write("| Signal layer | turtlex/research/qullamaggie.py (parity-tested against QullamaggieStrategy) |\n")
        fh.write(
            "| Universe note | companies with a NULL sector are excluded from every variant, matching the "
            "production universe; the pre-migration run of this study admitted them, so the baseline row "
            "is not comparable with earlier versions of this document |\n"
        )
        fh.write("| Variants | each relaxes exactly one dimension (see table) |\n")
        fh.write(
            f"| Combo selection | variants with Sortino AND Mean% >= {QUALITY_TOL:.0%} of baseline, "
            f"ranked by F/mo; top-2 and top-3 combined (qualified: {quality_note}) |\n"
        )
        fh.write("| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |\n\n")
        fh.write(
            "Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor "
            "$1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate; `p2` min price "
            "$5→$2; `sma16`/`sma12` close-above-SMA50 threshold 20%→16%/12%; `adr2.5` ADR%(20) floor "
            "3.0%→2.5%.\n\n"
        )
        fh.write("## Results\n\n```text\n")
        fh.write(table)
        fh.write("\n```\n\n")
        fh.write("## F/mo gain per unit of Sortino given up\n\n")
        fh.write(findings)
        fh.write("\n\n## Caveats\n\n")
        fh.write(
            "- Same survivorship/static-market-cap caveats as the v4 backtest (see "
            "docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants "
            "lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the "
            "snapshot are over-represented, so treat their gains as a ceiling.\n"
            "- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels "
            "are not directly comparable across the two docs — compare variants against the baseline row of "
            "THIS table.\n"
            "- Single 366d hold only; relaxations may rank differently at 91d/184d.\n"
        )
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
