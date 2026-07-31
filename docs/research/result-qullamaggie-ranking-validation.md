# Qullamaggie Ranking — Out-of-Sample Validation

Run date: 2026-08-01 02:00:50 Tallinn time

Reference config: bk50d_s15_v1.3_roc100 / 366d hold | Period: 2015-01-01 - 2026-06-26 | Split date: 2021-01-01 (train N=1004, held-out N=722)

Three scorers, all evaluated on the same held-out (entries >= split date) signals:

1. **Refit-on-train** — bands independently re-derived from training-slice-only Sortino (genuine out-of-sample test of the ranking methodology)
2. **Shipped** — whatever `QullamaggieRanking` currently scores. Since 2026-07-29 that is the three-dimension 40/35/25 weighting, which this script's refit arm does *not* mirror: the refit still fits six dimensions by reachable-Sortino-spread, the methodology that was in production when this study was written. Read arm 2 as 'how the shipped ranking behaves on the most recent slice', not as a validation of how its weights were chosen — that is `result-qullamaggie-ranking-weights.md`.
3. **Legacy (pre-change)** — the old 4-dimension bands (ADR/compression/price/SMA50 only, no ROC252/RSI), as the baseline to beat

```text
### Refit-on-train (out-of-sample)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1           8.1    72   +4.86  +12.53   59.7    0.682   2.23
D2          13.6    72  +12.58  +20.30   63.9    1.038   3.08
D3          17.2    72  +15.97  +28.91   58.3    1.585   3.94
D4          20.6    72  +16.07  +40.34   62.5    2.035   5.37
D5          26.2    73  +30.19  +42.88   68.5    2.110   5.62
D6          36.4    72  +21.95  +57.78   70.8    3.059   7.60
D7          44.7    72  +14.30  +43.86   63.9    2.604   6.33
D8          50.2    72  +10.37  +48.02   61.1    2.165   5.34
D9          58.8    72  +18.15  +72.42   63.9    3.208   7.09
D10         74.9    73  +52.91  +64.01   67.1    3.035   7.40

Sortino monotonicity: 6/9 decile steps non-decreasing
Mean% monotonicity: 7/9 decile steps non-decreasing
```

```text
### Production bands (reference)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          14.1    72  +10.35  +21.11   63.9    1.289   3.51
D2          22.7    72  +10.91  +25.72   65.3    1.435   3.97
D3          24.6    72  +13.45  +29.63   63.9    1.556   4.31
D4          31.1    72  +28.47  +66.68   68.1    4.008   9.72
D5          34.8    73  +27.63  +35.36   65.8    1.790   4.63
D6          41.7    72  +22.37  +44.10   63.9    2.140   5.26
D7          48.1    72  +11.49  +40.52   59.7    1.952   4.65
D8          59.1    72  +20.10  +51.41   63.9    3.097   7.08
D9          66.0    72  +18.95  +42.61   56.9    1.607   4.05
D10         84.1    73  +60.56  +73.88   68.5    3.331   7.77

Sortino monotonicity: 6/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

```text
### Legacy pre-change bands (baseline)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          34.2    72  +12.54  +20.64   66.7    1.338   3.70
D2          42.0    72   +4.33  +20.83   52.8    0.943   2.60
D3          47.4    72  +14.57  +25.10   63.9    1.211   3.57
D4          50.0    72  +22.20  +25.89   61.1    1.287   3.53
D5          56.5    73  +26.76  +54.99   64.4    2.874   7.06
D6          61.7    72  +28.66  +47.76   70.8    3.184   8.09
D7          66.6    72  +22.86  +57.09   69.4    3.160   7.60
D8          71.3    72   +9.75  +55.77   59.7    2.257   5.38
D9          76.5    72  +28.89  +59.07   63.9    3.018   7.08
D10         85.8    73  +41.65  +63.72   67.1    2.928   6.98

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 7/9 decile steps non-decreasing
```

## Summary

D10-D1 spread is the primary metric here -- the goal is optimizing Sortino and Mean%, so a scheme that widens the gap between its best and worst decile on those two is doing its job; Win% is reported in the tables above for context only, not used to judge fit.

- Refit-on-train: Sortino spread=2.353, Mean% spread=+51.5, Sortino mono=6/9, Mean% mono=7/9
- Production: Sortino spread=2.043, Mean% spread=+52.8, Sortino mono=6/9, Mean% mono=6/9
- Legacy: Sortino spread=1.590, Mean% spread=+43.1, Sortino mono=5/9, Mean% mono=7/9

## Weight-Split Stability Across Multiple Periods

Tests whether the six-dimension weight split this study was built around (price=13, adr=12, compression=12, roc=10, rsi=3, SMA50=50 — production until 2026-07-29) reflects a stable pattern or is sensitive to the single 2021 split date used above. For each cutoff below, weights are independently refit on signals entered before it (same reachable-Sortino-spread methodology as the production bands), with no reference to the production numbers.

```text
Split date    Train N        price          adr  compression          roc          rsi
--------------------------------------------------------------------------------------
2019-01-01        327           12           13            5           16            4
2020-01-01        430           16           12            6           14            2
2021-01-01       1004            8           12           11           12            7
2022-01-01       1146           11            9            8           10           12
2023-01-01       1237           10           13            9            9            9
```

Cross-fold average weight (renormalized to sum 50): price=11, adr=12, compression=8, roc=12, rsi=7

### Multi-fold out-of-sample comparison

For each cutoff, weights/bands are fit on data before it and scored on data at/after it (a genuine walk-forward fold for refit-per-fold and stabilized-avg; production/legacy are fixed constants scored on the same fold's held-out data for reference). Averaged across all folds -- this is the actual test of whether any scheme is *consistently* better, not just better on the single 2021 split above:

```text
Scheme            Avg Sortino spread  Avg Mean% spread  Folds
-------------------------------------------------------------
Refit-per-fold                 1.438             +33.2      5
Stabilized-avg                 1.347             +33.1      5
Production                     2.804             +57.9      5
Legacy                         3.241             +54.8      5
```

Highest average out-of-sample Sortino spread across folds: **Legacy**
