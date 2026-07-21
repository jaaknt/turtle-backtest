# Qullamaggie Ranking — Out-of-Sample Validation

Run date: 2026-07-22

Reference config: bk50d_s15_v1.3_roc100 / 366d hold | Period: 2015-01-01 - 2026-06-26 | Split date: 2021-01-01 (train N=1007, held-out N=720)

Three scorers, all evaluated on the same held-out (entries >= split date) signals:

1. **Refit-on-train** — bands independently re-derived from training-slice-only Sortino (genuine out-of-sample test of the ranking methodology)
2. **Production** — the actual shipped `QullamaggieRanking` bands (fit on the full 2015-2026 period, so not strictly out-of-sample here, but shows real-world behavior on the most recent slice)
3. **Legacy (pre-change)** — the old 4-dimension bands (ADR/compression/price/SMA50 only, no ROC252/RSI), as the baseline to beat

```text
### Refit-on-train (out-of-sample)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1           7.6    72   +4.86  +13.68   59.7    0.489   2.39
D2          14.9    72   +5.10  +25.49   56.9    0.905   3.55
D3          19.8    72  +23.31  +30.59   62.5    0.923   3.96
D4          23.2    72  +17.12  +35.02   65.3    0.972   4.53
D5          29.2    72  +24.56  +42.09   62.5    1.325   5.47
D6          40.4    72  +25.12  +52.57   72.2    1.539   7.62
D7          47.4    72  +26.07  +71.31   73.6    1.782   9.16
D8          53.2    72   +2.48  +24.27   54.2    0.827   3.27
D9          60.8    72  +23.17  +62.06   62.5    1.718   6.35
D10         73.9    72  +60.79  +68.62   66.7    1.832   7.51

Sortino monotonicity: 8/9 decile steps non-decreasing
Mean% monotonicity: 8/9 decile steps non-decreasing
```

```text
### Production bands (reference)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          25.8    72   +4.51  +14.06   56.9    0.490   2.27
D2          34.0    72   +8.77  +24.83   59.7    0.843   3.60
D3          40.3    72   +9.69  +22.15   58.3    0.578   2.75
D4          43.9    72  +25.65  +30.40   63.9    1.008   4.53
D5          48.8    72  +25.58  +50.10   65.3    1.601   6.24
D6          54.4    72  +25.90  +39.79   70.8    1.603   8.12
D7          59.1    72  +14.30  +47.72   63.9    1.258   5.17
D8          64.1    72  +18.68  +70.41   63.9    1.735   6.70
D9          69.4    72  +16.21  +57.25   59.7    2.183   7.62
D10         80.1    72  +61.23  +68.99   73.6    1.689   8.23

Sortino monotonicity: 6/9 decile steps non-decreasing
Mean% monotonicity: 6/9 decile steps non-decreasing
```

```text
### Legacy pre-change bands (baseline)

Decile     Score     N     Med%    Mean%   Win%  Sortino     PF
---------------------------------------------------------------
D1          34.2    72  +14.73  +22.39   68.1    0.820   3.93
D2          42.1    72   -0.34  +17.44   48.6    0.535   2.23
D3          47.4    72  +13.45  +27.63   65.3    0.800   4.01
D4          50.2    72  +21.67  +23.09   58.3    0.691   3.11
D5          56.7    72  +27.69  +59.72   65.3    2.141   8.31
D6          61.7    72  +28.66  +44.65   70.8    1.569   7.42
D7          66.7    72  +23.74  +63.17   69.4    1.827   8.10
D8          71.3    72   +9.75  +48.73   59.7    1.239   4.68
D9          76.8    72  +18.87  +54.86   61.1    1.584   6.12
D10         85.9    72  +41.28  +64.01   69.4    1.839   8.02

Sortino monotonicity: 5/9 decile steps non-decreasing
Mean% monotonicity: 5/9 decile steps non-decreasing
```

## Summary

D10-D1 spread is the primary metric here -- the goal is optimizing Sortino and Mean%, so a scheme that widens the gap between its best and worst decile on those two is doing its job; Win% is reported in the tables above for context only, not used to judge fit.

- Refit-on-train: Sortino spread=1.343, Mean% spread=+54.9, Sortino mono=8/9, Mean% mono=8/9
- Production: Sortino spread=1.198, Mean% spread=+54.9, Sortino mono=6/9, Mean% mono=6/9
- Legacy: Sortino spread=1.019, Mean% spread=+41.6, Sortino mono=5/9, Mean% mono=5/9

## Weight-Split Stability Across Multiple Periods

Tests whether the production weight split (price=13, adr=12, compression=12, roc=10, rsi=3) reflects a stable pattern or is sensitive to the single 2021 split date used above. For each cutoff below, weights are independently refit on signals entered before it (same reachable-Sortino-spread methodology as the production bands), with no reference to the production numbers.

```text
Split date    Train N        price          adr  compression          roc          rsi
--------------------------------------------------------------------------------------
2019-01-01        330           12           12            4           20            2
2020-01-01        433           15           11            5           15            4
2021-01-01       1007           11           11            7           12            9
2022-01-01       1150           15            9            5            8           13
2023-01-01       1243           13           15            6            7            9
```

Cross-fold average weight (renormalized to sum 50): price=13, adr=13, compression=5, roc=12, rsi=7

### Multi-fold out-of-sample comparison

For each cutoff, weights/bands are fit on data before it and scored on data at/after it (a genuine walk-forward fold for refit-per-fold and stabilized-avg; production/legacy are fixed constants scored on the same fold's held-out data for reference). Averaged across all folds -- this is the actual test of whether any scheme is *consistently* better, not just better on the single 2021 split above:

```text
Scheme            Avg Sortino spread  Avg Mean% spread  Folds
-------------------------------------------------------------
Refit-per-fold                 0.927             +35.5      5
Stabilized-avg                 1.075             +41.0      5
Production                     1.334             +57.6      5
Legacy                         1.347             +51.6      5
```

Highest average out-of-sample Sortino spread across folds: **Legacy**
