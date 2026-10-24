# Qullamaggie SPY Regime (market SMA) Cohort Analysis

Run date: 2026-10-24 17:54:03 Tallinn time

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
SMA150          603   +26.15   +32.51    76.0     2.544    7.71    -45.88
SMA200 *        373   +13.79   +23.29    67.3     1.544    4.49    -51.33
SMA250          224    +7.09   +14.60    59.4     0.789    2.57    -59.72
SMA300          203    +5.45   +12.28    56.7     0.637    2.23    -61.29
SMA350          145    +5.77   +13.61    57.9     0.649    2.25    -66.38
regime off     1085   +29.39   +38.49    76.2     2.578    7.90    -55.01

### 2006-01-01 – 2010-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          668   +28.22   +33.05    76.2     2.679    8.02    -44.31
SMA200 *        426   +18.26   +24.80    69.5     1.774    5.07    -46.92
SMA250          255   +10.61   +17.51    63.1     1.050    3.16    -53.48
SMA300          231    +8.22   +14.38    59.3     0.824    2.62    -54.51
SMA350          165   +10.61   +16.53    61.8     0.907    2.84    -57.58
regime off     1242   +28.87   +36.87    75.0     2.427    7.32    -55.04

### 2006-01-01 – 2010-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          690   +28.87   +33.53    77.2     2.718    8.22    -44.47
SMA200 *        455   +19.87   +25.70    71.2     1.788    5.26    -49.53
SMA250          284   +11.07   +18.53    65.1     1.084    3.32    -55.73
SMA300          253    +9.08   +14.70    60.1     0.804    2.61    -58.56
SMA350          182   +10.58   +15.90    61.5     0.795    2.63    -64.90
regime off     1315   +28.26   +35.94    74.7     2.261    6.80    -57.27

### 2018-01-01 – 2023-12-31 — bk50d_s20_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1084   +43.93   +54.79    76.8     3.374    9.72    -57.86
SMA200 *       1045   +44.64   +55.95    77.8     3.467   10.14    -58.21
SMA250         1033   +46.40   +58.63    79.5     3.702   11.07    -57.91
SMA300         1060   +48.10   +60.15    80.4     3.864   11.75    -57.45
SMA350         1086   +49.55   +61.15    81.2     3.923   12.20    -58.19
regime off     1355   +42.57   +53.63    75.4     3.129    8.78    -60.24

### 2018-01-01 – 2023-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1195   +41.02   +52.55    74.6     3.122    8.73    -58.63
SMA200 *       1156   +42.39   +53.80    75.9     3.225    9.16    -58.97
SMA250         1124   +43.84   +56.12    77.1     3.385    9.77    -58.74
SMA300         1146   +45.14   +57.57    77.8     3.498   10.20    -59.07
SMA350         1167   +46.64   +58.75    78.6     3.552   10.52    -59.64
regime off     1480   +39.34   +50.82    72.8     2.832    7.72    -61.19

### 2018-01-01 – 2023-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1225   +41.00   +51.89    74.4     2.981    8.32    -60.46
SMA200 *       1186   +41.53   +53.21    75.4     3.079    8.72    -60.86
SMA250         1152   +43.29   +55.44    76.8     3.227    9.30    -60.92
SMA300         1175   +44.92   +56.66    77.5     3.317    9.64    -61.23
SMA350         1199   +45.95   +57.68    78.2     3.347    9.85    -62.04
regime off     1521   +39.11   +50.08    72.8     2.730    7.45    -62.53

```
