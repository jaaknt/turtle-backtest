# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 09:30:37 Tallinn time

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
| Eval period | 2016-01-01 – 2020-12-31 |
| Burn-in (indicators only) | 2014-01-01 – 2016-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `ungated` takes every signal that meets the entering condition, `R>=40` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate. The two rows come from the same signals, held and exited identically, so the difference isolates the gate — the drop in `N` between them is how selective it is. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Rows are ordered by SMA threshold (s20, s16, s12), ungated before gated.

```text
Entry Signal      Gate         N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo
─────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    ungated    814   82.3   +56.62   +46.35  13.87    4.233   -51.59   13.8
bk50d_s20_v2.0    R>=40      635   83.9   +63.99   +51.87  17.49    5.193   -48.64   10.8
bk50d_s16_v2.0    ungated   1200   79.2   +49.67   +41.43  10.84    3.506   -52.83   20.3
bk50d_s16_v2.0    R>=40      674   83.1   +64.26   +53.24  17.48    5.282   -47.82   11.4
bk50d_s12_v2.0    ungated   1679   77.8   +45.05   +37.55   9.20    3.009   -54.85   28.5
bk50d_s12_v2.0    R>=40      745   80.8   +60.38   +48.96  13.68    4.427   -51.05   12.6

Valid combinations: 6
```

## Monthly Mean% / N — bk50d_s12_v2.0 R>=40

Each cell is `Mean%|N` for the trades **entered** in that calendar month, held the full 366 days; `·` marks a month with no entries. The right-hand pair is the year's own aggregate across all its months, not the mean of the cells. Only this one combination is shown — it is the reference algorithm, and a grid per combination would be six tables.

```text
 Year |    Jan        Feb        Mar        Apr        May        Jun        Jul        Aug        Sep        Oct        Nov        Dec     |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------------------------------------------
 2016 |      ·          ·      +46.1|34   +33.8|48    +4.1|7     -6.7|14   +21.9|15   +50.4|8    +94.4|4    +31.3|4     +2.2|1    +44.1|8   |  +33.0%   143
 2017 |  +41.6|5    +44.5|4    +50.1|4        ·      +20.9|5    +40.7|2    +59.1|4     -1.7|4    +35.4|2     -0.6|3        ·      +79.5|3   |  +36.4%    36
 2018 |  +24.8|6        ·      +22.0|2    +31.8|4    -17.1|3    -28.0|1    -15.5|2    +37.7|2        ·          ·          ·      -38.5|2   |   +9.5%    22
 2019 |      ·      +23.6|10   -35.6|8     +6.8|3     -2.2|1    -17.2|3     -1.7|7    +48.6|2    +91.8|2    +38.8|7     +6.7|3    +57.4|8   |  +17.4%    54
 2020 |  +26.7|2   +384.9|4        ·          ·     +101.1|171  +67.3|135  +52.9|40   +87.2|27  +189.2|8    +61.3|15   +47.0|32   +28.5|56  |  +77.5%   490
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
