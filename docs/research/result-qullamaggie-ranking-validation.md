# Qullamaggie Ranking — Out-of-Sample Validation

Run date: 2026-10-24 18:18:18 Tallinn time

Reference config: bk50d_s15_v1.3_roc100 / 366d hold | Period: 2015-01-01 - 2026-06-26 | Split date: 2021-01-01 (train N=1967, held-out N=1415)

Three scorers, all evaluated on the same held-out (entries >= split date) signals:

1. **Refit-on-train** — bands independently re-derived from training-slice-only Sortino (genuine out-of-sample test of the ranking methodology)
2. **Shipped** — whatever `QullamaggieRanking` currently scores. Since 2026-07-29 that is the three-dimension 40/35/25 weighting, which this script's refit arm does *not* mirror: the refit still fits six dimensions by reachable-Sortino-spread, the methodology that was in production when this study was written. Read arm 2 as 'how the shipped ranking behaves on the most recent slice', not as a validation of how its weights were chosen — that is `result-qullamaggie-ranking-weights.md`.
3. **Legacy (pre-change)** — the old 4-dimension bands (ADR/compression/price/SMA50 only, no ROC252/RSI), as the baseline to beat

```text
### Refit-on-train (out-of-sample)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1           9.4   141   +3.63  +14.11   52.5    0.754   2.36
D2          15.4   142  +18.40  +25.02   68.3    1.386   3.98
D3          19.4   141  +25.61  +41.57   70.9    2.675   6.95
D4          22.9   142  +14.72  +36.00   64.1    2.241   5.62
D5          26.5   141  +16.98  +43.94   61.7    1.976   4.92
D6          30.8   142  +20.11  +47.36   63.4    2.210   5.46
D7          35.6   141  +18.71  +42.52   66.7    2.872   7.13
D8          40.0   142  +17.51  +49.49   65.5    2.654   6.56
D9          50.5   141  +32.40  +82.58   71.6    4.318  10.50
D10         75.0   142  +45.60  +60.69   66.2    2.946   6.94

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

```text
### Production bands (reference)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          25.4   141   +7.38  +18.14   56.0    0.967   2.77
D2          30.0   142  +13.36  +23.42   66.9    1.388   4.07
D3          34.1   141  +20.81  +45.07   67.4    2.570   6.72
D4          37.5   142  +20.76  +34.76   71.1    2.216   5.95
D5          41.1   141  +12.07  +33.85   58.9    1.631   4.04
D6          45.1   142  +19.24  +47.68   61.3    2.617   6.12
D7          49.4   141  +23.39  +50.61   72.3    3.193   8.83
D8          54.6   142  +13.47  +56.25   59.2    2.895   6.41
D9          63.4   141  +22.14  +57.89   67.4    2.716   6.76
D10         83.5   142  +61.81  +75.48   70.4    3.553   8.49

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 7/9 decile steps non-decreasing
```

```text
### Legacy pre-change bands (baseline)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          33.6   141  +11.13  +25.89   64.5    1.561   4.19
D2          40.6   142   +9.17  +32.15   60.6    1.882   4.71
D3          46.4   141   +8.34  +31.20   61.0    1.547   4.09
D4          48.7   142  +14.92  +21.89   64.1    1.232   3.53
D5          54.3   141  +23.75  +37.66   63.1    1.715   4.38
D6          60.4   142  +20.09  +46.67   66.2    2.713   6.74
D7          65.0   141  +18.17  +38.84   66.7    2.479   6.23
D8          70.2   142  +25.85  +71.59   65.5    3.370   7.78
D9          75.5   141  +30.52  +56.26   65.2    2.958   7.14
D10         84.4   142  +54.32  +80.89   73.9    4.259  10.79

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 5/9 decile steps non-decreasing
```

## Summary

D10-D1 spread is the primary metric here -- the goal is optimizing Sortino and Mean%, so a scheme that widens the gap between its best and worst decile on those two is doing its job; Win% is reported in the tables above for context only, not used to judge fit.

- Refit-on-train: Sortino spread=2.192, Mean% spread=+46.6, Sortino mono=5/9, Mean% mono=6/9
- Production: Sortino spread=2.586, Mean% spread=+57.3, Sortino mono=5/9, Mean% mono=7/9
- Legacy: Sortino spread=2.698, Mean% spread=+55.0, Sortino mono=5/9, Mean% mono=5/9

## Weight-Split Stability Across Multiple Periods

Tests whether the six-dimension weight split this study was built around (price=13, adr=12, compression=12, roc=10, rsi=3, SMA50=50 — production until 2026-07-29) reflects a stable pattern or is sensitive to the single 2021 split date used above. For each cutoff below, weights are independently refit on signals entered before it (same reachable-Sortino-spread methodology as the production bands), with no reference to the production numbers.

```text
Split date    Train N        price          adr  compression          roc          rsi
--------------------------------------------------------------------------------------
2019-01-01        622           10           16            8           14            2
2020-01-01        840           11           13            1           24            1
2021-01-01       1967            4           12           18           14            2
2022-01-01       2245            7            9           16           13            5
2023-01-01       2397            6           19           12            9            4
```

Cross-fold average weight (renormalized to sum 50): price=7, adr=14, compression=11, roc=15, rsi=3

### Multi-fold out-of-sample comparison

For each cutoff, weights/bands are fit on data before it and scored on data at/after it (a genuine walk-forward fold for refit-per-fold and stabilized-avg; production/legacy are fixed constants scored on the same fold's held-out data for reference). Averaged across all folds -- this is the actual test of whether any scheme is *consistently* better, not just better on the single 2021 split above:

```text
Scheme            Avg Sortino spread  Avg Mean% spread  Folds
-------------------------------------------------------------
Refit-per-fold                 2.136             +43.9      5
Stabilized-avg                 2.443             +44.7      5
Production                     2.704             +55.2      5
Legacy                         3.282             +55.6      5
```

Highest average out-of-sample Sortino spread across folds: **Legacy**
