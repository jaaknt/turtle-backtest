# Qullamaggie Tight-Range Cohort Analysis

Run date: 2026-10-24 17:46:13 Tallinn time

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
[0.0-0.1)       702   +28.91   +42.60    70.5     2.521    6.94    -58.17
[0.1-0.15)      383   +36.97   +53.96    73.6     2.985    7.86    -58.11
[0.15-0.2)      232   +56.72   +70.83    81.5     5.227   15.68    -49.72
[0.2-0.25)      114   +63.73   +76.44    81.6     4.364   12.73    -63.33
[0.25-0.3)       55   +86.85  +118.94    98.2       n/a  357.38     -4.22
[>0.3)           31  +117.17  +120.97    87.1       n/a   28.47    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1517   +41.23   +56.70    75.1     3.447    9.54    -57.41
<=0.10 (cap)    702   +28.91   +42.60    70.5     2.521    6.94    -58.17

### bk50d_s20_tr20_v2.0  (current tr cap: <=0.20)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       702   +28.91   +42.60    70.5     2.521    6.94    -58.17
[0.1-0.15)      383   +36.97   +53.96    73.6     2.985    7.86    -58.11
[0.15-0.2)      232   +56.72   +70.83    81.5     5.227   15.68    -49.72
[0.2-0.25)      114   +63.73   +76.44    81.6     4.364   12.73    -63.33
[0.25-0.3)       55   +86.85  +118.94    98.2       n/a  357.38     -4.22
[>0.3)           31  +117.17  +120.97    87.1       n/a   28.47    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1517   +41.23   +56.70    75.1     3.447    9.54    -57.41
<=0.20 (cap)   1317   +36.74   +50.88    73.3     3.042    8.31    -57.37

### bk50d_s15_tr15_v2.0  (current tr cap: <=0.15)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       862   +25.21   +41.98    67.3     2.309    6.14    -60.12
[0.1-0.15)      444   +36.41   +54.90    75.0     3.212    8.65    -57.40
[0.15-0.2)      251   +57.29   +73.98    79.3     4.842   13.82    -55.17
[0.2-0.25)      118   +63.59   +74.33    81.4     4.302   12.56    -63.33
[0.25-0.3)       58   +86.80  +115.66    98.3       n/a  366.44     -4.22
[>0.3)           31  +117.17  +120.97    87.1       n/a   28.47    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1764   +38.21   +55.76    73.2     3.261    8.81    -58.53
<=0.15 (cap)   1306   +28.64   +46.37    69.9     2.602    6.92    -59.20

```
