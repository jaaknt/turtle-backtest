#!/usr/bin/env python3
"""
Relaxation sweep for bk50d_s20_v1.2_roc100 / 366d hold.

Goal: increase signals per month (F/mo) without degrading Sortino and Mean%.
Each variant relaxes exactly ONE dimension of the baseline (all other filters
unchanged); the best 2 and 3 quality-preserving relaxations are then combined.

Baseline filters match scripts/qullamaggie-backtest-v4.py (tight_range and
sma_alignment disabled): vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x, RSI<70,
ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K,
cooldown 30d, mcap>=1.5B excl Comm/RE.

Variants: cd15 (cooldown 15d), p3 (min price $3), mcap1.0B (mcap floor $1.0B),
sect+CommRE (re-admit Comm Services/Real Estate).

Eval: 2015-01-01 – 2026-06-26 | 366d calendar hold | bars loaded from 2013-01-01
References: docs/research/qullamaggie-backtest-v4.md,
            docs/research/result-qullamaggie-backtest-v4.md,
            docs/research/result-qullamaggie-tightrange-cohorts.md,
            docs/research/result-qullamaggie-price-cohorts.md
"""

import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
BAR_LOAD_START = date(2013, 1, 1)
HOLD_CAL = 366
MIN_AVG_VOL = 500_000
MAX_PRICE = 250.0
MIN_HISTORY = 300
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
SMA_T = 0.20
MIN_NEG = 10
EXCLUDED_SECTORS = ("Communication Services", "Real Estate")

# Baseline parameter values; each variant overrides exactly one.
BASE_PARAMS = {"cooldown": 30, "min_price": 5.0, "min_mcap": 1.5e9, "include_comm_re": False, "vol_dry_up": 0.90}

VARIANTS: list[tuple[str, dict]] = [
    ("cd15", {"cooldown": 15}),
    ("p3", {"min_price": 3.0}),
    ("mcap1.0B", {"min_mcap": 1.0e9}),
    ("sect+CommRE", {"include_comm_re": True}),
]

# "Same level" tolerance for the combo-selection quality gate.
QUALITY_TOL = 0.95

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-relax-sweep.md"


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= '2012-01-01'
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    spy = pl.DataFrame(
        {
            "date": pl.Series([r[0] for r in rows], dtype=pl.Date),
            "close": [float(r[1]) for r in rows],
        }
    )
    spy = spy.with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
    return set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())


def load_bars(engine: sa.Engine) -> pl.DataFrame:
    """Load bars for the LOOSEST universe (mcap >= 1.0B, all sectors); per-variant
    universe constraints are applied later via the symbol metadata, so the DB is
    hit only once. close/high/low are split/dividend-adjusted (adjusted_close/close
    scaling), raw_close kept for the point-in-time price band — same methodology as
    scripts/qullamaggie-backtest-v4.py."""
    sql = """
        SELECT db.symbol,
               db.date::date             AS date,
               db.close::float8          AS raw_close,
               db.adjusted_close::float8 AS close,
               db.high::float8           AS high,
               db.low::float8            AS low,
               db.volume::int8           AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 1000000000
          AND  db.date >= :start
          AND  db.close > 0
          AND  db.adjusted_close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"start": BAR_LOAD_START}).fetchall()
    factor = [float(r[3]) / float(r[2]) for r in rows]  # adjusted_close / raw_close
    return pl.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "date": pl.Series([r[1] for r in rows], dtype=pl.Date),
            "raw_close": [float(r[2]) for r in rows],
            "close": [float(r[3]) for r in rows],
            "high": [float(r[4]) * f for r, f in zip(rows, factor, strict=True)],
            "low": [float(r[5]) * f for r, f in zip(rows, factor, strict=True)],
            "volume": [int(r[6]) for r in rows],
        }
    )


def load_symbol_meta(engine: sa.Engine) -> dict[str, tuple[float, str]]:
    """symbol -> (market_cap, sector) for per-variant universe filtering."""
    sql = """
        SELECT t.code, c.market_cap::float8, c.sector
        FROM   turtle.ticker t
        JOIN   turtle.company c ON c.ticker_code = t.code
        WHERE  t.country = 'USA' AND t.type = 'Common Stock' AND c.market_cap >= 1000000000
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    return {r[0]: (float(r[1]), r[2] or "") for r in rows}


def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
            ((pl.col("high") - pl.col("low")) / pl.col("low")).shift(1).over("symbol").alias("_rp1"),
        ]
    )
    # RSI(14)
    df = df.with_columns(pl.col("_c1").diff(1).over("symbol").alias("_diff"))
    df = df.with_columns(
        [
            pl.when(pl.col("_diff") > 0).then(pl.col("_diff")).otherwise(0.0).alias("_gain"),
            pl.when(pl.col("_diff") < 0).then(-pl.col("_diff")).otherwise(0.0).alias("_loss"),
        ]
    )
    df = df.with_columns(
        [
            pl.col("_gain").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_gain"),
            pl.col("_loss").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_loss"),
        ]
    )
    df = df.with_columns((100.0 - 100.0 / (1.0 + pl.col("_avg_gain") / pl.col("_avg_loss"))).alias("rsi14"))
    df = df.drop(["_diff", "_gain", "_loss", "_avg_gain", "_avg_loss"])
    df = df.with_columns(
        [
            pl.col("_c1").rolling_mean(50, min_samples=50).over("symbol").alias("sma50"),
            pl.col("_v1").rolling_mean(50, min_samples=50).over("symbol").alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(20, min_samples=20).over("symbol").alias("avg_vol_20"),
            pl.col("_v1").rolling_mean(10, min_samples=10).over("symbol").alias("avg_vol_10"),
            pl.col("_c1").rolling_max(50, min_samples=50).over("symbol").alias("max_c_50d"),
            pl.col("_rp1").rolling_mean(20, min_samples=20).over("symbol").alias("adr_pct"),
            pl.col("_rp1").rolling_mean(10, min_samples=10).over("symbol").alias("_adr10"),
            pl.col("_rp1").rolling_mean(50, min_samples=50).over("symbol").alias("_adr50"),
            pl.col("_c1").shift(251).over("symbol").alias("_c_252d"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr10") / pl.col("_adr50")).alias("adr_pct_change"),
            (pl.col("close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
        ]
    )
    return df.drop(["_c1", "_v1", "_rp1", "_adr10", "_adr50", "_c_252d"])


def get_signals(df: pl.DataFrame, bull_dates: set[date], allowed_syms: set[str], params: dict) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
            & pl.col("symbol").is_in(list(allowed_syms))
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > params["min_price"])
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > SMA_T)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < params["vol_dry_up"] * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    cooldown = params["cooldown"]
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > cooldown:
            rows_out.append(row)
            last_trigger[sym] = d
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


def run_trades(signals: pl.DataFrame, sym_dates: dict[str, np.ndarray], sym_closes: dict[str, np.ndarray]) -> list[dict]:
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        entry_int = (row["date"] - _EPOCH).days
        idx_entry = int(np.searchsorted(dates, entry_int))
        if idx_entry >= len(dates) or dates[idx_entry] != entry_int:
            continue
        if dates[-1] < entry_int + HOLD_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        window = closes[idx_entry : idx_exit + 1]
        ret = float((closes[idx_exit] - closes[idx_entry]) / closes[idx_entry])
        running_max = np.maximum.accumulate(window)
        mdd = float((1.0 - window / running_max).max())
        records.append({"ret": ret, "mdd": mdd})
    return records


def compute_metrics(records: list[dict]) -> dict:
    a = np.array([r["ret"] for r in records])
    months = (EVAL_END.year - EVAL_START.year) * 12 + (EVAL_END.month - EVAL_START.month)
    downside = np.where(a < 0, a, 0.0)
    dd = float(np.sqrt(np.mean(downside**2)))
    neg = a[a < 0]
    sr = float(np.mean(a) * np.sqrt(365 / HOLD_CAL) / dd) if dd > 0 and len(neg) >= MIN_NEG else float("nan")
    gross_win = float(a[a > 0].sum())
    gross_loss = float(-a[a < 0].sum())
    mdds = np.array([r["mdd"] for r in records])
    return {
        "n": len(a),
        "freq": len(a) / max(months, 1),
        "win": float((a > 0).mean() * 100),
        "mean": float(a.mean() * 100),
        "med": float(np.median(a) * 100),
        "sr": sr,
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
        "mdd": float(mdds.mean() * 100),
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

    print("Loading SPY regime …", flush=True)
    bull_dates = load_spy_regime(settings.engine)

    print("Loading bars (loosest universe: mcap>=1.0B, all sectors) …", flush=True)
    df = load_bars(settings.engine)
    meta = load_symbol_meta(settings.engine)
    valid_syms = set(df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"].to_list())
    df = df.filter(pl.col("symbol").is_in(list(valid_syms)))
    print(f"  {df.height:,} bars, {len(valid_syms):,} symbols", flush=True)

    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)

    def universe(params: dict) -> set[str]:
        return {
            sym
            for sym in valid_syms
            if sym in meta and meta[sym][0] >= params["min_mcap"] and (params["include_comm_re"] or meta[sym][1] not in EXCLUDED_SECTORS)
        }

    def run_variant(label: str, params: dict) -> dict:
        print(f"  {label} …", flush=True)
        signals = get_signals(df, bull_dates, universe(params), params)
        records = run_trades(signals, sym_dates, sym_closes)
        m = compute_metrics(records)
        print(f"    {fmt_row(label, m)}", flush=True)
        return m

    print("Running baseline + single-dimension variants …", flush=True)
    base_m = run_variant("baseline (bk50d_s20_v1.2_roc100)", BASE_PARAMS)
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
    table_lines = [_HDR, _SEP, fmt_row("baseline (bk50d_s20_v1.2_roc100)", base_m)]
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
        fh.write("# Qullamaggie Relax Sweep — bk50d_s20_v1.2_roc100 / 366d\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Eval period | {EVAL_START} – {EVAL_END} |\n")
        fh.write(f"| Hold | {HOLD_CAL}d (calendar); entries without {HOLD_CAL}d of forward data skipped |\n")
        fh.write("| Baseline | bk50d_s20_v1.2_roc100: 50d-high breakout, close >20% above SMA50 |\n")
        fh.write(
            "| Baseline fixed filters | vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, "
            "ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, "
            "mcap>=1.5B excl Comm/RE |\n"
        )
        fh.write("| Variants | each relaxes exactly one dimension (see table) |\n")
        fh.write(
            f"| Combo selection | variants with Sortino AND Mean% >= {QUALITY_TOL:.0%} of baseline, "
            f"ranked by F/mo; top-2 and top-3 combined (qualified: {quality_note}) |\n"
        )
        fh.write("| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |\n\n")
        fh.write(
            "Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor "
            "$1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate.\n\n"
        )
        fh.write("## Results\n\n```\n")
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
