#!/usr/bin/env python3
"""
Qullamaggie-style breakout backtest v4.
Spec: docs/research/qullamaggie-backtest-v4.md

Fixed filters: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%,
               ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sweep: SMA_THRESH ∈ {12%,16%,20%} × HOLD_CAL ∈ {366 cal days}
       (tight_range, sma_alignment and vol_dry_up disabled)
Eval: --start-date .. --end-date, default 2021-01-01 – today; bars are loaded from WARMUP_DAYS
      before the window (burn-in, indicators only) to FORWARD_DAYS after it (exit data).
Entry: next trading day's split/dividend-adjusted open (not the signal-day close).
Every signal is scored 0-100 by the production QullamaggieRanking; results are reported both
without a ranking condition and gated at each threshold in MIN_RANKINGS.
"""

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import sqlalchemy as sa

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.cli import iso_date_type
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2021, 1, 1)
EVAL_END = date.today()
HOLD_MAX_CAL = 366  # skip entries without 366 cal days of fwd data
# Calendar days of bars loaded either side of the eval window: before it so roc_252d/SMA50/
# MIN_HISTORY are warm on its first day (the burn-in — indicators only, no signals evaluated),
# and after it so a signal on the last day still has its 366d exit. Mirrors
# turtlex/research/qullamaggie.py's WARMUP_DAYS / MARKET_SMA_WARMUP_DAYS.
WARMUP_DAYS = 730
SPY_WARMUP_DAYS = 300
LOAD_BATCH_ROWS = 200_000  # server-side cursor batch for load_bars; see the note there
MIN_AVG_VOL = 500_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
ENTRY_SEARCH_DAYS = 7  # give up if no tradeable bar appears this many calendar days after the signal
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MIN_TRADES = 30
MIN_NEG = 10
MIN_RANKINGS = [40]  # QullamaggieRanking gates to sweep; 40 is the portfolio-runner default
ALGO_VERSION = "2.0"  # version encoded in the bk50d_sX_vN labels — an identity, not a filter value

SMA_THRESHS = [0.12, 0.16, 0.20]
HOLD_CALS = [366]
FORWARD_DAYS = HOLD_MAX_CAL + ENTRY_SEARCH_DAYS + 10  # bars needed past EVAL_END to exit its last signals

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-backtest-v4.md"


# ── Data loading ───────────────────────────────────────────────────────────────


def load_spy_regime(engine: sa.Engine, start: date) -> set[date]:
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = 'SPY.US' AND date >= :start
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"start": start}).fetchall()
    spy = pl.DataFrame(
        {
            "date": pl.Series([r[0] for r in rows], dtype=pl.Date),
            "close": [float(r[1]) for r in rows],
        }
    )
    spy = spy.with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
    return set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())


def load_bars(engine: sa.Engine, start: date, end: date) -> pl.DataFrame:
    """Load daily bars with open/high/low/close adjusted for splits and dividends.

    `raw_close` (unadjusted) is kept separately for the absolute MIN_PRICE/MAX_PRICE
    filter, since adjusting it would leak knowledge of splits that hadn't happened yet
    as of the signal date. `open`/`close`/`high`/`low` are split/dividend-adjusted (scaled by
    adjusted_close/close) so rolling indicators and trade returns aren't corrupted by
    the price discontinuity a raw close shows on a split date. `open` is the entry fill
    price: trades are bought at the bar after the signal, not at the signal close.

    Args:
        engine: SQLAlchemy engine for the trading database
        start: First bar date to load — the eval-window start less WARMUP_DAYS
        end: Last bar date to load — the eval-window end plus FORWARD_DAYS
    """
    sql = """
        SELECT db.symbol,
               db.date::date             AS date,
               db.close::float8          AS raw_close,
               db.adjusted_close::float8 AS close,
               db.open::float8           AS open,
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
          AND  db.date >= :data_start
          AND  db.date <= :data_end
          AND  db.close > 0
          AND  db.adjusted_close > 0
          AND  db.volume > 0
        ORDER  BY db.symbol, db.date
    """
    # Streamed through a server-side cursor and adjusted in polars rather than fetchall()'d
    # into per-column Python lists: the earlier windows pull ~7M rows, which costs several GB
    # as row tuples plus lists and OOM-kills the host before the DataFrame is even built.
    with engine.connect().execution_options(stream_results=True, max_row_buffer=LOAD_BATCH_ROWS) as conn:
        df = pl.concat(
            pl.read_database(
                query=sa.text(sql),
                connection=conn,
                iter_batches=True,
                batch_size=LOAD_BATCH_ROWS,
                execute_options={"parameters": {"data_start": start, "data_end": end}},
            ),
            rechunk=True,
        )
    factor = pl.col("close") / pl.col("raw_close")  # adjusted_close / raw_close
    # a null/zero open leaves the bar usable for close-based indicators; run_trades rejects it
    # as an entry bar instead of dropping the row
    return df.with_columns(pl.col("open", "high", "low") * factor)


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
            pl.col("_c1").rolling_mean(50, min_samples=50).over("symbol").alias("sma50"),
            pl.col("_v1").rolling_mean(50, min_samples=50).over("symbol").alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(20, min_samples=20).over("symbol").alias("avg_vol_20"),
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


# ── Ranking ────────────────────────────────────────────────────────────────────

_ranker = QullamaggieRanking()


def compute_ranking(row: dict) -> int:
    """Score one signal row 0-100 with the production QullamaggieRanking.

    Maps `raw_close` onto the `close` column the ranking reads, because
    `QullamaggieStrategy` keeps `close` unadjusted (its adjusted series lives in
    `adj_close`) and the price bands are dollar-denominated. `adr_pct` and
    `pct_vs_sma50` are the same shift-1 indicators the entry filter used.
    """
    row_df = pl.DataFrame(
        [
            {
                "date": row["date"],
                "close": row["raw_close"],
                "adr_pct": row["adr_pct"],
                "pct_vs_sma50": row["pct_vs_sma50"],
            }
        ]
    )
    return _ranker.ranking(row_df, row["date"])


# ── Signal generation ──────────────────────────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
    """Apply the entering condition, then the per-symbol cooldown.

    The cooldown chain runs over the whole frame including the burn-in window, so a trigger
    just before EVAL_START correctly suppresses an early in-range signal; only accepted
    triggers inside [EVAL_START, EVAL_END] are returned. Mirrors
    `turtlex/research/qullamaggie.py:get_signals`.
    """
    cands = (
        df.filter(
            (pl.col("date") <= EVAL_END)
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
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(sorted(bull_dates))
        )
        .select(["symbol", "date", "close", "raw_close", "adr_pct", "pct_vs_sma50"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is not None and (d - prev).days <= COOLDOWN:
            continue
        last_trigger[sym] = d
        if d >= EVAL_START:
            rows_out.append({**row, "ranking": compute_ranking(row)})
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runner (calendar-day exits) ─────────────────────────────────────────


def run_trades(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_opens: dict[str, np.ndarray],
    hold_cal: int,
) -> list[dict]:
    """Turn signals into round-trip trades bought at the next trading day's adjusted open.

    The entry bar is the first bar strictly after the signal date; the signal is dropped if no
    bar appears within ENTRY_SEARCH_DAYS calendar days or that bar's adjusted open is not
    positive — mirroring `SignalProcessor.calculate_entry_data` and `resolve_entries` in
    `turtlex/research/qullamaggie.py`. The exit is the close of the first bar at or after
    `entry_date + hold_cal`; signals without that much forward data are dropped.
    """
    records: list[dict] = []
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        opens = sym_opens[sym]
        signal_int = (row["date"] - _EPOCH).days
        idx_entry = int(np.searchsorted(dates, signal_int, side="right"))
        if idx_entry >= len(dates) or dates[idx_entry] > signal_int + ENTRY_SEARCH_DAYS:
            continue
        if not opens[idx_entry] > 0:  # `not (x > 0)` also rejects a null open, read back as NaN
            continue
        entry_int = int(dates[idx_entry])
        entry_px = float(opens[idx_entry])
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + hold_cal))
        if idx_exit >= len(dates):
            continue
        entry_date = _EPOCH + timedelta(days=entry_int)
        # the position starts at the entry open, so that is the first point of the price path
        window = np.concatenate(([entry_px], closes[idx_entry : idx_exit + 1]))
        ret = float((closes[idx_exit] - entry_px) / entry_px)
        running_max = np.maximum.accumulate(window)
        mdd = float((1.0 - window / running_max).max())
        records.append(
            {
                "symbol": sym,
                "signal_date": row["date"],
                "entry_date": entry_date,
                "exit_date": _EPOCH + timedelta(days=int(dates[idx_exit])),
                "year": entry_date.year,
                "ret": ret,
                "mdd": mdd,
                "ranking": row["ranking"],
            }
        )
    return records


# ── Metrics ────────────────────────────────────────────────────────────────────


def compute_metrics(records: list[dict], hold_cal: int) -> dict | None:
    """Study-level metrics: the shared trade metrics plus this study's own Q75 and frequency."""
    if len(records) < MIN_TRADES:
        return None
    a = np.array([r["ret"] for r in records])
    mdds = np.array([r["mdd"] for r in records])
    ranks = np.array([r["ranking"] for r in records], dtype=float)
    m = compute_trade_metrics(a * 100, hold_cal, trade_drawdowns_pct=mdds * 100, min_losers=MIN_NEG)
    if m is None or np.isnan(m.sortino) or m.sortino <= 0:
        return None
    months = (EVAL_END.year - EVAL_START.year) * 12 + (EVAL_END.month - EVAL_START.month)
    return {
        "n": m.n,
        "rank_avg": float(ranks.mean()),
        "rank_med": float(np.median(ranks)),
        "win": m.win_pct,
        "mean": m.mean_pct,
        "ann_mean": m.ann_mean_pct,
        "med": m.median_pct,
        "q75": float(np.percentile(a, 75) * 100),
        "pf": m.profit_factor,
        "sr": m.sortino,
        "mdd": m.mean_trade_mdd_pct,
        "cvar": m.cvar95_pct,
        "freq": len(a) / max(months, 1),
    }


def consistency_flag(records: list[dict], hold_cal: int) -> tuple[str, bool]:
    by_year: dict[int, list[float]] = {}
    for r in records:
        by_year.setdefault(r["year"], []).append(r["ret"])
    valid = pos = 0
    for yr, rets in sorted(by_year.items()):
        if date(yr, 12, 31) > EVAL_END:  # incomplete calendar year
            continue
        m = compute_trade_metrics(np.array(rets) * 100, hold_cal, min_losers=MIN_NEG)
        if m is None or np.isnan(m.sortino):  # too few losing trades to judge the year
            continue
        valid += 1
        if m.sortino > 0:
            pos += 1
    consistent = valid >= 3 and (pos / valid) >= 0.70 if valid > 0 else False
    return f"{pos}/{valid}", consistent


# ── Output ─────────────────────────────────────────────────────────────────────

_HDR = (
    f"{'#':>4}  {'Entry Signal':<30}  {'Exit':>6}  "
    f"{'N':>4}  {'Win%':>5}  {'Mean%':>7}  {'AnnMean%':>8}  {'Med%':>7}  {'Q75%':>7}  {'PF':>5}  {'Sortino':>7}  "
    f"{'MaxDD%':>7}  {'CVaR%':>7}  {'F/mo':>5}  {'RkAvg':>5}  {'RkMed':>5}  {'Yrs+':>5}  {'C':>1}"
)
_SEP = "─" * len(_HDR)


def fmt_row(rank: int, label: str, hold_cal: int, m: dict, yrs: str, cons: bool) -> str:
    c = "✓" if cons else " "
    return (
        f"{rank:>4}  {label:<30}  {hold_cal:>4}d  "
        f"{m['n']:>4}  {m['win']:>5.1f}  {m['mean']:>+7.2f}  {m['ann_mean']:>+8.2f}  {m['med']:>+7.2f}  "
        f"{m['q75']:>+7.2f}  {m['pf']:>5.2f}  {m['sr']:>7.3f}  "
        f"{m['mdd']:>7.2f}  {m['cvar']:>+7.2f}  {m['freq']:>5.1f}  "
        f"{m['rank_avg']:>5.1f}  {m['rank_med']:>5.0f}  {yrs:>5}  {c}"
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


def parse_args() -> argparse.Namespace:
    """Parse the evaluation window and output path.

    Returns:
        Namespace with start_date, end_date and output.
    """
    parser = argparse.ArgumentParser(description="Qullamaggie breakout backtest v4 (SMA-threshold × ranking-gate sweep)")
    parser.add_argument("--start-date", type=iso_date_type, default=EVAL_START, help="evaluation window start (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=iso_date_type, default=EVAL_END, help="evaluation window end (YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, default=RESULT_PATH, help="markdown result path")
    return parser.parse_args()


def main() -> None:
    global EVAL_START, EVAL_END, RESULT_PATH

    args = parse_args()
    EVAL_START, EVAL_END, RESULT_PATH = args.start_date, args.end_date, args.output
    if EVAL_END <= EVAL_START:
        raise ValueError(f"--end-date {EVAL_END} must be after --start-date {EVAL_START}")

    settings = Settings.from_toml()
    data_start = EVAL_START - timedelta(days=WARMUP_DAYS)
    data_end = EVAL_END + timedelta(days=FORWARD_DAYS)
    print(f"Eval {EVAL_START} – {EVAL_END}  |  bars {data_start} – {data_end}", flush=True)

    print("Loading SPY regime …", flush=True)
    bull_dates = load_spy_regime(settings.engine, data_start - timedelta(days=SPY_WARMUP_DAYS))

    print("Loading bars …", flush=True)
    df = load_bars(settings.engine, data_start, data_end)
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    df = add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    sym_opens: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_opens[sym] = g["open"].cast(pl.Float64).to_numpy(allow_copy=True)

    results: list[tuple[str, int, dict, list[dict]]] = []
    results_gated: list[tuple[str, int, dict, list[dict]]] = []
    gate_stats: list[tuple[str, int, int, int]] = []  # (label, gate, signals_total, signals_passing)

    for sma_t in SMA_THRESHS:
        lbl = f"bk50d_s{round(sma_t * 100)}_v{ALGO_VERSION}"
        print(f"  {lbl} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        if signals.is_empty():
            continue
        for hold_cal in HOLD_CALS:
            records = run_trades(signals, sym_dates, sym_closes, sym_opens, hold_cal)
            m = compute_metrics(records, hold_cal)
            if m is not None:
                results.append((lbl, hold_cal, m, records))
        for min_rank in MIN_RANKINGS:
            signals_gated = signals.filter(pl.col("ranking") >= min_rank)
            gate_stats.append((lbl, min_rank, signals.height, signals_gated.height))
            if signals_gated.is_empty():
                continue
            for hold_cal in HOLD_CALS:
                records_gated = run_trades(signals_gated, sym_dates, sym_closes, sym_opens, hold_cal)
                m_gated = compute_metrics(records_gated, hold_cal)
                if m_gated is not None:
                    results_gated.append((f"{lbl} R≥{min_rank}", hold_cal, m_gated, records_gated))

    results.sort(key=lambda x: x[2]["sr"], reverse=True)
    results_gated.sort(key=lambda x: x[2]["sr"], reverse=True)

    # ── Print tables ───────────────────────────────────────────────────────────
    header_lines = [
        f"Period: {EVAL_START} – {EVAL_END}  |  HOLD_MAX_CAL={HOLD_MAX_CAL}d",
        f"Fixed: roc_12m<{int(ROC_CAP * 100)}%, "
        f"vol_surge<{VOL_SURGE_MAX}x (no lower bound), RSI<{int(RSI_CAP)}, ADR>={ADR_MIN * 100:.1f}%, "
        f"ADR_change<{int(ADR_CHANGE_CAP * 100)}%, SPY>200d SMA, "
        f"close>${MIN_PRICE:.0f}&<${MAX_PRICE:.0f}, avg_vol>={MIN_AVG_VOL // 1000}K",
        f"Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py)",
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

    gates_str = ", ".join(str(r) for r in MIN_RANKINGS)
    output_gated, consistent_gated = build_rankings(
        results_gated, [*header_lines[:-1], f"Ranking gate sweep: QullamaggieRanking ≥ {gates_str}", ""]
    )
    print("\n" + output_gated)
    print_consistent(
        f"Consistent (Ranking ≥ {gates_str}) — Sortino>0 in ≥70% of complete eval years, ≥3 valid years",
        consistent_gated,
    )

    gate_lines = [
        f"{'Entry Signal':<24}  {'Gate':>5}  {'Signals':>8}  {'Passing':>8}  {'Rejected':>9}  {'Reject%':>8}",
        "─" * 72,
    ]
    for lbl, gate, total, passing in gate_stats:
        rejected = total - passing
        gate_lines.append(f"{lbl:<24}  {gate:>5}  {total:>8}  {passing:>8}  {rejected:>9}  {rejected / total * 100:>7.1f}%")
    gate_table = "\n".join(gate_lines)
    print(f"\n=== Ranking gate selectivity (signal level) ===\n{gate_table}")

    # ── Write markdown result ──────────────────────────────────────────────────
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Backtest v4 — Results\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        sma_vals = ", ".join(f"{int(v * 100)}%" for v in SMA_THRESHS)
        hold_vals = ", ".join(f"{h}d" for h in HOLD_CALS)
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Algorithm version | {ALGO_VERSION} (encoded as `_v{ALGO_VERSION}` in the names below) |\n")
        fh.write("| Breakout | 50d high |\n")
        fh.write(f"| Entry | next trading day's adjusted open (within {ENTRY_SEARCH_DAYS} cal days of the signal) |\n")
        fh.write("| Exit | close of the first bar at or after entry + hold |\n")
        fh.write(f"| SMA thresh sweep | {sma_vals} |\n")
        fh.write("| Tight range | disabled (commented out) |\n")
        fh.write(f"| Hold sweep | {hold_vals} (calendar) |\n")
        fh.write("| Ranking | QullamaggieRanking (ADR 40 / SMA50 35 / price 25) |\n")
        fh.write(f"| Ranking gate sweep | ungated, ≥ {gates_str} |\n")
        fh.write("| vol_dry_up | disabled (commented out) |\n")
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
        fh.write(f"| Eval period | {EVAL_START} – {EVAL_END} |\n")
        fh.write(f"| Burn-in (indicators only) | {EVAL_START - timedelta(days=WARMUP_DAYS)} – {EVAL_START} |\n")
        fh.write("| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |\n\n")
        fh.write("## Rankings — No Ranking Condition\n\n```text\n")
        fh.write(output)
        fh.write("\n```\n\n")
        fh.write(consistent_md("Consistent Combinations", consistent_rows))

        fh.write(f"\n## Rankings — Ranking Gate Sweep (R ≥ {gates_str})\n\n")
        fh.write(
            "Same signals, but a trade is taken only if its `QullamaggieRanking` score "
            f"(`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over {gates_str} (40 is the "
            "`--min-signal-ranking` default). The score is computed from the same shift-1 indicators the "
            "entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no "
            "look-ahead.\n\n```text\n"
        )
        fh.write(output_gated)
        fh.write("\n```\n\n")
        fh.write(consistent_md(f"Consistent Combinations (Ranking ≥ {gates_str})", consistent_gated))

        fh.write("\n## Ranking Gate Selectivity\n\nHow many signals each gate removes, at signal level.\n\n")
        fh.write(f"```text\n{gate_table}\n```\n")

        fh.write("\n## Findings & Caveats\n\n")
        fh.write("### Ideas to improve\n\n")
        ideas = [
            "source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot",
            "source a delisted-ticker history if available to address survivorship",
            "add a slippage/commission assumption on top of the next-day-open fill",
            f"widen the gate sweep past {max(MIN_RANKINGS)} to find where the score stops separating outcomes",
            "report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold",
            "account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence",
            "re-run all three windows (2010-2015, 2016-2020, 2021-present) before accepting any parameter change — "
            "a change that only improves the window it was chosen on is fitted to that window",
            f"pick the ranking gate per SMA threshold rather than one R≥{MIN_RANKINGS[0]} across s12/s16/s20; the same "
            "score rejects a very different share of each, so it is not the same filter at each",
            "report each year's negative-trade count next to its Sortino — under the gate a thin window can fall below "
            f"the {MIN_NEG}-loser bar and silently drop out of the Yrs+ denominator",
        ]
        for idea in ideas:
            fh.write(f"- {idea}\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
