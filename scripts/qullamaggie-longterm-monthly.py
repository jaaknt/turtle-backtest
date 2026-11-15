#!/usr/bin/env python3
"""
Long-term monthly analysis for multiple bk50d configs (366d hold).

Same fixed filters as scripts/qullamaggie-backtest-v4.py (RSI<70,
roc_12m<100%, vol_surge<2.0x, ADR>=3.0%, ADR_change<90%,
SPY>200d SMA, close>$5&<$250, avg_vol>=100K), extended back to 2007-01-01 to
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

from turtlex.backtest.metrics import compute_trade_metrics
from turtlex.common.report import run_timestamp
from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

EVAL_START = date(2007, 1, 1)
EVAL_END = date(2026, 6, 26)
MIN_NEG = 3

STRATEGIES = [
    ("bk50d_s20_v2.0", 0.20),
    ("bk50d_s16_v2.0", 0.16),
    ("bk50d_s12_v2.0", 0.12),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-longterm-monthly.md"


# ── Benchmarks (study-specific) ───────────────────────────────────────────────


def load_benchmark_yearly_returns(engine: sa.Engine, symbol: str) -> dict[int, float]:
    """Calendar-year close-to-close return for a benchmark ticker, in percent.

    Kept local: the shared signal layer loads the qualified stock universe, not index proxies.
    """
    sql = """
        SELECT date::date, close::float8
        FROM   turtle.daily_bars
        WHERE  symbol = :symbol AND date >= :start AND date <= :end
        ORDER  BY date
    """
    with engine.connect() as conn:
        rows = conn.execute(sa.text(sql), {"symbol": symbol, "start": EVAL_START, "end": EVAL_END}).fetchall()
    by_year: dict[int, list[float]] = {}
    for d, c in rows:
        by_year.setdefault(d.year, []).append(float(c))
    return {y: (v[-1] / v[0] - 1.0) * 100.0 for y, v in by_year.items() if len(v) > 1}


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
        m = compute_trade_metrics(a * 100, qm.HOLD_CAL, min_losers=MIN_NEG)
        if m is None:  # unreachable: the years come from the trades themselves
            return f"{0:>5} {'—':>6} {'—':>7} {fmt_pct(qqq_pct)} {fmt_pct(spy_pct)} {'—':>7} {'n/a':>8} {'—':>8}"
        sr_str = f"{m.sortino:>8.3f}" if not np.isnan(m.sortino) else f"{'n/a':>8}"
        return (
            f"{m.n:>5} {m.win_pct:>6.1f} {m.mean_pct:>+7.2f} {fmt_pct(qqq_pct)} {fmt_pct(spy_pct)} "
            f"{m.median_pct:>+7.2f} {sr_str} {m.cvar95_pct:>+8.2f}"
        )

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

    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, EVAL_START, EVAL_END)

    print("Loading benchmark returns …", flush=True)
    qqq_yearly = load_benchmark_yearly_returns(settings.engine, "QQQ.US")
    spy_yearly = load_benchmark_yearly_returns(settings.engine, "SPY.US")

    df, bars = cohorts.load_universe(bars_history, EVAL_START)

    fixed_hdr = (
        f"Hold: {qm.HOLD_CAL}d | Period: {EVAL_START} – {EVAL_END}\n"
        f"Fixed: roc_12m<{int(qm.ROC_CAP * 100)}%, "
        f"vol_surge<{qm.VOL_SURGE_MAX}x (no lower bound), RSI<{int(qm.RSI_CAP)}, ADR>={qm.ADR_MIN * 100:.1f}%, "
        f"ADR_change<{int(qm.ADR_CHANGE_CAP * 100)}%, "
        f"SPY>200d SMA, close>${qm.MIN_PRICE:.0f}&<${qm.MAX_PRICE:.0f}, avg_vol>={qm.MIN_AVG_VOL // 1000}K, "
        f"QullamaggieRanking>={qm.MIN_RANKING}\n"
    )
    print("\n" + fixed_hdr)

    all_lines: list[str] = [fixed_hdr]

    for strat_label, sma_t in STRATEGIES:
        print(f"Generating signals for {strat_label} …", flush=True)
        trades = cohorts.cohort_trades(df, bars, bull_dates, sma_t, start=EVAL_START, end=EVAL_END)
        print(f"  {trades.height} trades", flush=True)
        records = [
            {"year": d.year, "month": d.month, "ret": r} for d, r in zip(trades["date"].to_list(), trades["ret"].to_list(), strict=True)
        ]

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
        fh.write(f"Run date: {run_timestamp()}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
