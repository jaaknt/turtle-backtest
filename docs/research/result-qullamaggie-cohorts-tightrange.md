# Qullamaggie Tight-Range Cohort Analysis

Run date: 2026-08-02 23:44:46 Tallinn time

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
[0.0-0.1)       570   +29.43   +44.33    69.6     2.653    7.03    -56.76
[0.1-0.15)      361   +39.41   +57.74    75.3     3.210    8.51    -57.36
[0.15-0.2)      240   +56.33   +69.13    80.8     4.569   13.86    -55.87
[0.2-0.25)      122   +63.73   +77.00    82.0     4.445   13.00    -60.88
[0.25-0.3)       58   +96.27  +120.18    96.6       n/a  123.22    -28.52
[>0.3)           30  +128.69  +125.60    90.0       n/a   32.77    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1381   +44.26   +59.98    75.7     3.635    9.99    -57.09
<=0.10 (cap)    570   +29.43   +44.33    69.6     2.653    7.03    -56.76

### bk50d_s20_tr20_v2.0  (current tr cap: <=0.20)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       570   +29.43   +44.33    69.6     2.653    7.03    -56.76
[0.1-0.15)      361   +39.41   +57.74    75.3     3.210    8.51    -57.36
[0.15-0.2)      240   +56.33   +69.13    80.8     4.569   13.86    -55.87
[0.2-0.25)      122   +63.73   +77.00    82.0     4.445   13.00    -60.88
[0.25-0.3)       58   +96.27  +120.18    96.6       n/a  123.22    -28.52
[>0.3)           30  +128.69  +125.60    90.0       n/a   32.77    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1381   +44.26   +59.98    75.7     3.635    9.99    -57.09
<=0.20 (cap)   1171   +39.11   +53.55    73.7     3.185    8.60    -57.18

### bk50d_s15_tr15_v2.0  (current tr cap: <=0.15)

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
[<0)              0        —        —       —         —       —         —
[0.0-0.1)       739   +26.19   +43.76    66.8     2.401    6.24    -60.37
[0.1-0.15)      419   +38.47   +57.77    75.4     3.241    8.65    -58.39
[0.15-0.2)      260   +56.53   +71.74    78.5     4.121   11.76    -62.89
[0.2-0.25)      126   +63.59   +75.00    81.7     4.385   12.83    -60.88
[0.25-0.3)       61   +95.01  +117.00    96.7       n/a  126.13    -15.71
[>0.3)           30  +128.69  +125.60    90.0       n/a   32.77    -75.02
─────────────────────────────────────────────────────────────────────────
ALL            1635   +41.10   +58.44    73.6     3.333    8.93    -59.69
<=0.15 (cap)   1158   +30.68   +48.83    69.9     2.700    7.06    -59.48

```
