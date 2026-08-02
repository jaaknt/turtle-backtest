# Qullamaggie Average-Volume Cohort Analysis

Run date: 2026-08-02 23:48:12 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 40 |
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
(<100K)          78   +17.37   +67.39    60.3     2.775    6.51    -83.65
[100-250K)      135   +40.27   +60.92    71.1     3.391    8.73    -61.23
[250-500K)      204   +44.97   +58.44    77.9     4.128   11.29    -48.99
[500K-1M)       274   +45.46   +52.65    80.3     3.482   10.37    -54.96
[1-2M)          283   +44.44   +57.65    72.1     3.109    8.48    -62.39
[2-5M)          257   +41.23   +64.82    73.9     3.648    9.61    -59.00
[5-10M)         120   +49.53   +69.09    79.2     5.146   14.03    -45.59
(>10M)          108   +43.17   +64.84    75.9     3.971   11.03    -60.74
─────────────────────────────────────────────────────────────────────────
ALL            1459   +43.32   +60.38    74.9     3.550    9.66    -58.62
>=100K (cap)   1381   +44.26   +59.98    75.7     3.635    9.99    -57.09

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)          97   +17.09   +59.75    61.9     2.426    5.98    -84.83
[100-250K)      158   +40.50   +60.74    71.5     3.368    8.75    -62.32
[250-500K)      226   +42.77   +60.49    74.8     3.454    9.10    -59.77
[500K-1M)       301   +43.53   +55.46    78.1     3.600   10.43    -55.19
[1-2M)          306   +38.69   +56.01    72.2     3.199    8.74    -59.15
[2-5M)          296   +37.51   +58.33    71.3     2.983    7.69    -62.22
[5-10M)         138   +47.28   +64.96    76.8     4.492   11.93    -49.21
(>10M)          122   +42.73   +61.78    73.0     3.538    9.31    -61.55
─────────────────────────────────────────────────────────────────────────
ALL            1644   +40.54   +58.80    73.2     3.293    8.81    -60.51
>=100K (cap)   1547   +41.43   +58.74    73.9     3.387    9.10    -58.90

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)         117    +6.77   +55.44    59.0     2.162    5.29    -86.61
[100-250K)      193   +40.27   +62.15    71.5     3.221    8.53    -64.76
[250-500K)      255   +40.53   +54.66    72.9     3.017    7.84    -60.88
[500K-1M)       336   +41.86   +52.83    77.4     3.349    9.72    -57.16
[1-2M)          364   +37.09   +55.82    71.7     3.173    8.48    -58.76
[2-5M)          339   +32.37   +56.69    69.3     2.791    7.01    -63.41
[5-10M)         156   +43.76   +60.33    73.1     3.875    9.83    -51.96
(>10M)          142   +42.73   +59.01    72.5     3.311    8.62    -60.10
─────────────────────────────────────────────────────────────────────────
ALL            1902   +37.83   +56.52    71.8     3.054    8.04    -61.90
>=100K (cap)   1785   +39.29   +56.59    72.7     3.154    8.35    -60.08

```
