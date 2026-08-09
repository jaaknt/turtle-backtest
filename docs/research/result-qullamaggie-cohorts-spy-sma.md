# Qullamaggie SPY Regime (market SMA) Cohort Analysis

Run date: 2026-08-09 18:53:54 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Periods | **2006-01-01 – 2010-12-31, 2018-01-01 – 2023-12-31** — each straddles a bear market |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | **the regime lookback N in `spy_close > mean(spy_close[-(N+1):-1])`** |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **SPY > 200d SMA — swept over N = 150/200/250/300/350 and switched off entirely; `SMA200 *` is the production setting and `regime off` the dropped-filter reference** |
| Rows overlap | **variant sweep, not a partition — rows do not sum to `regime off`** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | QullamaggieRanking >= 44 |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days, applied after the regime gate as in production |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

Each row is the **whole** signal population under that regime setting, so the rows overlap and do not sum to `regime off` — a signal clearing SMA150 usually clears SMA350 too. `SMA200 *` is the production setting; `regime off` applies no market filter at all. The gate runs before the 30-day cooldown, as in production, so a different lookback also changes which triggers win the cooldown slot — the row counts are not a pure subset relationship either.

Both windows deliberately straddle a bear market, since that is the only condition under which a regime filter can pay for itself: 2006-2010 covers the 2008 crash, 2018-2023 covers 2018 Q4, the 2020 Covid crash and 2022. They are **not** comparable with the other cohort studies, which all run 2015-2026.

```text
### 2006-01-01 – 2010-12-31 — bk50d_s20_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          606   +25.92   +32.73    75.9     2.606    7.91    -45.18
SMA200 *        376   +13.87   +23.03    67.0     1.531    4.45    -51.41
SMA250          226    +6.79   +14.00    58.4     0.758    2.49    -59.85
SMA300          204    +4.03   +11.49    55.4     0.596    2.14    -61.44
SMA350          142    +5.57   +12.79    56.3     0.603    2.14    -66.38
regime off     1091   +29.80   +38.90    76.2     2.631    8.05    -54.48

### 2006-01-01 – 2010-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          666   +27.64   +32.88    76.0     2.667    7.95    -44.09
SMA200 *        425   +18.22   +24.15    68.9     1.699    4.85    -47.39
SMA250          253   +10.00   +16.13    61.7     0.946    2.90    -53.75
SMA300          228    +7.20   +12.72    57.5     0.710    2.36    -54.64
SMA350          158    +8.64   +14.38    58.9     0.755    2.47    -59.35
regime off     1243   +28.97   +37.14    74.9     2.434    7.33    -55.15

### 2006-01-01 – 2010-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          689   +28.63   +33.37    77.1     2.716    8.20    -44.25
SMA200 *        454   +19.50   +25.21    70.9     1.735    5.11    -49.94
SMA250          281   +10.87   +17.47    64.1     1.006    3.12    -56.00
SMA300          249    +8.22   +13.35    58.6     0.717    2.41    -58.62
SMA350          175    +8.41   +13.93    58.9     0.672    2.32    -66.79
regime off     1314   +28.26   +36.06    74.7     2.269    6.84    -57.18

### 2018-01-01 – 2023-12-31 — bk50d_s20_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1120   +44.49   +56.95    76.8     3.522   10.07    -57.43
SMA200 *       1079   +45.12   +57.83    77.8     3.600   10.48    -58.04
SMA250         1069   +47.35   +60.49    79.5     3.817   11.38    -57.86
SMA300         1098   +48.90   +61.91    80.5     3.988   12.12    -57.66
SMA350         1122   +49.99   +62.57    81.3     4.009   12.42    -58.09
regime off     1396   +43.00   +54.56    75.2     3.139    8.75    -60.75

### 2018-01-01 – 2023-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1235   +42.23   +54.65    74.8     3.264    9.07    -58.28
SMA200 *       1194   +43.02   +55.64    76.0     3.354    9.49    -58.58
SMA250         1163   +44.53   +58.01    77.3     3.500   10.06    -58.70
SMA300         1187   +45.95   +59.31    78.0     3.610   10.50    -59.01
SMA350         1207   +47.79   +60.32    78.7     3.643   10.72    -59.57
regime off     1527   +39.85   +51.79    72.7     2.829    7.66    -62.17

### 2018-01-01 – 2023-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1263   +41.49   +54.12    74.7     3.163    8.79    -59.51
SMA200 *       1221   +42.57   +55.23    75.8     3.247    9.18    -59.95
SMA250         1188   +44.32   +57.54    77.2     3.391    9.77    -60.34
SMA300         1213   +45.54   +58.72    78.0     3.514   10.23    -60.12
SMA350         1236   +46.98   +59.56    78.6     3.523   10.37    -60.95
regime off     1564   +39.58   +51.32    72.9     2.793    7.58    -62.52

```
