# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-08-02 23:45:09 Tallinn time

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
(<10)        1125   +10.10   +16.60    61.8     0.785    2.56    -64.80
[10-12)       834   +11.89   +19.64    62.7     1.034    3.15    -61.73
[12-15)      1174   +18.74   +27.92    66.8     1.560    4.39    -58.41
[15-17)       669   +23.69   +36.74    69.4     1.992    5.49    -60.61
[17-20)       670   +25.37   +35.84    70.3     2.111    5.79    -56.85
[20-30)      1123   +34.70   +48.29    74.6     3.032    8.40    -55.15
(>30)         437   +56.50   +71.68    77.6     4.462   12.76    -58.03
───────────────────────────────────────────────────────────────────────
ALL          6032   +21.87   +33.48    68.2     1.840    5.06    -59.73
>=12% (s12)   4073   +27.27   +40.98    71.1     2.393    6.53    -57.60
>=15% (s15)   2899   +31.29   +46.27    72.9     2.754    7.55    -57.36
>=17% (s17)   2230   +35.19   +49.13    73.9     3.019    8.30    -56.18
>=20% (s20)   1560   +39.67   +54.84    75.4     3.435    9.56    -55.89

```
