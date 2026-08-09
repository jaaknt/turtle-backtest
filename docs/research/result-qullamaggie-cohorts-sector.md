# Qullamaggie Sector Cohort Analysis

Run date: 2026-08-09 18:54:24 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 44 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | **US common stocks, market_cap >= 1.5B — sector exclusion lifted (the cohort variable)** |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       62   +24.02   +52.89    64.5     2.423    5.82    -66.92
Consumer Discretionary      233   +55.36   +67.50    84.5     5.610   18.84    -46.64
Consumer Staples             22   +45.20   +78.72    72.7    10.350   31.23    -31.73
Energy                      214   +34.78   +43.86    75.7     2.771    7.96    -57.67
Financials                  215   +49.76   +52.11    86.0     4.121   14.47    -49.77
Health Care                 305   +25.03   +50.62    60.3     2.289    5.30    -63.36
Industrials                 228   +53.40   +72.99    79.4     6.221   18.92    -43.40
Information Technology      161   +33.90   +63.89    68.9     2.966    7.28    -67.83
Materials                   153   +41.64   +55.50    73.9     3.221    8.32    -55.18
Real Estate                  54   +40.60   +36.27    87.0     1.998    8.47    -82.63
Utilities                    10   +10.89    +9.25    50.0     0.348    1.62    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1657   +41.00   +56.87    74.9     3.348    9.17    -58.56
excl Comm/RE (cap)         1541   +41.49   +57.76    74.9     3.454    9.41    -57.40

### bk50d_s16_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       75   +23.89   +48.09    68.0     2.245    5.51    -64.49
Consumer Discretionary      263   +49.46   +62.30    79.8     4.087   12.42    -56.37
Consumer Staples             27   +43.39   +69.71    74.1     9.517   29.02    -31.73
Energy                      236   +34.25   +44.24    75.4     2.816    8.18    -57.99
Financials                  226   +48.30   +54.69    86.3     4.491   15.81    -47.31
Health Care                 363   +22.98   +47.87    59.0     2.114    4.88    -64.59
Industrials                 240   +51.70   +72.20    79.2     6.183   18.75    -42.30
Information Technology      182   +30.53   +71.33    68.7     3.435    8.35    -66.17
Materials                   174   +37.13   +55.39    71.8     3.183    8.11    -54.97
Real Estate                  60   +41.64   +39.02    88.3     2.266    9.93    -74.19
Utilities                    12   +25.33   +16.48    66.7       n/a    2.50    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1858   +38.71   +56.27    73.7     3.231    8.71    -59.22
excl Comm/RE (cap)         1723   +39.80   +57.22    73.4     3.323    8.89    -58.39

### bk50d_s12_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       78   +21.98   +49.07    65.4     2.241    5.29    -64.46
Consumer Discretionary      265   +48.73   +61.63    78.9     3.917   11.68    -58.08
Consumer Staples             28   +44.25   +66.03    75.0     9.180   28.52    -31.73
Energy                      251   +32.78   +44.07    74.5     2.691    7.73    -59.02
Financials                  224   +47.53   +54.70    86.6     4.888   17.47    -43.23
Health Care                 388   +24.44   +49.52    60.8     2.160    5.04    -66.06
Industrials                 248   +51.70   +72.41    79.4     6.262   19.04    -42.30
Information Technology      188   +30.53   +68.38    68.6     3.210    7.91    -68.39
Materials                   182   +36.54   +53.82    70.3     3.001    7.45    -55.81
Real Estate                  61   +40.62   +37.36    86.9     2.187    9.63    -74.19
Utilities                    12    +4.06    +7.68    58.3     0.314    1.60    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1925   +37.82   +55.85    73.4     3.149    8.45    -60.11
excl Comm/RE (cap)         1786   +38.61   +56.78    73.2     3.234    8.64    -59.55

```
