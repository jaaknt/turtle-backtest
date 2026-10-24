# Qullamaggie Exit-Strategy Sweep

Run date: 2026-10-24 18:30:42 Tallinn time

Config: `bk50d_s12_v2.0` | 2021-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 44 | time-cap backstop 366d

829 signals entered the simulation (1478 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here come from `turtlex.research.qullamaggie`, whose cooldown chain runs through the warmup window, while `qullamaggie-portfolio-sim.py` starts its chain at the evaluation start. A small divergence is expected; a large one would invalidate every comparison below.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (committed)     285,404  +50.88   -28.01    2.129
this harness                  347,392  +56.39   -29.98    2.320
```

CAGR divergence: 5.51pp (ABOVE the 1.0pp tolerance).

Pass bar: CAGR > +56.39%, Sortino > 2.320, MaxDD > -34.98%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                     111,084  +27.00   -27.91   0.967    1.608    352    477  fail
regime 1d (losers only)       150,442  +34.23   -25.78   1.328    1.759    287    542  fail
regime 3d                     132,067  +31.08   -27.13   1.145    1.732    301    528  fail
regime 3d (losers only)       144,416  +33.23   -25.27   1.315    1.735    252    577  fail
regime 5d                     139,554  +32.40   -25.48   1.272    1.777    288    541  fail
regime 5d (losers only)       161,332  +35.96   -23.13   1.554    1.827    246    583  fail
regime 10d                    208,182  +42.44   -22.87   1.855    2.137    244    585  fail
regime 10d (losers only)      190,552  +40.15   -20.57   1.952    2.007    216    613  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          183,440  +39.18   -24.68   1.587    2.387    372    457  fail
arm +15% / trail 20%          185,563  +39.48   -27.98   1.411    2.264    315    514  fail
arm +15% / trail 25%          163,870  +36.34   -28.16   1.291    2.022    272    557  fail
arm +15% / trail 30%          167,337  +36.87   -25.22   1.462    1.957    236    593  fail
arm +25% / trail 15%          154,789  +34.93   -23.50   1.487    2.051    314    515  fail
arm +25% / trail 20%          192,211  +40.37   -27.71   1.457    2.184    279    550  fail
arm +25% / trail 25%          186,334  +39.58   -25.88   1.530    2.083    252    577  fail
arm +25% / trail 30%          165,274  +36.56   -25.54   1.431    1.819    222    607  fail
arm +40% / trail 15%          168,450  +37.03   -20.09   1.843    2.048    259    570  fail
arm +40% / trail 20%          170,447  +37.33   -23.38   1.597    2.015    239    590  fail
arm +40% / trail 25%          194,664  +40.70   -26.37   1.544    2.072    226    603  fail
arm +40% / trail 30%          215,247  +43.31   -24.68   1.755    2.136    212    617  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            132,119  +31.09   -24.74   1.257    1.607    403    426  fail
<+5% after 20 bars            132,802  +31.21   -20.43   1.528    1.774    471    358  fail
<+10% after 20 bars           149,920  +34.15   -20.03   1.705    1.939    517    312  fail
<+0% after 40 bars            135,797  +31.75   -29.68   1.070    1.515    320    509  fail
<+5% after 40 bars            165,983  +36.66   -29.85   1.228    1.760    346    483  fail
<+10% after 40 bars           177,602  +38.36   -27.20   1.411    1.824    373    456  fail
<+0% after 60 bars            134,541  +31.52   -30.67   1.028    1.566    285    544  fail
<+5% after 60 bars            131,104  +30.90   -31.52   0.980    1.513    304    525  fail
<+10% after 60 bars           171,807  +37.53   -28.76   1.305    1.743    312    517  fail
<+0% after 90 bars            199,337  +41.31   -32.21   1.283    1.939    246    583  fail
<+5% after 90 bars            222,745  +44.20   -34.08   1.297    2.005    251    578  fail
<+10% after 90 bars           268,206  +49.18   -32.08   1.533    2.187    259    570  fail
<+0% after 120 bars           223,115  +44.25   -30.98   1.428    2.043    224    605  fail
<+5% after 120 bars           229,554  +45.00   -30.41   1.480    2.094    227    602  fail
<+10% after 120 bars          193,048  +40.49   -33.61   1.205    1.907    237    592  fail
<+0% after 150 bars           138,838  +32.28   -30.52   1.058    1.538    203    626  fail
<+5% after 150 bars           191,616  +40.30   -32.43   1.242    1.800    210    619  fail
<+10% after 150 bars          142,539  +32.92   -29.85   1.103    1.596    221    608  fail
<+0% after 180 bars           213,386  +43.08   -30.77   1.400    1.871    198    631  fail
<+5% after 180 bars           206,760  +42.26   -32.77   1.290    1.842    199    630  fail
<+10% after 180 bars          234,503  +45.57   -30.98   1.471    2.043    201    628  fail
<+0% after 240 bars           270,385  +49.40   -26.18   1.887    2.144    188    641  fail
<+5% after 240 bars           265,237  +48.88   -26.72   1.829    2.111    188    641  fail
<+10% after 240 bars          274,538  +49.82   -26.21   1.900    2.135    189    640  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     52,683  +10.83   -20.96   0.517    1.278    735     94  fail
ema20 x 3d                     73,864  +17.88   -18.21   0.982    1.699    651    178  fail
ema20 x 5d                    112,235  +27.24   -18.38   1.482    2.064    583    246  fail
sma50 x 1d                     73,408  +17.75   -24.64   0.720    1.423    580    249  fail
sma50 x 3d                     85,838  +21.16   -18.80   1.126    1.559    523    306  fail
sma50 x 5d                     93,252  +23.01   -17.56   1.310    1.619    477    352  fail
sma200 x 1d                   188,506  +39.88   -23.73   1.681    2.048    338    491  fail
sma200 x 3d                   171,577  +37.49   -23.27   1.611    1.904    319    510  fail
sma200 x 5d                   117,326  +28.28   -27.10   1.043    1.390    297    532  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              179,893  +38.69   -21.48   1.801    1.918    280    549  fail
entry - 4x ATR14              161,933  +36.05   -26.67   1.352    1.790    239    590  fail
entry - 5x ATR14              159,019  +35.60   -27.36   1.301    1.728    222    607  fail
entry - 6x ATR14              167,645  +36.91   -26.67   1.384    1.712    207    622  fail
entry - 8x ATR14              162,163  +36.08   -28.28   1.276    1.677    196    633  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## Controls

The four exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim` (`stop30`, `trail25`, `sma200x5`, `dead120` — its `EXIT_MODES = ["time"]` never selects them), at that script's own constants.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
stop30 — fixed -30% stop      162,064  +36.07   -26.41   1.366    1.747    209    620  fail
trail25 — 25% from day one     91,439  +22.57   -24.66   0.915    1.486    334    495  fail
sma200 x 5d                   117,326  +28.28   -27.10   1.043    1.390    297    532  fail
dead120 — <+5% after 120 c    151,004  +34.32   -27.70   1.239    1.608    266    563  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `arm +15% / trail 15% + <+10% after 90 bars` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15% + <+1    144,810  +33.30   -26.50   1.257    2.147    442    387  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          347,392  +56.39   -29.98   1.881    2.320    184    645  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     0 regime 10d                -13.96    -0.182    +7.11
2. trail — profit-armed trailing stop      12     0 arm +15% / trail 15%      -17.21    +0.067    +5.29
3. dead — dead-money time stop             24     0 <+10% after 90 bars        -7.22    -0.133    -2.10
4. trend — closes below own MA              9     0 ema20 x 5d                -29.15    -0.255   +11.60
5. atr — volatility-normalised stop         5     0 entry - 3x ATR14          -17.71    -0.401    +8.50
```

## Finalists — trade metrics and exit attribution

**No variant cleared the bar.** Showing the best variant of each idea instead, for diagnosis.

```text
variant                       N   Win%    Mean%     Med%     PF  CVaR95%  tSortino  exits by rule
-------------------------------------------------------------------------------------------------
baseline (366d only)        184   71.7   +62.47   +24.52   8.60   -60.49     3.600  time=155
arm +15% / trail 15%        372   71.5   +19.73    +8.31   5.06   -56.86     2.157  time=44, trail=292
<+10% after 90 bars         259   62.2   +38.76    +6.51   5.76   -48.76     3.369  dead=181, time=48
regime 10d                  244   53.7   +35.78    +2.35   5.45   -50.28     3.113  regime=119, time=93
ema20 x 5d                  583   44.4    +9.57    -2.70   2.56   -26.89     2.640  trend=556
entry - 3x ATR14            280   37.1   +27.43   -13.36   3.65   -26.66     3.008  stop=169, time=84
```

## Finalists — per-year decomposition

An edge concentrated in one year is regime-contingent, not a general improvement.

```text
variant                        2021     2022     2023     2024     2025     2026
--------------------------------------------------------------------------------
baseline (366d only)          +52.6    +26.2    +33.7    +56.2   +145.7    +17.2
arm +15% / trail 15%          +20.8     +3.1    +24.4    +30.6   +165.6    +13.8
<+10% after 90 bars           +48.3     +0.4    +36.2    +43.7   +140.0    +27.9
regime 10d                    +52.6     -9.4    +37.2    +51.4    +85.4    +30.3
ema20 x 5d                     +8.9     -9.3    +22.6     +7.2   +126.3    +27.4
entry - 3x ATR14              +53.1     -6.5    +33.0    +35.4    +85.8    +25.2
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
arm +15% / trail 15%              6.0          56.9
<+10% after 90 bars              15.1          27.3
regime 10d                       12.5          31.6
ema20 x 5d                        1.9          30.9
entry - 3x ATR14                  1.8           8.4
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s12 / 2021-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20   146 |    +16.28    +14.08   -2.20 |    1.169    1.139  -0.030 |   -25.89   -23.80 |  fail
2010-2015    s16   158 |    +14.69    +14.91   +0.22 |    1.039    1.081  +0.043 |   -27.39   -28.67 |  PASS
2010-2015    s12   164 |    +12.94    +13.51   +0.57 |    0.900    0.981  +0.081 |   -27.99   -27.92 |  PASS
2016-2020    s20   140 |    +30.86    +18.29  -12.57 |    1.946    1.236  -0.709 |   -21.66   -32.20 |  fail
2016-2020    s16   142 |    +30.79    +32.97   +2.18 |    1.954    1.943  -0.011 |   -19.99   -28.95 |  fail
2016-2020    s12   142 |    +34.90    +31.15   -3.75 |    2.171    1.845  -0.326 |   -22.66   -33.55 |  fail
2021-2026    s20   178 |    +45.03    +39.28   -5.75 |    2.016    1.867  -0.148 |   -32.09   -34.83 |  fail
2021-2026    s16   186 |    +53.31    +43.17  -10.14 |    2.168    1.948  -0.220 |   -32.42   -34.67 |  fail
2021-2026    s12   184 |    +56.39    +44.20  -12.19 |    2.320    2.005  -0.315 |   -29.98   -34.08 |  fail
```

**2 of 9 cells pass**, on the same bar used for the sweep.

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
HCC.US     2021-01-05   2021-02-25       19.96     17.81   -10.79    51  trail
KRYS.US    2021-01-06   2021-03-04       61.37     71.65   +16.75    57  trail
ESTA.US    2021-02-05   2021-03-04       53.84     62.44   +15.97    27  trail
WHD.US     2021-01-06   2021-03-09       28.23     30.77    +9.00    62  trail
AMR.US     2021-01-15   2021-03-15       13.09     12.53    -4.28    59  trail
PARR.US    2021-01-06   2021-03-16       14.50     16.64   +14.76    69  trail
```

## Limitations

- Single evaluation window; parameters are scored on the same data they were chosen on. The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it.
- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees companies that are large today. This survivorship bias inflates every absolute figure here, baseline included; relative comparisons are unaffected.
- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.
