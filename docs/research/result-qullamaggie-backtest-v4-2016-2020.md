# Qullamaggie Backtest v4 — Results

Run date: 2026-08-09 18:47:56 Tallinn time

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
| Eval period | 2016-01-01 – 2020-12-31 |
| Burn-in (indicators only) | 2014-01-01 – 2016-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=44` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated   1135   82.1   +56.35   +44.31  13.93    4.299   -50.20   19.2
bk50d_s20_v2.0    R>=44      941   81.7   +60.66   +48.04  14.51    4.590   -49.84   15.9
bk50d_s16_v2.0    ungated   1731   79.5   +49.59   +40.24  10.98    3.550   -51.97   29.3
bk50d_s16_v2.0    R>=44     1014   81.2   +61.47   +48.10  14.56    4.629   -50.08   17.2
bk50d_s12_v2.0    ungated   2468   78.4   +44.19   +35.90   9.48    3.073   -52.77   41.8
bk50d_s12_v2.0    R>=44     1033   80.7   +60.17   +47.00  13.80    4.448   -50.61   17.5

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=44

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2016 |      ·          ·      +50.0|39   +33.7|61   +25.4|14    +3.3|16   +50.3|15   +34.7|14   +88.0|8    +31.3|4     +2.2|1    +21.0|14  |  +36.4%   186
 2017 |   -4.8|5    +28.8|5    +74.6|2        ·      +42.5|3    +37.0|3    +17.2|4    +82.9|5    +74.3|4    +11.8|8   +176.8|2    +32.4|5   |  +41.3%    46
 2018 |  +15.0|8        ·      +68.2|3    +61.3|4    +62.6|9     +1.6|4    +14.2|2   +107.6|1    -26.7|1        ·          ·      -36.6|1   |  +36.7%    33
 2019 |      ·      +25.0|14    -6.6|13   +19.0|6    +67.9|3    +15.5|3     +7.2|12   +43.7|4    +91.8|2    +21.0|10    -1.1|3    +70.9|15  |  +27.6%    85
 2020 |   +7.7|8   +315.8|5        ·          ·      +96.9|237  +68.0|175  +59.9|50   +76.7|34  +159.2|10   +63.8|17   +42.6|48   +33.2|98  |  +73.4%   682
 2021 |  +55.2|1        ·          ·          ·          ·          ·          ·          ·          ·          ·          ·          ·     |  +55.2%     1
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
