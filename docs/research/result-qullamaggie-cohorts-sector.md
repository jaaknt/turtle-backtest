# Qullamaggie Sector Cohort Analysis

Run date: 2026-08-02 23:46:51 Tallinn time

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
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | **US common stocks, market_cap >= 1.5B — sector exclusion lifted (the cohort variable)** |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       46   +33.46   +60.79    67.4     3.190    7.84    -65.61
Consumer Discretionary      209   +58.55   +72.28    85.2     6.184   21.83    -45.85
Consumer Staples             19   +47.00   +81.87    73.7     5.877   17.85    -51.39
Energy                      188   +35.98   +48.76    77.7     3.724   10.78    -48.58
Financials                  190   +51.64   +55.19    86.8     4.195   14.93    -52.44
Health Care                 281   +25.63   +47.75    60.5     2.129    5.01    -64.22
Industrials                 201   +52.97   +72.66    79.1     6.114   17.92    -42.26
Information Technology      151   +42.90   +70.35    74.2     3.520    9.07    -65.44
Materials                   134   +45.92   +58.36    73.1     3.257    8.32    -56.39
Real Estate                  48   +43.68   +37.91    85.4     1.969    7.94    -82.63
Utilities                     8    -1.84    +7.25    50.0       n/a    1.52    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1475   +43.68   +59.29    75.8     3.554    9.85    -58.18
excl Comm/RE (cap)         1381   +44.26   +59.98    75.7     3.635    9.99    -57.09

### bk50d_s16_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       56   +28.69   +50.10    66.1     2.302    5.64    -65.61
Consumer Discretionary      238   +57.47   +66.70    80.7     4.383   13.68    -58.08
Consumer Staples             22   +37.45   +70.60    72.7     5.196   14.91    -51.39
Energy                      210   +35.87   +49.00    76.7     3.782   10.82    -48.16
Financials                  203   +50.85   +55.43    86.2     4.257   14.96    -51.53
Health Care                 339   +22.75   +44.73    59.3     1.913    4.55    -67.95
Industrials                 210   +49.66   +71.03    78.1     5.809   16.64    -43.75
Information Technology      162   +40.89   +79.46    72.8     4.007   10.14    -63.88
Materials                   152   +41.85   +57.58    71.7     3.156    7.90    -55.98
Real Estate                  56   +40.94   +36.65    85.7     1.942    7.65    -82.63
Utilities                    12   +21.48   +18.35    75.0       n/a    3.36    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1660   +41.07   +57.68    74.1     3.285    8.89    -59.72
excl Comm/RE (cap)         1548   +41.42   +58.72    74.0     3.387    9.10    -58.90

### bk50d_s12_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       70   +24.51   +43.57    65.7     2.015    4.92    -64.46
Consumer Discretionary      267   +53.58   +62.57    77.5     3.791   10.88    -58.77
Consumer Staples             27   +46.28   +68.32    77.8     5.571   17.52    -51.39
Energy                      254   +33.73   +45.87    74.4     2.960    8.25    -54.99
Financials                  222   +47.53   +53.72    85.6     4.125   14.30    -51.71
Health Care                 396   +20.47   +44.97    60.1     1.925    4.60    -67.66
Industrials                 233   +49.74   +72.23    78.5     5.862   17.04    -44.88
Information Technology      188   +40.89   +75.07    72.3     3.835    9.91    -65.20
Materials                   181   +39.90   +55.21    68.5     2.839    6.96    -58.92
Real Estate                  63   +41.31   +38.23    85.7     2.142    8.73    -74.19
Utilities                    18    +0.48    +9.00    55.6     0.452    1.86    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1919   +38.53   +55.49    72.9     3.069    8.18    -60.72
excl Comm/RE (cap)         1786   +39.21   +56.57    72.7     3.154    8.35    -60.08

```
