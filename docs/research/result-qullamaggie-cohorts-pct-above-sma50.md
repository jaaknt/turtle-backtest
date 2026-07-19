# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-07-19

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: all bk50d fixed filters applied; pct_vs_sma50 > X threshold removed for cohort view
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)

### bk50d_<X>_v1.2_roc100 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         460    +3.73   +10.14    54.3     0.279    1.74
[10-12)       373    +7.15   +19.19    57.1     0.618    2.86
[12-15)       569   +17.63   +28.81    66.3     0.898    4.33
[15-17)       328   +24.08   +36.85    67.4     1.141    5.35
[17-20)       326   +18.73   +25.93    67.2     0.754    3.77
[20-30)       602   +31.58   +50.08    75.2     1.503    8.65
(>30)         233   +53.40   +64.74    76.4     1.678    9.66
─────────────────────────────────────────────────────────────
ALL          2891   +19.62   +32.51    66.1     0.963    4.54
>12% (s12)   2058   +25.84   +39.92    70.4     1.193    6.00
>15% (s15)   1489   +29.14   +44.17    71.9     1.296    6.71
>17% (s17)   1161   +30.74   +46.24    73.2     1.334    7.14
>20% (s20)    835   +37.14   +54.17    75.6     1.556    8.96

```
