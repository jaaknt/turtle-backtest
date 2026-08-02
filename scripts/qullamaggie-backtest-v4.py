#!/usr/bin/env python3
"""
Qullamaggie-style breakout backtest v4.
Spec: docs/research/qullamaggie-backtest-v4.md

Fixed filters: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%,
               ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sweep: SMA_THRESH ∈ {12%,16%,20%} × HOLD_CAL ∈ {366 cal days}
       (tight_range, sma_alignment and vol_dry_up disabled)
Eval: --start-date .. --end-date, default 2021-01-01 – 2025-12-31; bars are loaded from WARMUP_DAYS
      before the window (burn-in, indicators only) forward to DATA_END, so a trade entered late in
      the window can still reach its 366d exit; entries whose exit falls past DATA_END are skipped.
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
# Fixed, not date.today(): a trade needs HOLD_MAX_CAL days of forward data to reach its exit, so
# scanning up to today only generates signals that are then dropped for want of an exit. Bump this
# as new years complete — or pass --end-date.
EVAL_END = date(2025, 12, 31)
# Last bar date the study may use. Signals stop at EVAL_END, but exits may reach forward to here,
# so a trade entered late in the window can still complete its 366d hold. Capped rather than
# open-ended so the historical windows don't drag in a decade of bars they never look at.
DATA_END = date(2026, 6, 30)
HOLD_MAX_CAL = 366  # skip entries without 366 cal days of fwd data
# Calendar days of bars loaded before the eval window so roc_252d/SMA50/MIN_HISTORY are warm on
# its first day (the burn-in — indicators only, no signals evaluated). Mirrors
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
# Only this variant, gated at MIN_RANKINGS[0], gets the monthly Mean%/N grid — it is the
# reference algorithm (see CLAUDE.md), and one grid per combination would be six tables.
MONTHLY_GRID_SMA_THRESH = 0.12
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Monthly-grid cell layout: `<mean>|<n>`, each half padded on its own so the `|` stays in a
# fixed column. 6 fits +1234.5-style means without shifting; 3 fits a 999-trade month.
_MEAN_W = 6
_N_W = 3

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
        end: Last bar date to load — the eval-window end
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
        ret = float((closes[idx_exit] - entry_px) / entry_px)
        records.append(
            {
                "symbol": sym,
                "signal_date": row["date"],
                "entry_date": entry_date,
                "exit_date": _EPOCH + timedelta(days=int(dates[idx_exit])),
                "ret": ret,
                "ranking": row["ranking"],
            }
        )
    return records


# ── Metrics ────────────────────────────────────────────────────────────────────


def compute_metrics(records: list[dict], hold_cal: int) -> dict | None:
    """Study-level metrics: the shared trade metrics plus this study's own signal frequency.

    `mean` carries the **annualized** mean return — with a single 366d hold it differs from the
    raw mean only by the 365/366 factor, but reporting one annualized figure keeps the column
    comparable with studies run at other holding periods.
    """
    if len(records) < MIN_TRADES:
        return None
    a = np.array([r["ret"] for r in records])
    m = compute_trade_metrics(a * 100, hold_cal, min_losers=MIN_NEG)
    if m is None or np.isnan(m.sortino) or m.sortino <= 0:
        return None
    months = (EVAL_END.year - EVAL_START.year) * 12 + (EVAL_END.month - EVAL_START.month)
    return {
        "n": m.n,
        "win": m.win_pct,
        "mean": m.ann_mean_pct,
        "med": m.median_pct,
        "pf": m.profit_factor,
        "sr": m.sortino,
        "cvar": m.cvar95_pct,
        "freq": len(a) / max(months, 1),
    }


# ── Output ─────────────────────────────────────────────────────────────────────

# The hold is fixed at HOLD_CALS, so an Exit column would repeat one value on every row; Mean%
# carries the annualized figure directly rather than reporting raw and annualized side by side.
_HDR = (
    f"{'Entry Signal':<16}  {'Gate':<8}  "
    f"{'N':>4}  {'Win%':>5}  {'Mean%':>7}  {'Med%':>7}  {'PF':>5}  {'Sortino':>7}  "
    f"{'CVaR%':>7}  {'F/mo':>5}"
)
_SEP = "─" * len(_HDR)


def fmt_row(label: str, gate_label: str, m: dict) -> str:
    return (
        f"{label:<16}  {gate_label:<8}  "
        f"{m['n']:>4}  {m['win']:>5.1f}  {m['mean']:>+7.2f}  {m['med']:>+7.2f}  "
        f"{m['pf']:>5.2f}  {m['sr']:>7.3f}  "
        f"{m['cvar']:>+7.2f}  {m['freq']:>5.1f}"
    )


def build_rankings(results: list[tuple[str, str, dict]]) -> str:
    """Render one table carrying both ranking treatments.

    `results` arrives already ordered: algorithm groups in SMA-threshold order, and within each
    group the ungated row followed by the gated one, so the pair reads across instead of across
    two separate tables (Step 6 of the spec).

    Args:
        results: `(label, gate_label, metrics)` in display order

    Returns:
        The rendered table.
    """
    lines = [_HDR, _SEP]
    for lbl, gate_label, m in results:
        lines.append(fmt_row(lbl, gate_label, m))
    lines += ["", f"Valid combinations: {len(results)}"]
    return "\n".join(lines)


def build_monthly_grid(records: list[dict]) -> str:
    """Monthly `Mean%|N` grid, rows = entry year, columns = entry month.

    Each cell is the mean 366d return of the trades *entered* that month and how many there
    were; `·` marks a month with no entries. The right-hand pair is the year's own aggregate
    across all its months, not the mean of the cells.

    The two halves of a cell are padded independently — mean right-aligned in `_MEAN_W`, count
    left-aligned in `_N_W` — so the `|` lands in the same column on every row. Right-aligning
    the joined string instead lets the separator drift with each cell's width, which is what
    makes the numbers impossible to scan down a column.

    Args:
        records: trade records carrying `entry_date` and `ret`

    Returns:
        The rendered fixed-width grid.
    """
    by_ym: dict[tuple[int, int], list[float]] = {}
    for r in records:
        entry = r["entry_date"]
        by_ym.setdefault((entry.year, entry.month), []).append(r["ret"])

    empty = f"{'·':>{_MEAN_W}}{'':{_N_W + 1}}"  # dot sits under the mean column
    hdr = f"{'Year':>5} | " + " ".join(f"{mo:>{_MEAN_W}}{'':{_N_W + 1}}" for mo in MONTHS) + f" | {'Mean%':>7} {'N':>5}"
    lines = [hdr, "-" * len(hdr)]
    if not by_ym:
        return "\n".join([*lines, "(no trades)"])

    for year in sorted({y for y, _m in by_ym}):
        cells: list[str] = []
        year_rets: list[float] = []
        for month_idx in range(1, 13):
            vals = by_ym.get((year, month_idx))
            if vals:
                cells.append(f"{np.mean(vals) * 100:>+{_MEAN_W}.1f}|{len(vals):<{_N_W}}")
                year_rets.extend(vals)
            else:
                cells.append(empty)
        year_mean = float(np.mean(year_rets)) * 100 if year_rets else float("nan")
        lines.append(f"{year:>5} | " + " ".join(cells) + f" | {year_mean:>+6.1f}% {len(year_rets):>5}")
    return "\n".join(lines)


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
    # Forward bars only as far as the last entry could need (EVAL_END + hold + entry search),
    # and never past DATA_END — so a 2010-2015 run loads ~7 years, not ~18.
    data_end = min(DATA_END, EVAL_END + timedelta(days=HOLD_MAX_CAL + ENTRY_SEARCH_DAYS))
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

    # Spec Step 6 fixes the output order: algorithms from the widest SMA threshold down
    # (s20, s16, s12), and within each the ungated row before the gated one.
    results: list[tuple[str, str, dict]] = []
    monthly_label = ""
    monthly_records: list[dict] = []

    for sma_t in sorted(SMA_THRESHS, reverse=True):
        lbl = f"bk50d_s{round(sma_t * 100)}_v{ALGO_VERSION}"
        print(f"  {lbl} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        if signals.is_empty():
            continue
        for hold_cal in HOLD_CALS:
            records = run_trades(signals, sym_dates, sym_closes, sym_opens, hold_cal)
            m = compute_metrics(records, hold_cal)
            if m is not None:
                results.append((lbl, "ungated", m))
        for min_rank in MIN_RANKINGS:
            signals_gated = signals.filter(pl.col("ranking") >= min_rank)
            if signals_gated.is_empty():
                continue
            for hold_cal in HOLD_CALS:
                records_gated = run_trades(signals_gated, sym_dates, sym_closes, sym_opens, hold_cal)
                m_gated = compute_metrics(records_gated, hold_cal)
                if m_gated is not None:
                    results.append((lbl, f"R>={min_rank}", m_gated))
                    if sma_t == MONTHLY_GRID_SMA_THRESH and min_rank == MIN_RANKINGS[0]:
                        monthly_label, monthly_records = f"{lbl} R>={min_rank}", records_gated

    # ── Print tables ───────────────────────────────────────────────────────────

    gates_str = ", ".join(str(r) for r in MIN_RANKINGS)
    output = build_rankings(results)
    print("\n" + output)

    monthly_grid = build_monthly_grid(monthly_records) if monthly_records else ""
    if monthly_grid:
        print(f"\n=== {monthly_label} — Monthly Mean% / N ===\n{monthly_grid}")

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
        fh.write(f"| Hold sweep | {hold_vals} (calendar); entries without {HOLD_MAX_CAL}d of forward data are skipped |\n")
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
        fh.write("| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |\n")
        fh.write(f"| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min {MIN_NEG} losers (turtlex/backtest/metrics.py) |\n\n")
        fh.write("## Rankings\n\n")
        fh.write(
            "Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: "
            "`ungated` takes every signal that meets the entering condition, "
            f"`R>={gates_str}` takes a trade only if its `QullamaggieRanking` score "
            "(`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. "
            "The two rows come from the same signals, held and exited identically, so the difference "
            "isolates the gate — the drop in `N` between them is how selective it is. The score uses "
            "the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw "
            "signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold "
            "(s20, s16, s12), ungated before gated.\n\n```text\n"
        )
        fh.write(output)
        fh.write("\n```\n\n")
        if monthly_grid:
            fh.write(f"## Monthly Mean% / N — {monthly_label}\n\n")
            fh.write(
                "Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the "
                "full 366 days; `·` marks a month with no entries. The right-hand pair is the year's "
                "own aggregate across all its months, not the mean of the cells. Only this one "
                "combination is shown — it is the reference algorithm, and a grid per combination "
                "would be six tables.\n\n```text\n"
            )
            fh.write(monthly_grid)
            fh.write("\n```\n\n")

        fh.write("## Findings & Caveats\n\n")
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
            "report per-year Sortino again — the Yrs+/Consistent columns were dropped from the table, so a "
            "combination that only works in one year is no longer visible at a glance",
        ]
        for idea in ideas:
            fh.write(f"- {idea}\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
