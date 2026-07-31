# Qullamaggie pct_above_sma50 Cohort Analysis

Run date: 2026-08-01 01:26:28 Tallinn time

```text
pct_above_sma50 cohort analysis | Hold: 366d | Period: 2015-01-01 – 2026-06-26
Filters: RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, breakout>50d high, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, tight_range disabled; pct_above_sma50>X threshold removed for cohort view (reference rows shown for X=12%/15%/17%/20%); ungated (see docstring)
(one shared candidate pool — the s12/s15/s17/s20 variants differ only by this threshold)
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py)

### bk50d_<X>_v2.0 (pct_vs_sma50 threshold removed)

Cohort          N     Med%    Mean%    Win%   Sortino      PF
─────────────────────────────────────────────────────────────
(<10)         470    +5.69   +10.97    57.4     0.462    1.85
[10-12)       379    +7.99   +20.36    59.1     1.021    3.02
[12-15)       594   +20.25   +30.20    66.7     1.637    4.55
[15-17)       348   +25.62   +39.93    70.1     2.293    6.26
[17-20)       331   +22.04   +28.51    67.4     1.581    4.37
[20-30)       611   +35.07   +52.82    76.1     3.338    9.52
(>30)         240   +56.61   +67.32    77.1     3.633   10.30
─────────────────────────────────────────────────────────────
ALL          2973   +22.06   +34.50    67.5     1.822    4.96
>12% (s12)   2124   +27.80   +42.23    71.2     2.413    6.60
>15% (s15)   1530   +31.38   +46.90    73.0     2.739    7.54
>17% (s17)   1182   +33.83   +48.96    73.9     2.874    7.95
>20% (s20)    851   +40.34   +56.91    76.4     3.422    9.77

```
