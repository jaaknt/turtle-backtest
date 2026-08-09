# Qullamaggie Exit-Strategy Sweep

Run date: 2026-08-09 20:53:40 Tallinn time

Config: `bk50d_s12_v2.0` | 2021-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 44 | time-cap backstop 366d

890 signals entered the simulation (1515 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here come from `turtlex.research.qullamaggie`, whose cooldown chain runs through the warmup window, while `qullamaggie-portfolio-sim.py` starts its chain at the evaluation start. A small divergence is expected; a large one would invalidate every comparison below.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (committed)     285,404  +50.88   -28.01    2.129
this harness                  284,922  +50.84   -27.91    2.168
```

CAGR divergence: 0.04pp (within the 1.0pp tolerance).

Pass bar: CAGR > +50.84%, Sortino > 2.168, MaxDD > -32.91%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                     115,099  +27.83   -26.98   1.032    1.646    356    534  fail
regime 1d (losers only)       151,075  +34.34   -25.74   1.334    1.778    289    601  fail
regime 3d                     116,179  +28.05   -26.85   1.044    1.591    305    585  fail
regime 3d (losers only)       163,270  +36.25   -24.95   1.453    1.856    260    630  fail
regime 5d                     123,058  +29.40   -25.13   1.170    1.643    291    599  fail
regime 5d (losers only)       173,879  +37.83   -21.63   1.749    1.928    250    640  fail
regime 10d                    180,166  +38.73   -24.47   1.583    1.998    244    646  fail
regime 10d (losers only)      197,802  +41.11   -20.66   1.990    2.056    220    670  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          165,471  +36.59   -26.17   1.398    2.251    384    506  fail
arm +15% / trail 20%          182,560  +39.06   -26.48   1.475    2.232    318    572  fail
arm +15% / trail 25%          151,742  +34.44   -25.68   1.341    1.930    282    608  fail
arm +15% / trail 30%          144,136  +33.19   -25.69   1.292    1.828    238    652  fail
arm +25% / trail 15%          185,837  +39.51   -25.28   1.563    2.200    325    565  fail
arm +25% / trail 20%          167,209  +36.85   -29.20   1.262    1.990    285    605  fail
arm +25% / trail 25%          164,509  +36.44   -27.30   1.335    1.914    254    636  fail
arm +25% / trail 30%          151,303  +34.37   -26.82   1.282    1.812    228    662  fail
arm +40% / trail 15%          156,915  +35.27   -26.90   1.311    1.963    259    631  fail
arm +40% / trail 20%          156,865  +35.26   -32.17   1.096    1.879    243    647  fail
arm +40% / trail 25%          204,064  +41.92   -27.02   1.551    2.124    229    661  fail
arm +40% / trail 30%          173,324  +37.75   -33.26   1.135    1.836    215    675  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            139,136  +32.33   -24.48   1.321    1.721    414    476  fail
<+5% after 20 bars            149,181  +34.03   -19.83   1.716    1.892    485    405  fail
<+10% after 20 bars           145,708  +33.45   -20.45   1.635    1.909    541    349  fail
<+0% after 40 bars            123,306  +29.45   -29.01   1.015    1.517    335    555  fail
<+5% after 40 bars            125,944  +29.95   -28.77   1.041    1.559    361    529  fail
<+10% after 40 bars           177,491  +38.35   -28.10   1.365    1.911    377    513  fail
<+0% after 60 bars            135,102  +31.62   -27.91   1.133    1.578    289    601  fail
<+5% after 60 bars            136,521  +31.87   -27.94   1.141    1.552    304    586  fail
<+10% after 60 bars           138,789  +32.27   -27.32   1.181    1.559    324    566  fail
<+0% after 90 bars            199,368  +41.31   -25.92   1.594    1.985    252    638  fail
<+5% after 90 bars            226,831  +44.68   -31.50   1.419    1.977    254    636  fail
<+10% after 90 bars           222,776  +44.21   -32.41   1.364    1.980    264    626  fail
<+0% after 120 bars           203,078  +41.79   -30.48   1.371    1.888    228    662  fail
<+5% after 120 bars           233,982  +45.51   -30.17   1.508    2.020    225    665  fail
<+10% after 120 bars          239,985  +46.18   -34.37   1.343    2.066    240    650  fail
<+0% after 150 bars           194,354  +40.66   -28.80   1.412    1.840    206    684  fail
<+5% after 150 bars           167,478  +36.89   -28.18   1.309    1.767    212    678  fail
<+10% after 150 bars          157,079  +35.30   -31.66   1.115    1.681    219    671  fail
<+0% after 180 bars           223,088  +44.25   -31.44   1.408    1.929    200    690  fail
<+5% after 180 bars           167,043  +36.82   -33.04   1.115    1.708    202    688  fail
<+10% after 180 bars          221,501  +44.06   -31.71   1.389    2.010    207    683  fail
<+0% after 240 bars           250,764  +47.36   -27.31   1.734    2.050    191    699  fail
<+5% after 240 bars           255,504  +47.86   -27.31   1.753    2.052    192    698  fail
<+10% after 240 bars          252,377  +47.53   -27.30   1.741    2.041    191    699  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     57,821  +12.73   -19.39   0.657    1.437    784    106  fail
ema20 x 3d                     75,300  +18.30   -17.02   1.075    1.704    684    206  fail
ema20 x 5d                     96,594  +23.80   -18.73   1.271    1.857    605    285  fail
sma50 x 1d                     81,368  +19.98   -25.01   0.799    1.553    594    296  fail
sma50 x 3d                    100,945  +24.80   -18.77   1.321    1.746    533    357  fail
sma50 x 5d                     98,550  +24.26   -18.81   1.289    1.678    485    405  fail
sma200 x 1d                   175,287  +38.03   -23.46   1.621    1.966    358    532  fail
sma200 x 3d                   205,134  +42.05   -24.46   1.719    2.070    315    575  fail
sma200 x 5d                   129,946  +30.69   -24.29   1.263    1.521    306    584  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              185,638  +39.49   -21.73   1.817    1.937    276    614  fail
entry - 4x ATR14              155,176  +34.99   -27.42   1.276    1.736    243    647  fail
entry - 5x ATR14              152,040  +34.49   -26.02   1.325    1.686    221    669  fail
entry - 6x ATR14              159,822  +35.72   -25.63   1.394    1.668    212    678  fail
entry - 8x ATR14              235,129  +45.64   -27.03   1.688    2.034    200    690  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## Controls

The four exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim` (`stop30`, `trail25`, `sma200x5`, `dead120` — its `EXIT_MODES = ["time"]` never selects them), at that script's own constants.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
stop30 — fixed -30% stop      202,259  +41.69   -31.24   1.334    1.906    209    681  fail
trail25 — 25% from day one     94,710  +23.36   -24.31   0.961    1.538    347    543  fail
sma200 x 5d                   129,946  +30.69   -24.29   1.263    1.521    306    584  fail
dead120 — <+5% after 120 c    156,931  +35.27   -30.07   1.173    1.682    275    615  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `arm +15% / trail 15% + sma200 x 3d` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15% + sma     98,438  +24.23   -23.67   1.023    1.856    541    349  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          284,922  +50.84   -27.91   1.821    2.168    188    702  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     0 regime 10d (losers only)   -9.72    -0.112    +7.25
2. trail — profit-armed trailing stop      12     0 arm +15% / trail 15%      -14.25    +0.083    +1.74
3. dead — dead-money time stop             24     0 <+10% after 120 bars       -4.65    -0.102    -6.46
4. trend — closes below own MA              9     0 sma200 x 3d                -8.78    -0.098    +3.46
5. atr — volatility-normalised stop         5     0 entry - 8x ATR14           -5.20    -0.134    +0.88
```

## Finalists — trade metrics and exit attribution

**No variant cleared the bar.** Showing the best variant of each idea instead, for diagnosis.

```text
variant                       N   Win%    Mean%     Med%     PF  CVaR95%  tSortino  exits by rule
-------------------------------------------------------------------------------------------------
baseline (366d only)        188   72.9   +56.94   +22.31   7.87   -64.18     3.218  time=161
arm +15% / trail 15%        384   70.6   +17.76    +8.19   4.18   -61.79     1.759  time=51, trail=299
sma200 x 3d                 315   47.6   +27.10    -0.72   4.72   -33.11     3.478  time=42, trend=247
<+10% after 120 bars        240   61.7   +42.99    +6.85   5.77   -58.11     3.040  dead=160, time=49
regime 10d (losers only)    220   54.1   +39.40    +5.60   6.10   -50.21     3.251  regime=70, time=125
entry - 8x ATR14            200   66.0   +48.58   +14.56   5.30   -55.98     2.623  stop=41, time=130
```

## Finalists — per-year decomposition

An edge concentrated in one year is regime-contingent, not a general improvement.

```text
variant                        2021     2022     2023     2024     2025     2026
--------------------------------------------------------------------------------
baseline (366d only)          +53.7    +25.3    +27.6    +26.6   +133.2    +31.0
arm +15% / trail 15%          +19.2     -0.6    +25.9    +29.2   +136.3    +21.1
sma200 x 3d                   +50.7    -10.2    +31.2    +71.5    +49.8    +49.9
<+10% after 120 bars          +48.1     -6.0    +30.1    +36.8   +137.3    +36.0
regime 10d (losers only)      +53.7     -2.7    +20.0    +41.9    +86.9    +38.5
entry - 8x ATR14              +53.7    +15.9    +26.0    +26.0   +120.8    +25.5
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
arm +15% / trail 15%              9.2          57.9
sma200 x 3d                      19.0          38.7
<+10% after 120 bars             28.2          37.3
regime 10d (losers only)         16.4          37.8
entry - 8x ATR14                  7.1          14.3
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s12 / 2021-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20   146 |    +15.43    +14.60   -0.83 |    1.118    1.177  +0.059 |   -27.00   -23.37 |  fail
2010-2015    s16   157 |    +15.43    +14.44   -1.00 |    1.079    1.076  -0.002 |   -28.60   -27.25 |  fail
2010-2015    s12   164 |    +12.50    +13.59   +1.08 |    0.881    0.999  +0.119 |   -29.00   -27.47 |  PASS
2016-2020    s20   139 |    +41.94    +28.76  -13.19 |    2.409    1.719  -0.690 |   -21.74   -30.81 |  fail
2016-2020    s16   141 |    +39.92    +38.20   -1.71 |    2.299    2.120  -0.179 |   -24.87   -30.34 |  fail
2016-2020    s12   140 |    +42.66    +37.23   -5.43 |    2.502    2.098  -0.404 |   -21.00   -32.00 |  fail
2021-2026    s20   185 |    +45.83    +37.14   -8.69 |    1.996    1.776  -0.220 |   -31.31   -32.15 |  fail
2021-2026    s16   189 |    +48.87    +39.07   -9.81 |    2.021    1.815  -0.207 |   -26.88   -32.02 |  fail
2021-2026    s12   188 |    +50.84    +44.68   -6.15 |    2.168    1.977  -0.191 |   -27.91   -31.50 |  fail
```

**1 of 9 cells pass**, on the same bar used for the sweep.

`N` is the baseline trade count, which doubles as a read on how capital-constrained each cell is: the rule's second mechanism is recycling capital into signals that would otherwise go unfunded, so it has less to work with where cash was already idle.

## Audit sample — first 10 rule-driven exits of the top finalist

Every field below is checkable against `turtle.daily_bars`: `exit $` is that symbol's split/dividend-adjusted close on `exit date`, and the rule that fired is named.
Rule: arm +15% / trail 15%

```text
symbol     entry date   exit date      entry $    exit $     ret%  calD  rule
-----------------------------------------------------------------------------
SM.US      2021-01-06   2021-01-15        6.91      7.68   +11.04     9  trail
GSL.US     2021-01-06   2021-01-22        8.39      9.08    +8.26    16  trail
FTI.US     2021-01-06   2021-01-25        7.83      7.69    -1.77    19  trail
OII.US     2021-01-06   2021-01-25        9.67      9.72    +0.52    19  trail
HROW.US    2021-02-04   2021-02-11        9.46      9.37    -0.95     7  trail
HCC.US     2021-01-05   2021-02-25       19.96     17.81   -10.79    51  trail
PGNY.US    2021-01-07   2021-02-25       43.80     43.31    -1.12    49  trail
KRYS.US    2021-01-06   2021-03-04       61.37     71.65   +16.75    57  trail
WHD.US     2021-01-06   2021-03-09       28.23     30.77    +9.00    62  trail
AMR.US     2021-01-15   2021-03-15       13.09     12.53    -4.28    59  trail
```

## Limitations

- Single evaluation window; parameters are scored on the same data they were chosen on. The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it.
- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees companies that are large today. This survivorship bias inflates every absolute figure here, baseline included; relative comparisons are unaffected.
- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.
