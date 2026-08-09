# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-08-09 18:52:43 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | **`bk50d_s<X>_v2.0` (366d) — one shared pool; reference rows for X = 12% / 15% / 17% / 20%** |
| Cohort variable | pct_vs_sma50 = close / mean(close[-51:-1]) - 1 |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **pct_vs_sma50 >= X — removed; returns as one reference row per X** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | **not applied — %abv_sma50 is the score's 35-point dimension and the cohort variable (ungated)** |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
───────────────────────────────────────────────────────────────────────
(<10)        1133   +10.10   +16.80    61.7     0.797    2.58    -64.93
[10-12)       840   +11.54   +19.29    62.4     1.010    3.09    -61.89
[12-15)      1175   +19.03   +28.24    66.9     1.598    4.47    -57.52
[15-17)       675   +23.55   +36.00    69.0     1.946    5.36    -60.61
[17-20)       682   +24.73   +35.71    69.9     2.105    5.74    -56.41
[20-30)      1138   +34.40   +48.99    74.5     3.069    8.47    -55.36
(>30)         443   +56.50   +73.11    77.4     4.472   12.82    -58.97
───────────────────────────────────────────────────────────────────────
ALL          6086   +21.85   +33.72    68.1     1.855    5.08    -59.65
>=12% (s12)   4113   +27.27   +41.33    71.0     2.417    6.58    -57.41
>=15% (s15)   2938   +31.06   +46.56    72.6     2.761    7.54    -57.45
>=17% (s17)   2263   +34.70   +49.71    73.7     3.041    8.33    -56.31
>=20% (s20)   1581   +39.41   +55.75    75.3     3.469    9.63    -56.24

```
