# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 18:15:43 Tallinn time

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
| Eval period | 2010-01-01 – 2015-12-31 |
| Burn-in (indicators only) | 2008-01-02 – 2010-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=40` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated    251   60.6   +19.92   +10.38   2.73    0.908   -62.94    3.5
bk50d_s20_v2.0    R>=40      169   60.4   +20.40   +12.00   2.74    0.921   -62.64    2.4
bk50d_s16_v2.0    ungated    546   62.8   +20.03   +12.90   3.04    1.021   -59.96    7.7
bk50d_s16_v2.0    R>=40      222   60.8   +19.08   +12.67   2.72    0.886   -64.13    3.1
bk50d_s12_v2.0    ungated   1048   59.2   +15.81    +9.85   2.57    0.795   -60.99   14.8
bk50d_s12_v2.0    R>=40      304   59.2   +17.69   +10.88   2.47    0.778   -65.74    4.3

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=40

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2010 |  +18.6|7    +17.7|3        ·       +5.5|7        ·          ·       -8.3|1    +13.1|3     -4.9|4    +43.3|10    +6.7|7     +1.3|13  |  +13.3%    55
 2011 |  +10.6|4    -37.7|1    -22.4|2        ·          ·      -12.9|1     +0.8|1        ·          ·       +5.5|29   +42.1|6    +57.0|8   |  +15.7%    52
 2012 |  +33.5|18    +5.1|17   +23.6|9        ·          ·      -14.0|2    +38.6|8    +61.9|8    +33.0|4    +25.7|1   +102.5|1   +117.5|4   |  +33.5%    72
 2013 |  +76.6|6   +125.2|2    +55.2|4    +21.3|2    +32.5|7    +96.9|2     -7.2|2    +31.8|2    +46.5|1    -29.9|2    -47.5|1        ·     |  +44.6%    31
 2014 |  -11.0|5     +0.5|6    +48.3|6    +58.7|3    +42.5|2    +12.4|3    +47.8|2    -75.3|1     +0.1|2     -2.8|1    +39.4|5     +9.9|4   |  +19.8%    40
 2015 |  -40.7|7    -19.8|11   -14.1|7     -6.3|7    +37.5|2    +31.2|3    -56.9|5        ·          ·      -10.7|2    -10.9|4    +14.8|6   |  -13.7%    54
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
