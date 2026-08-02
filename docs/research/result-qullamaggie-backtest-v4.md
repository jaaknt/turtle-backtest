# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 18:14:46 Tallinn time

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
| Min avg vol (20d) | ≥ 100K |
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
bk50d_s20_v2.0    ungated    662   65.1   +52.08   +24.21   6.58    2.725   -60.10   11.2
bk50d_s20_v2.0    R>=40      474   63.9   +55.25   +25.51   6.35    2.665   -63.87    8.0
bk50d_s16_v2.0    ungated   1130   63.7   +41.62   +17.82   5.29    2.133   -60.55   19.2
bk50d_s16_v2.0    R>=40      563   62.5   +51.17   +21.75   5.65    2.378   -64.57    9.5
bk50d_s12_v2.0    ungated   1795   62.2   +35.34   +14.46   4.70    1.851   -59.66   30.4
bk50d_s12_v2.0    R>=40      676   63.8   +53.12   +22.21   6.02    2.519   -64.97   11.5

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=40

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2021 |  +56.7|56   +47.6|34    -0.9|3    +11.8|5    +49.3|2    +79.6|16   -45.9|3    +59.9|1    -22.7|2     -3.1|6    -24.2|3        ·     |  +45.9%   131
 2022 |  +14.1|2    +38.0|8     +8.7|24   +28.8|19       ·          ·          ·          ·          ·          ·          ·      +20.5|45  |  +20.5%    98
 2023 |   +1.6|22   +35.0|25   +46.8|11   +33.7|12   +57.6|14   +35.3|20   +27.3|33   +15.7|7    +66.7|3        ·      +55.8|15   +51.6|35  |  +36.5%   197
 2024 |  +60.4|25   +26.0|15   -12.7|9     +1.6|10   +37.6|15   +70.9|10  +109.5|11   +21.0|21   +94.2|11   +98.6|17    +4.1|11    +9.2|5   |  +47.0%   160
 2025 |  -28.9|3    +84.3|6   +1248.2|1        ·      +99.4|19  +159.7|61       ·          ·          ·          ·          ·          ·     | +147.7%    90
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
