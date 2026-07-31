#!/usr/bin/env python3
"""
Limit-order fill sensitivity test for the 366d-hold cohorts of qullamaggie-backtest-v4.

Cohorts: bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (all 366d hold, MIN_RANKING >= 40).
Bars, indicators, the SPY regime and entry resolution come from turtlex.research.qullamaggie,
which is parity-tested against QullamaggieStrategy; the filter chain and cooldown are local
copies of it (RSI<70, ADR mean-of-ratios>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x,
vol_dry_up<90%, no tight_range, SPY>200d SMA, close>$5&<$250, avg_vol>=500K).
open/close/high/low are split/dividend-adjusted; the $5-$250 band stays on the raw close.

Entry convention is the dimension under study, so three are reported side by side:
  next-open  buy at the next trading day's adjusted open — the canonical v2.0 entry and the
             reference the limit variants should be judged against.
  EOD        buy at signal-day close. The pre-v2.0 convention, kept so this study's numbers
             remain comparable with its earlier runs; it is also what the monthly grids use.
Limit sweep: place a resting limit buy at signal_day_close * (1 - X%) for X% in {0, 1, 2, 3, 4, 5},
             good for 30 calendar days from the signal day. It fills on the first trading day within
             that window whose low <= limit price (entry price = limit price); if no day in the
             window touches the limit, the order expires unfilled. Hold 366 calendar days from the
             fill day (same HOLD_MAX_CAL forward-data requirement as the backtest).

Also reports monthly seasonality (Mean%/N by entry year x month) for the EOD baseline of each cohort.

Period: 2010-01-01 - 2026-06-26  (warmup handled by qm.load_bars).

References: docs/research/qullamaggie-backtest-v4.md, docs/research/result-qullamaggie-backtest-v4.md
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

_EPOCH = date(1970, 1, 1)
EVAL_START = date(2010, 1, 1)
EVAL_END = date(2026, 6, 26)
HOLD_CAL = 366
HOLD_MAX_CAL = 366
LIMIT_WINDOW_CAL = 30  # limit order stays resting this many calendar days after the signal

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
MIN_NEG = 10

LIMIT_PCTS = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
MIN_RANKING = 40  # QullamaggieRanking gate, matching the portfolio-runner default
SMA_THRESHS = [(0.20, "bk50d_s20_v2.0"), (0.16, "bk50d_s16_v2.0"), (0.12, "bk50d_s12_v2.0")]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-cohorts-limit-order.md"


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


# ── Signal generation ────────────────────────────────────────────────────────


def get_signals(df: pl.DataFrame, bull_dates: set[date], sma_t: float) -> pl.DataFrame:
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
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < ROC_CAP)
            & pl.col("date").is_in(bull_dates)
        )
        .select(["symbol", "date", "raw_close", "adj_close", "adr_pct", "pct_vs_sma50"])
        .sort(["symbol", "date"])
    )
    if cands.is_empty():
        return cands
    rows_out: list[dict] = []
    last_trigger: dict[str, date] = {}
    # Cooldown runs from the warmup window rather than EVAL_START, so a trigger just before
    # the window suppresses an early in-window signal — the ordering qm.get_signals uses.
    # Only accepted triggers on or after EVAL_START are emitted.
    for row in cands.iter_rows(named=True):
        sym, d = row["symbol"], row["date"]
        prev = last_trigger.get(sym)
        if prev is None or (d - prev).days > COOLDOWN:
            last_trigger[sym] = d
            if d >= EVAL_START and compute_ranking(row) >= MIN_RANKING:
                rows_out.append(row)
    return pl.DataFrame(rows_out) if rows_out else cands.clear()


# ── Trade runners ──────────────────────────────────────────────────────────────


def run_trades_eod(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
    """Buy at signal-day close (backtest-v4 baseline). Records entry year/month for the monthly breakdown."""
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
        ret = float(closes[idx_exit] / closes[idx_entry] - 1.0)
        records.append({"year": row["date"].year, "month": row["date"].month, "ret": ret})
    return records


def run_trades_open(
    entered: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
) -> list[dict]:
    """Buy at the next trading day's adjusted open — the canonical v2.0 entry.

    This is the reference the limit variants should be judged against: it is what the live
    strategy actually does, whereas the EOD row below is the older same-day-close convention
    kept for continuity with the earlier runs of this study.

    Takes the already-resolved frame rather than calling `qm.resolve_entries` itself, so the
    caller can report how many signals it dropped for want of a next bar.
    """
    records: list[dict] = []
    for row in entered.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        entry_int = (row["entry_date"] - _EPOCH).days
        if dates[-1] < entry_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, entry_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue
        ret = float(closes[idx_exit] / float(row["entry_price"]) - 1.0)
        records.append({"year": row["date"].year, "month": row["date"].month, "ret": ret})
    return records


def run_trades_limit(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_lows: dict[str, np.ndarray],
    limit_pct: float,
) -> tuple[list[dict], int, int]:
    """Buy via a resting limit order, good for LIMIT_WINDOW_CAL calendar days after the signal.

    Fills on the first trading day in that window whose low <= limit price; entry price = limit
    price. Returns (records, n_attempted, n_filled).
    """
    records: list[dict] = []
    n_attempted = 0
    n_filled = 0
    for row in signals.iter_rows(named=True):
        sym = row["symbol"]
        if sym not in sym_dates:
            continue
        dates = sym_dates[sym]
        closes = sym_closes[sym]
        lows = sym_lows[sym]
        signal_int = (row["date"] - _EPOCH).days
        idx_signal = int(np.searchsorted(dates, signal_int))
        if idx_signal >= len(dates) or dates[idx_signal] != signal_int:
            continue

        idx_start = idx_signal + 1
        if idx_start >= len(dates):
            continue

        n_attempted += 1
        limit_price = closes[idx_signal] * (1.0 - limit_pct)
        idx_end = int(np.searchsorted(dates, signal_int + LIMIT_WINDOW_CAL, side="right")) - 1
        idx_end = min(idx_end, len(dates) - 1)

        fill_idx: int | None = None
        for idx in range(idx_start, idx_end + 1):
            if lows[idx] <= limit_price:
                fill_idx = idx
                break
        if fill_idx is None:
            continue  # order expired unfilled
        n_filled += 1

        fill_day_int = int(dates[fill_idx])
        if dates[-1] < fill_day_int + HOLD_MAX_CAL:
            continue
        idx_exit = int(np.searchsorted(dates, fill_day_int + HOLD_CAL))
        if idx_exit >= len(dates):
            continue

        ret = float(closes[idx_exit] / limit_price - 1.0)
        records.append({"ret": ret})
    return records, n_attempted, n_filled


# ── Metrics ────────────────────────────────────────────────────────────────────


def sortino(a: np.ndarray) -> float:
    neg = a[a < 0]
    if len(neg) < MIN_NEG:
        return float("nan")
    dd = float(np.sqrt(np.mean(neg**2)))
    return float(np.mean(a) * np.sqrt(365 / HOLD_CAL) / dd) if dd > 0 else float("nan")


def compute_metrics(records: list[dict]) -> dict:
    if not records:
        return {"n": 0, "win": float("nan"), "mean": float("nan"), "med": float("nan"), "pf": float("nan"), "sr": float("nan")}
    a = np.array([r["ret"] for r in records])
    gross_win = float(a[a > 0].sum())
    gross_loss = float(-a[a < 0].sum())
    return {
        "n": len(a),
        "win": float((a > 0).mean() * 100),
        "mean": float(a.mean() * 100),
        "med": float(np.median(a) * 100),
        "pf": gross_win / gross_loss if gross_loss > 0 else float("inf"),
        "sr": sortino(a),
    }


# ── Output ─────────────────────────────────────────────────────────────────────

_HDR = f"{'Cohort':<16} {'Fill%':>7} {'N':>5} {'Med%':>8} {'Mean%':>8} {'Win%':>7} {'Sortino':>8} {'PF':>7}"
_SEP = "-" * len(_HDR)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_calendar_table(records: list[dict], label: str) -> str:
    """Monthly Mean%/N grid (rows=year, cols=month) grouped by each trade's entry year/month."""
    by_ym: dict[tuple[int, int], list[float]] = {}
    for r in records:
        by_ym.setdefault((r["year"], r["month"]), []).append(r["ret"])

    hdr = f"{'Year':>5} |" + "".join(f"{m:>8}" for m in MONTHS) + f" | {'Mean%':>7} {'N':>5}"
    sep = "-" * len(hdr)
    lines = [f"### {label} — Monthly Mean% / N (EOD, entry month/year)\n", "```text", hdr, sep]

    if not by_ym:
        lines += ["(no trades)", "```\n"]
        return "\n".join(lines)

    for year in sorted({y for y, _m in by_ym}):
        cells: list[str] = []
        year_rets: list[float] = []
        for month_idx in range(1, 13):
            vals = by_ym.get((year, month_idx))
            if vals:
                cell = f"{np.mean(vals) * 100:+.1f}|{len(vals)}"
                year_rets.extend(vals)
            else:
                cell = "·"
            cells.append(f"{cell:>8}")
        year_mean_pct = float(np.mean(year_rets)) * 100 if year_rets else float("nan")
        lines.append(f"{year:>5} |" + "".join(cells) + f" | {year_mean_pct:>+6.1f}% {len(year_rets):>4}")

    lines.append("```\n")
    return "\n".join(lines)


def fill_pct_of(m: dict, n_signals: int) -> str:
    """Completed trades as a share of signals generated.

    The two reference rows are not 100% fills: both drop entries lacking 366d of forward
    data, and next-open additionally drops signals with no next bar. Reporting the real
    share keeps their Mean%/Sortino gap readable as an entry-convention effect rather
    than an invisible difference in sample composition.
    """
    return f"{m['n'] / n_signals * 100:.1f}%" if n_signals > 0 else "n/a"


def fmt_row(label: str, fill_pct: str, m: dict) -> str:
    sr_str = f"{m['sr']:>8.3f}" if not np.isnan(m["sr"]) else f"{'n/a':>8}"
    pf_str = f"{m['pf']:>7.2f}" if np.isfinite(m["pf"]) else f"{'inf':>7}"
    if m["n"] == 0:
        return f"{label:<16} {fill_pct:>7} {0:>5}      --       --      --      n/a      --"
    return f"{label:<16} {fill_pct:>7} {m['n']:>5} {m['med']:>+7.1f}% {m['mean']:>+7.1f}% {m['win']:>6.1f}% {sr_str} {pf_str}"


def main() -> None:
    settings = Settings.from_toml()

    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading bars …", flush=True)
    # Bars run past EVAL_END: a 366d hold needs forward data beyond the last signal date.
    df = qm.load_bars(bars_history, EVAL_START, date.today())
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    # Project down to the columns qm.resolve_entries reads before building the indicator
    # frame, so the full-width bar frame is released rather than held alongside it.
    bars = df.select("symbol", "date", "adj_open")
    df = qm.add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    sym_lows: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_lows[sym] = g["adj_low"].cast(pl.Float64).to_numpy(allow_copy=True)

    report_sections: list[str] = []
    calendar_sections: list[str] = []
    for sma_t, label in SMA_THRESHS:
        print(f"Generating signals for {label} …", flush=True)
        signals = get_signals(df, bull_dates, sma_t)
        entered = qm.resolve_entries(signals, bars)
        n_sig = len(signals)
        print(f"  {n_sig} gated signals, {len(entered)} with an entry bar", flush=True)

        lines = [f"### {label} — 366d\n", "```text", _HDR, _SEP]

        open_m = compute_metrics(run_trades_open(entered, sym_dates, sym_closes))
        lines.append(fmt_row("next-open (v2.0)", fill_pct_of(open_m, n_sig), open_m))

        eod_records = run_trades_eod(signals, sym_dates, sym_closes)
        eod_m = compute_metrics(eod_records)
        lines.append(fmt_row("EOD (legacy)", fill_pct_of(eod_m, n_sig), eod_m))
        lines.append(_SEP)

        for lp in LIMIT_PCTS:
            records, n_att, n_fill = run_trades_limit(signals, sym_dates, sym_closes, sym_lows, lp)
            fill_pct = f"{n_fill / n_att * 100:.1f}%" if n_att > 0 else "n/a"
            m = compute_metrics(records)
            lines.append(fmt_row(f"{lp * 100:.0f}%", fill_pct, m))

        lines.append("```\n")
        section = "\n".join(lines)
        report_sections.append(section)
        print("\n" + section)

        calendar_section = build_calendar_table(eod_records, label)
        calendar_sections.append(calendar_section)
        print("\n" + calendar_section)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write("# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write(f"Period: {EVAL_START} – {EVAL_END}  |  Hold: {HOLD_CAL}d (calendar)\n\n")
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Cohorts | {', '.join(label for _t, label in SMA_THRESHS)} (366d) |\n")
        fh.write(f"| Limit sweep | X% = {', '.join(f'{int(lp * 100)}%' for lp in LIMIT_PCTS)} |\n")
        fh.write(
            f"| Limit order rule | resting limit at signal_day_close x (1 - X%), good for {LIMIT_WINDOW_CAL} calendar days; "
            "fills on the first day in that window whose low <= limit price, else expires unfilled |\n"
        )
        fh.write(
            "| Baselines | next-open — buy at the next trading day's adjusted open (canonical v2.0); "
            "EOD — buy at signal-day close (pre-v2.0, retained for continuity) |\n"
        )
        fh.write("| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90% (no tight_range) |\n")
        fh.write(f"| Ranking gate | QullamaggieRanking >= {MIN_RANKING} |\n")
        fh.write("| Market regime | SPY close > 200d SMA |\n")
        fh.write(f"| Price range | > ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f} |\n")
        fh.write(f"| Min avg vol (20d) | >= {MIN_AVG_VOL // 1000}K |\n")
        fh.write(f"| Cooldown | {COOLDOWN} calendar days |\n")
        fh.write("| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |\n\n")
        fh.write("## Results\n\n")
        for section in report_sections:
            fh.write(section)
            fh.write("\n")
        fh.write("## Monthly Seasonality (EOD baseline)\n\n")
        fh.write(
            "Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the "
            "EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The "
            "Mean%/N columns on the right are the year's aggregate across all its months.\n\n"
        )
        for section in calendar_sections:
            fh.write(section)
            fh.write("\n")
        fh.write("## Findings & Caveats\n\n")
        fh.write(
            f"- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for "
            f"{LIMIT_WINDOW_CAL} calendar days and fills on the *first* day the low touches the limit price. This "
            "raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are "
            "increasingly dominated by trades that took most of the window to retrace that far — those signals "
            "have effectively already spent part of their 366d hold going nowhere (or down) before the position "
            "even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the "
            "signal day).\n\n"
        )
        fh.write(
            "- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering "
            "the breakout signal — this is not a neutral resampling of the same trade population as the EOD "
            "baseline; it systematically selects for breakouts that gave back some of the signal-day gain before "
            "continuing (or failing), which can bias mean/median returns in either direction depending on regime.\n\n"
        )
        fh.write(
            "- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under "
            "30 are not statistically reliable, even if the ratios look attractive.\n\n"
        )
        fh.write(
            "- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are "
            "split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the "
            "modeled discount), and hold length is measured in calendar days from the fill day, not the original "
            "signal day.\n\n"
        )
        fh.write(
            "- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit "
            "order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the "
            "limit price would fill better than modeled).\n"
        )
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
