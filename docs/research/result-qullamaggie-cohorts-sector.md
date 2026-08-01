# Qullamaggie Sector Cohort Analysis

Run date: 2026-08-01 10:37:09 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | company GICS sector |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **Comm Services / Real Estate universe exclusion — removed; returns as the `excl Comm/RE (cap)` row** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
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
Communication Services       43   +33.00   +60.06    67.4     2.936    7.16    -65.61
Consumer Discretionary      168   +58.53   +73.49    85.7     6.970   26.38    -41.93
Consumer Staples             16   +45.20   +91.70    75.0       n/a   25.22    -51.39
Energy                      158   +43.62   +54.05    81.6     4.255   13.66    -51.69
Financials                  139   +54.90   +56.59    85.6     3.944   13.43    -58.82
Health Care                 184   +23.21   +40.33    60.3     1.810    4.36    -63.09
Industrials                 129   +49.74   +73.51    76.7     5.527   15.80    -49.14
Information Technology      112   +42.19   +74.51    72.3     3.366    8.38    -69.28
Materials                   120   +45.92   +56.83    71.7     3.081    7.77    -55.86
Real Estate                  45   +44.69   +37.07    84.4     1.865    7.36    -82.63
Utilities                     7    -4.37    -3.57    42.9       n/a    0.78    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1121   +44.26   +59.33    75.9     3.475    9.71    -59.30
excl Comm/RE (cap)         1033   +44.53   +60.27    75.9     3.591    9.95    -58.16

### bk50d_s16_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       48   +31.95   +56.29    68.8     2.817    6.96    -65.61
Consumer Discretionary      199   +57.04   +66.85    80.9     4.995   15.86    -51.21
Consumer Staples             19   +31.52   +77.10    73.7     6.084   19.33    -51.39
Energy                      175   +41.00   +53.27    79.4     4.190   13.00    -50.77
Financials                  148   +53.71   +55.09    85.1     3.882   13.21    -56.60
Health Care                 221   +16.99   +37.79    58.4     1.631    3.95    -65.43
Industrials                 134   +49.21   +72.83    76.1     5.441   15.53    -50.12
Information Technology      121   +37.37   +73.31    70.2     3.334    8.18    -66.55
Materials                   132   +45.92   +59.77    72.0     3.360    8.51    -55.86
Real Estate                  53   +41.31   +37.21    84.9     1.918    7.39    -82.63
Utilities                    10   +10.56    +7.66    70.0       n/a    1.82    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1260   +40.87   +57.04    74.3     3.267    8.93    -59.47
excl Comm/RE (cap)         1159   +41.43   +57.97    74.0     3.360    9.10    -58.69

### bk50d_s12_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       60   +28.69   +49.90    70.0     2.585    6.43    -59.52
Consumer Discretionary      223   +48.73   +63.51    78.0     4.369   12.65    -51.77
Consumer Staples             22   +37.45   +72.41    72.7     6.136   20.13    -51.39
Energy                      213   +34.91   +48.93    77.0     3.189    9.47    -57.20
Financials                  165   +49.37   +52.65    83.6     3.691   12.11    -55.05
Health Care                 254   +17.44   +38.30    59.4     1.717    4.14    -64.20
Industrials                 149   +49.74   +76.14    77.2     5.944   17.42    -47.89
Information Technology      138   +38.03   +72.92    71.0     3.346    8.39    -69.53
Materials                   158   +42.64   +56.62    68.4     2.915    7.13    -60.82
Real Estate                  59   +41.96   +38.82    84.7     2.105    8.35    -82.63
Utilities                    12    -2.05    -0.37    50.0    -0.016    0.97    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1453   +37.92   +55.21    73.1     3.107    8.34    -59.83
excl Comm/RE (cap)         1334   +38.36   +56.18    72.7     3.180    8.44    -59.17

```
