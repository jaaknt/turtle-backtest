# Qullamaggie Tight-Range Cohort Analysis

Run date: 2026-08-01 10:41:27 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | **bk50d_s20_tr10_v2.0, bk50d_s20_tr20_v2.0, bk50d_s15_tr15_v2.0 (366d)** |
| Cohort variable | tight_range_ratio = (max - min) / mean of the previous 10 closes |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **each variant's tight_range cap — removed; returns as its `<=0.10` / `<=0.20` / `<=0.15 (cap)` row** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x |
| Ranking gate | QullamaggieRanking >= 40 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |
| Note | s20_tr10 and s20_tr20 share pct_above_sma50=20%, so with the cap removed they draw from the same candidate pool — only the reference row differs |

## Results

```text
### bk50d_s20_tr10_v2.0  (current tr cap: <=0.10)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       424   +28.67   +44.23    69.3     2.509    6.74    -59.27
[0.1-0.15)      263   +38.73   +54.68    74.9     3.004    7.91    -57.06
[0.15-0.2)      183   +58.00   +73.97    83.1     5.449   18.12    -52.13
[0.2-0.25)       98   +66.82   +81.20    82.7     4.650   13.45    -61.96
[0.25-0.3)       44   +96.27  +115.62    95.5       n/a   90.19    -28.52
[>0.3)           21  +140.21  +121.33    85.7       n/a   22.48    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1033   +44.53   +60.27    75.9     3.591    9.95    -58.16
<=0.10 (cap)    424   +28.67   +44.23    69.3     2.509    6.74    -59.27

### bk50d_s20_tr20_v2.0  (current tr cap: <=0.20)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       424   +28.67   +44.23    69.3     2.509    6.74    -59.27
[0.1-0.15)      263   +38.73   +54.68    74.9     3.004    7.91    -57.06
[0.15-0.2)      183   +58.00   +73.97    83.1     5.449   18.12    -52.13
[0.2-0.25)       98   +66.82   +81.20    82.7     4.650   13.45    -61.96
[0.25-0.3)       44   +96.27  +115.62    95.5       n/a   90.19    -28.52
[>0.3)           21  +140.21  +121.33    85.7       n/a   22.48    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1033   +44.53   +60.27    75.9     3.591    9.95    -58.16
<=0.20 (cap)    870   +37.88   +53.64    73.9     3.148    8.60    -58.18

### bk50d_s15_tr15_v2.0  (current tr cap: <=0.15)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       555   +25.70   +43.54    66.7     2.366    6.20    -60.77
[0.1-0.15)      309   +37.41   +52.98    75.1     3.017    8.08    -56.98
[0.15-0.2)      193   +58.00   +74.02    80.3     4.915   14.72    -56.71
[0.2-0.25)      101   +63.86   +77.85    82.2     4.506   13.00    -59.30
[0.25-0.3)       46   +96.27  +113.42    95.7       n/a   92.48    -28.52
[>0.3)           21  +140.21  +121.33    85.7       n/a   22.48    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1225   +41.00   +57.51    73.6     3.329    8.98    -58.73
<=0.15 (cap)    864   +29.89   +46.92    69.7     2.591    6.83    -59.13

```
