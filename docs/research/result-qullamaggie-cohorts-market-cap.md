# Qullamaggie Market-Cap Cohort Analysis

Run date: 2026-10-24 18:01:42 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 44 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, excl. Comm/RE — **no market-cap floor** |
| Universe read | 2 market-cap slabs, lossless vs one wide read (see docstring) |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         405   -22.98    -3.83    33.6    -0.093    0.87    -86.50
[300M-1B)       545    +8.27   +21.78    55.2     0.794    2.43    -76.91
[1B-1.5B)       216   +12.81   +40.05    56.5     1.652    3.97    -71.89
[1.5-3B)        459   +30.71   +40.73    65.8     1.989    5.20    -65.38
[3-10B)         679   +44.93   +61.78    78.5     3.974   11.42    -55.72
[10-30B)        228   +45.57   +56.57    75.9     4.027   11.51    -51.87
[30-100B)       128   +58.15   +88.31    86.7    10.638   33.71    -32.12
(>100B)          23   +42.51   +50.85    91.3       n/a   65.79    -11.30
─────────────────────────────────────────────────────────────────────────
ALL            2683   +24.67   +39.13    63.3     1.584    4.16    -74.81
>=1.5B (cap)   1517   +41.23   +56.70    75.1     3.447    9.54    -57.41

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         505   -22.70    -3.16    34.1    -0.077    0.89    -87.00
[300M-1B)       649    +9.85   +22.63    56.4     0.821    2.48    -77.45
[1B-1.5B)       258   +12.81   +38.64    56.2     1.563    3.78    -71.48
[1.5-3B)        547   +28.70   +41.74    64.7     2.031    5.25    -64.45
[3-10B)         761   +42.28   +61.40    77.1     3.777   10.64    -57.30
[10-30B)        240   +42.98   +54.50    73.8     3.908   10.79    -49.91
[30-100B)       133   +58.56   +90.25    87.2    10.717   34.53    -32.64
(>100B)          21   +42.51   +52.17    90.5       n/a   61.71    -11.30
─────────────────────────────────────────────────────────────────────────
ALL            3114   +22.10   +38.15    62.2     1.508    3.96    -75.65
>=1.5B (cap)   1702   +39.20   +56.25    73.6     3.321    9.03    -58.26

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         549   -22.30    -4.01    34.4    -0.098    0.86    -86.58
[300M-1B)       732    +7.70   +21.88    55.2     0.786    2.40    -77.78
[1B-1.5B)       283   +12.88   +35.76    56.2     1.404    3.53    -74.13
[1.5-3B)        585   +27.33   +41.92    65.3     1.976    5.16    -67.01
[3-10B)         783   +41.43   +59.87    76.5     3.621   10.08    -57.68
[10-30B)        251   +42.23   +52.47    72.5     3.439    9.42    -54.80
[30-100B)       133   +58.56   +93.16    85.7    11.019   33.93    -32.30
(>100B)          20   +43.15   +54.24    90.0       n/a   61.10    -11.30
─────────────────────────────────────────────────────────────────────────
ALL            3336   +19.81   +36.57    61.4     1.420    3.75    -76.21
>=1.5B (cap)   1772   +37.83   +55.33    73.1     3.154    8.53    -60.18

```
