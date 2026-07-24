#!/usr/bin/env python3
"""
Dynamic cohort ranking for bk50d_s15_v1.3_roc100 (366d hold).

Estimates the probability that a signal succeeds (trade return > 0 at the 366d exit)
from the per-dimension cohort statistics of the existing cohort studies (ADR%,
ADR compression, RSI(14), entry price, vol surge, ROC252). For each signal the
per-dimension probability is the Win% of its cohort computed WALK-FORWARD — only
from s15 trades whose 366d hold completed before the signal date (expanding window,
no look-ahead) — shrunk toward the running pool win rate:
    p_hat = (wins + K_SHRINK * p0) / (n + K_SHRINK)
The composite score averages the per-dimension log-odds:
    P = sigmoid(mean_d(ln(p_hat_d / (1 - p_hat_d))))
Scoring starts once WARMUP_TRADES completed trades exist; earlier signals are
excluded from validation. Validation: decile table (by P) with calibration
(PredP% vs realized Win%) and monotonicity check.

All standardized v1.3 filters applied (vol_dry_up<90%, no tight_range).
Period: 2015-01-01 – 2026-06-26  (burn-in from 2013-01-01)

References: docs/research/qullamaggie-backtest-v4.md and the cohort studies in
docs/research/result-qullamaggie-{adr,adr-compression,rsi,price,volsurge,roc}-cohorts.md
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.config.settings import Settings

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.90
VOL_SURGE_MAX = 2.0
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
ROC_CAP = 1.00
MIN_NEG = 5

STRATEGY_LABEL = "bk50d_s15_v1.3_roc100"
SMA_T = 0.15

K_SHRINK = 20.0
WARMUP_TRADES = 300
N_DECILES = 10

# Cohort boundaries reused from the cohort studies. RSI uses the fine partition
# ([40-50) and [50-60) instead of the study's overlapping [40-60) row) so bins
# are disjoint. Values outside every bin (e.g. ADR% in the study's [7.0-8.0)
# gap) fall back to the running pool win rate via n=0 shrinkage.
COHORTS: dict[str, list[tuple[float, float]]] = {
    "adr": [
        (0.000, 0.010),
        (0.010, 0.020),
        (0.020, 0.025),
        (0.025, 0.030),
        (0.030, 0.035),
        (0.035, 0.040),
        (0.040, 0.045),
        (0.045, 0.050),
        (0.050, 0.070),
        (0.080, float("inf")),
    ],
    "comp": [
        (float("-inf"), 0.5),
        (0.5, 0.7),
        (0.7, 0.8),
        (0.8, 0.9),
        (0.9, 1.0),
        (1.0, 1.3),
        (1.3, float("inf")),
    ],
    "rsi": [
        (0.0, 20.0),
        (20.0, 40.0),
        (40.0, 50.0),
        (50.0, 60.0),
        (60.0, 70.0),
        (70.0, 75.0),
        (75.0, 80.0),
        (80.0, 90.0),
        (90.0, 100.001),
    ],
    "price": [
        (0.0, 5.0),
        (5.0, 10.0),
        (10.0, 20.0),
        (20.0, 50.0),
        (50.0, 100.0),
        (100.0, 250.0),
        (250.0, 700.0),
        (700.0, 2000.0),
        (2000.0, float("inf")),
    ],
    "vsurge": [
        (0.00, 0.70),
        (0.70, 0.80),
        (0.80, 0.90),
        (0.90, 1.00),
        (1.00, 1.10),
        (1.10, 1.20),
        (1.20, 1.30),
        (1.30, 1.40),
        (1.40, 1.60),
        (1.60, 2.00),
        (2.00, 3.00),
        (3.00, 4.00),
        (4.00, 6.00),
        (6.00, float("inf")),
    ],
    "roc": [
        (float("-inf"), -0.20),
        (-0.20, 0.00),
        (0.00, 0.20),
        (0.20, 0.40),
        (0.40, 0.60),
        (0.60, 0.80),
        (0.80, 1.00),
        (1.00, 1.20),
        (1.20, 1.40),
        (1.40, 1.60),
        (1.60, float("inf")),
    ],
}
DIMS = list(COHORTS.keys())

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohort-ranking.md"


# ── Data loading ─────────────────────────────────────────────────────────────


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= '2012-06-01'
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
    sql = """
        SELECT db.symbol,
               db.date::date    AS date,
               db.close::float8 AS close,
               db.high::float8  AS high,
               db.low::float8   AS low,
               db.volume::int8  AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= '2013-01-01'
          AND  db.close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    return pl.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "date": pl.Series([r[1] for r in rows], dtype=pl.Date),
            "close": [float(r[2]) for r in rows],
            "high": [float(r[3]) for r in rows],
            "low": [float(r[4]) for r in rows],
            "volume": [int(r[5]) for r in rows],
        }
    )


# ── Indicators ───────────────────────────────────────────────────────────────


def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
            ((pl.col("high") - pl.col("low")) / pl.col("low")).shift(1).over("symbol").alias("_rp1"),
        ]
    )
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
            (pl.col("volume").cast(pl.Float64) / pl.col("avg_vol_50")).alias("vol_surge_ratio"),
        ]
    )
    return df.drop(["_c1", "_v1", "_rp1", "_adr10", "_adr50", "_c_252d"])


# ── Signal generation (all v1.3 filters) ─────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
            & (pl.col("date") <= EVAL_END)
            & pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & pl.col("adr_pct").is_not_null()
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("close") > MIN_PRICE)
            & (pl.col("close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("roc_252d") < ROC_CAP)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "close", "adr_pct", "adr_pct_change", "rsi14", "vol_surge_ratio", "roc_252d"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            rows_out.append(row)
            last_trigger[sym] = d
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runner ──────────────────────────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
    """Completed 366d trades with entry/exit day ints and the six ranking features."""
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
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        ret = float((closes[idx_exit] - closes[idx_entry]) / closes[idx_entry])
        records.append(
            {
                "entry": entry_int,
                "exit": int(dates[idx_exit]),
                "ret": ret,
                "features": {
                    "adr": row["adr_pct"],
                    "comp": row["adr_pct_change"],
                    "rsi": row["rsi14"],
                    "price": row["close"],
                    "vsurge": row["vol_surge_ratio"],
                    "roc": row["roc_252d"],
                },
            }
        )
    return records


# ── Walk-forward scoring ──────────────────────────────────────────────────────


def cohort_index(dim: str, value: float) -> int | None:
    for i, (lo, hi) in enumerate(COHORTS[dim]):
        if lo <= value < hi:
            return i
    return None


def score_walk_forward(records: list[dict]) -> list[dict]:
    """Score each trade from cohort stats of trades completed before its entry date.

    Returns the subset of `records` that were scored (pool >= WARMUP_TRADES at entry),
    each with a `p` key added.
    """
    by_entry = sorted(records, key=lambda r: r["entry"])
    by_exit = sorted(records, key=lambda r: r["exit"])

    wins: dict[str, list[int]] = {d: [0] * len(COHORTS[d]) for d in DIMS}
    counts: dict[str, list[int]] = {d: [0] * len(COHORTS[d]) for d in DIMS}
    pool_wins = 0
    pool_n = 0

    scored: list[dict] = []
    j = 0
    for rec in by_entry:
        while j < len(by_exit) and by_exit[j]["exit"] < rec["entry"]:
            done = by_exit[j]
            win = 1 if done["ret"] > 0 else 0
            pool_wins += win
            pool_n += 1
            for dim in DIMS:
                idx = cohort_index(dim, done["features"][dim])
                if idx is not None:
                    wins[dim][idx] += win
                    counts[dim][idx] += 1
            j += 1
        if pool_n < WARMUP_TRADES:
            continue
        p0 = pool_wins / pool_n
        logits = []
        for dim in DIMS:
            idx = cohort_index(dim, rec["features"][dim])
            w, n = (wins[dim][idx], counts[dim][idx]) if idx is not None else (0, 0)
            p_hat = (w + K_SHRINK * p0) / (n + K_SHRINK)
            p_hat = min(max(p_hat, 1e-6), 1.0 - 1e-6)
            logits.append(np.log(p_hat / (1.0 - p_hat)))
        mean_logit = float(np.mean(logits))
        p = float(1.0 / (1.0 + np.exp(-mean_logit)))
        # regime-neutral score: feature contribution relative to the running pool
        # win rate, so time drift in p0 cannot dominate the cross-sectional ranking
        rel = mean_logit - float(np.log(p0 / (1.0 - p0)))
        p_rel = float(1.0 / (1.0 + np.exp(-rel)))
        scored.append({**rec, "p": p, "p_rel": p_rel})
    return scored


# ── Metrics ───────────────────────────────────────────────────────────────────


def compute_metrics(rets: np.ndarray) -> dict | None:
    n = len(rets)
    if n < 5:
        return None
    neg = rets[rets < 0]
    sr = float("nan")
    if len(neg) >= MIN_NEG:
        dd = float(np.sqrt(np.mean(neg**2)))
        if dd > 0:
            sr = float(np.mean(rets) * np.sqrt(365 / HOLD_CAL) / dd)
    gross_win = float(rets[rets > 0].sum())
    gross_loss = float(-rets[rets < 0].sum())
    return {
        "n": n,
        "med": float(np.median(rets) * 100),
        "mean": float(rets.mean() * 100),
        "win": float((rets > 0).mean() * 100),
        "sr": sr,
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
    }


# ── Output ────────────────────────────────────────────────────────────────────

_COL_HDR = f"{'Decile':<10}  {'PredP%':>6}  {'N':>5}  {'Med%':>7}  {'Mean%':>7}  {'Win%':>6}  {'Sortino':>8}  {'PF':>6}"
_COL_SEP = "─" * len(_COL_HDR)


def fmt_decile_row(label: str, pred_p: float, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not (isinstance(m["sr"], float) and np.isnan(m["sr"])) else "     n/a"
    return f"{label:<10}  {pred_p:>6.1f}  {m['n']:>5}  {m['med']:>+7.2f}  {m['mean']:>+7.2f}  {m['win']:>6.1f}  {sr_str}  {m['pf']:>6.2f}"


def build_decile_table(scored: list[dict], key: str, title: str) -> list[str]:
    lines = [f"### {STRATEGY_LABEL} — {title} (D1 = lowest, D{N_DECILES} = highest)", "", _COL_HDR, _COL_SEP]
    by_score = sorted(scored, key=lambda r: r[key])
    buckets = np.array_split(np.arange(len(by_score)), N_DECILES)
    win_series: list[float] = []
    for d, idxs in enumerate(buckets, start=1):
        rows = [by_score[i] for i in idxs]
        rets = np.array([r["ret"] for r in rows])
        pred_p = float(np.mean([r[key] for r in rows]) * 100)
        m = compute_metrics(rets)
        if m:
            lines.append(fmt_decile_row(f"D{d}", pred_p, m))
            win_series.append(m["win"])
    lines.append(_COL_SEP)
    m_all = compute_metrics(np.array([r["ret"] for r in by_score]))
    if m_all:
        pred_all = float(np.mean([r[key] for r in by_score]) * 100)
        lines.append(fmt_decile_row("ALL", pred_all, m_all))
    lines.append("")
    increases = sum(1 for a, b in zip(win_series, win_series[1:], strict=False) if b >= a)
    lines.append(f"Win% monotonicity: {increases}/{len(win_series) - 1} decile steps non-decreasing")
    lines.append("")
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()

    print("Loading SPY regime …", flush=True)
    bull_dates = load_spy_regime(settings.engine)

    print("Loading bars …", flush=True)
    df = load_bars(settings.engine)
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)

    print(f"Generating signals for {STRATEGY_LABEL} …", flush=True)
    signals = get_signals(df, bull_dates, SMA_T)
    print(f"  {len(signals)} signals", flush=True)

    records = run_trades(signals, sym_dates, sym_closes)
    print(f"  {len(records)} completed 366d trades", flush=True)

    scored = score_walk_forward(records)
    first_scored = _EPOCH.fromordinal(_EPOCH.toordinal() + min(r["entry"] for r in scored)) if scored else None

    header = (
        f"Dynamic cohort ranking | {STRATEGY_LABEL} | Hold: {HOLD_CAL}d | "
        f"Period: {EVAL_START} – {EVAL_END}\n"
        f"P(success) = sigmoid(mean log-odds of walk-forward cohort Win% across "
        f"ADR%, compression, RSI14, price, vol_surge, ROC252)\n"
        f"Shrinkage k={K_SHRINK:.0f} toward running pool win rate | warm-up: {WARMUP_TRADES} completed trades\n"
        f"Completed trades: {len(records)} | scored (post warm-up): {len(scored)}"
        + (f" | first scored entry: {first_scored}" if first_scored else "")
        + "\n"
    )
    print("\n" + header)

    all_lines: list[str] = [header]
    for key, title in [
        ("p", "walk-forward P(success) deciles"),
        ("p_rel", "regime-neutral (pool-relative) score deciles"),
    ]:
        table_lines = build_decile_table(scored, key, title)
        all_lines.extend(table_lines)
        for line in table_lines:
            print(line)

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Dynamic Cohort Ranking (s15)\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
