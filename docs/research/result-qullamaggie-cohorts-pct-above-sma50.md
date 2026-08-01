# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-08-01 10:22:16 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | **`bk50d_s<X>_v2.0` (366d) — one shared pool; reference rows for X = 12% / 15% / 17% / 20%** |
| Cohort variable | pct_vs_sma50 = close / mean(close[-51:-1]) - 1 |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **pct_vs_sma50 > X — removed; returns as one reference row per X** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | **not applied — %abv_sma50 is the score's 35-point dimension and the cohort variable (ungated)** |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
───────────────────────────────────────────────────────────────────────
(<10)         686    +6.36   +12.04    57.9     0.505    1.94    -69.52
[10-12)       527   +10.92   +20.91    61.7     1.062    3.21    -64.96
[12-15)       788   +19.10   +29.03    65.4     1.579    4.37    -59.48
[15-17)       455   +25.25   +40.08    69.7     2.177    5.84    -58.98
[17-20)       457   +23.87   +33.07    67.8     1.830    5.00    -60.17
[20-30)       811   +33.03   +48.67    74.1     2.998    8.30    -56.19
(>30)         344   +57.07   +72.01    77.6     4.345   12.34    -58.23
───────────────────────────────────────────────────────────────────────
ALL          4068   +22.07   +34.35    67.2     1.806    4.92    -61.63
>12% (s12)   2855   +28.17   +42.19    70.4     2.406    6.49    -58.29
>15% (s15)   2067   +31.76   +47.21    72.3     2.745    7.45    -57.83
>17% (s17)   1612   +34.40   +49.23    73.1     2.923    7.98    -57.59
>20% (s20)   1155   +39.80   +55.62    75.2     3.405    9.46    -56.80

```
