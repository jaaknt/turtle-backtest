# Qullamaggie SPY Regime (market SMA) Cohort Analysis

Run date: 2026-08-02 23:46:22 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 40 |
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
SMA150          547   +26.44   +33.73    76.8     2.814    8.79    -44.27
SMA200 *        335   +15.09   +24.66    68.1     1.751    5.13    -49.56
SMA250          189    +8.60   +15.88    59.3     0.906    2.86    -58.79
SMA300          166    +4.14   +12.44    55.4     0.672    2.33    -60.64
SMA350          110    +5.73   +15.39    57.3     0.743    2.46    -66.79
regime off     1025   +30.32   +39.84    76.5     2.751    8.51    -53.82

### 2006-01-01 – 2010-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          598   +27.07   +33.51    76.1     2.883    8.71    -42.52
SMA200 *        378   +15.60   +24.51    68.3     1.818    5.16    -45.96
SMA250          219    +9.77   +17.47    61.2     1.084    3.21    -52.37
SMA300          191    +5.77   +12.85    56.0     0.750    2.44    -53.51
SMA350          128    +7.32   +15.66    57.0     0.849    2.65    -57.10
regime off     1164   +28.68   +37.51    74.6     2.503    7.52    -54.44

### 2006-01-01 – 2010-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          664   +25.46   +32.16    75.3     2.387    7.39    -48.97
SMA200 *        443   +15.40   +23.78    68.2     1.535    4.59    -53.50
SMA250          283   +10.00   +16.69    61.5     0.910    2.91    -60.49
SMA300          247    +6.19   +12.40    56.3     0.632    2.25    -63.52
SMA350          178    +5.57   +12.70    55.6     0.574    2.11    -71.36
regime off     1360   +25.56   +33.79    72.5     2.002    5.98    -59.77

### 2018-01-01 – 2023-12-31 — bk50d_s20_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1022   +47.82   +59.32    78.1     3.757   10.92    -56.59
SMA200 *        984   +48.87   +60.25    79.3     3.874   11.51    -56.72
SMA250          979   +51.85   +62.85    81.0     4.134   12.63    -56.43
SMA300         1010   +53.59   +64.32    82.3     4.350   13.70    -55.91
SMA350         1033   +54.38   +65.24    83.2     4.370   14.11    -57.02
regime off     1298   +45.39   +56.24    76.4     3.304    9.33    -59.86

### 2018-01-01 – 2023-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1131   +44.26   +56.33    75.6     3.356    9.38    -58.30
SMA200 *       1087   +45.00   +57.54    77.0     3.485    9.96    -58.47
SMA250         1062   +47.70   +60.01    78.3     3.669   10.68    -58.31
SMA300         1090   +48.99   +61.61    79.4     3.827   11.37    -58.66
SMA350         1112   +51.29   +62.90    80.2     3.889   11.78    -59.33
regime off     1422   +42.53   +53.44    73.7     2.929    7.97    -61.87

### 2018-01-01 – 2023-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150         1264   +43.01   +54.34    74.4     3.106    8.59    -60.60
SMA200 *       1218   +43.66   +55.57    75.5     3.222    9.06    -60.86
SMA250         1188   +46.29   +57.98    76.9     3.375    9.65    -60.76
SMA300         1213   +47.05   +59.00    77.8     3.503   10.18    -60.55
SMA350         1238   +48.56   +60.04    78.7     3.545   10.48    -61.41
regime off     1600   +40.29   +50.61    72.4     2.696    7.27    -62.92

```
