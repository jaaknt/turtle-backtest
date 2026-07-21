#!/usr/bin/env python3
"""
Long-term monthly analysis for multiple bk50d configs (366d hold).

Same fixed filters as scripts/qullamaggie-backtest-v4.py (RSI<70,
roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, ADR>=3.0%, ADR_change<90%,
SPY>200d SMA, close>$5&<$250, avg_vol>=500K), extended back to 2007-01-01 to
cover the 2008 GFC, 2011/2015/2018 corrections, 2020 COVID crash and 2022
bear market.

close/high/low are split/dividend-adjusted (scaled by adjusted_close/close),
same convention as qullamaggie-backtest-v4.py — over a 19-year window this
matters far more than over a 5-year one (many more split events).
raw_close (unadjusted) is used only for the MIN_PRICE/MAX_PRICE filter, the
real tradeable price at entry.

Period: 2007-01-01 – 2026-06-26  (burn-in from 2005-01-01)
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.config.settings import Settings

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2007, 1, 1)
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
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MIN_NEG = 3

STRATEGIES = [
    ("bk50d_s12_v1.3_roc100", 0.12),
    ("bk50d_s15_v1.3_roc100", 0.15),
    ("bk50d_s17_v1.3_roc100", 0.17),
    ("bk50d_s20_v1.3_roc100", 0.20),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-longterm-monthly.md"


# ── Data loading ─────────────────────────────────────────────────────────────


def load_spy_regime(engine: sa.Engine) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= '2004-06-01'
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


def load_benchmark_yearly_returns(engine: sa.Engine, symbol: str) -> dict[int, float]:
    """Buy-and-hold return per calendar year for a benchmark ticker."""
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = :symbol AND date >= :start AND date <= :end
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol, "start": EVAL_START, "end": EVAL_END}).fetchall()
    df = pl.DataFrame({"date": pl.Series([r[0] for r in rows], dtype=pl.Date), "close": [float(r[1]) for r in rows]}).with_columns(
        pl.col("date").dt.year().alias("year")
    )

    yearly: dict[int, float] = {}
    for (yr,), grp in df.group_by(["year"], maintain_order=False):
        g = grp.sort("date")
        if len(g) >= 2:
            yearly[yr] = float(g["close"][-1] / g["close"][0] - 1.0) * 100.0
    return yearly


def load_bars(engine: sa.Engine) -> pl.DataFrame:
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
          AND  db.date >= '2005-01-01'
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
        ]
    )
    return df.drop(["_c1", "_v1", "_rp1", "_adr10", "_adr50", "_c_252d"])


# ── Signal generation ──────────────────────────────────────────────────────────


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


# ── Trade runner ──────────────────────────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
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
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        ret = float((closes[idx_exit] - closes[idx_entry]) / closes[idx_entry])
        records.append({"year": row["date"].year, "month": row["date"].month, "ret": ret})
    return records


# ── Output ────────────────────────────────────────────────────────────────────


def build_monthly_table(records: list[dict]) -> list[str]:
    trades = pl.DataFrame(records) if records else pl.DataFrame(schema={"year": pl.Int64, "month": pl.Int64, "ret": pl.Float64})
    years = sorted(trades["year"].unique().to_list())

    header = f"{'Year':>5} | " + " ".join(f"{m:>6}" for m in MONTHS) + f" | {'Mean%':>7} {'N':>4}"
    sep = "-" * len(header)
    lines = [header, sep]

    for yr in years:
        yr_trades = trades.filter(pl.col("year") == yr)
        row_parts = []
        for mo in range(1, 13):
            mo_rets = yr_trades.filter(pl.col("month") == mo)["ret"].to_list()
            row_parts.append(f"{np.mean(mo_rets) * 100:>+6.1f}" if mo_rets else f"{'·':>6}")
        yr_rets = yr_trades["ret"].to_numpy()
        lines.append(f"{yr:>5} | " + " ".join(row_parts) + f" | {np.mean(yr_rets) * 100:>+7.1f} {len(yr_rets):>4}")

    row_parts = []
    for mo in range(1, 13):
        mo_rets = trades.filter(pl.col("month") == mo)["ret"].to_list()
        row_parts.append(f"{np.mean(mo_rets) * 100:>+6.1f}" if mo_rets else f"{'·':>6}")
    all_rets = trades["ret"].to_numpy()
    lines.append(sep)
    lines.append(f"{'All':>5} | " + " ".join(row_parts) + f" | {np.mean(all_rets) * 100:>+7.1f} {len(all_rets):>4}")
    return lines


def build_yearly_stats_table(
    records: list[dict],
    qqq_yearly: dict[int, float],
    spy_yearly: dict[int, float],
) -> list[str]:
    trades = pl.DataFrame(records) if records else pl.DataFrame(schema={"year": pl.Int64, "month": pl.Int64, "ret": pl.Float64})
    years = sorted(trades["year"].unique().to_list())

    header = f"{'Year':>5} {'N':>5} {'Win%':>6} {'Mean%':>7} {'QQQ%':>7} {'SPY%':>7} {'Med%':>7} {'Sortino':>8} {'CVaR95%':>8}"
    sep = "-" * len(header)
    lines = [header, sep]

    def fmt_pct(v: float) -> str:
        return f"{v:>+7.1f}" if not np.isnan(v) else f"{'—':>7}"

    def fmt_row(a: np.ndarray, qqq_pct: float, spy_pct: float) -> str:
        n = len(a)
        win = float((a > 0).sum() / n * 100)
        mean = float(np.mean(a) * 100)
        med = float(np.median(a) * 100)
        neg = a[a < 0]
        sr = float("nan")
        if len(neg) >= MIN_NEG:
            dd = float(np.sqrt(np.mean(neg**2)))
            if dd > 0:
                sr = float(np.mean(a) * np.sqrt(365 / HOLD_CAL) / dd)
        p5 = max(1, int(np.floor(n * 0.05)))
        cvar = float(np.sort(a)[:p5].mean() * 100)
        sr_str = f"{sr:>8.3f}" if not np.isnan(sr) else f"{'n/a':>8}"
        return f"{n:>5} {win:>6.1f} {mean:>+7.2f} {fmt_pct(qqq_pct)} {fmt_pct(spy_pct)} {med:>+7.2f} {sr_str} {cvar:>+8.2f}"

    for yr in years:
        a = trades.filter(pl.col("year") == yr)["ret"].to_numpy()
        lines.append(f"{yr:>5} " + fmt_row(a, qqq_yearly.get(yr, float("nan")), spy_yearly.get(yr, float("nan"))))

    lines.append(sep)
    all_rets = trades["ret"].to_numpy()
    # "All" row's QQQ%/SPY% is the mean of the per-year returns actually covered by trades,
    # comparable to the Mean%/Med% columns (per-trade, ~1yr holds) — not the ~19yr compounded total.
    qqq_covered = [qqq_yearly[yr] for yr in years if yr in qqq_yearly]
    spy_covered = [spy_yearly[yr] for yr in years if yr in spy_yearly]
    qqq_all = float(np.mean(qqq_covered)) if qqq_covered else float("nan")
    spy_all = float(np.mean(spy_covered)) if spy_covered else float("nan")
    lines.append(f"{'All':>5} " + fmt_row(all_rets, qqq_all, spy_all))
    return lines


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    settings = Settings.from_toml()

    print("Loading SPY regime …", flush=True)
    bull_dates = load_spy_regime(settings.engine)

    print("Loading benchmark returns …", flush=True)
    qqq_yearly = load_benchmark_yearly_returns(settings.engine, "QQQ.US")
    spy_yearly = load_benchmark_yearly_returns(settings.engine, "SPY.US")

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

    fixed_hdr = (
        f"Hold: {HOLD_CAL}d | Period: {EVAL_START} – {EVAL_END}\n"
        f"Fixed: vol_dry_up<{int(VOL_DRY_UP * 100)}%, roc_12m<{int(ROC_CAP * 100)}%, "
        f"vol_surge<{VOL_SURGE_MAX}x (no lower bound), RSI<{int(RSI_CAP)}, ADR>={ADR_MIN * 100:.1f}%, "
        f"ADR_change<{int(ADR_CHANGE_CAP * 100)}%, "
        f"SPY>200d SMA, close>${MIN_PRICE:.0f}&<${MAX_PRICE:.0f}, avg_vol>={MIN_AVG_VOL // 1000}K\n"
    )
    print("\n" + fixed_hdr)

    all_lines: list[str] = [fixed_hdr]

    for strat_label, sma_t in STRATEGIES:
        print(f"Generating signals for {strat_label} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        print(f"  {len(signals)} signals", flush=True)
        records = run_trades(signals, sym_dates, sym_closes)

        section = [f"### {strat_label}", ""]
        section += build_monthly_table(records)
        section.append("")
        section += build_yearly_stats_table(records, qqq_yearly, spy_yearly)
        section.append("")

        print("\n".join(section))
        all_lines += section

    output = "\n".join(all_lines)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Long-Term Monthly Analysis (2007-2026)\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
