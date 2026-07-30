# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-07-30

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, breakout>50d high, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, tight_range disabled; pct_above_sma50>X threshold removed for cohort view (reference rows shown for X=12%/15%/17%/20%)
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)

### bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         460    +5.54   +10.34    57.0     0.283    1.79
[10-12)       371    +7.99   +19.44    59.3     0.620    2.93
[12-15)       576   +19.60   +29.43    66.1     0.920    4.41
[15-17)       344   +25.62   +39.96    70.1     1.249    6.20
[17-20)       329   +22.16   +28.70    67.8     0.901    4.38
[20-30)       595   +34.11   +49.74    75.8     1.534    8.92
(>30)         234   +56.61   +66.40    76.9     1.704   10.05
─────────────────────────────────────────────────────────────
ALL          2909   +21.82   +33.43    67.3     1.002    4.79
>12% (s12)   2078   +27.67   +41.03    71.0     1.253    6.37
>15% (s15)   1502   +31.19   +45.49    72.9     1.373    7.27
>17% (s17)   1158   +33.21   +47.13    73.7     1.407    7.62
>20% (s20)    829   +39.23   +54.44    76.1     1.586    9.27

```
