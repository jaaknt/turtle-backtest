# Qullamaggie Backtest v4 — Results

Run date: 2026-08-09 18:47:42 Tallinn time

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
| Eval period | 2010-01-01 – 2015-12-31 |
| Burn-in (indicators only) | 2008-01-02 – 2010-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=44` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated    250   60.4   +19.80   +10.19   2.71    0.901   -62.94    3.5
bk50d_s20_v2.0    R>=44      215   60.9   +20.44   +10.38   2.66    0.885   -64.52    3.0
bk50d_s16_v2.0    ungated    550   62.9   +20.05   +12.90   3.06    1.026   -59.96    7.7
bk50d_s16_v2.0    R>=44      274   61.3   +20.84   +12.67   2.84    0.950   -65.44    3.9
bk50d_s12_v2.0    ungated   1052   59.2   +15.83    +9.86   2.58    0.801   -60.82   14.8
bk50d_s12_v2.0    R>=44      304   59.5   +19.22    +9.76   2.61    0.849   -66.53    4.3

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=44

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2010 |  +15.2|7    +17.7|3        ·       -1.9|4        ·          ·       -8.3|1    -13.9|6    +34.4|7    +38.0|11    +5.0|6     +1.6|13  |  +13.3%    58
 2011 |  +11.7|3    -29.2|1    +13.1|1        ·          ·      -12.9|1     +0.8|1        ·          ·       +5.6|32   +20.9|9    +51.3|9   |  +14.7%    57
 2012 |  +31.5|18   +11.8|21   +19.7|8        ·          ·      +29.8|3    +56.5|8    +60.2|9    +17.9|5    -17.4|2    +38.0|2   +113.1|4   |  +33.0%    80
 2013 | +185.8|1   +181.5|3    +78.3|3    +21.3|2    +34.7|6    +82.0|2    -24.2|1    +31.8|2    +46.5|1    +14.5|1    -47.5|1    -13.0|1   |  +59.2%    24
 2014 |   +3.4|5     -7.1|6    +63.0|6    +58.7|3    -36.4|1    +53.1|3    +47.8|2    -35.5|2     +0.1|2     -2.8|1    +51.7|6    -21.7|3   |  +22.9%    40
 2015 |  -40.7|7    -17.2|10    -8.8|5     -6.8|4    +37.5|2    +11.0|2    -56.9|5        ·          ·      +11.7|1     -9.2|5     +7.6|4   |  -16.0%    45
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
