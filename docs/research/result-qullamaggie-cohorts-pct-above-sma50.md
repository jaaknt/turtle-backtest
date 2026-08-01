# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-08-01 08:50:45 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | **`bk50d_s<X>_v2.0` (366d) — one shared pool; reference rows for X = 12% / 15% / 17% / 20%** |
| Cohort variable | pct_vs_sma50 = close / mean(close[-51:-1]) - 1 |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **pct_vs_sma50 > X — removed; returns as one reference row per X** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90% (no tight_range) |
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
(<10)         470    +5.69   +10.97    57.4     0.462    1.85    -68.27
[10-12)       379    +7.99   +20.36    59.1     1.021    3.02    -63.91
[12-15)       594   +20.25   +30.20    66.7     1.637    4.55    -59.82
[15-17)       348   +25.62   +39.93    70.1     2.293    6.26    -57.77
[17-20)       331   +22.04   +28.51    67.4     1.581    4.37    -58.23
[20-30)       611   +35.07   +52.82    76.1     3.338    9.52    -56.53
(>30)         240   +56.61   +67.32    77.1     3.633   10.30    -63.51
───────────────────────────────────────────────────────────────────────
ALL          2973   +22.06   +34.50    67.5     1.822    4.96    -61.27
>12% (s12)   2124   +27.80   +42.23    71.2     2.413    6.60    -58.66
>15% (s15)   1530   +31.38   +46.90    73.0     2.739    7.54    -58.27
>17% (s17)   1182   +33.83   +48.96    73.9     2.874    7.95    -58.41
>20% (s20)    851   +40.34   +56.91    76.4     3.422    9.77    -58.78

```
