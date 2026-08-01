# Qullamaggie Ranking — Out-of-Sample Validation

Run date: 2026-08-01 11:01:31 Tallinn time

Reference config: bk50d_s15_v1.3_roc100 / 366d hold | Period: 2015-01-01 - 2026-06-26 | Split date: 2021-01-01 (train N=1390, held-out N=982)

Three scorers, all evaluated on the same held-out (entries >= split date) signals:

1. **Refit-on-train** — bands independently re-derived from training-slice-only Sortino (genuine out-of-sample test of the ranking methodology)
2. **Shipped** — whatever `QullamaggieRanking` currently scores. Since 2026-07-29 that is the three-dimension 40/35/25 weighting, which this script's refit arm does *not* mirror: the refit still fits six dimensions by reachable-Sortino-spread, the methodology that was in production when this study was written. Read arm 2 as 'how the shipped ranking behaves on the most recent slice', not as a validation of how its weights were chosen — that is `result-qullamaggie-ranking-weights.md`.
3. **Legacy (pre-change)** — the old 4-dimension bands (ADR/compression/price/SMA50 only, no ROC252/RSI), as the baseline to beat

```text
### Refit-on-train (out-of-sample)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1           7.4    98   +2.21  +11.48   52.0    0.465   1.82
D2          13.3    98  +13.69  +23.36   60.2    1.317   3.44
D3          16.9    98  +26.68  +40.23   70.4    2.272   5.80
D4          20.9    98  +26.54  +44.25   67.3    3.159   8.36
D5          24.2    99   +7.94  +22.96   55.6    0.961   2.71
D6          28.1    98  +27.70  +58.74   72.4    4.529  11.24
D7          32.5    98   +7.61  +38.00   59.2    1.624   4.17
D8          36.7    98  +29.42  +54.54   70.4    2.884   7.05
D9          49.9    98  +19.85  +83.78   67.3    4.395  10.27
D10         75.3    99  +56.29  +64.51   66.7    2.967   6.86

Sortino monotonicity: 6/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

```text
### Production bands (reference)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          14.3    98  +10.58  +20.48   61.2    1.157   3.19
D2          22.7    98   +8.33  +28.05   65.3    1.590   4.47
D3          24.9    98  +13.85  +28.75   61.2    1.541   4.08
D4          31.5    98  +25.50  +50.45   64.3    2.702   6.35
D5          35.6    99  +23.08  +34.84   63.6    1.661   4.26
D6          42.2    98  +22.37  +53.02   64.3    2.840   6.70
D7          48.8    98  +18.88  +44.08   64.3    2.367   5.64
D8          59.8    98  +23.39  +46.45   61.2    2.130   5.12
D9          66.6    98  +23.94  +48.53   64.3    2.156   5.42
D10         84.8    99  +62.59  +86.85   71.7    3.979   9.49

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 7/9 decile steps non-decreasing
```

```text
### Legacy pre-change bands (baseline)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          34.0    98   +9.82  +21.51   61.2    1.261   3.41
D2          41.3    98   +7.96  +29.45   58.2    1.458   3.62
D3          47.1    98  +11.54  +23.67   62.2    1.152   3.34
D4          49.6    98  +15.05  +25.46   60.2    1.092   3.14
D5          55.6    99  +23.08  +47.95   62.6    2.666   6.28
D6          61.1    98  +24.40  +42.54   68.4    2.573   6.41
D7          66.0    98  +28.62  +72.27   73.5    4.482  11.62
D8          71.0    98   +9.38  +41.94   60.2    1.704   4.20
D9          76.5    98  +38.20  +61.20   65.3    3.359   7.83
D10         85.1    99  +55.21  +75.50   69.7    3.530   8.42

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

## Summary

D10-D1 spread is the primary metric here -- the goal is optimizing Sortino and Mean%, so a scheme that widens the gap between its best and worst decile on those two is doing its job; Win% is reported in the tables above for context only, not used to judge fit.

- Refit-on-train: Sortino spread=2.502, Mean% spread=+53.0, Sortino mono=6/9, Mean% mono=6/9
- Production: Sortino spread=2.822, Mean% spread=+66.4, Sortino mono=5/9, Mean% mono=7/9
- Legacy: Sortino spread=2.269, Mean% spread=+54.0, Sortino mono=5/9, Mean% mono=6/9

## Weight-Split Stability Across Multiple Periods

Tests whether the six-dimension weight split this study was built around (price=13, adr=12, compression=12, roc=10, rsi=3, SMA50=50 — production until 2026-07-29) reflects a stable pattern or is sensitive to the single 2021 split date used above. For each cutoff below, weights are independently refit on signals entered before it (same reachable-Sortino-spread methodology as the production bands), with no reference to the production numbers.

```text
Split date    Train N        price          adr  compression          roc          rsi
--------------------------------------------------------------------------------------
2019-01-01        447           10           10            7           17            6
2020-01-01        594           15            7            2           23            3
2021-01-01       1390            5           10           17           17            1
2022-01-01       1569            7           10           14           12            7
2023-01-01       1686            7           18           12            9            4
```

Cross-fold average weight (renormalized to sum 50): price=9, adr=11, compression=10, roc=16, rsi=4

### Multi-fold out-of-sample comparison

For each cutoff, weights/bands are fit on data before it and scored on data at/after it (a genuine walk-forward fold for refit-per-fold and stabilized-avg; production/legacy are fixed constants scored on the same fold's held-out data for reference). Averaged across all folds -- this is the actual test of whether any scheme is *consistently* better, not just better on the single 2021 split above:

```text
Scheme            Avg Sortino spread  Avg Mean% spread  Folds
-------------------------------------------------------------
Refit-per-fold                 2.397             +44.6      5
Stabilized-avg                 2.218             +44.6      5
Production                     3.358             +68.7      5
Legacy                         3.599             +59.4      5
```

Highest average out-of-sample Sortino spread across folds: **Legacy**
