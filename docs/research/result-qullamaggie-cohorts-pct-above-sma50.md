# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-10-24 17:48:41 Tallinn time

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
(<10)        1165   +11.18   +17.96    62.7     0.869    2.76    -64.48
[10-12)       838   +11.76   +19.74    62.3     1.028    3.13    -62.40
[12-15)      1197   +19.03   +28.34    66.6     1.551    4.35    -59.75
[15-17)       677   +23.62   +36.56    69.1     2.095    5.69    -56.85
[17-20)       681   +23.87   +35.44    69.3     2.085    5.68    -56.46
[20-30)      1132   +34.31   +48.55    74.6     3.104    8.70    -54.99
(>30)         439   +55.75   +70.54    77.9     4.397   12.73    -58.65
───────────────────────────────────────────────────────────────────────
ALL          6129   +21.97   +33.64    68.2     1.863    5.12    -59.55
>=12% (s12)   4126   +27.20   +40.90    70.9     2.405    6.56    -57.25
>=15% (s15)   2929   +30.78   +46.03    72.6     2.797    7.67    -56.28
>=17% (s17)   2252   +34.42   +48.87    73.7     3.028    8.37    -56.13
>=20% (s20)   1571   +39.11   +54.69    75.6     3.472    9.79    -55.98

```
