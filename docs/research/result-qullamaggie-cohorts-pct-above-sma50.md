# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-07-31 11:02:10 Tallinn time

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, breakout>50d high, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, tight_range disabled; pct_above_sma50>X threshold removed for cohort view (reference rows shown for X=12%/15%/17%/20%); ungated (see docstring)
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)

### bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         470    +5.69   +10.97    57.4     0.301    1.85
[10-12)       379    +7.99   +20.36    59.1     0.653    3.02
[12-15)       594   +20.25   +30.20    66.7     0.945    4.55
[15-17)       348   +25.62   +39.93    70.1     1.254    6.26
[17-20)       331   +22.04   +28.51    67.4     0.903    4.37
[20-30)       611   +35.07   +52.82    76.1     1.631    9.52
(>30)         240   +56.61   +67.32    77.1     1.739   10.30
─────────────────────────────────────────────────────────────
ALL          2973   +22.06   +34.50    67.5     1.038    4.96
>12% (s12)   2124   +27.80   +42.23    71.2     1.294    6.60
>15% (s15)   1530   +31.38   +46.90    73.0     1.423    7.54
>17% (s17)   1182   +33.83   +48.96    73.9     1.469    7.95
>20% (s20)    851   +40.34   +56.91    76.4     1.663    9.77

```
