#!/usr/bin/env python3
"""
Walk-forward backtest of Qullamaggie-style breakout signals v2.
Reference: docs/research/qullamaggie-backtest-v2.md

Entry: rising_price (close > SMA10 AND SMA20)
       AND breakout_N_week AND pct_above_sma50 > X
       AND tight_base[-11:-1] < X AND vol_surge > N × 50d avg vol [-50,-1]
Exit:  time-based only (21d or 63d); skip if forward bars unavailable
Metric: annualized Sortino (annualization_factor = 252 / holding_days)
Walk-forward: 12M in-sample, 3M OOS, roll 3M.
"""

import calendar
import itertools
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

_EPOCH = date(1970, 1, 1)

# ── Constants ──────────────────────────────────────────────────────────────────
MIN_AVG_VOL = 300_000
MIN_PRICE = 5.0
MIN_HISTORY = 300
COOLDOWN = 30
MIN_OOS_TRADES = 30
MIN_NEG_TRADES = 10

BREAKOUT_WEEKS = [10, 20, 50]  # trading days: 50, 100, 250
SMA50_THRESHOLDS = [0.10, 0.15, 0.20]
TIGHT_BASE_THRESHOLDS = [0.05, 0.10]
VOL_SURGE_MULTIPLES = [1.2, 1.3, 1.4]

EXIT_RULES: list[tuple[str, int]] = [
    ("time_21d", 21),
    ("time_63d", 63),
]

RESULT_PATH = Path(__file__).parent.parent / "research" / "result-qullamaggie-backtest-v2.md"

# ── Walk-forward windows (IS=12M, OOS=3M, roll=3M) ────────────────────────────
OOS_WINDOWS: list[tuple[date, date, date, date]] = []
for _year in range(2021, 2027):
    for _q in range(1, 5):
        _om = (_q - 1) * 3 + 1
        _oos_start = date(_year, _om, 1)
        _oos_end_month = _om + 2
        _oos_end_year = _year + (_oos_end_month > 12)
        _oos_end_month = _oos_end_month if _oos_end_month <= 12 else _oos_end_month - 12
        _oos_end = date(
            _oos_end_year,
            _oos_end_month,
            calendar.monthrange(_oos_end_year, _oos_end_month)[1],
        )
        if _oos_end > date(2026, 3, 31):
            break
        _is_start = date(_oos_start.year - 1, _oos_start.month, 1)
        if _is_start < date(2020, 1, 1):
            _is_start = date(2020, 1, 1)
        _is_end = _oos_start - timedelta(days=1)
        OOS_WINDOWS.append((_is_start, _is_end, _oos_start, _oos_end))

OOS_TOTAL_MONTHS = len(OOS_WINDOWS) * 3


def sig_label(bw: int, sma: float, tb: float, vs: float) -> str:
    return f"bk{bw}w_s{int(sma * 100)}_tb{int(tb * 100)}_v{vs}"


# ── Data loading ───────────────────────────────────────────────────────────────
def load_bars(engine: sa.Engine) -> pl.DataFrame:
    sql = """
        SELECT db.symbol,
               db.date::date    AS date,
               db.open::float8  AS open,
               db.close::float8 AS close,
               db.volume::int8  AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code        = db.symbol
        JOIN   turtle.company c  ON c.ticker_code = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 2000000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= '2019-06-01'
          AND  db.close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    log.info("Loading daily bars …")
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
    df = pl.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "date": pl.Series([r[1] for r in rows], dtype=pl.Date),
            "open": [float(r[2]) for r in rows],
            "close": [float(r[3]) for r in rows],
            "volume": [int(r[4]) for r in rows],
        }
    )
    log.info("Loaded %d rows, %d symbols", len(df), df["symbol"].n_unique())
    return df


# ── Indicators ─────────────────────────────────────────────────────────────────
def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    df = df.sort(["symbol", "date"])
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
        ]
    )
    df = df.with_columns(
        [
            # Trend filter (fixed condition)
            pl.col("close").rolling_mean(window_size=10, min_samples=10).over("symbol").alias("sma10"),
            pl.col("close").rolling_mean(window_size=20, min_samples=20).over("symbol").alias("sma20"),
            pl.col("close").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("sma50"),
            # Volume baselines exclude today: [-50,-1] and [-20,-1]
            pl.col("_v1").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(window_size=20, min_samples=20).over("symbol").alias("avg_vol_20"),
            # Breakout highs exclude today: 10w=50d, 20w=100d, 50w=250d
            pl.col("_c1").rolling_max(window_size=50, min_samples=50).over("symbol").alias("max_c_10w"),
            pl.col("_c1").rolling_max(window_size=100, min_samples=100).over("symbol").alias("max_c_20w"),
            pl.col("_c1").rolling_max(window_size=250, min_samples=250).over("symbol").alias("max_c_50w"),
            # Tight base [-11,-1]: std/mean of last 10 closes excluding today
            pl.col("_c1").rolling_std(window_size=10, min_samples=10).over("symbol").alias("_std10"),
            pl.col("_c1").rolling_mean(window_size=10, min_samples=10).over("symbol").alias("_mean10"),
        ]
    )
    df = df.with_columns(
        [
            ((pl.col("close") - pl.col("sma50")) / pl.col("sma50")).alias("pct_vs_sma50"),
            (pl.col("_std10") / pl.col("_mean10")).alias("tight_base_cv"),
            (pl.col("volume").cast(pl.Float64) / pl.col("avg_vol_50")).alias("vol_ratio"),
        ]
    )
    return df.drop(["_c1", "_v1", "_std10", "_mean10"])


# ── Signal generation ──────────────────────────────────────────────────────────
def get_signals(
    df: pl.DataFrame,
    bw: int,
    sma: float,
    tb: float,
    vs: float,
    from_date: date,
    to_date: date,
) -> pl.DataFrame:
    """Return (symbol, date, close) entries passing all entry conditions with 30-day cooldown."""
    max_col = {10: "max_c_10w", 20: "max_c_20w", 50: "max_c_50w"}[bw]
    cands = (
        df.filter(
            (pl.col("date") >= from_date)
            & (pl.col("date") <= to_date)
            & pl.col("sma10").is_not_null()
            & pl.col("sma20").is_not_null()
            & pl.col("sma50").is_not_null()
            & pl.col(max_col).is_not_null()
            & pl.col("tight_base_cv").is_not_null()
            & (pl.col("close") >= MIN_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            & (pl.col("close") > pl.col("sma10"))  # rising_price
            & (pl.col("close") > pl.col("sma20"))  # rising_price
            & (pl.col("close") > pl.col(max_col))  # breakout
            & (pl.col("pct_vs_sma50") >= sma)  # above SMA50
            & (pl.col("tight_base_cv") <= tb)  # tight base
            & (pl.col("vol_ratio") >= vs)  # volume surge
        )
        .select(["symbol", "date", "close"])
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
    if not rows_out:
        return cands.clear()
    return pl.DataFrame(rows_out)


# ── Return computation ─────────────────────────────────────────────────────────
def compute_returns(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    hold: int,
) -> tuple[list[float], list[float]]:
    """Time-based returns and per-trade max drawdown; skip entries without hold forward bars."""
    rets: list[float] = []
    max_dds: list[float] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        entry_int = (row["date"] - _EPOCH).days
        idx = int(np.searchsorted(dates, entry_int))
        if idx + hold >= len(closes):
            continue
        window = closes[idx : idx + hold + 1]
        rets.append((window[-1] - window[0]) / window[0])
        peak = np.maximum.accumulate(window)
        max_dds.append(float(((peak - window) / peak).max()))
    return rets, max_dds


# ── Metrics ────────────────────────────────────────────────────────────────────
def calc_metrics(rets: list[float], max_dds: list[float], holding_days: int) -> dict:
    """Sortino + Calmar metrics. Returns {} if fewer than MIN_NEG_TRADES negative returns."""
    if len(rets) < 2:
        return {}
    a = np.array(rets)
    neg = a[a < 0]
    if len(neg) < MIN_NEG_TRADES:
        return {}
    wins = a[a > 0]
    down_std = neg.std(ddof=1)
    if down_std == 0:
        return {}
    scale = 252 / holding_days
    sortino = (a.mean() / down_std) * np.sqrt(scale)
    cagr = (1 + a.mean()) ** scale - 1
    mean_mdd = float(np.mean(max_dds)) if max_dds else 0.0
    calmar = cagr / mean_mdd if mean_mdd > 0 else 0.0
    return {
        "n": len(a),
        "win_rate": float(len(wins) / len(a)),
        "median": float(np.median(a)),
        "q75": float(np.percentile(a, 75)),
        "sortino": float(sortino),
        "pf": float(wins.sum() / abs(neg.sum())),
        "mean_mdd": mean_mdd,
        "calmar": float(calmar),
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    settings = Settings.from_toml()
    df = load_bars(settings.engine)

    counts = df.group_by("symbol").agg(pl.len().alias("n"))
    valid = counts.filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid.to_list()))
    log.info("After history filter: %d symbols", df["symbol"].n_unique())

    log.info("Computing indicators …")
    df = add_indicators(df)

    log.info("Building symbol lookup tables …")
    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)

    param_combos = list(
        itertools.product(
            BREAKOUT_WEEKS,
            SMA50_THRESHOLDS,
            TIGHT_BASE_THRESHOLDS,
            VOL_SURGE_MULTIPLES,
        )
    )
    n_windows = len(OOS_WINDOWS)
    log.info(
        "%d walk-forward windows, %d signal combos, %d exit rules → %d total combinations",
        n_windows,
        len(param_combos),
        len(EXIT_RULES),
        len(param_combos) * len(EXIT_RULES),
    )

    oos_rets: dict[str, list[float]] = {}
    oos_dds: dict[str, list[float]] = {}
    is_sortinos: dict[str, list[float]] = {}
    for bw, sma, tb, vs in param_combos:
        for exit_key, _ in EXIT_RULES:
            key = f"{sig_label(bw, sma, tb, vs)}|{exit_key}"
            oos_rets[key] = []
            oos_dds[key] = []
            is_sortinos[key] = []

    for w_idx, (is_start, is_end, oos_start, oos_end) in enumerate(OOS_WINDOWS):
        log.info("Window %2d/%d  IS %s–%s  OOS %s–%s", w_idx + 1, n_windows, is_start, is_end, oos_start, oos_end)

        for bw, sma, tb, vs in param_combos:
            sl = sig_label(bw, sma, tb, vs)
            is_sigs = get_signals(df, bw, sma, tb, vs, is_start, is_end)
            oos_sigs = get_signals(df, bw, sma, tb, vs, oos_start, oos_end)

            if is_sigs.is_empty() and oos_sigs.is_empty():
                continue

            for exit_key, hold in EXIT_RULES:
                key = f"{sl}|{exit_key}"
                if not is_sigs.is_empty():
                    is_r, _ = compute_returns(is_sigs, sym_dates, sym_closes, hold)
                    m = calc_metrics(is_r, [], hold)
                    if m:
                        is_sortinos[key].append(m["sortino"])
                if not oos_sigs.is_empty():
                    oos_r, oos_dd = compute_returns(oos_sigs, sym_dates, sym_closes, hold)
                    oos_rets[key].extend(oos_r)
                    oos_dds[key].extend(oos_dd)

    # ── Build results table ────────────────────────────────────────────────────
    rows = []
    hold_map = dict(EXIT_RULES)
    for key, rets in oos_rets.items():
        if len(rets) < MIN_OOS_TRADES:
            continue
        sl, exit_key = key.split("|", 1)
        m = calc_metrics(rets, oos_dds[key], hold_map[exit_key])
        if not m:
            continue
        avg_is = float(np.mean(is_sortinos[key])) if is_sortinos[key] else 0.0
        degradation = (avg_is - m["sortino"]) / abs(avg_is) if avg_is != 0 else 999.0
        consistent = degradation < 0.30 and m["sortino"] > 0
        rows.append(
            {
                "signal": sl,
                "exit": exit_key,
                "n": m["n"],
                "win%": round(m["win_rate"] * 100, 1),
                "median%": round(m["median"] * 100, 2),
                "q75%": round(m["q75"] * 100, 2),
                "oos_sr": round(m["sortino"], 3),
                "is_sr": round(avg_is, 3),
                "deg%": round(degradation * 100, 1),
                "pf": round(m["pf"], 2),
                "calmar": round(m["calmar"], 3),
                "freq_mo": round(m["n"] / OOS_TOTAL_MONTHS, 1),
                "consistent": "✓" if consistent else "",
            }
        )

    rows.sort(key=lambda r: r["oos_sr"], reverse=True)

    # ── Print output ───────────────────────────────────────────────────────────
    H = (
        f"{'#':<4} {'Signal':<30} {'Exit':<12} {'N':>5} {'Win%':>5} "
        f"{'Med%':>6} {'Q75%':>6} {'OOS-SR':>7} {'IS-SR':>6} "
        f"{'Deg%':>6} {'PF':>5} {'Calmar':>7} {'F/mo':>5} {'C':>2}"
    )
    print("\n" + H)
    print("-" * len(H))
    for i, r in enumerate(rows[:30], 1):
        print(
            f"{i:<4} {r['signal']:<30} {r['exit']:<12} "
            f"{r['n']:>5} {r['win%']:>5} {r['median%']:>6} {r['q75%']:>6} "
            f"{r['oos_sr']:>7.3f} {r['is_sr']:>6.3f} {r['deg%']:>6.1f} "
            f"{r['pf']:>5.2f} {r['calmar']:>7.3f} {r['freq_mo']:>5.1f} {r['consistent']:>2}"
        )

    top10 = [r for r in rows if r["consistent"] == "✓"][:10]
    if top10:
        print("\n=== Top 10 consistent combinations (OOS Sortino > 0, IS→OOS degradation < 30%) ===")
        for i, r in enumerate(top10, 1):
            print(
                f"  {i}. {r['signal']} | {r['exit']}  "
                f"OOS-SR={r['oos_sr']}  Win%={r['win%']}  "
                f"Median={r['median%']}%  PF={r['pf']}  Calmar={r['calmar']}  N={r['n']}"
            )

    print(f"\nTotal combinations with ≥{MIN_OOS_TRADES} OOS trades: {len(rows)}")

    # ── Write results file ─────────────────────────────────────────────────────
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Backtest v2 — Results\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write("## Parameters\n\n")
        fh.write(f"- Breakout weeks: {BREAKOUT_WEEKS} (= {[bw * 5 for bw in BREAKOUT_WEEKS]} trading days)\n")
        fh.write(f"- SMA50 thresholds: {[f'{int(s * 100)}%' for s in SMA50_THRESHOLDS]}\n")
        fh.write(f"- Tight base CV: {[f'{int(t * 100)}%' for t in TIGHT_BASE_THRESHOLDS]}\n")
        fh.write(f"- Vol surge: {VOL_SURGE_MULTIPLES}× 50-day avg vol (baseline [-50,-1])\n")
        fh.write("- Fixed conditions: rising_price (close > SMA10 AND SMA20)\n")
        fh.write(f"- Exit rules: {[e for e, _ in EXIT_RULES]}\n")
        fh.write(f"- Walk-forward windows: {len(OOS_WINDOWS)}\n")
        fh.write(f"- Total combinations tested: {len(param_combos) * len(EXIT_RULES)}\n")
        fh.write(f"- Combinations with ≥{MIN_OOS_TRADES} OOS trades: {len(rows)}\n\n")
        fh.write("## Full Rankings (by OOS Sortino)\n\n")
        fh.write("```\n")
        fh.write(H + "\n")
        fh.write("-" * len(H) + "\n")
        for i, r in enumerate(rows, 1):
            fh.write(
                f"{i:<4} {r['signal']:<30} {r['exit']:<12} "
                f"{r['n']:>5} {r['win%']:>5} {r['median%']:>6} {r['q75%']:>6} "
                f"{r['oos_sr']:>7.3f} {r['is_sr']:>6.3f} {r['deg%']:>6.1f} "
                f"{r['pf']:>5.2f} {r['calmar']:>7.3f} {r['freq_mo']:>5.1f} {r['consistent']:>2}\n"
            )
        fh.write("```\n\n")
        if top10:
            fh.write("## Top 10 Consistent Combinations\n\n")
            fh.write("OOS Sortino > 0 and IS→OOS degradation < 30%\n\n")
            for i, r in enumerate(top10, 1):
                fh.write(
                    f"{i}. `{r['signal']} | {r['exit']}`  "
                    f"OOS-SR={r['oos_sr']}  Win%={r['win%']}  "
                    f"Median={r['median%']}%  PF={r['pf']}  Calmar={r['calmar']}  N={r['n']}\n"
                )
        else:
            fh.write("## Top 10 Consistent Combinations\n\n")
            fh.write("No combinations met both criteria (OOS Sortino > 0 AND IS→OOS degradation < 30%).\n")
    log.info("Results written to %s", RESULT_PATH)


if __name__ == "__main__":
    main()
