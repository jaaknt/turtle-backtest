# Qullamaggie Dynamic Cohort Ranking (s15)

Run date: 2026-07-22

```text
Dynamic cohort ranking | bk50d_s15_v1.2_roc100 | Hold: 366d | Period: 2015-01-01 – 2026-06-26
P(success) = sigmoid(mean log-odds of walk-forward cohort Win% across ADR%, compression, RSI14, price, vol_surge, ROC252)
Shrinkage k=20 toward running pool win rate | warm-up: 300 completed trades
Completed trades: 1695 | scored (post warm-up): 1369 | first scored entry: 2019-02-12

### bk50d_s15_v1.2_roc100 — walk-forward P(success) deciles (D1 = lowest, D10 = highest)

Decile      PredP%      N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────────────
D1            59.1    137   +58.18   +62.61    86.9     2.023   19.49
D2            61.0    137   +52.77   +58.25    88.3     1.512   16.69
D3            62.1    137   +42.99   +58.63    86.9     1.840   17.42
D4            63.0    137   +38.51   +51.41    83.9     1.625   13.75
D5            63.8    137   +33.86   +45.24    78.8     1.203    8.21
D6            66.9    137   +25.73   +39.88    70.1     1.236    6.37
D7            71.8    137   +26.32   +68.78    64.2     2.106    8.40
D8            73.7    137   +18.38   +57.09    65.7     2.141    8.28
D9            75.5    137    -6.85   +12.68    46.0     0.340    1.76
D10           77.4    136   +11.53   +23.27    59.6     0.596    2.72
─────────────────────────────────────────────────────────────────────
ALL           67.4   1369   +31.74   +47.80    73.0     1.389    7.32

Win% monotonicity: 3/9 decile steps non-decreasing

### bk50d_s15_v1.2_roc100 — regime-neutral (pool-relative) score deciles (D1 = lowest, D10 = highest)

Decile      PredP%      N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────────────
D1            46.3    137   +33.76   +42.71    70.8     1.155    5.99
D2            47.9    137   +29.70   +39.79    69.3     1.432    6.54
D3            48.7    137   +22.24   +48.52    70.8     1.240    6.11
D4            49.2    137   +38.33   +49.34    71.5     1.480    7.33
D5            49.8    137   +30.35   +45.75    73.0     1.454    7.44
D6            50.3    137   +30.52   +47.90    73.0     1.388    7.32
D7            50.8    137   +32.95   +53.52    78.8     1.595   10.06
D8            51.3    137   +26.57   +47.28    70.8     1.492    7.02
D9            51.9    137   +33.86   +51.08    76.6     1.577    8.95
D10           53.1    136   +30.33   +52.16    75.7     1.237    7.70
─────────────────────────────────────────────────────────────────────
ALL           49.9   1369   +31.74   +47.80    73.0     1.389    7.32

Win% monotonicity: 6/9 decile steps non-decreasing

```
