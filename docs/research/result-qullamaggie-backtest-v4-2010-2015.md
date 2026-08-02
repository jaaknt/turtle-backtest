# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 09:29:26 Tallinn time

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
| Eval period | 2010-01-01 – 2015-12-31 |
| Burn-in (indicators only) | 2008-01-02 – 2010-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=40` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated    178   56.2   +16.44    +4.94   2.23    0.682   -66.45    2.5
bk50d_s20_v2.0    R>=40      116   56.9   +17.86    +9.62   2.30    0.729   -66.48    1.6
bk50d_s16_v2.0    ungated    361   59.0   +16.79    +8.64   2.45    0.766   -63.94    5.1
bk50d_s16_v2.0    R>=40      150   56.7   +16.22   +10.71   2.24    0.677   -68.77    2.1
bk50d_s12_v2.0    ungated    663   57.2   +13.61    +7.14   2.23    0.645   -62.75    9.3
bk50d_s12_v2.0    R>=40      194   57.2   +15.22   +10.56   2.16    0.626   -70.79    2.7

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=40

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2010 |  +32.9|5     +3.8|2        ·       +3.3|4        ·          ·       -8.3|1     -1.2|1    -82.7|1    +13.6|7    -24.1|2     -4.2|8   |   +3.4%    31
 2011 |  +12.4|2    -37.7|1        ·          ·          ·          ·          ·          ·          ·       +5.5|17   +65.3|4    +57.4|5   |  +21.7%    29
 2012 |  +50.5|10    +6.6|17   +38.7|6        ·          ·      -14.8|1    +45.1|7    +61.9|8    +16.7|3        ·     +102.5|1   +120.2|1   |  +35.5%    54
 2013 |  +98.2|4    +71.0|1    +23.9|2    +32.7|1    +29.0|3   +130.7|1    -24.2|1    +31.8|2    +46.5|1    -29.9|2    -47.5|1        ·     |  +39.0%    19
 2014 |  -14.4|3    -19.1|4    -48.2|2    +66.5|2    +42.5|2    +91.4|1        ·      -75.3|1    -12.3|1     -2.8|1    +58.3|4    -21.7|3   |   +7.1%    24
 2015 |  -37.4|5    -21.4|9    -18.1|5     -2.8|5     -9.3|1    +31.2|3    -60.7|3        ·          ·      -10.7|2    -19.5|3    +58.0|1   |  -16.3%    37
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
