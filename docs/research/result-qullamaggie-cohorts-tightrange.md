# Qullamaggie Tight-Range Cohort Analysis

Run date: 2026-08-09 18:52:19 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 44 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
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
[0.0-0.1)       704   +28.55   +42.57    70.2     2.541    6.81    -56.53
[0.1-0.15)      389   +37.83   +58.89    74.0     3.320    8.64    -57.41
[0.15-0.2)      242   +56.53   +68.39    80.2     4.163   12.40    -60.11
[0.2-0.25)      119   +63.60   +76.71    81.5     4.374   12.66    -63.33
[0.25-0.3)       56   +92.20  +119.48    96.4       n/a  118.31    -28.52
[>0.3)           31  +117.17  +120.97    87.1       n/a   28.47    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1541   +41.49   +57.76    74.9     3.454    9.41    -57.40
<=0.10 (cap)    704   +28.55   +42.57    70.2     2.541    6.81    -56.53

### bk50d_s20_tr20_v2.0  (current tr cap: <=0.20)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       704   +28.55   +42.57    70.2     2.541    6.81    -56.53
[0.1-0.15)      389   +37.83   +58.89    74.0     3.320    8.64    -57.41
[0.15-0.2)      242   +56.53   +68.39    80.2     4.163   12.40    -60.11
[0.2-0.25)      119   +63.60   +76.71    81.5     4.374   12.66    -63.33
[0.25-0.3)       56   +92.20  +119.48    96.4       n/a  118.31    -28.52
[>0.3)           31  +117.17  +120.97    87.1       n/a   28.47    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1541   +41.49   +57.76    74.9     3.454    9.41    -57.40
<=0.20 (cap)   1335   +36.74   +52.01    73.1     3.061    8.22    -57.54

### bk50d_s15_tr15_v2.0  (current tr cap: <=0.15)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       859   +25.32   +42.32    67.2     2.302    6.02    -60.46
[0.1-0.15)      450   +37.02   +59.24    75.6     3.505    9.38    -56.64
[0.15-0.2)      262   +56.53   +70.84    77.9     3.994   11.23    -63.10
[0.2-0.25)      123   +63.58   +74.67    81.3     4.314   12.50    -60.88
[0.25-0.3)       59   +86.85  +116.22    96.6       n/a  121.23    -28.52
[>0.3)           31  +117.17  +120.97    87.1       n/a   28.47    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1784   +38.74   +56.82    73.2     3.246    8.66    -59.29
<=0.15 (cap)   1309   +29.05   +48.14    70.1     2.691    7.05    -58.95

```
