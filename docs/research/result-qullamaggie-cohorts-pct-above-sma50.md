# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-07-20

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: all bk50d fixed filters applied; pct_vs_sma50 > X threshold removed for cohort view
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)

### bk50d_<X>_v1.3_roc100 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         506    +3.00    +9.89    53.8     0.278    1.73
[10-12)       416    +7.46   +18.76    58.2     0.595    2.82
[12-15)       657   +17.63   +29.03    66.1     0.895    4.29
[15-17)       383   +21.69   +34.22    65.5     1.021    4.63
[17-20)       405   +16.77   +22.41    64.2     0.674    3.30
[20-30)       729   +30.85   +50.60    73.4     1.493    8.00
(>30)         308   +48.30   +66.06    78.6     1.720   10.63
─────────────────────────────────────────────────────────────
ALL          3404   +19.07   +32.70    65.7     0.968    4.50
>12% (s12)   2482   +24.81   +39.68    69.4     1.177    5.75
>15% (s15)   1825   +27.45   +43.52    70.6     1.272    6.32
>17% (s17)   1442   +29.29   +45.98    71.9     1.335    6.86
>20% (s20)   1037   +34.86   +55.19    74.9     1.573    8.75

```
