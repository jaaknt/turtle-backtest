# Qullamaggie Exit-Strategy Sweep

Run date: 2026-08-01 02:16:18 Tallinn time

Config: `bk50d_s20_v2.0` | 2020-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 40 | time-cap backstop 366d

683 signals entered the simulation (213 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here come from `turtlex.research.qullamaggie`, whose cooldown chain runs through the warmup window, while `qullamaggie-portfolio-sim.py` starts its chain at the evaluation start. A small divergence is expected; a large one would invalidate every comparison below.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (committed)     264,355  +39.87   -21.76    2.082
this harness                  221,734  +36.13   -25.00    1.985
```

CAGR divergence: 3.74pp (ABOVE the 1.0pp tolerance).

Pass bar: CAGR > +36.13%, Sortino > 1.985, MaxDD > -30.00%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                      77,336  +15.72   -31.78   0.495    1.200    298    385  fail
regime 1d (losers only)       155,867  +28.93   -22.76   1.271    1.808    250    433  fail
regime 3d                     112,272  +22.57   -34.05   0.663    1.523    230    453  fail
regime 3d (losers only)       187,942  +32.70   -23.81   1.374    1.989    212    471  fail
regime 5d                     110,113  +22.20   -32.54   0.682    1.492    230    453  fail
regime 5d (losers only)       187,488  +32.65   -23.63   1.382    1.937    211    472  fail
regime 10d                    195,701  +33.53   -28.32   1.184    1.976    209    474  fail
regime 10d (losers only)      236,197  +37.46   -22.31   1.679    2.108    193    490  PASS
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          167,437  +30.36   -22.70   1.338    2.092    337    346  fail
arm +15% / trail 20%          184,898  +32.37   -24.29   1.333    2.093    299    384  fail
arm +15% / trail 25%          242,894  +38.06   -23.76   1.602    2.292    259    424  PASS
arm +15% / trail 30%          262,838  +39.75   -24.38   1.631    2.292    224    459  PASS
arm +25% / trail 15%          140,918  +26.94   -22.57   1.193    1.771    291    392  fail
arm +25% / trail 20%          181,580  +32.00   -24.70   1.296    1.993    258    425  fail
arm +25% / trail 25%          234,493  +37.31   -22.77   1.638    2.206    234    449  PASS
arm +25% / trail 30%          253,953  +39.01   -24.70   1.580    2.238    210    473  PASS
arm +40% / trail 15%          205,628  +34.56   -24.95   1.385    2.096    254    429  fail
arm +40% / trail 20%          220,386  +36.00   -24.34   1.479    2.144    234    449  fail
arm +40% / trail 25%          246,061  +38.33   -23.91   1.603    2.256    217    466  PASS
arm +40% / trail 30%          269,004  +40.25   -25.12   1.602    2.268    196    487  PASS
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            115,494  +23.11   -22.90   1.009    1.543    354    329  fail
<+5% after 20 bars            104,573  +21.23   -21.66   0.980    1.494    383    300  fail
<+10% after 20 bars           100,270  +20.45   -23.21   0.881    1.459    414    269  fail
<+0% after 40 bars            181,197  +31.96   -20.29   1.575    1.871    289    394  fail
<+5% after 40 bars            198,291  +33.81   -20.29   1.666    2.053    313    370  fail
<+10% after 40 bars           186,243  +32.52   -20.29   1.603    1.998    336    347  fail
<+0% after 60 bars            189,786  +32.90   -22.35   1.472    1.942    257    426  fail
<+5% after 60 bars            179,783  +31.80   -24.54   1.296    1.926    271    412  fail
<+10% after 60 bars           196,117  +33.58   -23.12   1.452    2.003    276    407  fail
<+0% after 90 bars            275,843  +40.79   -25.74   1.585    2.169    232    451  PASS
<+5% after 90 bars            256,443  +39.22   -26.59   1.475    2.112    238    445  PASS
<+10% after 90 bars           250,291  +38.70   -27.02   1.432    2.123    244    439  PASS
<+0% after 120 bars           200,747  +34.06   -27.49   1.239    1.878    207    476  fail
<+5% after 120 bars           206,112  +34.61   -27.21   1.272    1.880    217    466  fail
<+10% after 120 bars          203,826  +34.38   -25.54   1.346    1.898    220    463  fail
<+0% after 150 bars           226,731  +36.60   -28.04   1.305    1.966    199    484  fail
<+5% after 150 bars           207,959  +34.79   -27.28   1.275    1.942    200    483  fail
<+10% after 150 bars          222,695  +36.22   -31.98   1.133    1.928    205    478  fail
<+0% after 180 bars           177,092  +31.49   -25.92   1.215    1.816    187    496  fail
<+5% after 180 bars           205,963  +34.59   -25.32   1.366    1.978    189    494  fail
<+10% after 180 bars          235,956  +37.44   -27.95   1.340    1.974    189    494  fail
<+0% after 240 bars           207,134  +34.71   -25.14   1.381    1.939    172    511  fail
<+5% after 240 bars           201,753  +34.16   -25.34   1.348    1.911    173    510  fail
<+10% after 240 bars          210,623  +35.06   -25.20   1.391    1.954    174    509  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     45,289   +6.56   -18.84   0.348    0.872    498    185  fail
ema20 x 3d                     65,739  +12.86   -18.67   0.689    1.415    465    218  fail
ema20 x 5d                     94,802  +19.41   -18.67   1.040    1.790    429    254  fail
sma50 x 1d                     78,083  +15.89   -19.60   0.811    1.411    418    265  fail
sma50 x 3d                     92,958  +19.05   -20.03   0.951    1.560    384    299  fail
sma50 x 5d                    102,280  +20.82   -22.00   0.946    1.618    366    317  fail
sma200 x 1d                   175,683  +31.33   -22.02   1.423    1.893    363    320  fail
sma200 x 3d                   177,414  +31.53   -20.00   1.576    1.894    318    365  fail
sma200 x 5d                   163,450  +29.88   -21.44   1.393    1.795    314    369  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              140,413  +26.87   -20.62   1.303    1.677    246    437  fail
entry - 4x ATR14              220,149  +35.98   -21.60   1.666    2.039    213    470  fail
entry - 5x ATR14              176,697  +31.45   -21.26   1.479    1.853    194    489  fail
entry - 6x ATR14              177,840  +31.58   -22.40   1.409    1.815    184    499  fail
entry - 8x ATR14              199,578  +33.94   -22.84   1.486    1.946    172    511  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## Controls

The three exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim`.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
fixed -30% stop               189,574  +32.88   -20.18   1.629    1.933    188    495  fail
25% trail from day one        194,632  +33.42   -20.20   1.655    2.212    302    381  fail
sma200 x 3d                   177,414  +31.53   -20.00   1.576    1.894    318    365  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `arm +15% / trail 25% + <+0% after 90 bars` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 25% + <+0    197,583  +33.73   -21.28   1.585    2.156    299    384  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          221,734  +36.13   -25.00   1.446    1.985    167    516  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     1 regime 10d (losers only)   +1.33    +0.123    +2.69
2. trail — profit-armed trailing stop      12     6 arm +15% / trail 25%       +1.93    +0.308    +1.23
3. dead — dead-money time stop             24     3 <+0% after 90 bars         +4.66    +0.184    -0.74
4. trend — closes below own MA              9     0 sma200 x 3d                -4.60    -0.090    +4.99
5. atr — volatility-normalised stop         5     0 entry - 4x ATR14           -0.15    +0.054    +3.40
```

## Finalists — trade metrics and exit attribution

10 variant(s) cleared the bar, ordered by Sortino.

```text
variant                       N   Win%    Mean%     Med%     PF  CVaR95%  tSortino  exits by rule
-------------------------------------------------------------------------------------------------
baseline (366d only)        167   68.3   +58.06   +29.80   6.37   -71.64     2.636  time=156
arm +15% / trail 25%        259   62.2   +35.59    +8.99   6.01   -61.33     2.866  time=74, trail=153
arm +15% / trail 30%        224   62.5   +46.56   +15.13   6.74   -61.82     3.250  time=91, trail=108
arm +40% / trail 30%        196   73.5   +53.19   +25.40   7.28   -70.34     2.889  time=119, trail=52
arm +40% / trail 25%        217   77.4   +44.12   +26.11   6.71   -68.47     2.659  time=106, trail=80
arm +25% / trail 30%        210   65.7   +48.67   +19.08   7.13   -64.16     3.137  time=104, trail=81
arm +25% / trail 25%        234   67.1   +40.26   +15.00   6.57   -63.42     2.814  time=92, trail=109
<+0% after 90 bars          232   36.6   +46.69    -1.31   6.56   -51.41     3.847  dead=145, time=66
<+10% after 90 bars         244   59.4   +42.03    +4.66   5.90   -51.13     3.439  dead=169, time=54
<+5% after 90 bars          238   55.0   +43.85    +2.89   5.96   -51.79     3.499  dead=160, time=59
regime 10d (losers only)    193   53.4   +52.75   +11.60   6.16   -60.27     3.208  regime=63, time=113
```

## Finalists — per-year decomposition

An edge concentrated in one year is regime-contingent, not a general improvement.

```text
variant                        2020     2021     2022     2023     2024     2025     2026
-----------------------------------------------------------------------------------------
baseline (366d only)          +77.7    +35.4    -15.6    +31.4    +21.1    +54.8    +47.8
arm +15% / trail 25%          +60.3    +43.3    -19.1    +27.1    +44.6    +78.3    +33.0
arm +15% / trail 30%          +69.2    +45.3    -19.6    +26.7    +44.2    +61.7    +50.0
arm +40% / trail 30%          +81.1    +39.5    -16.6    +28.3    +40.5    +53.6    +53.7
arm +40% / trail 25%          +74.7    +39.3    -15.4    +27.5    +39.8    +65.2    +35.2
arm +25% / trail 30%          +68.4    +42.2    -18.3    +28.4    +37.3    +68.6    +45.7
arm +25% / trail 25%          +59.6    +46.5    -17.5    +20.0    +40.3    +73.5    +38.7
<+0% after 90 bars            +76.0    +44.7    -10.6    +24.9    +27.9    +73.5    +45.8
<+10% after 90 bars           +71.1    +49.0    -10.6    +12.8    +24.1    +67.8    +55.8
<+5% after 90 bars            +75.3    +43.9    -11.1    +16.7    +30.4    +72.1    +45.6
regime 10d (losers only)      +43.7    +36.9    -12.4    +36.6    +42.6    +57.3    +49.0
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
arm +15% / trail 25%             61.0          84.4
arm +15% / trail 30%             77.4          88.9
arm +40% / trail 30%             82.5          90.5
arm +40% / trail 25%             69.5          89.0
arm +25% / trail 30%             72.3          86.2
arm +25% / trail 25%             60.5          81.8
<+0% after 90 bars               83.4          79.2
<+10% after 90 bars              68.7          71.4
<+5% after 90 bars               72.5          69.5
regime 10d (losers only)         58.0          65.5
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s20 / 2020-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20    71 |     +6.45     +3.98   -2.47 |    0.829    0.678  -0.151 |   -14.97   -13.38 |  fail
2010-2015    s15    96 |     +7.21     +3.91   -3.30 |    0.766    0.571  -0.195 |   -21.22   -16.17 |  fail
2010-2015    s12   107 |     +5.28     +3.12   -2.16 |    0.553    0.434  -0.119 |   -24.43   -21.79 |  fail
2016-2020    s20   112 |    +27.81    +25.36   -2.45 |    1.894    1.843  -0.051 |   -25.98   -19.31 |  fail
2016-2020    s15   124 |    +33.15    +29.06   -4.08 |    2.060    2.000  -0.060 |   -30.35   -20.90 |  fail
2016-2020    s12   134 |    +30.01    +26.16   -3.85 |    1.828    1.809  -0.020 |   -33.74   -25.19 |  fail
2021-2026    s20   151 |    +36.17    +36.66   +0.50 |    1.857    1.881  +0.024 |   -22.91   -26.59 |  PASS
2021-2026    s15   161 |    +48.97    +37.16  -11.81 |    2.271    1.945  -0.326 |   -21.36   -24.78 |  fail
2021-2026    s12   173 |    +50.03    +40.44   -9.59 |    2.231    2.021  -0.210 |   -26.01   -28.57 |  fail
```

**1 of 9 cells pass**, on the same bar used for the sweep.

`N` is the baseline trade count, which doubles as a read on how capital-constrained each cell is: the rule's second mechanism is recycling capital into signals that would otherwise go unfunded, so it has less to work with where cash was already idle.

## Audit sample — first 10 rule-driven exits of the top finalist

Every field below is checkable against `turtle.daily_bars`: `exit $` is that symbol's split/dividend-adjusted close on `exit date`, and the rule that fired is named.
Rule: arm +15% / trail 25%

```text
symbol     entry date   exit date      entry $    exit $     ret%  calD  rule
-----------------------------------------------------------------------------
PCG.US     2020-01-16   2020-03-09       12.36     12.40    +0.32    53  trail
CYTK.US    2020-01-31   2020-03-11       12.79     12.03    -5.94    40  trail
OCUL.US    2020-02-13   2020-03-11        5.52      5.35    -3.08    27  trail
CPRI.US    2020-05-28   2020-06-11       17.99     16.65    -7.45    14  trail
ADNT.US    2020-05-28   2020-06-24       18.47     15.76   -14.67    27  trail
BHF.US     2020-05-28   2020-06-24       32.26     28.27   -12.37    27  trail
AER.US     2020-05-28   2020-06-26       33.04     28.13   -14.85    29  trail
AIG.US     2020-05-28   2020-07-07       27.35     25.21    -7.82    40  trail
AL.US      2020-05-28   2020-07-07       28.32     25.04   -11.57    40  trail
CFG.US     2020-05-28   2020-07-09       20.20     17.59   -12.95    42  trail
```

## Limitations

- Single evaluation window; parameters are scored on the same data they were chosen on. The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it.
- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees companies that are large today. This survivorship bias inflates every absolute figure here, baseline included; relative comparisons are unaffected.
- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.
