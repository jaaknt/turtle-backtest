# Qullamaggie Exit-Strategy Sweep

Run date: 2026-08-03 23:05:42 Tallinn time

Config: `bk50d_s12_v2.0` | 2021-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 40 | time-cap backstop 366d

902 signals entered the simulation (1472 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here come from `turtlex.research.qullamaggie`, whose cooldown chain runs through the warmup window, while `qullamaggie-portfolio-sim.py` starts its chain at the evaluation start. A small divergence is expected; a large one would invalidate every comparison below.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (committed)     257,159  +48.04   -25.46    2.099
this harness                  269,027  +49.26   -25.14    2.152
```

CAGR divergence: 1.22pp (ABOVE the 1.0pp tolerance).

Pass bar: CAGR > +49.26%, Sortino > 2.152, MaxDD > -30.14%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                     129,698  +30.65   -23.39   1.310    1.796    359    543  fail
regime 1d (losers only)       151,445  +34.40   -28.46   1.208    1.787    297    605  fail
regime 3d                     123,360  +29.46   -24.00   1.227    1.675    306    596  fail
regime 3d (losers only)       176,522  +38.21   -24.88   1.536    1.941    266    636  fail
regime 5d                     130,733  +30.83   -24.00   1.285    1.725    293    609  fail
regime 5d (losers only)       165,878  +36.65   -25.24   1.452    1.871    262    640  fail
regime 10d                    176,459  +38.20   -25.28   1.511    1.980    244    658  fail
regime 10d (losers only)      174,459  +37.91   -21.56   1.759    1.906    225    677  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          177,135  +38.30   -26.47   1.447    2.370    382    520  fail
arm +15% / trail 20%          172,531  +37.63   -24.48   1.537    2.184    312    590  fail
arm +15% / trail 25%          184,555  +39.34   -28.32   1.389    2.163    273    629  fail
arm +15% / trail 30%          138,109  +32.15   -26.07   1.233    1.761    243    659  fail
arm +25% / trail 15%          142,950  +32.99   -26.05   1.266    1.926    318    584  fail
arm +25% / trail 20%          161,884  +36.04   -24.72   1.458    2.007    273    629  fail
arm +25% / trail 25%          174,578  +37.93   -29.08   1.304    1.999    247    655  fail
arm +25% / trail 30%          123,822  +29.54   -28.18   1.048    1.624    223    679  fail
arm +40% / trail 15%          165,482  +36.59   -27.42   1.334    2.063    261    641  fail
arm +40% / trail 20%          170,472  +37.33   -26.66   1.400    1.994    239    663  fail
arm +40% / trail 25%          159,430  +35.66   -30.66   1.163    1.849    228    674  fail
arm +40% / trail 30%          155,121  +34.99   -33.53   1.044    1.793    212    690  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            147,707  +33.78   -27.34   1.236    1.720    422    480  fail
<+5% after 20 bars            174,734  +37.95   -24.69   1.537    2.035    495    407  fail
<+10% after 20 bars           168,539  +37.05   -21.96   1.687    1.946    545    357  fail
<+0% after 40 bars            222,022  +44.12   -22.85   1.930    2.147    319    583  fail
<+5% after 40 bars            206,777  +42.26   -23.62   1.789    2.123    355    547  fail
<+10% after 40 bars           227,409  +44.75   -23.76   1.884    2.223    385    517  fail
<+0% after 60 bars            158,883  +35.58   -26.99   1.318    1.765    283    619  fail
<+5% after 60 bars            160,625  +35.85   -25.03   1.432    1.819    302    600  fail
<+10% after 60 bars           137,641  +32.07   -25.16   1.275    1.597    332    570  fail
<+0% after 90 bars            231,823  +45.26   -29.86   1.516    2.138    250    652  fail
<+5% after 90 bars            243,190  +46.54   -28.37   1.640    2.129    259    643  fail
<+10% after 90 bars           246,398  +46.89   -24.36   1.925    2.213    265    637  fail
<+0% after 120 bars           237,679  +45.92   -28.94   1.587    2.099    232    670  fail
<+5% after 120 bars           243,483  +46.57   -30.59   1.522    2.085    230    672  fail
<+10% after 120 bars          208,034  +42.42   -34.28   1.238    1.987    243    659  fail
<+0% after 150 bars           207,876  +42.40   -30.12   1.408    1.975    207    695  fail
<+5% after 150 bars           209,970  +42.66   -28.22   1.511    1.994    210    692  fail
<+10% after 150 bars          175,545  +38.07   -29.85   1.275    1.844    215    687  fail
<+0% after 180 bars           201,924  +41.64   -33.77   1.233    1.905    205    697  fail
<+5% after 180 bars           162,939  +36.20   -32.65   1.109    1.786    205    697  fail
<+10% after 180 bars          158,656  +35.54   -34.01   1.045    1.597    206    696  fail
<+0% after 240 bars           238,544  +46.02   -25.44   1.809    2.070    193    709  fail
<+5% after 240 bars           278,346  +50.19   -26.05   1.927    2.216    193    709  PASS
<+10% after 240 bars          285,090  +50.85   -25.84   1.968    2.234    193    709  PASS
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     56,940  +12.41   -21.69   0.572    1.394    808     94  fail
ema20 x 3d                     68,177  +16.17   -17.91   0.903    1.502    702    200  fail
ema20 x 5d                     89,304  +22.04   -20.74   1.062    1.687    615    287  fail
sma50 x 1d                     85,457  +21.06   -22.45   0.938    1.587    611    291  fail
sma50 x 3d                    107,020  +26.14   -17.47   1.496    1.790    538    364  fail
sma50 x 5d                    101,378  +24.90   -21.13   1.179    1.677    494    408  fail
sma200 x 1d                   110,782  +26.94   -25.17   1.070    1.524    389    513  fail
sma200 x 3d                   135,534  +31.70   -26.22   1.209    1.706    334    568  fail
sma200 x 5d                   106,729  +26.08   -28.79   0.906    1.400    331    571  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              174,712  +37.95   -21.45   1.769    1.909    280    622  fail
entry - 4x ATR14              148,560  +33.92   -22.71   1.494    1.742    249    653  fail
entry - 5x ATR14              154,745  +34.93   -29.11   1.200    1.685    230    672  fail
entry - 6x ATR14              137,762  +32.09   -25.93   1.238    1.598    212    690  fail
entry - 8x ATR14              231,024  +45.17   -28.50   1.585    2.048    203    699  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## Controls

The four exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim` (`stop30`, `trail25`, `sma200x5`, `dead120` — its `EXIT_MODES = ["time"]` never selects them), at that script's own constants.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
stop30 — fixed -30% stop      162,016  +36.06   -24.93   1.446    1.675    215    687  fail
trail25 — 25% from day one    131,799  +31.03   -27.69   1.121    1.951    332    570  fail
sma200 x 5d                   106,729  +26.08   -28.79   0.906    1.400    331    571  fail
dead120 — <+5% after 120 c    187,035  +39.68   -29.30   1.354    1.899    270    632  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `arm +15% / trail 15% + <+10% after 240 bars` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15% + <+1    151,393  +34.39   -27.29   1.260    2.140    382    520  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          269,027  +49.26   -25.14   1.959    2.152    194    708  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     0 regime 10d                -11.06    -0.172    -0.14
2. trail — profit-armed trailing stop      12     0 arm +15% / trail 15%      -10.97    +0.218    -1.32
3. dead — dead-money time stop             24     2 <+10% after 240 bars       +1.59    +0.082    -0.69
4. trend — closes below own MA              9     0 sma50 x 3d                -23.12    -0.362    +7.67
5. atr — volatility-normalised stop         5     0 entry - 8x ATR14           -4.09    -0.104    -3.36
```

## Finalists — trade metrics and exit attribution

2 variant(s) cleared the bar, ordered by Sortino.

```text
variant                       N   Win%    Mean%     Med%     PF  CVaR95%  tSortino  exits by rule
-------------------------------------------------------------------------------------------------
baseline (366d only)        194   67.5   +50.51   +13.83   6.80   -62.31     2.916  time=162
<+10% after 240 bars        193   63.2   +51.84    +9.80   6.79   -63.98     2.973  dead=80, time=82
<+5% after 240 bars         193   62.7   +51.28    +9.77   7.02   -62.03     3.065  dead=74, time=87
```

## Finalists — per-year decomposition

An edge concentrated in one year is regime-contingent, not a general improvement.

```text
variant                        2021     2022     2023     2024     2025     2026
--------------------------------------------------------------------------------
baseline (366d only)          +54.5    +16.7    +40.8    +45.0   +112.0    +14.9
<+10% after 240 bars          +52.6    +14.8    +40.7    +56.0   +110.1    +17.6
<+5% after 240 bars           +52.5    +14.5    +43.5    +56.0   +114.4    +10.6
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
<+10% after 240 bars             67.0          75.1
<+5% after 240 bars              59.7          69.4
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s12 / 2021-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20   137 |    +14.40    +12.38   -2.02 |    1.028    1.100  +0.072 |   -27.10   -21.68 |  fail
2010-2015    s16   148 |    +12.23    +13.03   +0.80 |    0.884    1.009  +0.124 |   -26.93   -24.91 |  PASS
2010-2015    s12   166 |    +11.89    +14.55   +2.65 |    0.854    1.060  +0.206 |   -28.28   -25.93 |  PASS
2016-2020    s20   138 |    +34.57    +29.17   -5.40 |    2.065    1.738  -0.327 |   -25.97   -32.57 |  fail
2016-2020    s16   140 |    +38.05    +32.19   -5.86 |    2.248    1.905  -0.343 |   -23.43   -28.91 |  fail
2016-2020    s12   149 |    +33.06    +32.20   -0.86 |    1.895    1.887  -0.008 |   -27.50   -26.33 |  fail
2021-2026    s20   182 |    +48.46    +41.80   -6.66 |    2.052    1.853  -0.199 |   -30.52   -35.08 |  fail
2021-2026    s16   190 |    +45.86    +42.03   -3.82 |    1.926    1.890  -0.036 |   -28.02   -28.96 |  fail
2021-2026    s12   194 |    +49.26    +46.54   -2.73 |    2.152    2.129  -0.023 |   -25.14   -28.37 |  fail
```

**2 of 9 cells pass**, on the same bar used for the sweep.

`N` is the baseline trade count, which doubles as a read on how capital-constrained each cell is: the rule's second mechanism is recycling capital into signals that would otherwise go unfunded, so it has less to work with where cash was already idle.

## Audit sample — first 10 rule-driven exits of the top finalist

Every field below is checkable against `turtle.daily_bars`: `exit $` is that symbol's split/dividend-adjusted close on `exit date`, and the rule that fired is named.
Rule: <+10% after 240 bars

```text
symbol     entry date   exit date      entry $    exit $     ret%  calD  rule
-----------------------------------------------------------------------------
HBM.US     2021-01-05   2021-12-16        7.26      6.57    -9.58   345  dead
HCC.US     2021-01-05   2021-12-16       19.96     20.75    +3.97   345  dead
CRS.US     2021-01-06   2021-12-17       29.75     29.02    -2.44   345  dead
HAL.US     2021-01-06   2021-12-17       18.95     20.19    +6.49   345  dead
LBRT.US    2021-01-06   2021-12-17       11.35      8.87   -21.81   345  dead
PARR.US    2021-01-06   2021-12-17       14.50     13.80    -4.83   345  dead
WT.US      2021-01-06   2021-12-17        5.33      5.61    +5.28   345  dead
AIR.US     2021-01-07   2021-12-20       38.82     35.41    -8.78   347  dead
AROC.US    2021-01-07   2021-12-20        7.34      5.88   -19.91   347  dead
MOD.US     2021-01-07   2021-12-20       13.75      9.51   -30.84   347  dead
```

## Limitations

- Single evaluation window; parameters are scored on the same data they were chosen on. The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it.
- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees companies that are large today. This survivorship bias inflates every absolute figure here, baseline included; relative comparisons are unaffected.
- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.
