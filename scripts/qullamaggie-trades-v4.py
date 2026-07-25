#!/usr/bin/env python3
"""
Current-period trade report for bk50d_s15_v1.3_roc100.

Signal logic is imported from turtlex.research.qullamaggie, which is parity-tested against
QullamaggieStrategy (the strategy behind `backtest-runner --trading-strategy qullamaggie`), so
this report and the backtest runner agree on (symbol, signal_date, entry_date, entry_price).

Filters: RSI<70, ADR mean-of-ratios>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x,
vol_dry_up<90%, SPY>200d SMA, raw close>$5&<$250, avg_vol>=500K, >15% above the 50d SMA.
Indicators run on split/dividend-adjusted prices; the $5-$250 band stays on the raw close.
Entry is the next trading bar's adjusted open, matching the production runner. Positions are
open — each is marked to its symbol's latest available adjusted close.

Display window: 2025-07-01 - today. The candidate window starts WARMUP_DAYS earlier so the
30-day cooldown state is correct at the start of the display window.
"""

from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from turtlex.config.settings import Settings
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository
from turtlex.research import qullamaggie as qm

DISPLAY_START = date(2025, 7, 1)
DISPLAY_END = date.today()

STRATEGY_LABEL = "bk50d_s15_v1.3_roc100"

RESULT_PATH = Path(__file__).parent.parent / "docs" / "research" / "result-qullamaggie-trades-v4.md"


def main() -> None:
    settings = Settings.from_toml()
    bars_history = DailyBarsQueryRepository(engine=settings.engine)

    print("Loading SPY regime …", flush=True)
    bull_dates = qm.load_spy_regime(bars_history, DISPLAY_START, DISPLAY_END)

    print("Loading bars …", flush=True)
    bars = qm.load_bars(bars_history, DISPLAY_START, DISPLAY_END)

    print("Computing indicators …", flush=True)
    df = qm.add_indicators(bars)

    latest = (
        bars.sort(["symbol", "date"])
        .group_by("symbol")
        .agg(pl.col("date").last().alias("latest_date"), pl.col("adj_close").last().alias("latest_close"))
    )
    latest_date = dict(zip(latest["symbol"].to_list(), latest["latest_date"].to_list(), strict=True))
    latest_close = dict(zip(latest["symbol"].to_list(), latest["latest_close"].to_list(), strict=True))

    print(f"Generating signals for {STRATEGY_LABEL} …", flush=True)
    sig = qm.get_signals(df, bull_dates, DISPLAY_START)
    sig = qm.resolve_entries(sig, bars)
    print(f"  {len(sig)} entered signals in display window", flush=True)

    hdr = (
        f"{'Signal':<11}│ {'Entry':<11}│ {'Symbol':<7}│ {'Entry $':>8} │ {'Curr Price':>10} │ {'Change %':>9} │ "
        f"{'%abv SMA50':>10} │ {'ADR%':>6} │ {'ADR_CHG':>7} │ {'RSI14':>6} │ {'ROC252%':>8} │ {'Latest Data':>11}"
    )
    sep = "─" * len(hdr)

    lines: list[str] = [hdr, sep]
    rets: list[float] = []
    for row in sig.iter_rows(named=True):
        sym = row["symbol"]
        entry = row["entry_price"]
        curr = latest_close.get(sym, float("nan"))
        chg = (curr / entry - 1.0) * 100 if entry else float("nan")
        rets.append(chg)
        lines.append(
            f"{str(row['date']):<11}│ {str(row['entry_date']):<11}│ {sym:<7}│ {entry:>8.2f} │ {curr:>10.2f} │ {chg:>+8.1f}% │ "
            f"{row['pct_vs_sma50'] * 100:>+9.1f}% │ {row['adr_pct'] * 100:>5.1f}% │ {row['adr_pct_change']:>7.2f} │ "
            f"{row['rsi14']:>6.1f} │ {row['roc_252d'] * 100:>+7.1f}% │ {str(latest_date.get(sym)):>11}"
        )

    lines.append(sep)
    n = len(rets)
    mean_ret = float(np.mean(rets)) if n else float("nan")
    summary = (
        f"\nIf every open trade were closed at its symbol's latest available adjusted close:\n"
        f"  Trade count (N): {n}\n"
        f"  Mean trade performance: {mean_ret:+.2f}%"
    )
    lines.append(summary)

    output = "\n".join(lines)
    print("\n" + output)

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULT_PATH.open("w") as fh:
        fh.write(f"# {STRATEGY_LABEL} — Trade Report\n\n")
        fh.write(f"Run date: {date.today()}\n\n")
        fh.write(f"Period: {DISPLAY_START} – {DISPLAY_END}\n\n")
        fh.write("```text\n")
        fh.write(output)
        fh.write("\n```\n")
    print(f"\nResults saved to {RESULT_PATH}", flush=True)


if __name__ == "__main__":
    main()
