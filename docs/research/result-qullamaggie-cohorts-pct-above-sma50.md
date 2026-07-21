# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-07-22

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: all bk50d fixed filters applied; pct_vs_sma50 > X threshold removed for cohort view
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)

### bk50d_<X>_v1.3_roc100 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         461    +3.80   +10.14    54.4     0.279    1.74
[10-12)       376    +7.43   +19.64    57.4     0.632    2.92
[12-15)       572   +17.49   +28.62    66.1     0.891    4.28
[15-17)       330   +24.08   +36.97    67.3     1.150    5.38
[17-20)       327   +18.38   +25.83    67.0     0.754    3.76
[20-30)       605   +31.64   +51.46    75.4     1.545    8.90
(>30)         235   +53.40   +64.82    76.2     1.691    9.65
─────────────────────────────────────────────────────────────
ALL          2906   +19.63   +32.84    66.1     0.975    4.58
>12% (s12)   2069   +25.90   +40.30    70.3     1.207    6.04
>15% (s15)   1497   +29.17   +44.77    71.9     1.318    6.80
>17% (s17)   1167   +30.85   +46.97    73.2     1.358    7.26
>20% (s20)    840   +37.21   +55.20    75.6     1.588    9.14

```
