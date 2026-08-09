# Qullamaggie Average-Volume Cohort Analysis

Run date: 2026-08-09 18:55:46 Tallinn time

> **⚠ A sub-floor cohort scoring well is not automatically a relaxation.** The `avg_vol_20 >= 100K` floor is partly a *tradability* constraint rather than a pure alpha filter: a 3-5% portfolio position in a thin name moves the price the backtest measures it at, so these returns are less attainable the lower the cohort sits. The floor is also denominated in **shares, not dollars**, so it is not a constant liquidity bar across the $5-$250 price band — a $200 name at 400K shares ($80M/day) is excluded while a $6 name at 600K shares ($3.6M/day) passes.

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | avg_vol_20 = mean(volume[-21:-1]) — raw shares, shift-1 |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **`avg_vol_20 >= 100K` — removed, otherwise the sub-floor cohort would be empty; returns as the `>=100K (cap)` row** |
| ⚠ Tradability | **this floor is partly a fill constraint, not pure alpha — a sub-floor cohort scoring well is not necessarily takeable at 3-5% position size. It is also denominated in shares, not dollars** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | QullamaggieRanking >= 44 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)          84   +17.70   +66.76    61.9     2.870    6.94    -80.24
[100-250K)      161   +40.67   +63.25    72.0     3.792    9.94    -57.42
[250-500K)      230   +43.75   +56.13    78.7     3.780   10.72    -53.05
[500K-1M)       303   +41.49   +49.23    77.9     3.168    9.24    -55.25
[1-2M)          307   +44.44   +59.82    72.6     3.264    8.80    -61.59
[2-5M)          287   +37.57   +60.82    72.5     3.360    8.76    -59.68
[5-10M)         133   +45.97   +62.01    74.4     4.093   10.14    -47.52
(>10M)          120   +40.28   +57.71    75.8     3.408    9.57    -60.35
─────────────────────────────────────────────────────────────────────────
ALL            1625   +40.85   +58.22    74.2     3.401    9.20    -58.61
>=100K (cap)   1541   +41.49   +57.76    74.9     3.454    9.41    -57.40

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)         108   +16.31   +56.57    62.0     2.372    5.95    -81.87
[100-250K)      187   +41.42   +63.71    73.3     3.760   10.00    -59.06
[250-500K)      252   +42.07   +59.96    77.0     3.794   10.16    -54.07
[500K-1M)       327   +38.47   +52.42    76.1     3.343    9.63    -56.35
[1-2M)          334   +39.59   +56.87    71.6     3.234    8.56    -58.38
[2-5M)          332   +33.43   +57.25    71.1     3.013    7.84    -62.39
[5-10M)         155   +43.00   +57.96    72.3     3.384    8.65    -56.51
(>10M)          135   +40.05   +54.95    71.9     2.998    7.90    -62.75
─────────────────────────────────────────────────────────────────────────
ALL            1830   +38.21   +57.20    72.7     3.234    8.62    -59.89
>=100K (cap)   1722   +39.85   +57.24    73.4     3.323    8.88    -58.39

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)         116   +13.72   +54.99    59.5     2.040    5.13    -91.04
[100-250K)      204   +41.04   +66.12    73.0     3.578    9.65    -64.01
[250-500K)      259   +41.05   +55.15    75.7     3.307    8.74    -56.59
[500K-1M)       328   +38.47   +51.89    76.8     3.302    9.55    -56.27
[1-2M)          352   +38.04   +57.68    72.4     3.286    8.77    -58.91
[2-5M)          336   +31.93   +58.38    70.8     3.044    7.83    -62.56
[5-10M)         163   +36.26   +55.13    70.6     3.153    8.08    -58.00
(>10M)          143   +40.50   +53.76    71.3     3.001    7.87    -61.10
─────────────────────────────────────────────────────────────────────────
ALL            1901   +37.45   +56.69    72.4     3.102    8.27    -61.93
>=100K (cap)   1785   +38.69   +56.80    73.2     3.234    8.64    -59.55

```
