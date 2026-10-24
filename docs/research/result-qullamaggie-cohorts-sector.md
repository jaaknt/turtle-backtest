# Qullamaggie Sector Cohort Analysis

Run date: 2026-10-24 17:56:52 Tallinn time

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
Communication Services       60   +25.74   +56.75    66.7     2.629    6.42    -66.92
Consumer Discretionary      227   +53.07   +66.82    84.6     5.599   19.36    -46.57
Consumer Staples             21   +47.00   +83.20    76.2    11.819   42.54    -31.73
Energy                      224   +34.78   +43.26    75.0     2.701    7.71    -57.06
Financials                  206   +49.20   +51.04    85.9     4.035   14.24    -48.85
Health Care                 305   +27.95   +50.61    62.3     2.359    5.68    -65.23
Industrials                 217   +52.97   +73.42    80.2     6.879   21.38    -41.67
Information Technology      152   +32.70   +59.15    69.7     2.796    6.88    -65.44
Materials                   155   +39.90   +54.47    72.3     3.141    8.01    -55.18
Real Estate                  53   +40.58   +35.34    84.9     1.865    7.30    -82.63
Utilities                    10   +10.89    +9.25    50.0     0.348    1.62    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1630   +40.93   +56.01    75.2     3.343    9.30    -58.44
excl Comm/RE (cap)         1517   +41.23   +56.70    75.1     3.447    9.54    -57.41

### bk50d_s16_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       73   +24.38   +51.55    69.9     2.430    6.04    -64.49
Consumer Discretionary      259   +47.49   +62.02    80.3     4.105   12.86    -57.94
Consumer Staples             26   +37.45   +69.56    73.1     9.319   27.92    -31.73
Energy                      247   +33.97   +43.69    74.9     2.756    7.96    -57.41
Financials                  217   +47.46   +53.62    86.2     4.408   15.60    -48.30
Health Care                 365   +25.49   +47.60    60.5     2.171    5.18    -66.08
Industrials                 228   +50.92   +72.38    79.8     6.734   20.78    -40.92
Information Technology      171   +29.77   +68.86    69.6     3.372    8.20    -63.88
Materials                   177   +35.66   +54.18    70.1     3.107    7.86    -54.97
Real Estate                  59   +41.96   +38.23    86.4     2.128    8.59    -82.63
Utilities                    12   +25.33   +16.48    66.7       n/a    2.50    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1834   +38.47   +55.48    73.9     3.233    8.84    -59.10
excl Comm/RE (cap)         1702   +39.20   +56.25    73.6     3.321    9.03    -58.26

### bk50d_s12_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────────────────
Communication Services       75   +24.15   +53.07    66.7     2.430    5.74    -64.46
Consumer Discretionary      261   +48.73   +62.01    79.7     3.979   12.28    -58.08
Consumer Staples             27   +43.39   +65.74    74.1     8.976   27.42    -31.73
Energy                      267   +30.36   +41.93    72.7     2.383    6.72    -61.60
Financials                  215   +46.40   +53.63    86.5     4.816   17.32    -43.82
Health Care                 393   +25.03   +47.64    61.3     2.082    5.03    -69.06
Industrials                 237   +50.50   +72.47    80.2     6.818   21.13    -40.92
Information Technology      175   +29.77   +66.42    69.7     3.279    8.08    -63.88
Materials                   185   +31.76   +52.70    68.6     2.935    7.26    -55.81
Real Estate                  60   +40.94   +36.55    85.0     2.052    8.33    -74.19
Utilities                    12    +4.06    +7.68    58.3     0.314    1.60    -69.57
─────────────────────────────────────────────────────────────────────────────────────
ALL                        1907   +37.45   +54.65    73.2     3.081    8.36    -60.69
excl Comm/RE (cap)         1772   +37.83   +55.33    73.1     3.154    8.53    -60.18

```
