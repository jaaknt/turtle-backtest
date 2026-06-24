#!/usr/bin/env python3
"""
Walk-forward backtest of Qullamaggie-style breakout signals.
Reference: docs/research/qullamaggie-backtest.md

Entry: close > N-week high AND roc_21 > T AND pct_above_sma50 > X
       AND tight_base[-11:-1] < X AND vol_surge > N
Exit:  time-based / trailing stop / fixed stop / stop+time
Walk-forward: 12M in-sample, 3M OOS, roll 3M.
"""

import itertools
import logging
import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_HOLD = 63
MIN_AVG_VOL = 300_000
MIN_PRICE = 5.0
MIN_HISTORY = 120
COOLDOWN = 30
MIN_OOS_TRADES = 30

BREAKOUT_WEEKS = [3, 15]
ROC_THRESHOLDS = [0.10, 0.20]
SMA50_THRESHOLDS = [0.05, 0.15]
TIGHT_BASE_THRESHOLDS = [0.05, 0.10]
VOL_SURGE_MULTIPLES = [1.1, 1.3]

EXIT_RULES: list[tuple[str, dict]] = [
    ("time_21d", {"kind": "time", "hold": 21}),
    ("time_63d", {"kind": "time", "hold": 63}),
    ("trail_10", {"kind": "trail", "stop": 0.10}),
    ("trail_15", {"kind": "trail", "stop": 0.15}),
    ("trail_20", {"kind": "trail", "stop": 0.20}),
    ("fixed_7", {"kind": "fixed", "stop": 0.07}),
    ("fixed_12", {"kind": "fixed", "stop": 0.12}),
    ("st_10_21", {"kind": "stop_time", "stop": 0.10, "hold": 21}),
    ("st_10_63", {"kind": "stop_time", "stop": 0.10, "hold": 63}),
    ("st_15_21", {"kind": "stop_time", "stop": 0.15, "hold": 21}),
    ("st_15_63", {"kind": "stop_time", "stop": 0.15, "hold": 63}),
    ("st_20_21", {"kind": "stop_time", "stop": 0.20, "hold": 21}),
    ("st_20_63", {"kind": "stop_time", "stop": 0.20, "hold": 63}),
]

# Walk-forward: OOS windows (3-month quarters)
OOS_WINDOWS: list[tuple[date, date, date, date]] = []
for _year in range(2021, 2027):
    for _q in range(1, 5):
        _om = (_q - 1) * 3 + 1
        _oos_start = date(_year, _om, 1)
        _oos_end_month = _om + 2
        _oos_end_year = _year + (_oos_end_month > 12)
        _oos_end_month = _oos_end_month if _oos_end_month <= 12 else _oos_end_month - 12
        import calendar as _cal

        _oos_end = date(_oos_end_year, _oos_end_month, _cal.monthrange(_oos_end_year, _oos_end_month)[1])
        if _oos_end > date(2026, 3, 31):  # need 63-day forward buffer
            break
        _is_start = date(_oos_start.year - 1, _oos_start.month, 1)
        if _is_start < date(2020, 1, 1):
            _is_start = date(2020, 1, 1)
        _is_end = date(_oos_start.year, _oos_start.month, 1)
        from datetime import timedelta as _td

        _is_end = _oos_start - _td(days=1)
        OOS_WINDOWS.append((_is_start, _is_end, _oos_start, _oos_end))


def sig_label(bw: int, roc: float, sma: float, tb: float, vs: float) -> str:
    return f"bk{bw}w_r{int(roc * 100)}_s{int(sma * 100)}_tb{int(tb * 100)}_v{vs}"


# ── Data loading ───────────────────────────────────────────────────────────────


def load_bars(engine: sa.Engine) -> pl.DataFrame:
    sql = """
        SELECT db.symbol,
               db.date::date    AS date,
               db.open::float8  AS open,
               db.close::float8 AS close,
               db.volume::int8  AS volume
        FROM   turtle.daily_bars db
        JOIN   turtle.ticker  t  ON t.code          = db.symbol
        JOIN   turtle.company c  ON c.ticker_code   = t.code
        WHERE  t.country = 'USA'
          AND  t.type    = 'Common Stock'
          AND  c.market_cap >= 10000000
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

    # Shift close/volume by 1 to exclude today from lookback windows
    df = df.with_columns(
        [
            pl.col("close").shift(1).over("symbol").alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
        ]
    )

    df = df.with_columns(
        [
            # SMA50 (includes today — standard)
            pl.col("close").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("sma50"),
            # 50-day avg volume (excludes today)
            pl.col("_v1").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("avg_vol_50"),
            # 20-day avg volume for liquidity filter (excludes today)
            pl.col("_v1").rolling_mean(window_size=20, min_samples=20).over("symbol").alias("avg_vol_20"),
            # Breakout: max close over last 3w=15d and 15w=75d (excludes today)
            pl.col("_c1").rolling_max(window_size=15, min_samples=15).over("symbol").alias("max_c_3w"),
            pl.col("_c1").rolling_max(window_size=75, min_samples=75).over("symbol").alias("max_c_15w"),
            # Tight base over [-11,-1]: std/mean of last 10 closes (excludes today)
            pl.col("_c1").rolling_std(window_size=10, min_samples=10).over("symbol").alias("_std10"),
            pl.col("_c1").rolling_mean(window_size=10, min_samples=10).over("symbol").alias("_mean10"),
            # ROC-21
            (pl.col("close") / pl.col("close").shift(21).over("symbol") - 1).alias("roc21"),
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
    roc: float,
    sma: float,
    tb: float,
    vs: float,
    from_date: date,
    to_date: date,
) -> pl.DataFrame:
    """Return (symbol, date, close) entries passing all conditions."""
    max_col = "max_c_3w" if bw == 3 else "max_c_15w"

    cands = (
        df.filter(
            (pl.col("date") >= from_date)
            & (pl.col("date") <= to_date)
            & pl.col("close").is_not_null()
            & pl.col("sma50").is_not_null()
            & pl.col(max_col).is_not_null()
            & pl.col("tight_base_cv").is_not_null()
            # Liquidity
            & (pl.col("close") >= MIN_PRICE)
            & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
            # Breakout
            & (pl.col("close") > pl.col(max_col))
            # Momentum
            & (pl.col("roc21") >= roc)
            # Above SMA50
            & (pl.col("pct_vs_sma50") >= sma)
            # Tight base
            & (pl.col("tight_base_cv") <= tb)
            # Volume surge
            & (pl.col("vol_ratio") >= vs)
        )
        .select(["symbol", "date", "close"])
        .sort(["symbol", "date"])
    )

    if cands.is_empty():
        return cands

    # Apply cooldown: drop re-triggers within COOLDOWN days per symbol
    rows_out: list[dict] = []
    last_date: dict[str, date] = {}
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_date.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            rows_out.append(row)
            last_date[sym] = d
    if not rows_out:
        return cands.clear()
    return pl.DataFrame(rows_out)


# ── Exit simulation ────────────────────────────────────────────────────────────


def _exit_return(
    closes: np.ndarray,
    opens: np.ndarray,
    entry_price: float,
    rule: dict,
) -> float:
    """Compute return for a single trade under the given exit rule."""
    kind = rule["kind"]
    hold = rule.get("hold", MAX_HOLD)
    stop = rule.get("stop", None)

    n = min(hold + 2, len(closes))
    if n < 2:
        return 0.0

    c = closes[:n]
    o = opens[:n]

    if kind == "time":
        idx = min(hold, len(c) - 1)
        return float((c[idx] - entry_price) / entry_price)

    # For trail / fixed / stop_time:
    # peak_before[d] = max(c[0..d-1]), check if c[d] < peak_before[d] * (1-stop)
    # exit at o[d+1]
    assert stop is not None
    peak_before = np.empty(n)
    peak_before[0] = entry_price
    if n > 1:
        peak_before[1:] = np.maximum.accumulate(c[:-1])

    max_d = hold if kind in ("fixed", "stop_time") else MAX_HOLD

    for d in range(1, min(max_d + 1, n)):
        if kind in ("trail", "stop_time"):
            stop_level = peak_before[d] * (1 - stop)
        else:  # fixed
            stop_level = entry_price * (1 - stop)

        if c[d] < stop_level:
            exit_idx = d + 1
            ep = o[exit_idx] if exit_idx < len(o) else c[d]
            return float((ep - entry_price) / entry_price)

        if kind == "stop_time" and d >= hold:
            return float((c[d] - entry_price) / entry_price)

    idx = min(max_d, len(c) - 1)
    return float((c[idx] - entry_price) / entry_price)


def compute_returns(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_opens: dict[str, np.ndarray],
    rule: dict,
) -> list[float]:
    rets = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        opens = sym_opens[sym]
        # Convert date to days-since-epoch int for searchsorted
        entry_int = (row["date"] - date(1970, 1, 1)).days
        idx = int(np.searchsorted(dates, entry_int))
        if idx >= len(closes) - 1:
            continue
        fwd_c = closes[idx:]
        fwd_o = opens[idx:]
        if len(fwd_c) < 2:
            continue
        ret = _exit_return(fwd_c, fwd_o, float(row["close"]), rule)
        rets.append(ret)
    return rets


# ── Metrics ────────────────────────────────────────────────────────────────────


def metrics(rets: list[float]) -> dict:
    if len(rets) < 2:
        return {}
    a = np.array(rets)
    wins = a[a > 0]
    losses = a[a < 0]
    std = a.std(ddof=1)
    # Annualise: assume avg hold ~21d → ~12 trades/year
    sharpe = (a.mean() * 12) / (std * np.sqrt(12)) if std > 0 else 0.0
    return {
        "n": len(a),
        "win_rate": len(wins) / len(a),
        "median": float(np.median(a)),
        "q75": float(np.percentile(a, 75)),
        "sharpe": float(sharpe),
        "pf": float(wins.sum() / abs(losses.sum())) if len(losses) > 0 else 99.0,
    }


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()
    df = load_bars(settings.engine)

    # Drop tickers with insufficient history
    counts = df.group_by("symbol").agg(pl.len().alias("n"))
    valid = counts.filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid.to_list()))
    log.info("After history filter: %d symbols", df["symbol"].n_unique())

    log.info("Computing indicators …")
    df = add_indicators(df)

    # Build per-symbol lookup arrays (dates as int32 days-since-epoch)
    log.info("Building symbol lookup tables …")
    epoch = date(1970, 1, 1)
    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    sym_opens: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - epoch).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_opens[sym] = g["open"].cast(pl.Float64).to_numpy(allow_copy=True)

    param_combos = list(
        itertools.product(
            BREAKOUT_WEEKS,
            ROC_THRESHOLDS,
            SMA50_THRESHOLDS,
            TIGHT_BASE_THRESHOLDS,
            VOL_SURGE_MULTIPLES,
        )
    )
    n_windows = len(OOS_WINDOWS)
    log.info("%d walk-forward windows, %d signal combos, %d exit rules", n_windows, len(param_combos), len(EXIT_RULES))

    # Accumulate OOS returns per (sig_key, exit_key)
    oos_rets: dict[str, list[float]] = {}
    is_sharpes: dict[str, list[float]] = {}
    for bw, roc, sma, tb, vs in param_combos:
        for exit_key, _ in EXIT_RULES:
            key = f"{sig_label(bw, roc, sma, tb, vs)}|{exit_key}"
            oos_rets[key] = []
            is_sharpes[key] = []

    for w_idx, (is_start, is_end, oos_start, oos_end) in enumerate(OOS_WINDOWS):
        log.info("Window %2d/%d  IS %s–%s  OOS %s–%s", w_idx + 1, n_windows, is_start, is_end, oos_start, oos_end)

        for bw, roc, sma, tb, vs in param_combos:
            sl = sig_label(bw, roc, sma, tb, vs)

            is_sigs = get_signals(df, bw, roc, sma, tb, vs, is_start, is_end)
            oos_sigs = get_signals(df, bw, roc, sma, tb, vs, oos_start, oos_end)

            if is_sigs.is_empty() and oos_sigs.is_empty():
                continue

            for exit_key, exit_rule in EXIT_RULES:
                key = f"{sl}|{exit_key}"

                if not is_sigs.is_empty():
                    is_r = compute_returns(is_sigs, sym_dates, sym_closes, sym_opens, exit_rule)
                    m = metrics(is_r)
                    if m:
                        is_sharpes[key].append(m["sharpe"])

                if not oos_sigs.is_empty():
                    oos_r = compute_returns(oos_sigs, sym_dates, sym_closes, sym_opens, exit_rule)
                    oos_rets[key].extend(oos_r)

    # ── Build results table ────────────────────────────────────────────────────
    rows = []
    for key, rets in oos_rets.items():
        if len(rets) < MIN_OOS_TRADES:
            continue
        sl, exit_key = key.split("|", 1)
        m = metrics(rets)
        avg_is = float(np.mean(is_sharpes[key])) if is_sharpes[key] else 0.0
        degradation = (avg_is - m["sharpe"]) / abs(avg_is) if avg_is != 0 else 999.0
        rows.append(
            {
                "signal": sl,
                "exit": exit_key,
                "oos_trades": m["n"],
                "win%": round(m["win_rate"] * 100, 1),
                "median_ret": round(m["median"] * 100, 2),
                "q75_ret": round(m["q75"] * 100, 2),
                "oos_sharpe": round(m["sharpe"], 3),
                "is_sharpe": round(avg_is, 3),
                "degrade%": round(degradation * 100, 1),
                "pf": round(m["pf"], 2),
                "consistent": "✓" if degradation < 0.30 else "",
            }
        )

    rows.sort(key=lambda r: r["oos_sharpe"], reverse=True)

    # ── Print output ───────────────────────────────────────────────────────────
    H = (
        f"{'#':<4} {'Signal':<42} {'Exit':<12} {'N':>5} {'Win%':>5} "
        f"{'Med%':>6} {'Q75%':>6} {'OOS-SR':>7} {'IS-SR':>6} {'Deg%':>6} "
        f"{'PF':>5} {'C':>2}"
    )
    print("\n" + H)
    print("-" * len(H))
    for i, r in enumerate(rows[:30], 1):
        print(
            f"{i:<4} {r['signal']:<42} {r['exit']:<12} "
            f"{r['oos_trades']:>5} {r['win%']:>5} {r['median_ret']:>6} {r['q75_ret']:>6} "
            f"{r['oos_sharpe']:>7.3f} {r['is_sharpe']:>6.3f} {r['degrade%']:>6.1f} "
            f"{r['pf']:>5.2f} {r['consistent']:>2}"
        )

    top3 = [r for r in rows if r["consistent"] == "✓"][:3]
    if top3:
        print("\n=== Top 3 consistent combinations (IS→OOS degradation < 30%) ===")
        for r in top3:
            print(
                f"  {r['signal']} | {r['exit']}  OOS Sharpe={r['oos_sharpe']}  "
                f"Win%={r['win%']}  Median={r['median_ret']}%  N={r['oos_trades']}"
            )

    print(f"\nTotal combinations with ≥{MIN_OOS_TRADES} OOS trades: {len(rows)}")


if __name__ == "__main__":
    main()
