# Qullamaggie Sector Cohort Analysis

Run date: 2026-08-01 01:31:40 Tallinn time

```text
Company-sector cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, breakout>50d high, %abv_sma50>12%/16%/20% (swept), SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, tight_range disabled; Comm Services/Real Estate sector exclusion removed for cohort view; QullamaggieRanking>=40
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py)

### bk50d_s20_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF
───────────────────────────────────────────────────────────────────────────
Communication Services       33   +28.14   +47.84    63.6     2.129    5.14
Consumer Discretionary      123   +58.51   +70.59    86.2     6.497   25.04
Consumer Staples             12   +37.45  +106.14    75.0       n/a   24.31
Energy                      116   +41.20   +52.90    80.2     4.189   12.81
Financials                  104   +57.64   +56.64    84.6     3.514   11.59
Health Care                 129   +22.98   +41.55    60.5     1.944    4.62
Industrials                  90   +51.90   +76.19    77.8     5.220   15.49
Information Technology       72   +44.78   +74.82    75.0     3.138    8.15
Materials                    85   +43.00   +58.32    74.1     3.389    9.04
Real Estate                  32   +45.38   +38.79    84.4     1.662    6.13
Utilities                     6    -1.84    -0.95    50.0       n/a    0.94
───────────────────────────────────────────────────────────────────────────
ALL                         802   +44.26   +59.05    76.3     3.370    9.56
excl Comm/RE (cap)          737   +45.00   +60.43    76.5     3.562   10.08

### bk50d_s16_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF
───────────────────────────────────────────────────────────────────────────
Communication Services       38   +28.69   +44.68    65.8     2.062    5.09
Consumer Discretionary      143   +50.32   +63.00    80.4     4.373   13.50
Consumer Staples             14   +27.19   +90.18    71.4       n/a   18.07
Energy                      129   +36.26   +50.44    77.5     3.692   11.06
Financials                  109   +56.72   +56.42    84.4     3.619   12.23
Health Care                 161   +21.75   +40.35    58.4     1.887    4.39
Industrials                  94   +50.18   +74.63    76.6     5.016   14.62
Information Technology       77   +39.37   +79.59    72.7     3.352    8.56
Materials                    94   +41.85   +58.02    73.4     3.477    9.31
Real Estate                  38   +41.64   +37.45    84.2     1.650    5.94
Utilities                     7    +0.69    +7.56    71.4       n/a    1.72
───────────────────────────────────────────────────────────────────────────
ALL                         904   +41.25   +56.63    74.1     3.164    8.68
excl Comm/RE (cap)          828   +42.39   +58.06    74.0     3.327    9.07

### bk50d_s12_v2.0

Cohort                        N     Med%    Mean%    Win%   Sortino      PF
───────────────────────────────────────────────────────────────────────────
Communication Services       46   +26.15   +41.30    67.4     1.979    4.95
Consumer Discretionary      163   +45.00   +57.62    76.1     3.749   10.47
Consumer Staples             15   +31.52   +87.17    73.3       n/a   18.68
Energy                      150   +34.72   +47.38    76.7     3.103    9.23
Financials                  123   +51.85   +53.76    81.3     3.303   10.38
Health Care                 183   +22.69   +40.89    60.1     1.971    4.60
Industrials                 107   +49.74   +78.18    78.5     5.548   16.67
Information Technology       87   +43.53   +79.03    74.7     3.539    9.42
Materials                   110   +40.66   +57.15    70.9     3.377    8.58
Real Estate                  44   +43.33   +39.51    84.1     1.851    6.90
Utilities                     8    +0.48    +3.51    62.5       n/a    1.28
───────────────────────────────────────────────────────────────────────────
ALL                        1036   +39.58   +55.11    73.4     3.090    8.35
excl Comm/RE (cap)          946   +40.24   +56.51    73.2     3.230    8.65

```
