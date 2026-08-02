#!/usr/bin/env python3
"""
Limit-order fill-rate grid for bk50d_s12_v2.0 signals (pure fill-probability
study — no hold/return computation).

For each signal, a resting limit buy is placed at signal_day_close * (1 - X%) for
X% in {0, 1, 2, 3, 4, 5}, eligible from the day after the signal. The order fills on
the first trading day whose low <= limit price within Y calendar days of the signal
day (Y in {30, 60, 90}), else expires unfilled. Reports Fill% plus median/mean
trading days from signal to fill (filled orders only) per X x Y cell.

Bars, indicators and the SPY regime come from turtlex.research.qullamaggie, which is
parity-tested against QullamaggieStrategy; the filter chain and cooldown are local copies
of it (RSI<70, ADR mean-of-ratios >=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x,
SPY>200d SMA, close>$5&<$250, avg_vol>=100K, no tight_range, cooldown 30d,
mcap>=1.5B excl Comm/RE), plus a QullamaggieRanking >= MIN_RANKING gate. open/close/high/low
are split/dividend-adjusted; the fill test uses adjusted prices — same convention as
scripts/qullamaggie-cohorts-limit-order.py's run_trades_limit.

Period: 2010-06-01 - today  (warmup handled by qm.load_bars).

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
EVAL_START = date(2010, 6, 1)
EVAL_END = date.today()

MIN_AVG_VOL = 100_000
MIN_PRICE = 5.0
MAX_PRICE = 250.0
MIN_HISTORY = 300
COOLDOWN = 30
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90

SMA_T = 0.12
LABEL = "bk50d_s12_v2.0"

LIMIT_PCTS = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
MIN_RANKING = 40  # QullamaggieRanking gate, matching the portfolio-runner default
WINDOWS_CAL = [30, 60, 90]  # limit order stays resting this many calendar days after the signal

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-limit-fill-rate.md"


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


# ── Signal generation ─


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
            & (pl.col("pct_vs_sma50") >= sma_t)
            & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
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


# ── Fill analysis ──────────────────────────────────────────────────────────────


def run_fill_analysis(
    signals: pl.DataFrame,
    sym_dates: dict[str, np.ndarray],
    sym_closes: dict[str, np.ndarray],
    sym_lows: dict[str, np.ndarray],
) -> tuple[int, int, dict[tuple[float, int], list[int]]]:
    """Sweep the X% x Y-day fill grid over all signals.

    For each signal and each limit discount X%, finds the first trading day (starting
    the day after the signal) whose low <= signal_day_close * (1 - X%); the fill counts
    toward every window Y that the touch falls inside (calendar days from the signal).

    Returns (n_attempted, n_full_window, fills) where n_attempted counts signals with at
    least one following bar, n_full_window counts those with data covering the longest
    window, and fills maps (limit_pct, window_cal) -> list of trading-days-to-fill.
    """
    max_window = max(WINDOWS_CAL)
    fills: dict[tuple[float, int], list[int]] = {(lp, w): [] for lp in LIMIT_PCTS for w in WINDOWS_CAL}
    n_attempted = 0
    n_full_window = 0
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
        if dates[-1] >= signal_int + max_window:
            n_full_window += 1
        idx_end = int(np.searchsorted(dates, signal_int + max_window, side="right")) - 1
        idx_end = min(idx_end, len(dates) - 1)

        for lp in LIMIT_PCTS:
            limit_price = closes[idx_signal] * (1.0 - lp)
            for idx in range(idx_start, idx_end + 1):
                if lows[idx] <= limit_price:
                    days_cal = int(dates[idx]) - signal_int
                    days_trading = idx - idx_signal
                    for w in WINDOWS_CAL:
                        if days_cal <= w:
                            fills[(lp, w)].append(days_trading)
                    break
    return n_attempted, n_full_window, fills


# ── Output ─────────────────────────────────────────────────────────────────────


def build_grid(n_attempted: int, fills: dict[tuple[float, int], list[int]]) -> str:
    blocks = [f"{f'Y={w}d':^22}" for w in WINDOWS_CAL]
    hdr1 = f"{'X%':>4}  | " + " | ".join(blocks)
    hdr2 = f"{'':>4}  | " + " | ".join(f"{'Fill%':>7} {'MedD':>6} {'MeanD':>6}" for _ in WINDOWS_CAL)
    sep = "-" * len(hdr2)
    lines = [hdr1, hdr2, sep]
    for lp in LIMIT_PCTS:
        cells = []
        for w in WINDOWS_CAL:
            d = fills[(lp, w)]
            if d:
                fill_pct = len(d) / n_attempted * 100
                cells.append(f"{fill_pct:>6.1f}% {float(np.median(d)):>6.1f} {float(np.mean(d)):>6.1f}")
            else:
                cells.append(f"{'--':>7} {'--':>6} {'--':>6}")
        lines.append(f"{lp * 100:>3.0f}%  | " + " | ".join(cells))
    return "\n".join(lines)


def build_counts(n_attempted: int, fills: dict[tuple[float, int], list[int]]) -> str:
    hdr = f"{'X%':>4}  | " + " | ".join(f"{f'n_filled Y={w}d':>14}" for w in WINDOWS_CAL)
    sep = "-" * len(hdr)
    lines = [hdr, sep]
    for lp in LIMIT_PCTS:
        cells = [f"{len(fills[(lp, w)]):>14}" for w in WINDOWS_CAL]
        lines.append(f"{lp * 100:>3.0f}%  | " + " | ".join(cells))
    return "\n".join(lines)


def main() -> None:
    settings = Settings.from_toml()

    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading bars …", flush=True)
    df = qm.load_bars(bars_history, EVAL_START, EVAL_END)
    valid_syms = df.group_by("symbol").agg(pl.len().alias("n")).filter(pl.col("n") >= MIN_HISTORY)["symbol"]
    df = df.filter(pl.col("symbol").is_in(valid_syms.to_list()))

    print("Computing indicators …", flush=True)
    df = qm.add_indicators(df)

    sym_dates: dict[str, np.ndarray] = {}
    sym_closes: dict[str, np.ndarray] = {}
    sym_lows: dict[str, np.ndarray] = {}
    for (sym,), grp in df.sort(["symbol", "date"]).group_by(["symbol"], maintain_order=False):
        g = grp.sort("date")
        sym_dates[sym] = np.array([(d - _EPOCH).days for d in g["date"].to_list()], dtype=np.int32)
        sym_closes[sym] = g["adj_close"].cast(pl.Float64).to_numpy(allow_copy=True)
        sym_lows[sym] = g["adj_low"].cast(pl.Float64).to_numpy(allow_copy=True)

    print(f"Generating signals for {LABEL} …", flush=True)
    signals = get_signals(df, bull_dates, SMA_T)
    print(f"  {len(signals)} signals at ranking >= {MIN_RANKING}", flush=True)

    print("Running fill analysis …", flush=True)
    n_attempted, n_full_window, fills = run_fill_analysis(signals, sym_dates, sym_closes, sym_lows)

    grid = build_grid(n_attempted, fills)
    counts = build_counts(n_attempted, fills)
    summary = (
        f"N signals: {len(signals)}  |  N attempted (>=1 bar after signal): {n_attempted}  |  "
        f"N with full {max(WINDOWS_CAL)}d window of data: {n_full_window}"
    )

    print("\n" + summary)
    print("\n" + grid)
    print("\n" + counts)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write(f"# Limit-Order Fill Rate — {LABEL}\n\n")
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write(f"Period: {EVAL_START} – {EVAL_END}\n\n")
        fh.write("## Configuration\n\n")
        fh.write("| Parameter | Value |\n|---|---|\n")
        fh.write(f"| Signal | {LABEL}: 50d-high breakout, close >12% above SMA50, 12m ROC < 100% |\n")
        fh.write(f"| Limit sweep | X% = {', '.join(f'{lp * 100:.0f}%' for lp in LIMIT_PCTS)} |\n")
        fh.write(f"| Window sweep | Y = {', '.join(f'{w}d' for w in WINDOWS_CAL)} (calendar days after the signal day) |\n")
        fh.write(
            "| Fill rule | resting limit at signal_day_close x (1 - X%), eligible from the day after the signal; "
            "fills on the first trading day whose low <= limit price within Y calendar days, else expires unfilled "
            "(adjusted prices, same convention as scripts/qullamaggie-cohorts-limit-order.py) |\n"
        )
        fh.write("| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, no tight_range |\n")
        fh.write("| Market regime | SPY close > 200d SMA |\n")
        fh.write(f"| Price range | > ${MIN_PRICE:.0f} and < ${MAX_PRICE:.0f} |\n")
        fh.write(f"| Min avg vol (20d) | >= {MIN_AVG_VOL // 1000}K |\n")
        fh.write(f"| Cooldown | {COOLDOWN} calendar days |\n")
        fh.write("| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |\n")
        fh.write(f"| Ranking gate | QullamaggieRanking >= {MIN_RANKING} |\n\n")
        fh.write("## Results\n\n")
        fh.write(f"{summary}\n\n")
        fh.write(
            "Fill% = n_filled / N attempted. MedD/MeanD = median/mean trading days from the signal day to the "
            "fill day, filled orders only (1 = fills on the first trading day after the signal).\n\n"
        )
        fh.write("```text\n")
        fh.write(grid)
        fh.write("\n```\n\n")
        fh.write("### n_filled per cell\n\n")
        fh.write("```text\n")
        fh.write(counts)
        fh.write("\n```\n\n")
        fh.write("## Findings & Caveats\n\n")
        fh.write(
            "- **Truncated windows near the end of data**: signals in the last 90 calendar days of the period "
            "have fewer forward bars than the window nominally allows, so Fill% for the longer windows is "
            "slightly understated for those signals (denominator counts every signal with at least one "
            "following bar, matching scripts/qullamaggie-cohorts-limit-order.py).\n\n"
        )
        fh.write(
            "- **First-touch convention**: a fill is the first day the low touches the limit; MedD/MeanD "
            "therefore measure time to the *first* touch, not how long the price stayed below the limit.\n\n"
        )
        fh.write(
            "- **No execution costs or queue effects**: touching the limit is assumed to fill in full; a real "
            "resting order carries queue-priority risk at exactly-touched prices, and a gap-down open below the "
            "limit would fill at the open (better than modeled).\n"
        )
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
