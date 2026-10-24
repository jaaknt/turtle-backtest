# Qullamaggie Backtest v4 — Results

Run date: 2026-10-24 17:16:42 Tallinn time

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
| Ranking gate sweep | ungated, ≥ 44 |
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

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=44` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated    641   65.5   +51.40   +22.81   6.63    2.722   -59.75   10.9
bk50d_s20_v2.0    R>=44      509   66.0   +53.13   +25.90   6.67    2.735   -61.53    8.6
bk50d_s16_v2.0    ungated   1100   64.0   +41.14   +17.94   5.34    2.141   -60.09   18.6
bk50d_s16_v2.0    R>=44      603   64.3   +50.29   +21.88   6.07    2.507   -62.50   10.2
bk50d_s12_v2.0    ungated   1753   62.5   +35.20   +14.46   4.79    1.890   -58.57   29.7
bk50d_s12_v2.0    R>=44      635   65.4   +51.57   +22.33   6.31    2.585   -63.24   10.8

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=44

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2021 |  +52.5|69   +44.5|28    -4.1|2     +8.2|3        ·      +71.1|17   -42.7|2    +28.5|2    -22.7|2     -9.5|5    -24.2|3        ·     |  +44.4%   133
 2022 |  +14.1|2    +75.0|5     +2.7|21   +18.8|13       ·          ·          ·          ·          ·          ·          ·      +14.5|45  |  +15.8%    86
 2023 |   +7.4|22   +29.9|28   +22.3|10    +2.7|8    +58.9|15   +35.7|20   +11.5|33   +13.7|5    +91.0|3        ·      +39.2|11   +49.8|37  |  +30.4%   192
 2024 |  +58.7|27   +42.8|13   -11.5|6     +1.0|5    +62.4|8    +92.3|8   +120.9|10   +24.4|19   +68.6|11   +96.9|14    +8.1|11   +15.8|7   |  +52.5%   139
 2025 |  +78.3|4    +70.2|7   +1248.2|1        ·      +91.9|15  +155.7|58       ·          ·          ·          ·          ·          ·     | +146.6%    85
```

## Findings & Caveats

### Ideas to improve

- source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot
- source a delisted-ticker history if available to address survivorship
- add a slippage/commission assumption on top of the next-day-open fill
- widen the gate sweep past 44 to find where the score stops separating outcomes
- report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold
- account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence
- re-run all three windows (2010-2015, 2016-2020, 2021-present) before accepting any parameter change — a change that only improves the window it was chosen on is fitted to that window
- pick the ranking gate per SMA threshold rather than one R≥44 across s12/s16/s20; the same score rejects a very different share of each, so it is not the same filter at each
- report per-year Sortino again — the Yrs+/Consistent columns were dropped from the table, so a combination that only works in one year is no longer visible at a glance
