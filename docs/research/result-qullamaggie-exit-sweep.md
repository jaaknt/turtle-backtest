# Qullamaggie Exit-Strategy Sweep

Run date: 2026-11-15 10:32:06 Tallinn time

Config: `bk50d_s12_v2.0` | 2021-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 44 | time-cap backstop 366d

830 signals entered the simulation (1483 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here and in `qullamaggie-portfolio-sim.py` both come from `turtlex.research.qullamaggie`, and both fund same-day signals best-ranked first, so on the same day's data the two baselines should agree. A divergence means either the harness no longer reproduces portfolio-sim, which would invalidate every comparison below, or the data has moved since the REF_* run: re-run portfolio-sim on the same data before reading it as the former.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (2026-11-15)    307,819  +52.98   -31.15    2.210
this harness                  307,819  +52.98   -31.15    2.209
```

CAGR divergence: 0.00pp (within the 1.0pp tolerance).

Pass bar: CAGR > +52.98%, Sortino > 2.209, MaxDD > -36.15%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                     102,494  +25.15   -24.88   1.011    1.520    358    472  fail
regime 1d (losers only)       175,759  +38.10   -23.91   1.594    1.945    289    541  fail
regime 3d                     112,096  +27.21   -24.63   1.105    1.557    305    525  fail
regime 3d (losers only)       137,643  +32.07   -24.48   1.310    1.692    262    568  fail
regime 5d                     118,755  +28.56   -23.48   1.216    1.607    291    539  fail
regime 5d (losers only)       143,165  +33.02   -22.57   1.463    1.750    254    576  fail
regime 10d                    171,007  +37.41   -24.05   1.556    1.932    246    584  fail
regime 10d (losers only)      167,021  +36.82   -22.57   1.631    1.884    225    605  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          130,189  +30.74   -27.68   1.110    1.901    372    458  fail
arm +15% / trail 20%          175,209  +38.02   -28.60   1.330    2.153    317    513  fail
arm +15% / trail 25%          148,048  +33.84   -23.20   1.458    1.900    275    555  fail
arm +15% / trail 30%          153,401  +34.71   -25.30   1.372    1.849    241    589  fail
arm +25% / trail 15%          137,681  +32.08   -25.49   1.258    1.875    315    515  fail
arm +25% / trail 20%          134,174  +31.46   -29.74   1.058    1.753    279    551  fail
arm +25% / trail 25%          149,320  +34.05   -25.88   1.316    1.845    248    582  fail
arm +25% / trail 30%          142,457  +32.90   -28.00   1.175    1.727    228    602  fail
arm +40% / trail 15%          170,992  +37.41   -25.41   1.472    2.041    264    566  fail
arm +40% / trail 20%          142,554  +32.92   -29.48   1.117    1.765    247    583  fail
arm +40% / trail 25%          146,515  +33.59   -28.31   1.186    1.776    229    601  fail
arm +40% / trail 30%          162,425  +36.12   -25.08   1.440    1.773    213    617  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            126,279  +30.01   -24.50   1.225    1.654    410    420  fail
<+5% after 20 bars            119,253  +28.66   -21.51   1.332    1.602    489    341  fail
<+10% after 20 bars           133,024  +31.25   -19.57   1.597    1.843    523    307  fail
<+0% after 40 bars            165,444  +36.58   -32.06   1.141    1.686    308    522  fail
<+5% after 40 bars            168,515  +37.04   -32.58   1.137    1.767    345    485  fail
<+10% after 40 bars           195,027  +40.75   -30.50   1.336    1.941    366    464  fail
<+0% after 60 bars            140,757  +32.61   -32.49   1.004    1.548    281    549  fail
<+5% after 60 bars            144,477  +33.25   -33.62   0.989    1.587    301    529  fail
<+10% after 60 bars           143,581  +33.09   -32.55   1.017    1.552    315    515  fail
<+0% after 90 bars            178,716  +38.52   -35.03   1.100    1.805    248    582  fail
<+5% after 90 bars            256,579  +47.98   -34.32   1.398    2.108    248    582  fail
<+10% after 90 bars           250,239  +47.30   -33.25   1.423    2.090    257    573  fail
<+0% after 120 bars           178,149  +38.44   -31.02   1.239    1.765    226    604  fail
<+5% after 120 bars           186,318  +39.58   -31.71   1.248    1.788    233    597  fail
<+10% after 120 bars          196,327  +40.92   -34.52   1.185    1.887    236    594  fail
<+0% after 150 bars           180,526  +38.78   -33.60   1.154    1.738    205    625  fail
<+5% after 150 bars           168,625  +37.06   -31.77   1.166    1.704    213    617  fail
<+10% after 150 bars          156,432  +35.19   -30.62   1.149    1.668    218    612  fail
<+0% after 180 bars           150,354  +34.22   -34.77   0.984    1.540    201    629  fail
<+5% after 180 bars           152,494  +34.57   -35.39   0.977    1.634    203    627  fail
<+10% after 180 bars          168,592  +37.05   -36.38   1.018    1.629    201    629  fail
<+0% after 240 bars           270,574  +49.42   -25.11   1.968    2.151    190    640  fail
<+5% after 240 bars           259,009  +48.23   -25.11   1.921    2.093    190    640  fail
<+10% after 240 bars          260,605  +48.40   -25.11   1.928    2.098    190    640  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     53,962  +11.32   -21.64   0.523    1.316    735     95  fail
ema20 x 3d                     68,495  +16.27   -19.39   0.839    1.563    649    181  fail
ema20 x 5d                     91,446  +22.57   -21.14   1.068    1.796    582    248  fail
sma50 x 1d                     71,455  +17.17   -25.33   0.678    1.382    580    250  fail
sma50 x 3d                     80,707  +19.81   -25.52   0.776    1.458    527    303  fail
sma50 x 5d                     85,479  +21.07   -21.98   0.959    1.500    482    348  fail
sma200 x 1d                   139,184  +32.34   -23.64   1.368    1.741    371    459  fail
sma200 x 3d                   104,463  +25.58   -25.91   0.987    1.347    329    501  fail
sma200 x 5d                    92,795  +22.90   -23.87   0.959    1.210    307    523  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              153,865  +34.79   -23.46   1.483    1.719    286    544  fail
entry - 4x ATR14              146,717  +33.62   -27.59   1.218    1.671    248    582  fail
entry - 5x ATR14              143,311  +33.05   -26.40   1.252    1.634    228    602  fail
entry - 6x ATR14              155,735  +35.08   -24.54   1.430    1.706    212    618  fail
entry - 8x ATR14              216,281  +43.43   -24.78   1.753    1.992    201    629  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## Controls

The four exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim` (`stop30`, `trail25`, `sma200x5`, `dead120` — its `EXIT_MODES = ["time"]` never selects them), at that script's own constants.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
stop30 — fixed -30% stop      134,197  +31.46   -26.65   1.180    1.550    214    616  fail
trail25 — 25% from day one     84,001  +20.68   -24.46   0.846    1.381    346    484  fail
sma200 x 5d                    92,795  +22.90   -23.87   0.959    1.210    307    523  fail
dead120 — <+5% after 120 c    178,845  +38.54   -32.57   1.183    1.792    262    568  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `arm +15% / trail 20% + <+0% after 240 bars` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 20% + <+0    145,708  +33.45   -29.56   1.132    1.925    320    510  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +52.98   -31.15   1.701    2.209    188    642  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     0 regime 1d (losers only)   -14.88    -0.264    +7.24
2. trail — profit-armed trailing stop      12     0 arm +15% / trail 20%      -14.96    -0.056    +2.55
3. dead — dead-money time stop             24     0 <+0% after 240 bars        -3.56    -0.058    +6.04
4. trend — closes below own MA              9     0 ema20 x 5d                -30.41    -0.412   +10.01
5. atr — volatility-normalised stop         5     0 entry - 8x ATR14           -9.55    -0.217    +6.37
```

## Finalists — trade metrics and exit attribution

**No variant cleared the bar.** Showing the best variant of each idea instead, for diagnosis.

```text
variant                       N   Win%    Mean%     Med%     PF  CVaR95%  tSortino  exits by rule
-------------------------------------------------------------------------------------------------
baseline (366d only)        188   71.3   +57.19   +23.20   7.64   -64.25     3.162  time=155
arm +15% / trail 20%        317   61.8   +23.93    +6.47   4.48   -61.19     2.106  time=59, trail=226
<+0% after 240 bars         190   62.6   +51.35   +16.72   6.41   -64.26     2.780  dead=61, time=98
entry - 8x ATR14            201   63.2   +42.56   +15.87   4.69   -55.42     2.306  stop=43, time=127
regime 1d (losers only)     289   35.6   +27.17    -2.24   4.68   -44.42     2.991  regime=176, time=95
ema20 x 5d                  582   42.6    +7.49    -3.07   2.17   -26.71     2.047  trend=554
```

## Finalists — per-year decomposition

An edge concentrated in one year is regime-contingent, not a general improvement.

```text
variant                        2021     2022     2023     2024     2025     2026
--------------------------------------------------------------------------------
baseline (366d only)          +47.3    +31.8    +28.2    +46.0   +127.6    +24.0
arm +15% / trail 20%          +23.3     -8.9    +20.1    +38.4   +151.0    +24.5
<+0% after 240 bars           +46.0    +24.6    +32.8    +45.6   +109.7    +22.3
entry - 8x ATR14              +50.2    +18.4    +26.4    +37.9    +94.8    +19.3
regime 1d (losers only)       +47.3     +6.7    +26.9    +41.8    +57.6    +31.4
ema20 x 5d                     +9.6    -10.3    +20.3     +2.5   +116.4    +16.2
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
arm +15% / trail 20%              5.9          44.4
<+0% after 240 bars              15.8          32.3
entry - 8x ATR14                  1.2           7.7
regime 1d (losers only)           6.6          23.1
ema20 x 5d                        1.0          20.8
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s12 / 2021-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20   147 |    +15.47    +13.85   -1.63 |    1.115    1.130  +0.015 |   -25.99   -23.29 |  fail
2010-2015    s16   158 |    +15.71    +15.00   -0.70 |    1.095    1.097  +0.002 |   -27.90   -28.30 |  fail
2010-2015    s12   164 |    +13.01    +14.55   +1.55 |    0.905    1.046  +0.141 |   -28.55   -27.10 |  PASS
2016-2020    s20   139 |    +32.50    +23.54   -8.96 |    1.865    1.401  -0.465 |   -23.63   -31.81 |  fail
2016-2020    s16   140 |    +33.75    +32.79   -0.95 |    1.919    1.853  -0.067 |   -24.39   -27.83 |  fail
2016-2020    s12   141 |    +37.74    +31.89   -5.85 |    2.143    1.863  -0.280 |   -21.73   -25.41 |  fail
2021-2026    s20   181 |    +43.63    +33.15  -10.48 |    1.967    1.629  -0.339 |   -32.97   -33.48 |  fail
2021-2026    s16   182 |    +50.83    +42.85   -7.99 |    2.132    1.925  -0.206 |   -30.87   -34.59 |  fail
2021-2026    s12   188 |    +52.98    +47.98   -5.00 |    2.209    2.108  -0.100 |   -31.15   -34.32 |  fail
```

**1 of 9 cells pass**, on the same bar used for the sweep.

`N` is the baseline trade count, which doubles as a read on how capital-constrained each cell is: the rule's second mechanism is recycling capital into signals that would otherwise go unfunded, so it has less to work with where cash was already idle.

## Audit sample — first 10 rule-driven exits of the top finalist

Every field below is checkable against `turtle.daily_bars`: `exit $` is that symbol's split/dividend-adjusted close on `exit date`, and the rule that fired is named.
Rule: arm +15% / trail 20%

```text
symbol     entry date   exit date      entry $    exit $     ret%  calD  rule
-----------------------------------------------------------------------------
SM.US      2021-01-06   2021-01-21        6.91      7.50    +8.54    15  trail
GSL.US     2021-01-06   2021-01-22        8.39      9.08    +8.26    16  trail
OII.US     2021-01-06   2021-01-27        9.67      8.72    -9.82    21  trail
RYTM.US    2021-01-07   2021-01-27       33.67     31.11    -7.60    20  trail
FTI.US     2021-01-06   2021-02-09        7.83      7.23    -7.73    34  trail
HCC.US     2021-01-05   2021-02-25       19.96     17.81   -10.79    51  trail
ESTA.US    2021-02-05   2021-03-12       53.84     58.97    +9.53    35  trail
PARR.US    2021-01-06   2021-03-18       14.50     14.94    +3.03    71  trail
WHD.US     2021-01-06   2021-03-18       28.23     28.69    +1.62    71  trail
LBRT.US    2021-01-06   2021-03-19       11.35     10.88    -4.15    72  trail
```

## Limitations

- Single evaluation window; parameters are scored on the same data they were chosen on. The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it.
- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees companies that are large today. This survivorship bias inflates every absolute figure here, baseline included; relative comparisons are unaffected.
- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.
