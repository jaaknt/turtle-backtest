# Qullamaggie Market-Cap Cohort Analysis

Run date: 2026-08-02 15:27:36 Tallinn time

> **⚠ Descriptive only — this cohort variable carries look-ahead.** `company.market_cap` is a current snapshot with no history, so a 2015 trade is bucketed by its company's market cap *today*. The `(<300M)` bucket is therefore not 'small companies' but 'companies that are small in 2026' — ones that fell or stagnated over the following decade — and `(>100B)` is companies that grew into it. Trades are sorted partly by their own outcome, so a 'large caps did better' reading would be an artifact, not a finding. Every other cohort study measures its variable on the signal date; this one cannot until a point-in-time cap (shares outstanding x close) is available.

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | **`company.market_cap` — a current snapshot, NOT a signal-date value** |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **`market_cap >= 1.5B` — removed, otherwise the three sub-floor cohorts would be empty; returns as the `>=1.5B (cap)` row** |
| ⚠ Look-ahead | **market_cap has no history, so a 2015 trade is bucketed by its 2026 cap — trades are sorted partly by their own outcome. Descriptive only; do not read as 'size predicts returns'** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | QullamaggieRanking >= 40 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, excl. Comm/RE — **no market-cap floor** |
| Universe read | 2 market-cap slabs, lossless vs one wide read (see docstring) |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         131   -32.74    -5.72    28.2    -0.125    0.84    -88.33
[300M-1B)       207    -1.90   +15.47    46.9     0.519    1.85    -74.81
[1B-1.5B)       103    -1.13   +17.54    48.5     0.626    2.04    -71.16
[1.5-3B)        265   +30.71   +40.61    63.4     1.846    4.62    -65.67
[3-10B)         449   +47.54   +63.45    78.6     3.881   11.26    -58.01
[10-30B)        192   +47.68   +57.75    78.6     4.080   12.24    -54.36
[30-100B)       116   +58.89   +93.61    86.2    14.611   45.15    -24.62
(>100B)          21   +56.32   +80.93    95.2       n/a  252.67     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            1484   +30.37   +45.26    65.8     1.911    4.94    -71.98
>=1.5B (cap)   1043   +44.64   +60.31    75.9     3.607   10.00    -57.92

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         154   -29.35    -5.33    27.3    -0.118    0.84    -88.44
[300M-1B)       248    -3.84   +13.01    46.4     0.417    1.68    -78.84
[1B-1.5B)       126    -0.57   +18.30    49.2     0.652    2.10    -73.01
[1.5-3B)        319   +26.94   +39.43    61.8     1.768    4.42    -66.01
[3-10B)         507   +43.00   +61.45    76.9     3.671   10.35    -58.77
[10-30B)        205   +45.12   +56.46    78.0     4.166   12.48    -51.53
[30-100B)       117   +57.22   +92.33    84.6    11.765   35.96    -31.10
(>100B)          20   +61.13   +83.83    95.0       n/a  249.27     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            1696   +26.16   +42.75    63.9     1.761    4.55    -73.06
>=1.5B (cap)   1168   +41.53   +58.04    74.1     3.374    9.13    -58.48

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         168   -28.97    -4.87    29.8    -0.110    0.85    -87.58
[300M-1B)       298    -5.24   +11.35    45.0     0.372    1.60    -79.28
[1B-1.5B)       158    -2.14   +13.03    47.5     0.440    1.73    -78.00
[1.5-3B)        381   +22.75   +36.11    62.2     1.624    4.17    -66.17
[3-10B)         576   +42.56   +61.38    75.9     3.696   10.09    -57.33
[10-30B)        235   +44.53   +54.52    74.9     3.368    9.56    -59.35
[30-100B)       129   +48.73   +89.44    82.2     9.596   28.09    -34.56
(>100B)          23   +65.94   +92.59    95.7       n/a  316.33     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            1968   +23.39   +40.76    62.9     1.674    4.32    -73.23
>=1.5B (cap)   1344   +38.69   +56.25    72.8     3.181    8.44    -59.13

```
