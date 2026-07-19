#!/usr/bin/env python3
"""
Qullamaggie-style breakout backtest v4.
Spec: docs/research/qullamaggie-backtest-v4.md

Fixed filters: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%,
               ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sweep: SMA_THRESH ∈ {12%,15%,17%,20%} × HOLD_CAL ∈ {91,184,366 cal days}  (tight_range and sma_alignment disabled)
Eval: 2021-01-01 – present  |  Burn-in data from 2020-01-01
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).parent.parent))
from turtle.config.settings import Settings

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2021, 1, 1)
HOLD_MAX_CAL = 366  # skip entries without 366 cal days of fwd data
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
MIN_TRADES = 30
MIN_NEG = 10
CAPACITY_LIMITS = [30, 20]

SMA_THRESHS = [0.12, 0.15, 0.17, 0.20]
HOLD_CALS = [91, 184, 366]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-backtest-v4.md"


# ── Data loading ───────────────────────────────────────────────────────────────


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= '2019-06-01'
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
    """Load daily bars with high/low/close adjusted for splits and dividends.

    `raw_close` (unadjusted) is kept separately for the absolute MIN_PRICE/MAX_PRICE
    filter, since adjusting it would leak knowledge of splits that hadn't happened yet
    as of the entry date. `close`/`high`/`low` are split/dividend-adjusted (scaled by
    adjusted_close/close) so rolling indicators and trade returns aren't corrupted by
    the price discontinuity a raw close shows on a split date.
    """
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
          AND  c.market_cap >= 1500000000
          AND  c.sector NOT IN ('Communication Services', 'Real Estate')
          AND  db.date >= '2020-01-01'
          AND  db.close > 0
          AND  db.adjusted_close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql)).fetchall()
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


# ── Indicators ─────────────────────────────────────────────────────────────────


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
    # Rolling averages and reference levels
    df = df.with_columns(
        [
            pl.col("_c1").rolling_mean(10, min_samples=10).over("symbol").alias("sma10"),
            pl.col("_c1").rolling_mean(20, min_samples=20).over("symbol").alias("sma20"),
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


# ── Signal generation ──────────────────────────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    cands = (
        df.filter(
            (pl.col("date") >= EVAL_START)
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
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runner (calendar-day exits) ─────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    hold_cal: int,
) -> list[dict]:
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
        idx_exit = int(np.searchsorted(dates, entry_int + hold_cal))
        if idx_exit >= len(dates):
            continue
        window = closes[idx_entry : idx_exit + 1]
        ret = float((closes[idx_exit] - closes[idx_entry]) / closes[idx_entry])
        running_max = np.maximum.accumulate(window)
        mdd = float((1.0 - window / running_max).max())
        records.append(
            {
                "symbol": sym,
                "entry_date": row["date"],
                "exit_date": _EPOCH + timedelta(days=int(dates[idx_exit])),
                "year": row["date"].year,
                "ret": ret,
                "mdd": mdd,
            }
        )
    return records


def apply_capacity(records: list[dict], max_open: int) -> list[dict]:
    """Keep only the trades a portfolio limited to `max_open` concurrent positions could take.

    Processes candidate trades in chronological entry-date order (ties broken by symbol) and
    greedily accepts a trade if fewer than `max_open` positions are open on its entry date;
    otherwise the signal is skipped outright (no queueing for a freed-up slot later).
    """
    ordered = sorted(records, key=lambda r: (r["entry_date"], r["symbol"]))
    open_exits: list[date] = []
    accepted: list[dict] = []
    for r in ordered:
        open_exits = [d for d in open_exits if d >= r["entry_date"]]
        if len(open_exits) < max_open:
            open_exits.append(r["exit_date"])
            accepted.append(r)
    return accepted


# ── Metrics ────────────────────────────────────────────────────────────────────


def sortino(a: np.ndarray, hold_cal: int) -> float:
    neg = a[a < 0]
    if len(neg) < MIN_NEG:
        return float("nan")
    downside = np.where(a < 0, a, 0.0)
    dd = float(np.sqrt(np.mean(downside**2)))
    return float(np.mean(a) * np.sqrt(365 / hold_cal) / dd) if dd > 0 else float("nan")


def compute_metrics(records: list[dict], hold_cal: int) -> dict | None:
    if len(records) < MIN_TRADES:
        return None
    a = np.array([r["ret"] for r in records])
    sr = sortino(a, hold_cal)
    if np.isnan(sr) or sr <= 0:
        return None
    p5 = max(1, int(np.floor(len(a) * 0.05)))
    today = date.today()
    months = (today.year - EVAL_START.year) * 12 + (today.month - EVAL_START.month)
    gross_win = float(a[a > 0].sum())
    gross_loss = float(-a[a < 0].sum())
    mdds = np.array([r["mdd"] for r in records])
    return {
        "n": len(a),
        "win": float((a > 0).mean() * 100),
        "mean": float(a.mean() * 100),
        "ann_mean": float(((1.0 + a.mean()) ** (365.0 / hold_cal) - 1.0) * 100),
        "med": float(np.median(a) * 100),
        "q75": float(np.percentile(a, 75) * 100),
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
        "sr": sr,
        "mdd": float(mdds.mean() * 100),
        "cvar": float(np.sort(a)[:p5].mean() * 100),
        "freq": len(a) / max(months, 1),
    }


def consistency_flag(records: list[dict], hold_cal: int) -> tuple[str, bool]:
    by_year: dict[int, list[float]] = {}
    for r in records:
        by_year.setdefault(r["year"], []).append(r["ret"])
    today = date.today()
    valid = pos = 0
    for yr, rets in sorted(by_year.items()):
        if yr >= today.year:
            continue
        a = np.array(rets)
        neg = a[a < 0]
        if len(neg) < MIN_NEG:
            continue
        valid += 1
        downside = np.where(a < 0, a, 0.0)
        dd = float(np.sqrt(np.mean(downside**2)))
        sr = float(np.mean(a) * np.sqrt(365 / hold_cal) / dd) if dd > 0 else 0.0
        if sr > 0:
            pos += 1
    consistent = valid >= 3 and (pos / valid) >= 0.70 if valid > 0 else False
    return f"{pos}/{valid}", consistent


# ── Output ─────────────────────────────────────────────────────────────────────

_HDR = (
    f"{'#':>4}  {'Entry Signal':<30}  {'Exit':>6}  "
    f"{'N':>4}  {'Win%':>5}  {'Mean%':>7}  {'AnnMean%':>8}  {'Med%':>7}  {'Q75%':>7}  {'PF':>5}  {'Sortino':>7}  "
    f"{'MaxDD%':>7}  {'CVaR%':>7}  {'F/mo':>5}  {'Yrs+':>5}  {'C':>1}"
)
_SEP = "─" * len(_HDR)


def fmt_row(rank: int, label: str, hold_cal: int, m: dict, yrs: str, cons: bool) -> str:
    c = "✓" if cons else " "
    return (
        f"{rank:>4}  {label:<30}  {hold_cal:>4}d  "
        f"{m['n']:>4}  {m['win']:>5.1f}  {m['mean']:>+7.2f}  {m['ann_mean']:>+8.2f}  {m['med']:>+7.2f}  "
        f"{m['q75']:>+7.2f}  {m['pf']:>5.2f}  {m['sr']:>7.3f}  "
        f"{m['mdd']:>7.2f}  {m['cvar']:>+7.2f}  {m['freq']:>5.1f}  {yrs:>5}  {c}"
    )


def build_rankings(
    results: list[tuple[str, int, dict, list[dict]]], header_lines: list[str]
) -> tuple[str, list[tuple[int, str, int, dict, str]]]:
    lines = [*header_lines, _HDR, _SEP]
    consistent_rows = []
    for i, (lbl, hold_cal, m, records) in enumerate(results, 1):
        yrs, cons = consistency_flag(records, hold_cal)
        lines.append(fmt_row(i, lbl, hold_cal, m, yrs, cons))
        if cons:
            consistent_rows.append((i, lbl, hold_cal, m, yrs))
    lines += ["", f"Valid combinations: {len(results)}  |  Consistent: {len(consistent_rows)}"]
    return "\n".join(lines), consistent_rows


def consistent_md(title: str, consistent_rows: list[tuple[int, str, int, dict, str]]) -> str:
    if not consistent_rows:
        return f"## {title}\n\nNo combinations met the consistency criteria.\n"
    parts = [
        f"## {title}\n\n",
        f"Sortino > 0 in ≥70% of complete calendar years with ≥{MIN_NEG} negative trades, and ≥3 valid years.\n\n",
    ]
    for _rank, lbl, hold_cal, m, yrs in consistent_rows:
        parts.append(
            f"- `{lbl}` | `{hold_cal}d` — SR={m['sr']:.3f}, "
            f"Win%={m['win']:.1f}, Med%={m['med']:+.2f}, AnnMean%={m['ann_mean']:+.2f}, Q75%={m['q75']:+.2f}, "
            f"MaxDD%={m['mdd']:.2f}, CVaR%={m['cvar']:+.2f}, Yrs+={yrs}, N={m['n']}\n"
        )
    return "".join(parts)


# ── Main ───────────────────────────────────────────────────────────────────────


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

    results: list[tuple[str, int, dict, list[dict]]] = []
    results_by_cap: dict[int, list[tuple[str, int, dict, list[dict]]]] = {cap: [] for cap in CAPACITY_LIMITS}

    for sma_t in SMA_THRESHS:
        lbl = f"bk50d_s{int(sma_t * 100)}_v1.2_roc100"
        print(f"  {lbl} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        if signals.is_empty():
            continue
        for hold_cal in HOLD_CALS:
            records = run_trades(signals, sym_dates, sym_closes, hold_cal)
            m = compute_metrics(records, hold_cal)
            if m is not None:
                results.append((lbl, hold_cal, m, records))
            for cap in CAPACITY_LIMITS:
                records_capped = apply_capacity(records, cap)
                m_capped = compute_metrics(records_capped, hold_cal)
                if m_capped is not None:
                    results_by_cap[cap].append((lbl, hold_cal, m_capped, records_capped))

    results.sort(key=lambda x: x[2]["sr"], reverse=True)
    for cap in CAPACITY_LIMITS:
        results_by_cap[cap].sort(key=lambda x: x[2]["sr"], reverse=True)

    # ── Print tables ───────────────────────────────────────────────────────────
    header_lines = [
        f"Period: {EVAL_START} – {date.today()}  |  HOLD_MAX_CAL={HOLD_MAX_CAL}d",
        f"Fixed: vol_dry_up<{int(VOL_DRY_UP * 100)}%, roc_12m<{int(ROC_CAP * 100)}%, "
        f"vol_surge<{VOL_SURGE_MAX}x (no lower bound), RSI<{int(RSI_CAP)}, ADR>={ADR_MIN * 100:.1f}%, "
        f"ADR_change<{int(ADR_CHANGE_CAP * 100)}%, SPY>200d SMA, "
        f"close>${MIN_PRICE:.0f}&<${MAX_PRICE:.0f}, avg_vol>={MIN_AVG_VOL // 1000}K",
        "",
    ]

    def print_consistent(title: str, consistent_rows: list[tuple[int, str, int, dict, str]]) -> None:
        if not consistent_rows:
            return
        print(f"\n=== {title} ===")
        for rank, lbl, hold_cal, m, yrs in consistent_rows:
            print(
                f"  #{rank}  {lbl} | {hold_cal}d  SR={m['sr']:.3f}  "
                f"Win%={m['win']:.1f}  Med%={m['med']:+.2f}  AnnMean%={m['ann_mean']:+.2f}  Q75%={m['q75']:+.2f}  "
                f"MaxDD%={m['mdd']:.2f}  CVaR%={m['cvar']:+.2f}  Yrs+={yrs}  N={m['n']}"
            )

    output, consistent_rows = build_rankings(results, header_lines)
    print("\n" + output)
    print_consistent("Consistent (Sortino>0 in ≥70% of complete eval years, ≥3 valid years)", consistent_rows)

    capped: dict[int, tuple[str, list[tuple[int, str, int, dict, str]]]] = {}
    for cap in CAPACITY_LIMITS:
        out, cons_rows = build_rankings(results_by_cap[cap], [*header_lines[:-1], f"Max concurrent positions: {cap}", ""])
        capped[cap] = (out, cons_rows)
        print("\n" + out)
        print_consistent(
            f"Consistent (Max {cap} Concurrent) — Sortino>0 in ≥70% of complete eval years, ≥3 valid years",
            cons_rows,
        )

    # ── Write markdown result ──────────────────────────────────────────────────
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Backtest v4 — Results\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        sma_vals = ", ".join(f"{int(v * 100)}%" for v in SMA_THRESHS)
        hold_vals = ", ".join(f"{h}d" for h in HOLD_CALS)
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write("| Breakout | 50d high |\n")
        fh.write(f"| SMA thresh sweep | {sma_vals} |\n")
        fh.write("| Tight range | disabled (commented out) |\n")
        fh.write(f"| Hold sweep | {hold_vals} (calendar) |\n")
        fh.write(f"| Capacity limits | unconstrained, {', '.join(str(c) for c in CAPACITY_LIMITS)} concurrent (FIFO) |\n")
        fh.write(f"| vol_dry_up | avg_vol_10 < {int(VOL_DRY_UP * 100)}% × avg_vol_50 |\n")
        fh.write(f"| vol_surge | volume/avg_vol_50 < {VOL_SURGE_MAX}× (no lower bound) |\n")
        fh.write(f"| roc_12m_cap | 12m ROC < {int(ROC_CAP * 100)}% |\n")
        fh.write(f"| RSI | RSI(14) < {int(RSI_CAP)} |\n")
        fh.write(f"| ADR | mean((high-low)/low, last 20d, shift-1) ≥ {ADR_MIN * 100:.1f}% |\n")
        fh.write(f"| ADR change | ADR%(10d) / ADR%(50d) < {int(ADR_CHANGE_CAP * 100)}% |\n")
        fh.write("| SMA alignment | disabled (commented out) |\n")
        fh.write("| Market regime | SPY close > 200d SMA |\n")
        fh.write(f"| Price range | > ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f} |\n")
        fh.write(f"| Min avg vol (20d) | ≥ {MIN_AVG_VOL // 1000}K |\n")
        fh.write(f"| Min history | ≥ {MIN_HISTORY} trading days |\n")
        fh.write(f"| Cooldown | {COOLDOWN} calendar days |\n")
        fh.write(f"| Eval period | {EVAL_START} – {date.today()} |\n")
        fh.write("| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |\n\n")
        fh.write("## Rankings\n\n```text\n")
        fh.write(output)
        fh.write("\n```\n\n")
        fh.write(consistent_md("Consistent Combinations", consistent_rows))

        for cap in CAPACITY_LIMITS:
            out, cons_rows = capped[cap]
            fh.write(f"\n## Rankings — Max {cap} Concurrent Positions\n\n")
            fh.write(
                f"Same signals, but a trade is skipped if {cap} positions are already open on its entry "
                "date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).\n\n```text\n"
            )
            fh.write(out)
            fh.write("\n```\n\n")
            fh.write(consistent_md(f"Consistent Combinations (Max {cap} Concurrent)", cons_rows))
        fh.write("\n## Findings & Caveats\n\n")
        fh.write(
            "**Fixed**: `close`/`high`/`low` are now split/dividend-adjusted (scaled by `adjusted_close/close`). "
            "The prior version used raw `close`, which shows a fake ~90% one-day move on a stock's split date "
            "(e.g. NVDA's 2024-06-10 10:1 split) — this corrupted rolling indicators for ~50 days around any split "
            "and could make a real winning trade compute as a huge loss (or vice versa for a reverse split). "
            "13.1% of the qualifying universe (254/1,943 tickers) had at least one such split event since 2020. "
            "The MIN_PRICE/MAX_PRICE band still uses raw (unadjusted) close, since that's the real price a trader "
            "would have paid on the entry date — adjusting it would leak knowledge of future splits into a "
            "point-in-time filter.\n\n"
        )
        fh.write(
            "**Unresolved — survivorship bias**: every ticker in the qualifying universe has `status='active'`; "
            "the pipeline retains no delisted/bankrupt/acquired tickers. `company.market_cap` is also a single "
            "current-day snapshot applied retroactively to all history, not a point-in-time value. A momentum-"
            "breakout strategy specifically targets stocks that sometimes blow up afterward (fraud, failed trial, "
            "acquisition below entry) — those trades are structurally impossible to appear in this backtest. This "
            "likely explains part of the unusually high win rate/profit factor and should be treated as a ceiling "
            "on how much to trust the absolute return numbers.\n\n"
        )
        cap_list = " and ".join(str(cap) for cap in CAPACITY_LIMITS)
        fh.write(
            "**Partially addressed — overlapping trades**: at several signals/month with 6-12 month holds, most "
            "trades are open concurrently and share the same regime exposure, so the unconstrained N overstates "
            "the number of independent bets and the Sortino/consistency stats overstate statistical confidence. "
            f"The 'Max {cap_list} Concurrent Positions' tables above cap the portfolio at that many simultaneous "
            "positions (FIFO signal acceptance) as a rough realism check — comparing the tables shows how much each "
            "combination's apparent edge depends on taking every single signal versus a capital-constrained subset. "
            "This doesn't fix the underlying correlation between trades still held concurrently within a cap, and "
            "it uses an arbitrary FIFO rule rather than a real signal-quality ranking for which trade to take when "
            "capacity is full.\n\n"
        )
        fh.write(
            "**Unresolved — regime concentration**: the SPY>200d SMA filter concentrates trades in bull years. "
            "The Yrs+ denominator silently drops any complete calendar year with <10 losing trades from its count "
            "(see the Yrs+ column above, e.g. a stricter signal with fewer total trades may show fewer valid years "
            "than the number of complete calendar years in the eval period), which can exclude harder regimes "
            "rather than prove the strategy survived them.\n\n"
        )
        fh.write(
            "**Unresolved — no execution costs**: entry is assumed fillable at the same close that generated the "
            "signal, with no slippage, spread, commissions, or gap risk — unrealistic for breakout-day fills on "
            "high-ADR names.\n\n"
        )
        fh.write(
            "**Ideas to improve**: source point-in-time market cap (or shares outstanding × price at entry) instead "
            "of a static snapshot; source a delisted-ticker history if available to address survivorship; shift "
            "entry to next-day open (+ slippage assumption) for realistic fills; replace the FIFO acceptance rule in "
            "the capacity-constrained table with a real signal-quality ranking (e.g. ADR%, breakout strength) to "
            "pick which trade to take when capacity is full; account for trade overlap (e.g. block-bootstrap or "
            "effective-sample-size adjustment) when judging Sortino confidence.\n"
        )
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
