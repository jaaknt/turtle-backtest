# Qullamaggie Average-Volume Cohort Analysis

Run date: 2026-10-24 18:04:36 Tallinn time

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
(<100K)          78   +24.06   +66.99    65.4     2.771    7.06    -83.65
[100-250K)      144   +40.47   +60.31    73.6     3.861   10.56    -55.19
[250-500K)      225   +44.44   +58.44    80.0     3.952   11.76    -54.16
[500K-1M)       286   +42.62   +49.34    78.3     3.105    9.27    -57.82
[1-2M)          313   +43.68   +58.54    72.2     3.354    9.09    -59.65
[2-5M)          288   +36.88   +57.15    72.6     3.241    8.56    -58.03
[5-10M)         135   +44.53   +60.20    74.1     3.925    9.65    -47.52
(>10M)          126   +38.07   +56.84    75.4     3.303    9.41    -61.71
─────────────────────────────────────────────────────────────────────────
ALL            1595   +40.85   +57.20    74.7     3.383    9.35    -58.85
>=100K (cap)   1517   +41.23   +56.70    75.1     3.447    9.54    -57.41

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)          98   +21.78   +58.60    65.3     2.365    6.19    -84.83
[100-250K)      169   +40.34   +62.86    74.0     3.889   10.59    -57.74
[250-500K)      248   +43.22   +62.04    78.2     3.942   10.97    -55.12
[500K-1M)       308   +38.33   +51.54    76.3     3.253    9.63    -58.57
[1-2M)          342   +38.69   +55.90    71.9     3.378    9.09    -55.76
[2-5M)          333   +32.37   +54.15    71.2     2.909    7.66    -60.75
[5-10M)         158   +39.41   +55.86    71.5     3.198    8.06    -56.51
(>10M)          143   +36.09   +54.92    71.3     2.990    8.02    -62.27
─────────────────────────────────────────────────────────────────────────
ALL            1799   +38.23   +56.40    73.2     3.230    8.78    -60.11
>=100K (cap)   1701   +39.29   +56.27    73.6     3.321    9.02    -58.26

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<100K)         106   +16.31   +56.25    61.3     2.068    5.27    -86.61
[100-250K)      185   +40.27   +64.70    73.0     3.471    9.52    -64.23
[250-500K)      255   +41.10   +56.82    76.9     3.261    9.01    -61.49
[500K-1M)       312   +38.33   +50.25    76.9     3.121    9.29    -59.61
[1-2M)          360   +37.73   +56.29    72.2     3.373    9.04    -56.19
[2-5M)          342   +29.34   +54.60    70.2     2.900    7.48    -60.34
[5-10M)         166   +35.21   +53.18    69.9     2.989    7.56    -58.00
(>10M)          151   +40.05   +53.79    70.9     2.993    7.99    -62.27
─────────────────────────────────────────────────────────────────────────
ALL            1877   +37.33   +55.40    72.4     3.039    8.22    -62.51
>=100K (cap)   1771   +37.83   +55.35    73.1     3.154    8.53    -60.18

```
