# Qullamaggie Ranking — Out-of-Sample Validation

Run date: 2026-08-09 18:58:13 Tallinn time

Reference config: bk50d_s15_v1.3_roc100 / 366d hold | Period: 2015-01-01 - 2026-06-26 | Split date: 2021-01-01 (train N=2013, held-out N=1376)

Three scorers, all evaluated on the same held-out (entries >= split date) signals:

1. **Refit-on-train** — bands independently re-derived from training-slice-only Sortino (genuine out-of-sample test of the ranking methodology)
2. **Shipped** — whatever `QullamaggieRanking` currently scores. Since 2026-07-29 that is the three-dimension 40/35/25 weighting, which this script's refit arm does *not* mirror: the refit still fits six dimensions by reachable-Sortino-spread, the methodology that was in production when this study was written. Read arm 2 as 'how the shipped ranking behaves on the most recent slice', not as a validation of how its weights were chosen — that is `result-qullamaggie-ranking-weights.md`.
3. **Legacy (pre-change)** — the old 4-dimension bands (ADR/compression/price/SMA50 only, no ROC252/RSI), as the baseline to beat

```text
### Refit-on-train (out-of-sample)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1           9.1   137   +5.69  +12.53   54.0    0.615   2.13
D2          14.7   138  +13.03  +23.60   63.0    1.250   3.55
D3          18.8   137  +19.24  +26.23   69.3    1.371   3.92
D4          22.7   138  +10.59  +38.25   60.1    1.963   4.79
D5          26.1   138  +19.71  +46.04   60.1    2.049   4.99
D6          30.1   137  +25.90  +47.52   68.6    2.394   5.98
D7          35.1   138  +20.60  +39.51   65.9    2.403   6.16
D8          39.5   137  +17.53  +56.13   65.0    2.669   6.27
D9          51.6   138  +31.57  +77.66   68.8    3.987   9.78
D10         76.0   138  +48.25  +63.59   64.5    2.872   6.58

Sortino monotonicity: 8/9 decile steps non-decreasing
Mean% monotonicity: 7/9 decile steps non-decreasing
```

```text
### Production bands (reference)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          25.5   137   +7.13  +16.24   56.2    0.816   2.50
D2          30.1   138  +13.47  +21.71   65.2    1.233   3.64
D3          34.3   137  +23.68  +44.11   69.3    2.455   6.47
D4          37.8   138  +19.04  +33.71   67.4    1.926   5.15
D5          41.5   138   +9.35  +32.81   58.7    1.484   3.73
D6          45.3   137  +17.28  +49.68   59.9    2.530   5.81
D7          49.5   138  +25.04  +50.22   73.9    2.967   8.30
D8          55.1   137   +9.61  +52.31   55.5    2.479   5.41
D9          64.2   138  +19.55  +49.01   63.8    1.993   4.93
D10         85.3   138  +63.26  +81.41   69.6    3.828   8.93

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

```text
### Legacy pre-change bands (baseline)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          33.7   137  +11.11  +23.52   63.5    1.312   3.73
D2          40.7   138  +14.81  +35.85   63.0    1.962   4.80
D3          46.4   137   +5.69  +26.77   58.4    1.409   3.79
D4          48.7   138  +17.42  +21.70   63.8    1.059   3.10
D5          54.2   138  +21.06  +35.11   60.9    1.506   3.87
D6          60.3   137  +19.21  +42.90   64.2    2.286   5.65
D7          65.3   138  +23.53  +43.58   71.0    2.740   7.30
D8          70.6   137  +14.33  +64.00   59.9    2.551   5.66
D9          76.2   138  +29.42  +56.44   63.0    2.736   6.44
D10         85.2   138  +52.07  +81.30   71.7    4.289  10.51

Sortino monotonicity: 6/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

## Summary

D10-D1 spread is the primary metric here -- the goal is optimizing Sortino and Mean%, so a scheme that widens the gap between its best and worst decile on those two is doing its job; Win% is reported in the tables above for context only, not used to judge fit.

- Refit-on-train: Sortino spread=2.257, Mean% spread=+51.1, Sortino mono=8/9, Mean% mono=7/9
- Production: Sortino spread=3.013, Mean% spread=+65.2, Sortino mono=5/9, Mean% mono=6/9
- Legacy: Sortino spread=2.977, Mean% spread=+57.8, Sortino mono=6/9, Mean% mono=6/9

## Weight-Split Stability Across Multiple Periods

Tests whether the six-dimension weight split this study was built around (price=13, adr=12, compression=12, roc=10, rsi=3, SMA50=50 — production until 2026-07-29) reflects a stable pattern or is sensitive to the single 2021 split date used above. For each cutoff below, weights are independently refit on signals entered before it (same reachable-Sortino-spread methodology as the production bands), with no reference to the production numbers.

```text
Split date    Train N        price          adr  compression          roc          rsi
--------------------------------------------------------------------------------------
2019-01-01        631           18           13            5           13            1
2020-01-01        858           19            9            1           18            3
2021-01-01       2013            5           11           19           13            2
2022-01-01       2294           11            8           15           11            5
2023-01-01       2448            9           18           12            8            3
```

Cross-fold average weight (renormalized to sum 50): price=12, adr=12, compression=10, roc=13, rsi=3

### Multi-fold out-of-sample comparison

For each cutoff, weights/bands are fit on data before it and scored on data at/after it (a genuine walk-forward fold for refit-per-fold and stabilized-avg; production/legacy are fixed constants scored on the same fold's held-out data for reference). Averaged across all folds -- this is the actual test of whether any scheme is *consistently* better, not just better on the single 2021 split above:

```text
Scheme            Avg Sortino spread  Avg Mean% spread  Folds
-------------------------------------------------------------
Refit-per-fold                 2.188             +45.7      5
Stabilized-avg                 2.288             +46.4      5
Production                     2.963             +58.7      5
Legacy                         3.365             +59.1      5
```

Highest average out-of-sample Sortino spread across folds: **Legacy**
