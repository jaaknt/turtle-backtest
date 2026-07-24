# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-07-24

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, breakout>50d high, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, tight_range disabled; pct_above_sma50>X threshold removed for cohort view (reference rows shown for X=12%/15%/17%/20%)
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)

### bk50d_<X>_v1.3_roc100 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         462    +3.73   +10.08    54.3     0.277    1.74
[10-12)       378    +7.28   +19.46    57.1     0.630    2.90
[12-15)       574   +17.27   +28.52    66.0     0.890    4.28
[15-17)       332   +24.08   +36.86    67.5     1.147    5.40
[17-20)       327   +18.38   +25.83    67.0     0.754    3.76
[20-30)       605   +31.64   +51.46    75.4     1.545    8.90
(>30)         236   +54.10   +64.83    76.3     1.691    9.69
─────────────────────────────────────────────────────────────
ALL          2914   +19.60   +32.77    66.1     0.974    4.57
>12% (s12)   2074   +25.78   +40.25    70.3     1.206    6.05
>15% (s15)   1500   +29.15   +44.74    71.9     1.317    6.81
>17% (s17)   1168   +31.01   +46.99    73.2     1.359    7.26
>20% (s20)    841   +37.24   +55.21    75.6     1.588    9.15

```
