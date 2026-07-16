# Qullamaggie Dynamic Cohort Ranking (s15)

Run date: 2026-07-16

```text
Dynamic cohort ranking | bk50d_s15_v1.2_roc100 | Hold: 366d | Period: 2015-01-01 – 2026-06-26
P(success) = sigmoid(mean log-odds of walk-forward cohort Win% across ADR%, compression, RSI14, price, vol_surge, ROC252)
Shrinkage k=20 toward running pool win rate | warm-up: 300 completed trades
Completed trades: 1598 | scored (post warm-up): 1237 | first scored entry: 2019-06-06

### bk50d_s15_v1.2_roc100 — walk-forward P(success) deciles (D1 = lowest, D10 = highest)

Decile      PredP%      N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────────────
D1            59.9    124   +56.14   +57.02    85.5     1.868   16.07
D2            61.7    124   +54.52   +63.32    90.3     2.493   32.68
D3            62.6    124   +44.25   +56.94    83.9     1.655   13.22
D4            63.4    124   +40.01   +48.81    88.7     1.222   15.24
D5            64.2    124   +43.51   +49.68    81.5     1.601   11.58
D6            67.3    124   +29.39   +55.83    73.4     1.773   10.05
D7            72.5    124   +29.34   +67.49    66.1     2.192    9.29
D8            74.3    123   +18.08   +54.94    65.0     2.013    7.65
D9            75.9    123    -5.86   +11.05    47.2     0.304    1.70
D10           77.8    123   +13.41   +25.43    61.0     0.669    3.02
─────────────────────────────────────────────────────────────────────
ALL           67.9   1237   +32.95   +49.10    74.3     1.475    8.07

Win% monotonicity: 3/9 decile steps non-decreasing

### bk50d_s15_v1.2_roc100 — regime-neutral (pool-relative) score deciles (D1 = lowest, D10 = highest)

Decile      PredP%      N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────────────
D1            46.3    124   +35.38   +43.96    70.2     1.248    6.00
D2            47.9    124   +21.35   +35.06    68.5     1.276    6.06
D3            48.7    124   +38.78   +48.09    73.4     1.437    7.61
D4            49.3    124   +25.61   +53.79    70.2     1.686    7.99
D5            49.8    124   +38.02   +46.78    77.4     1.315    8.41
D6            50.3    124   +37.59   +63.20    77.4     2.007   11.34
D7            50.8    124   +27.65   +38.78    79.0     1.266    8.33
D8            51.3    123   +43.87   +55.08    77.2     1.636    9.30
D9            51.9    123   +32.18   +56.92    74.0     1.564    8.57
D10           53.0    123   +31.46   +49.42    75.6     1.341    8.23
─────────────────────────────────────────────────────────────────────
ALL           49.9   1237   +32.95   +49.10    74.3     1.475    8.07

Win% monotonicity: 5/9 decile steps non-decreasing

```

## Findings (2026-07-16 run — tables above regenerate on re-run)

1. **The raw walk-forward P(success) is anti-calibrated.** Predicted P rises D1→D10
   (59.9%→77.8%) while realized Win% falls (85.5%→61.0%, Win% monotonicity 3/9);
   D9 is the worst bucket outright (Med% −5.9, Sortino 0.30). The score is dominated
   by the *time drift* of the walk-forward pool win rate, not by signal quality:
   trades entered after strong stretches (e.g. scored off 2019–20 outcomes, entered
   in 2021) inherit high P and then meet the 2022 bear, and vice versa. Deciles are
   effectively time buckets, so the score inverts. Do **not** use raw P to rank live
   signals.
2. **Regime-neutral (pool-relative) score removes the inversion but leaves only a
   weak cross-sectional edge.** Subtracting the running pool log-odds flattens the
   gradient to mildly positive (Win% 70.2→75.6 D1→D10, monotonicity 5/9, no clear
   Mean%/Sortino trend). Once all v1.2 filters are applied, each dimension is already
   truncated to its favourable region and the six dimensions are correlated, so
   cohort Win% differences within the filtered pool carry little independent
   information. The strong gradients in the cohort studies come mostly from the
   regions the filters already exclude.
3. **Implication:** the cohort tables are better used for *filter placement* (as in
   the relax-sweep study) than for ranking the surviving signals. If a live ranking
   is still wanted, the regime-neutral score is the safe variant (its top half is
   modestly better than its bottom half), but expect a few points of Win%, not a
   decisive separation.
