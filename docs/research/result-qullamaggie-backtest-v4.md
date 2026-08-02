# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 09:31:53 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Algorithm version | 2.0 (encoded as `_v2.0` in the names below) |
| Breakout | 50d high |
| Entry | next trading day's adjusted open (within 7 cal days of the signal) |
| Exit | close of the first bar at or after entry + hold |
| SMA thresh sweep | 12%, 16%, 20% |
| Tight range | disabled (commented out) |
| Hold sweep | 366d (calendar); entries without 366d of forward data are skipped |
| Ranking | QullamaggieRanking (ADR 40 / SMA50 35 / price 25) |
| Ranking gate sweep | ungated, ≥ 40 |
| vol_dry_up | disabled (commented out) |
| vol_surge | volume/avg_vol_50 < 2.0× (no lower bound) |
| roc_12m_cap | 12m ROC < 100% |
| RSI | RSI(14) < 70 |
| ADR | mean((high-low)/low, last 20d, shift-1) ≥ 3.0% |
| ADR change | ADR%(10d) / ADR%(50d) < 90% |
| SMA alignment | disabled (commented out) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | ≥ 500K |
| Min history | ≥ 300 trading days |
| Cooldown | 30 calendar days |
| Eval period | 2021-01-01 – 2025-12-31 |
| Burn-in (indicators only) | 2019-01-02 – 2021-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=40` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated    501   64.5   +51.93   +25.01   6.46    2.683   -60.42    8.5
bk50d_s20_v2.0    R>=40      369   64.5   +54.66   +26.29   6.36    2.638   -64.15    6.3
bk50d_s16_v2.0    ungated    839   62.9   +41.50   +18.42   5.09    2.069   -61.15   14.2
bk50d_s16_v2.0    R>=40      440   63.0   +49.35   +22.61   5.57    2.314   -63.92    7.5
bk50d_s12_v2.0    ungated   1290   61.6   +35.76   +14.59   4.57    1.818   -59.98   21.9
bk50d_s12_v2.0    R>=40      531   63.8   +51.23   +23.11   5.95    2.466   -63.78    9.0

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=40

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2021 |  +67.7|39   +51.0|26    -4.1|2    +11.8|5    +49.3|2    +89.7|15   -42.7|2    +59.9|1    +18.4|1    -10.0|3     +1.0|2        ·     |  +55.4%    98
 2022 |  +14.1|2    +42.7|7     -3.7|21   +20.3|10       ·          ·          ·          ·          ·          ·          ·      +14.6|39  |  +13.0%    79
 2023 |   +1.4|17   +32.0|17   +73.1|6    +56.9|7    +62.0|13   +21.4|12   +19.4|28    +4.8|5    +66.7|3        ·      +59.6|14   +36.2|25  |  +33.9%   147
 2024 |  +59.5|17   +37.6|10    -8.7|7    +33.0|5    +22.2|11   +86.4|9    +99.7|10   +20.2|17   +92.3|10   +94.2|16    +5.1|9    -11.4|4   |  +50.3%   125
 2025 |  -12.6|3    +84.3|6        ·          ·     +104.5|18  +131.5|55       ·          ·          ·          ·          ·          ·     | +116.9%    82
```

## Findings & Caveats

### Ideas to improve

- source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot
- source a delisted-ticker history if available to address survivorship
- add a slippage/commission assumption on top of the next-day-open fill
- widen the gate sweep past 40 to find where the score stops separating outcomes
- report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold
- account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence
- re-run all three windows (2010-2015, 2016-2020, 2021-present) before accepting any parameter change — a change that only improves the window it was chosen on is fitted to that window
- pick the ranking gate per SMA threshold rather than one R≥40 across s12/s16/s20; the same score rejects a very different share of each, so it is not the same filter at each
- report per-year Sortino again — the Yrs+/Consistent columns were dropped from the table, so a combination that only works in one year is no longer visible at a glance
