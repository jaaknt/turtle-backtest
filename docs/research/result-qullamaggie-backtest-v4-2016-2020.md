# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 18:16:44 Tallinn time

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
| Eval period | 2016-01-01 – 2020-12-31 |
| Burn-in (indicators only) | 2014-01-01 – 2016-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=40` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated   1126   81.9   +54.97   +44.28  13.29    4.122   -50.89   19.1
bk50d_s20_v2.0    R>=40      859   83.4   +63.05   +50.85  16.76    5.107   -47.81   14.6
bk50d_s16_v2.0    ungated   1718   79.3   +48.43   +39.97  10.53    3.416   -52.68   29.1
bk50d_s16_v2.0    R>=40      919   82.4   +63.78   +51.03  16.06    4.967   -49.55   15.6
bk50d_s12_v2.0    ungated   2454   78.2   +43.28   +35.77   9.10    2.957   -53.58   41.6
bk50d_s12_v2.0    R>=40     1023   80.2   +59.40   +47.64  12.94    4.219   -52.43   17.3

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=40

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2016 |      ·          ·      +46.8|39   +32.9|60   +28.2|11    +1.3|17   +49.6|20   +32.9|14   +86.9|5    +30.8|5     +2.2|1    +32.7|11  |  +35.7%   183
 2017 |  +30.1|6    +24.7|5    +50.1|4        ·      +32.2|6    +44.6|3    +35.6|5    +59.1|5    +89.3|3    -13.6|6   +336.1|1    +36.3|4   |  +41.1%    48
 2018 |  +15.3|8        ·      +22.0|2    +31.8|4    -18.5|4     -1.3|4     +4.6|3    +37.7|2    -26.7|1    -56.8|1        ·      -38.5|2   |   +4.6%    31
 2019 |      ·      +14.8|15   -12.0|13   +19.1|6    +70.4|2     -3.1|4     +9.3|10   +25.3|3    +91.8|2    +32.1|9     +6.7|3    +84.7|14  |  +26.6%    81
 2020 |   +7.5|7   +280.0|6        ·          ·      +95.7|244  +63.4|178  +60.0|56   +81.3|36  +179.0|9    +60.0|17   +44.7|42   +35.2|84  |  +73.8%   679
 2021 |  +55.2|1        ·          ·          ·          ·          ·          ·          ·          ·          ·          ·          ·     |  +55.2%     1
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
