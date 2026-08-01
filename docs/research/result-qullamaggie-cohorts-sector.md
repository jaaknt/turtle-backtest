# Qullamaggie Sector Cohort Analysis

Run date: 2026-08-01 09:04:47 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | company GICS sector |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **Comm Services / Real Estate universe exclusion — removed; returns as the `excl Comm/RE (cap)` row** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90% (no tight_range) |
| Ranking gate | QullamaggieRanking >= 40 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | **US common stocks, market_cap >= 1.5B — sector exclusion lifted (the cohort variable)** |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       33   +28.14   +47.84    63.6     2.129    5.14    -66.42
Consumer Discretionary      123   +58.51   +70.59    86.2     6.497   25.04    -41.99
Consumer Staples             12   +37.45  +106.14    75.0       n/a   24.31    -51.39
Energy                      116   +41.20   +52.90    80.2     4.189   12.81    -49.95
Financials                  104   +57.64   +56.64    84.6     3.514   11.59    -62.84
Health Care                 129   +22.98   +41.55    60.5     1.944    4.62    -60.80
Industrials                  90   +51.90   +76.19    77.8     5.220   15.49    -56.03
Information Technology       72   +44.78   +74.82    75.0     3.138    8.15    -73.06
Materials                    85   +43.00   +58.32    74.1     3.389    9.04    -56.52
Real Estate                  32   +45.38   +38.79    84.4     1.662    6.13    -90.62
Utilities                     6    -1.84    -0.95    50.0       n/a    0.94    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                         802   +44.26   +59.05    76.3     3.370    9.56    -61.51
excl Comm/RE (cap)          737   +45.00   +60.43    76.5     3.562   10.08    -59.80

### bk50d_s16_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       38   +28.69   +44.68    65.8     2.062    5.09    -66.42
Consumer Discretionary      143   +50.32   +63.00    80.4     4.373   13.50    -53.39
Consumer Staples             14   +27.19   +90.18    71.4       n/a   18.07    -51.39
Energy                      129   +36.26   +50.44    77.5     3.692   11.06    -52.56
Financials                  109   +56.72   +56.42    84.4     3.619   12.23    -62.84
Health Care                 161   +21.75   +40.35    58.4     1.887    4.39    -58.95
Industrials                  94   +50.18   +74.63    76.6     5.016   14.62    -56.17
Information Technology       77   +39.37   +79.59    72.7     3.352    8.56    -73.06
Materials                    94   +41.85   +58.02    73.4     3.477    9.31    -56.52
Real Estate                  38   +41.64   +37.45    84.2     1.650    5.94    -90.62
Utilities                     7    +0.69    +7.56    71.4       n/a    1.72    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                         904   +41.25   +56.63    74.1     3.164    8.68    -61.17
excl Comm/RE (cap)          828   +42.39   +58.06    74.0     3.327    9.07    -59.62

### bk50d_s12_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       46   +26.15   +41.30    67.4     1.979    4.95    -65.56
Consumer Discretionary      163   +45.00   +57.62    76.1     3.749   10.47    -53.85
Consumer Staples             15   +31.52   +87.17    73.3       n/a   18.68    -51.39
Energy                      150   +34.72   +47.38    76.7     3.103    9.23    -57.01
Financials                  123   +51.85   +53.76    81.3     3.303   10.38    -61.54
Health Care                 183   +22.69   +40.89    60.1     1.971    4.60    -57.55
Industrials                 107   +49.74   +78.18    78.5     5.548   16.67    -52.90
Information Technology       87   +43.53   +79.03    74.7     3.539    9.42    -70.81
Materials                   110   +40.66   +57.15    70.9     3.377    8.58    -54.87
Real Estate                  44   +43.33   +39.51    84.1     1.851    6.90    -82.63
Utilities                     8    +0.48    +3.51    62.5       n/a    1.28    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1036   +39.58   +55.11    73.4     3.090    8.35    -60.43
excl Comm/RE (cap)          946   +40.24   +56.51    73.2     3.230    8.65    -58.91

```
