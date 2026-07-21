#!/usr/bin/env python3
"""
Out-of-sample validation of QullamaggieRanking's weighted-points score.

Uses bk50d_s15_v1.3_roc100 (366d hold) signals, 2015-01-01 - 2026-06-26 -- the same
reference config/period used to derive the production band tables in
turtlex/strategy/ranking/qullamaggie.py. Filters/indicators match
scripts/qullamaggie-backtest-v4.py exactly (RSI<70, ADR mean-of-ratios>=3.0%,
ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, SPY>200d SMA,
close>$5&<$250, avg_vol>=500K; tight_range and sma_alignment disabled).

Genuine train/test split (not expanding-window re-fit): signals entered before
SPLIT_DATE are used to *independently refit* reachable-only Sortino-by-bucket band
tables (same methodology as the production bands: weight-spread proportional across
price/ADR/compression/ROC252/RSI, SMA50 fixed at 50), then those refit bands score the
held-out signals entered on/after SPLIT_DATE. This directly tests whether the ranking
methodology would have separated forward returns using only evidence available before
the test period -- not just that it matches same-period cohort tables.

Held-out signals are also scored with (a) the actual production bands (fit on the full
2015-2026 period, so not strictly out-of-sample, but useful as "how the shipped ranking
performs on the most recent slice") and (b) the pre-change legacy 4-dimension bands, as
a baseline to beat.
"""

from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.config.settings import Settings
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2015, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
SPLIT_DATE = date(2021, 1, 1)  # train: entry_date < SPLIT_DATE, held-out: entry_date >= SPLIT_DATE
SMA_T = 0.15  # bk50d_s15 -- the same reference config used to derive the production bands

MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_DRY_UP = 0.90
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MIN_NEG = 10  # min negative-return trades in a bucket to trust its Sortino when refitting
N_DECILES = 10

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-ranking-validation.md"

# ── Reachable-only bucket boundaries (upper bounds, ascending) -- shared across the
# refit-on-train, production, and legacy scorers so all three are scored on the same grid ──
PRICE_BOUNDS = [10.0, 20.0, 50.0, 100.0, 250.0]
ADR_BOUNDS = [0.035, 0.04, 0.045, 0.05, 0.08]
COMPRESSION_BOUNDS = [0.7, 0.8, 0.9]
ROC_BOUNDS = [-0.20, 0.0, 0.20, 0.40, 0.60, 0.80, 1.00]
RSI_BOUNDS = [50.0, 60.0, 70.0]

# Production bands (turtlex/strategy/ranking/qullamaggie.py, fit on the full 2015-2026 period)
PROD_ADR = ([0, 0, 3, 4, 8], 12)
PROD_COMPRESSION = ([12, 0, 1], 0)
PROD_PRICE = ([13, 4, 1, 1, 0], 0)
PROD_ROC = ([10, 6, 5, 8, 10, 5, 0], 0)
PROD_RSI = ([3, 2, 0], 0)
PROD_SMA50_BOUNDS = [0.10, 0.12, 0.15, 0.17, 0.20, 0.30]
PROD_SMA50 = ([0, 12, 22, 31, 17, 44], 50)

# Legacy bands (pre-change, v1.2-era; ADR/compression/price only, no ROC/RSI dimensions)
LEGACY_ADR_BOUNDS = [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.08]
LEGACY_ADR = ([0, 2, 3, 4, 4, 8, 9, 13], 15)
LEGACY_COMPRESSION_BOUNDS = [0.7, 0.8, 0.9, 1.0]
LEGACY_COMPRESSION = ([14, 4, 4, 2], 0)
LEGACY_PRICE_BOUNDS = [5.0, 10.0, 20.0, 50.0, 100.0, 250.0]
LEGACY_PRICE = ([19, 21, 11, 9, 9, 6], 0)
LEGACY_SMA50_BOUNDS = PROD_SMA50_BOUNDS
LEGACY_SMA50 = PROD_SMA50


def bucket_index(value: float | None, bounds: list[float]) -> int | None:
    if value is None:
        return None
    for i, b in enumerate(bounds):
        if value < b:
            return i
    return len(bounds)


def score_from_bands(idx: int | None, points: list[int], top: int) -> int:
    if idx is None:
        return 0
    return points[idx] if idx < len(points) else top


# ── Data loading (identical to qullamaggie-backtest-v4.py) ─────────────────────


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8 FROM turtle.daily_bars
        WHERE symbol = 'SPY.US' AND date >= '2012-06-01' ORDER BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    spy = pl.DataFrame({"date": pl.Series([r[0] for r in rows], dtype=pl.Date), "close": [float(r[1]) for r in rows]})
    spy = spy.with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
    return set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())


def load_bars(engine: sa.Engine) -> pl.DataFrame:
    sql = """
        SELECT db.symbol, db.date::date AS date, db.close::float8 AS raw_close,
               db.adjusted_close::float8 AS close, db.high::float8 AS high,
               db.low::float8 AS low, db.volume::int8 AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA' AND t.type = 'Common Stock'
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= '2013-01-01' AND db.close > 0 AND db.adjusted_close > 0 AND db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    factor = [float(r[3]) / float(r[2]) for r in rows]
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
        ]
    )
    return df.drop(["_c1", "_v1", "_rp1", "_adr10", "_adr50", "_c_252d"])


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
            & (pl.col("rsi14") < RSI_CAP)
            & (pl.col("raw_close") > MIN_PRICE)
            & (pl.col("raw_close") < MAX_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("adr_pct") >= ADR_MIN)
            & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
            & (pl.col("close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "raw_close", "adr_pct", "adr_pct_change", "pct_vs_sma50", "roc_252d", "rsi14"])
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
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        ret = float((closes[idx_exit] - closes[idx_entry]) / closes[idx_entry])
        records.append({**row, "ret": ret})
    return records


# ── Refit bands on a training slice ─────────────────────────────────────────────


def sortino_by_bucket(records: list[dict], column: str, bounds: list[float]) -> dict[int, float]:
    buckets: dict[int, list[float]] = defaultdict(list)
    for r in records:
        idx = bucket_index(r.get(column), bounds)
        if idx is not None:
            buckets[idx].append(r["ret"])
    out: dict[int, float] = {}
    for idx, rets in buckets.items():
        a = np.array(rets)
        neg = a[a < 0]
        if len(neg) < MIN_NEG:
            continue
        dd = float(np.sqrt(np.mean(neg**2)))
        if dd > 0:
            out[idx] = float(np.mean(a) * np.sqrt(365 / HOLD_CAL) / dd)
    return out


def rescale(sortino: dict[int, float], n_buckets: int, weight: int) -> list[int]:
    if not sortino:
        return [0] * n_buckets
    lo, hi = min(sortino.values()), max(sortino.values())
    rng = hi - lo
    return [round(weight * (sortino.get(i, lo) - lo) / rng) if rng > 0 else 0 for i in range(n_buckets)]


def refit_bands(train_records: list[dict]) -> dict[str, tuple[list[int], int]]:
    """Independently re-derive weights (proportional to reachable Sortino spread) and
    points for the five secondary dimensions from train_records only. SMA50 stays fixed
    at weight 50 (matching the production 'by design' choice), its bands also refit."""
    dims = {
        "price": ("raw_close", PRICE_BOUNDS),
        "adr": ("adr_pct", ADR_BOUNDS),
        "compression": ("adr_pct_change", COMPRESSION_BOUNDS),
        "roc": ("roc_252d", ROC_BOUNDS),
        "rsi": ("rsi14", RSI_BOUNDS),
    }
    sortino_tables = {name: sortino_by_bucket(train_records, col, bounds) for name, (col, bounds) in dims.items()}
    spreads = {name: (max(t.values()) - min(t.values())) if t else 0.0 for name, t in sortino_tables.items()}
    total = sum(spreads.values())
    raw_weights = {name: 50.0 * s / total if total > 0 else 0.0 for name, s in spreads.items()}
    weights = {name: round(w) for name, w in raw_weights.items()}
    drift = 50 - sum(weights.values())
    if drift != 0 and raw_weights:
        key = max(raw_weights, key=lambda k: abs(raw_weights[k] - weights[k]))
        weights[key] += drift

    result: dict[str, tuple[list[int], int]] = {}
    for name, (_col, bounds) in dims.items():
        n = len(bounds) + 1
        pts = rescale(sortino_tables[name], n, weights[name])
        result[name] = (pts[:-1], pts[-1])  # (explicit bands, top_points)

    sma50_sortino = sortino_by_bucket(train_records, "pct_vs_sma50", PROD_SMA50_BOUNDS)
    sma50_pts = rescale(sma50_sortino, len(PROD_SMA50_BOUNDS) + 1, 50)
    result["sma50"] = (sma50_pts[:-1], sma50_pts[-1])
    return result


# ── Scoring ──────────────────────────────────────────────────────────────────────


def score_dynamic(r: dict, bands: dict[str, tuple[list[int], int]]) -> int:
    price_pts, price_top = bands["price"]
    adr_pts, adr_top = bands["adr"]
    comp_pts, comp_top = bands["compression"]
    roc_pts, roc_top = bands["roc"]
    rsi_pts, rsi_top = bands["rsi"]
    sma_pts, sma_top = bands["sma50"]
    return (
        score_from_bands(bucket_index(r.get("raw_close"), PRICE_BOUNDS), price_pts, price_top)
        + score_from_bands(bucket_index(r.get("adr_pct"), ADR_BOUNDS), adr_pts, adr_top)
        + score_from_bands(bucket_index(r.get("adr_pct_change"), COMPRESSION_BOUNDS), comp_pts, comp_top)
        + score_from_bands(bucket_index(r.get("roc_252d"), ROC_BOUNDS), roc_pts, roc_top)
        + score_from_bands(bucket_index(r.get("rsi14"), RSI_BOUNDS), rsi_pts, rsi_top)
        + score_from_bands(bucket_index(r.get("pct_vs_sma50"), PROD_SMA50_BOUNDS), sma_pts, sma_top)
    )


def score_production(r: dict) -> int:
    ranker = QullamaggieRanking()
    df = pl.DataFrame(
        [
            {
                "date": date(2000, 1, 1),
                "close": r["raw_close"],
                "adr_pct": r["adr_pct"],
                "adr_pct_change": r["adr_pct_change"],
                "pct_vs_sma50": r["pct_vs_sma50"],
                "roc_252d": r["roc_252d"],
                "rsi14": r["rsi14"],
            }
        ]
    )
    return ranker.ranking(df, date(2000, 1, 1))


def score_legacy(r: dict) -> int:
    price_pts, price_top = LEGACY_PRICE
    adr_pts, adr_top = LEGACY_ADR
    comp_pts, comp_top = LEGACY_COMPRESSION
    sma_pts, sma_top = LEGACY_SMA50
    return (
        score_from_bands(bucket_index(r.get("raw_close"), LEGACY_PRICE_BOUNDS), price_pts, price_top)
        + score_from_bands(bucket_index(r.get("adr_pct"), LEGACY_ADR_BOUNDS), adr_pts, adr_top)
        + score_from_bands(bucket_index(r.get("adr_pct_change"), LEGACY_COMPRESSION_BOUNDS), comp_pts, comp_top)
        + score_from_bands(bucket_index(r.get("pct_vs_sma50"), LEGACY_SMA50_BOUNDS), sma_pts, sma_top)
    )


# ── Decile reporting ─────────────────────────────────────────────────────────────


def compute_deciles(records: list[dict], scores: list[int]) -> list[dict]:
    """Bucket records into N_DECILES equal-size groups by ascending score, D1=lowest."""
    order = np.argsort(scores)
    n = len(records)
    edges = np.linspace(0, n, N_DECILES + 1).astype(int)
    deciles: list[dict] = []
    for d in range(N_DECILES):
        idx = order[edges[d] : edges[d + 1]]
        if len(idx) == 0:
            continue
        rets = np.array([records[i]["ret"] for i in idx])
        sc = np.array([scores[i] for i in idx])
        neg = rets[rets < 0]
        dd = float(np.sqrt(np.mean(neg**2))) if len(neg) else float("nan")
        sr = float(np.mean(rets) * np.sqrt(365 / HOLD_CAL) / dd) if dd and dd > 0 else float("nan")
        gross_win = float(rets[rets > 0].sum())
        gross_loss = float(-rets[rets < 0].sum())
        pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
        deciles.append(
            {
                "n": len(idx),
                "score": float(sc.mean()),
                "med": float(np.median(rets) * 100),
                "mean": float(rets.mean() * 100),
                "win": float((rets > 0).mean() * 100),
                "sortino": sr,
                "pf": pf,
            }
        )
    return deciles


def _monotonic_nondecreasing(values: list[float]) -> tuple[int, int]:
    """(non-decreasing steps, comparable steps) across consecutive deciles, skipping NaN pairs."""
    steps = comparable = 0
    for i in range(1, len(values)):
        a, b = values[i - 1], values[i]
        if np.isnan(a) or np.isnan(b):
            continue
        comparable += 1
        if b >= a:
            steps += 1
    return steps, comparable


def decile_table_text(deciles: list[dict], label: str) -> tuple[str, dict]:
    hdr = f"{'Decile':<8} {'Score':>7} {'N':>5} {'Med%':>8} {'Mean%':>8} {'Win%':>6} {'Sortino':>8} {'PF':>6}"
    lines = [f"### {label}", "", hdr, "-" * len(hdr)]
    for i, d in enumerate(deciles, 1):
        sr_str = f"{d['sortino']:>8.3f}" if not np.isnan(d["sortino"]) else f"{'n/a':>8}"
        lines.append(
            f"D{i:<7} {d['score']:>7.1f} {d['n']:>5} {d['med']:>+7.2f} {d['mean']:>+7.2f} {d['win']:>6.1f} {sr_str} {d['pf']:>6.2f}"
        )
    sortino_steps, sortino_n = _monotonic_nondecreasing([d["sortino"] for d in deciles])
    mean_steps, mean_n = _monotonic_nondecreasing([d["mean"] for d in deciles])
    mono = {"sortino_steps": sortino_steps, "sortino_n": sortino_n, "mean_steps": mean_steps, "mean_n": mean_n}
    lines.append("")
    lines.append(f"Sortino monotonicity: {sortino_steps}/{sortino_n} decile steps non-decreasing")
    lines.append(f"Mean% monotonicity: {mean_steps}/{mean_n} decile steps non-decreasing")
    return "\n".join(lines), mono


def decile_table(records: list[dict], scores: list[int], label: str) -> tuple[str, dict]:
    return decile_table_text(compute_deciles(records, scores), label)


def fold_spread(deciles: list[dict]) -> tuple[float, float, dict]:
    """(D10-D1 Sortino spread, D10-D1 Mean% spread, monotonicity dict) for one fold.
    Sortino/Mean% spread -- not Win% -- is the primary metric: the goal is optimizing
    Sortino and Mean%, and a scheme that widens the gap between its best and worst
    decile on those two metrics is doing its job, regardless of Win% shape."""
    d1, d10 = deciles[0], deciles[-1]
    sortino_spread = d10["sortino"] - d1["sortino"] if not (np.isnan(d10["sortino"]) or np.isnan(d1["sortino"])) else float("nan")
    mean_spread = d10["mean"] - d1["mean"]
    sortino_steps, sortino_n = _monotonic_nondecreasing([d["sortino"] for d in deciles])
    mean_steps, mean_n = _monotonic_nondecreasing([d["mean"] for d in deciles])
    mono = {"sortino_steps": sortino_steps, "sortino_n": sortino_n, "mean_steps": mean_steps, "mean_n": mean_n}
    return sortino_spread, mean_spread, mono


def bands_with_weights(records: list[dict], weights: dict[str, int]) -> dict[str, tuple[list[int], int]]:
    """Like refit_bands, but the five secondary weights are supplied rather than derived
    from records' own Sortino spread -- used to test a weight scheme fit on one slice
    (e.g. a cross-fold average) against Sortino-by-bucket points refit on another slice."""
    dims = {
        "price": ("raw_close", PRICE_BOUNDS),
        "adr": ("adr_pct", ADR_BOUNDS),
        "compression": ("adr_pct_change", COMPRESSION_BOUNDS),
        "roc": ("roc_252d", ROC_BOUNDS),
        "rsi": ("rsi14", RSI_BOUNDS),
    }
    result: dict[str, tuple[list[int], int]] = {}
    for name, (col, bounds) in dims.items():
        sortino = sortino_by_bucket(records, col, bounds)
        pts = rescale(sortino, len(bounds) + 1, weights[name])
        result[name] = (pts[:-1], pts[-1])
    sma50_sortino = sortino_by_bucket(records, "pct_vs_sma50", PROD_SMA50_BOUNDS)
    sma50_pts = rescale(sma50_sortino, len(PROD_SMA50_BOUNDS) + 1, 50)
    result["sma50"] = (sma50_pts[:-1], sma50_pts[-1])
    return result


def dimension_weight(bands: tuple[list[int], int]) -> int:
    pts, top = bands
    return max([*pts, top]) if pts or top else 0


STABILITY_SPLITS = [date(2019, 1, 1), date(2020, 1, 1), date(2021, 1, 1), date(2022, 1, 1), date(2023, 1, 1)]
SECONDARY_DIMS = ["price", "adr", "compression", "roc", "rsi"]
MIN_FOLD_N = 100  # skip a cutoff if either side has too few signals to fit/test meaningfully


def main() -> None:
    settings = Settings.from_toml()
    print("Loading SPY regime …", flush=True)
    bull_dates = load_spy_regime(settings.engine)
    print("Loading bars …", flush=True)
    df = load_bars(settings.engine)
    valid = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid.to_list()))
    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int64)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)

    print("Generating bk50d_s15_v1.3_roc100 signals …", flush=True)
    signals = get_signals(df, bull_dates, SMA_T)
    records = run_trades(signals, sym_dates, sym_closes)
    print(f"  {len(records)} total signals with 366d forward data", flush=True)

    train = [r for r in records if r["date"] < SPLIT_DATE]
    test = [r for r in records if r["date"] >= SPLIT_DATE]
    print(f"  train (entries < {SPLIT_DATE}): {len(train)}  |  held-out (entries >= {SPLIT_DATE}): {len(test)}", flush=True)

    print("Refitting bands on training slice …", flush=True)
    fitted_bands = refit_bands(train)
    for name, (pts, top) in fitted_bands.items():
        print(f"  {name}: bands={pts} top={top}")

    dyn_scores = [score_dynamic(r, fitted_bands) for r in test]
    prod_scores = [score_production(r) for r in test]
    legacy_scores = [score_legacy(r) for r in test]

    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("# Qullamaggie Ranking — Out-of-Sample Validation")
    out("")
    out(f"Run date: {date.today()}")
    out("")
    out(
        f"Reference config: bk50d_s15_v1.3_roc100 / {HOLD_CAL}d hold | Period: {EVAL_START} - {EVAL_END} | "
        f"Split date: {SPLIT_DATE} (train N={len(train)}, held-out N={len(test)})"
    )
    out("")
    out("Three scorers, all evaluated on the same held-out (entries >= split date) signals:")
    out("")
    out(
        "1. **Refit-on-train** — bands independently re-derived from training-slice-only Sortino "
        "(genuine out-of-sample test of the ranking methodology)"
    )
    out(
        "2. **Production** — the actual shipped `QullamaggieRanking` bands (fit on the full "
        "2015-2026 period, so not strictly out-of-sample here, but shows real-world behavior on "
        "the most recent slice)"
    )
    out("3. **Legacy (pre-change)** — the old 4-dimension bands (ADR/compression/price/SMA50 only, no ROC252/RSI), as the baseline to beat")

    refit_deciles = compute_deciles(test, dyn_scores)
    prod_deciles = compute_deciles(test, prod_scores)
    legacy_deciles = compute_deciles(test, legacy_scores)

    refit_table, refit_mono = decile_table_text(refit_deciles, "Refit-on-train (out-of-sample)")
    out("")
    out("```text")
    out(refit_table)
    out("```")

    prod_table, prod_mono = decile_table_text(prod_deciles, "Production bands (reference)")
    out("")
    out("```text")
    out(prod_table)
    out("```")

    legacy_table, legacy_mono = decile_table_text(legacy_deciles, "Legacy pre-change bands (baseline)")
    out("")
    out("```text")
    out(legacy_table)
    out("```")

    refit_sr, refit_mean_sp, _ = fold_spread(refit_deciles)
    prod_sr, prod_mean_sp, _ = fold_spread(prod_deciles)
    legacy_sr, legacy_mean_sp, _ = fold_spread(legacy_deciles)

    out("")
    out("## Summary")
    out("")
    out(
        "D10-D1 spread is the primary metric here -- the goal is optimizing Sortino and Mean%, "
        "so a scheme that widens the gap between its best and worst decile on those two is doing "
        "its job; Win% is reported in the tables above for context only, not used to judge fit."
    )
    out("")
    out(
        f"- Refit-on-train: Sortino spread={refit_sr:.3f}, Mean% spread={refit_mean_sp:+.1f}, "
        f"Sortino mono={refit_mono['sortino_steps']}/{refit_mono['sortino_n']}, "
        f"Mean% mono={refit_mono['mean_steps']}/{refit_mono['mean_n']}"
    )
    out(
        f"- Production: Sortino spread={prod_sr:.3f}, Mean% spread={prod_mean_sp:+.1f}, "
        f"Sortino mono={prod_mono['sortino_steps']}/{prod_mono['sortino_n']}, "
        f"Mean% mono={prod_mono['mean_steps']}/{prod_mono['mean_n']}"
    )
    out(
        f"- Legacy: Sortino spread={legacy_sr:.3f}, Mean% spread={legacy_mean_sp:+.1f}, "
        f"Sortino mono={legacy_mono['sortino_steps']}/{legacy_mono['sortino_n']}, "
        f"Mean% mono={legacy_mono['mean_steps']}/{legacy_mono['mean_n']}"
    )

    # ── Weight-split stability across multiple periods ──────────────────────────
    out("")
    out("## Weight-Split Stability Across Multiple Periods")
    out("")
    out(
        "Tests whether the production weight split (price=13, adr=12, compression=12, roc=10, "
        "rsi=3) reflects a stable pattern or is sensitive to the single 2021 split date used "
        "above. For each cutoff below, weights are independently refit on signals entered before "
        "it (same reachable-Sortino-spread methodology as the production bands), with no "
        "reference to the production numbers."
    )
    out("")

    print("\nTesting weight-split stability across multiple cutoffs …", flush=True)
    per_fold_weights: list[tuple[date, dict[str, int]]] = []
    per_fold_data: list[tuple[date, list[dict], list[dict], dict]] = []
    for cutoff in STABILITY_SPLITS:
        fold_train = [r for r in records if r["date"] < cutoff]
        fold_test = [r for r in records if r["date"] >= cutoff]
        if len(fold_train) < MIN_FOLD_N or len(fold_test) < MIN_FOLD_N:
            print(f"  {cutoff}: skipped (train N={len(fold_train)}, test N={len(fold_test)} -- too small)")
            continue
        fb = refit_bands(fold_train)
        weights = {name: dimension_weight(fb[name]) for name in SECONDARY_DIMS}
        per_fold_weights.append((cutoff, weights))
        per_fold_data.append((cutoff, fold_train, fold_test, fb))
        print(f"  {cutoff}: train N={len(fold_train)} test N={len(fold_test)} weights={weights}")

    weight_hdr = f"{'Split date':<12} {'Train N':>8} " + " ".join(f"{d:>12}" for d in SECONDARY_DIMS)
    weight_lines = [weight_hdr, "-" * len(weight_hdr)]
    for cutoff, weights in per_fold_weights:
        train_n = len([r for r in records if r["date"] < cutoff])
        weight_lines.append(f"{str(cutoff):<12} {train_n:>8} " + " ".join(f"{weights[d]:>12}" for d in SECONDARY_DIMS))
    out("```text")
    out("\n".join(weight_lines))
    out("```")

    avg_weights = {name: float(np.mean([w[name] for _, w in per_fold_weights])) for name in SECONDARY_DIMS}
    total_avg = sum(avg_weights.values())
    stabilized_weights = {name: round(50.0 * w / total_avg) for name, w in avg_weights.items()}
    drift = 50 - sum(stabilized_weights.values())
    if drift != 0:
        key = max(avg_weights, key=lambda k: abs(50.0 * avg_weights[k] / total_avg - stabilized_weights[k]))
        stabilized_weights[key] += drift
    out("")
    out("Cross-fold average weight (renormalized to sum 50): " + ", ".join(f"{name}={stabilized_weights[name]}" for name in SECONDARY_DIMS))

    out("")
    out("### Multi-fold out-of-sample comparison")
    out("")
    out(
        "For each cutoff, weights/bands are fit on data before it and scored on data at/after it "
        "(a genuine walk-forward fold for refit-per-fold and stabilized-avg; production/legacy "
        "are fixed constants scored on the same fold's held-out data for reference). Averaged "
        "across all folds -- this is the actual test of whether any scheme is *consistently* "
        "better, not just better on the single 2021 split above:"
    )
    out("")

    scheme_labels = {
        "refit_per_fold": "Refit-per-fold",
        "stabilized": "Stabilized-avg",
        "production": "Production",
        "legacy": "Legacy",
    }
    scheme_fold_results: dict[str, list[list[dict]]] = {name: [] for name in scheme_labels}
    for _cutoff, fold_train, fold_test, fb in per_fold_data:
        stab_bands = bands_with_weights(fold_train, stabilized_weights)
        scheme_fold_results["refit_per_fold"].append(compute_deciles(fold_test, [score_dynamic(r, fb) for r in fold_test]))
        scheme_fold_results["stabilized"].append(compute_deciles(fold_test, [score_dynamic(r, stab_bands) for r in fold_test]))
        scheme_fold_results["production"].append(compute_deciles(fold_test, [score_production(r) for r in fold_test]))
        scheme_fold_results["legacy"].append(compute_deciles(fold_test, [score_legacy(r) for r in fold_test]))

    fold_hdr = f"{'Scheme':<16} {'Avg Sortino spread':>19} {'Avg Mean% spread':>17} {'Folds':>6}"
    fold_lines = [fold_hdr, "-" * len(fold_hdr)]
    avg_sortino_by_scheme: dict[str, float] = {}
    for name, deciles_list in scheme_fold_results.items():
        spreads = [fold_spread(d) for d in deciles_list]
        sortino_spreads = [s[0] for s in spreads if not np.isnan(s[0])]
        mean_spreads = [s[1] for s in spreads]
        avg_sr = float(np.mean(sortino_spreads)) if sortino_spreads else float("nan")
        avg_mean = float(np.mean(mean_spreads)) if mean_spreads else float("nan")
        avg_sortino_by_scheme[name] = avg_sr
        fold_lines.append(f"{scheme_labels[name]:<16} {avg_sr:>19.3f} {avg_mean:>+17.1f} {len(deciles_list):>6}")
    out("```text")
    out("\n".join(fold_lines))
    out("```")

    valid_schemes = {k: v for k, v in avg_sortino_by_scheme.items() if not np.isnan(v)}
    if valid_schemes:
        best = max(valid_schemes, key=lambda k: valid_schemes[k])
        out("")
        out(f"Highest average out-of-sample Sortino spread across folds: **{scheme_labels[best]}**")

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nSaved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
