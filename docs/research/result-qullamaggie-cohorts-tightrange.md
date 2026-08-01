# Qullamaggie Tight-Range Cohort Analysis

Run date: 2026-08-01 09:10:10 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | **bk50d_s20_tr10_v2.0, bk50d_s20_tr20_v2.0, bk50d_s15_tr15_v2.0 (366d)** |
| Cohort variable | tight_range_ratio = (max - min) / mean of the previous 10 closes |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **each variant's tight_range cap — removed; returns as its `<=0.10` / `<=0.20` / `<=0.15 (cap)` row** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90% |
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
[0.0-0.1)       319   +27.19   +44.80    69.0     2.524    6.77    -60.65
[0.1-0.15)      189   +42.38   +57.32    78.8     3.381    9.60    -57.40
[0.15-0.2)      125   +59.22   +84.10    84.0     5.914   20.52    -56.73
[0.2-0.25)       68   +63.47   +70.99    82.4     3.712   10.33    -63.94
[0.25-0.3)       28   +86.80  +106.41    96.4       n/a   78.03    -38.68
[>0.3)            8  +156.97  +136.85    87.5       n/a   15.59    -75.02
─────────────────────────────────────────────────────────────────────────
ALL             737   +45.00   +60.43    76.5     3.562   10.08    -59.80
<=0.10 (cap)    319   +27.19   +44.80    69.0     2.524    6.77    -60.65

### bk50d_s20_tr20_v2.0  (current tr cap: <=0.20)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       319   +27.19   +44.80    69.0     2.524    6.77    -60.65
[0.1-0.15)      189   +42.38   +57.32    78.8     3.381    9.60    -57.40
[0.15-0.2)      125   +59.22   +84.10    84.0     5.914   20.52    -56.73
[0.2-0.25)       68   +63.47   +70.99    82.4     3.712   10.33    -63.94
[0.25-0.3)       28   +86.80  +106.41    96.4       n/a   78.03    -38.68
[>0.3)            8  +156.97  +136.85    87.5       n/a   15.59    -75.02
─────────────────────────────────────────────────────────────────────────
ALL             737   +45.00   +60.43    76.5     3.562   10.08    -59.80
<=0.20 (cap)    633   +40.54   +56.30    74.9     3.338    9.33    -59.27

### bk50d_s15_tr15_v2.0  (current tr cap: <=0.15)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       409   +25.82   +44.91    66.0     2.429    6.27    -60.53
[0.1-0.15)      218   +40.72   +53.57    78.0     3.296    9.33    -56.51
[0.15-0.2)      130   +59.28   +83.33    83.1     5.312   17.10    -62.16
[0.2-0.25)       71   +63.36   +69.97    81.7     3.720   10.31    -63.94
[0.25-0.3)       29   +86.85  +106.74    96.6       n/a   81.03    -38.68
[>0.3)            8  +156.97  +136.85    87.5       n/a   15.59    -75.02
─────────────────────────────────────────────────────────────────────────
ALL             865   +42.28   +57.85    74.1     3.326    9.06    -59.67
<=0.15 (cap)    627   +30.48   +47.92    70.2     2.700    7.15    -58.79

```
