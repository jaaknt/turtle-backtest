# Qullamaggie Exit-Strategy Sweep

Run date: 2026-07-29

Config: `bk50d_s20_v1.3_roc100` | 2020-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 40 | time-cap backstop 366d

896 signals entered the simulation (0 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here come from `turtlex.research.qullamaggie`, whose cooldown chain runs through the warmup window, while `qullamaggie-portfolio-sim.py` starts its chain at the evaluation start. A small divergence is expected; a large one would invalidate every comparison below.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (committed)     222,166  +36.17   -26.00    1.334
this harness                  222,166  +36.17   -26.00    1.331
```

CAGR divergence: 0.00pp (within the 1.0pp tolerance).

Pass bar: CAGR > +36.17%, Sortino > 1.331, MaxDD > -31.00%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                      66,634  +13.09   -26.77   0.489    0.630    339    557  fail
regime 1d (losers only)       140,030  +26.82   -20.51   1.308    1.107    276    620  fail
regime 3d                     110,291  +22.23   -28.02   0.794    0.955    255    641  fail
regime 3d (losers only)       177,430  +31.53   -20.89   1.510    1.269    233    663  fail
regime 5d                     106,294  +21.54   -26.82   0.803    0.927    255    641  fail
regime 5d (losers only)       212,618  +35.25   -22.60   1.560    1.367    232    664  fail
regime 10d                    176,375  +31.41   -22.20   1.415    1.202    222    674  fail
regime 10d (losers only)      185,404  +32.43   -23.04   1.408    1.264    206    690  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          149,963  +28.16   -22.77   1.237    1.328    340    556  fail
arm +15% / trail 20%          169,733  +30.64   -23.97   1.278    1.345    291    605  fail
arm +15% / trail 25%          204,509  +34.44   -23.69   1.454    1.429    262    634  fail
arm +15% / trail 30%          218,631  +35.84   -25.01   1.433    1.422    235    661  fail
arm +25% / trail 15%          140,947  +26.94   -24.21   1.113    1.221    288    608  fail
arm +25% / trail 20%          154,578  +28.76   -26.39   1.090    1.227    249    647  fail
arm +25% / trail 25%          225,837  +36.52   -25.39   1.438    1.456    237    659  PASS
arm +25% / trail 30%          195,538  +33.52   -25.33   1.323    1.349    216    680  fail
arm +40% / trail 15%          149,139  +28.06   -30.43   0.922    1.169    248    648  fail
arm +40% / trail 20%          183,284  +32.19   -31.20   1.032    1.304    230    666  fail
arm +40% / trail 25%          203,663  +34.36   -25.06   1.371    1.394    215    681  fail
arm +40% / trail 30%          205,020  +34.50   -25.49   1.353    1.353    209    687  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            172,071  +30.91   -20.77   1.488    1.202    377    519  fail
<+5% after 20 bars            102,478  +20.86   -18.45   1.131    0.935    455    441  fail
<+10% after 20 bars           103,819  +21.10   -19.47   1.083    0.942    495    401  fail
<+0% after 40 bars            213,103  +35.30   -20.56   1.717    1.313    302    594  fail
<+5% after 40 bars            218,688  +35.84   -21.57   1.661    1.383    329    567  fail
<+10% after 40 bars           191,293  +33.07   -19.71   1.678    1.309    363    533  fail
<+0% after 60 bars            191,029  +33.04   -26.21   1.260    1.224    275    621  fail
<+5% after 60 bars            213,118  +35.30   -27.27   1.295    1.339    281    615  fail
<+10% after 60 bars           179,146  +31.73   -26.30   1.206    1.214    298    598  fail
<+0% after 90 bars            292,155  +42.05   -27.54   1.527    1.537    239    657  PASS
<+5% after 90 bars            299,845  +42.62   -24.04   1.773    1.555    246    650  PASS
<+10% after 90 bars           283,413  +41.38   -26.77   1.546    1.478    255    641  PASS
<+0% after 120 bars           207,433  +34.74   -28.96   1.199    1.324    212    684  fail
<+5% after 120 bars           265,885  +40.00   -29.77   1.344    1.450    218    678  PASS
<+10% after 120 bars          293,708  +42.16   -28.18   1.496    1.499    222    674  PASS
<+0% after 150 bars           220,720  +36.04   -30.01   1.201    1.341    200    696  fail
<+5% after 150 bars           231,710  +37.06   -30.41   1.219    1.372    205    691  PASS
<+10% after 150 bars          237,261  +37.56   -28.40   1.323    1.405    209    687  PASS
<+0% after 180 bars           162,878  +29.81   -32.26   0.924    1.147    195    701  fail
<+5% after 180 bars           172,560  +30.97   -32.51   0.953    1.227    198    698  fail
<+10% after 180 bars          201,819  +34.17   -32.50   1.051    1.229    197    699  fail
<+0% after 240 bars           185,502  +32.44   -29.55   1.098    1.245    186    710  fail
<+5% after 240 bars           171,799  +30.88   -28.63   1.078    1.212    186    710  fail
<+10% after 240 bars          180,660  +31.90   -28.07   1.137    1.262    187    709  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     47,222   +7.25   -18.49   0.392    0.540    618    278  fail
ema20 x 3d                     67,755  +13.39   -18.32   0.731    0.863    559    337  fail
ema20 x 5d                     97,348  +19.90   -18.32   1.086    1.101    500    396  fail
sma50 x 1d                     82,598  +16.90   -19.02   0.889    0.922    481    415  fail
sma50 x 3d                     95,451  +19.54   -19.44   1.005    0.971    437    459  fail
sma50 x 5d                    101,463  +20.67   -19.39   1.066    1.029    408    488  fail
sma200 x 1d                   173,736  +31.11   -24.22   1.284    1.279    359    537  fail
sma200 x 3d                   231,447  +37.03   -26.25   1.411    1.369    308    588  PASS
sma200 x 5d                   245,338  +38.27   -26.19   1.461    1.460    298    598  PASS
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              159,751  +29.42   -19.71   1.493    1.186    259    637  fail
entry - 4x ATR14              209,328  +34.93   -19.87   1.758    1.350    228    668  fail
entry - 5x ATR14              211,636  +35.16   -23.13   1.520    1.338    217    679  fail
entry - 6x ATR14              152,141  +28.45   -25.70   1.107    1.152    200    696  fail
entry - 8x ATR14              173,057  +31.03   -26.57   1.168    1.239    188    708  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## Controls

The three exit modes already coded but unreachable in `qullamaggie-portfolio-sim.py:run_sim`.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
fixed -30% stop               180,958  +31.93   -22.67   1.408    1.323    198    698  fail
25% trail from day one        166,731  +30.28   -19.16   1.581    1.327    297    599  fail
sma200 x 3d                   231,447  +37.03   -26.25   1.411    1.369    308    588  PASS
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `<+5% after 90 bars + sma200 x 5d` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+5% after 90 bars + sma20    242,829  +38.05   -24.77   1.536    1.455    325    571  PASS
-------------------------------------------------------------------------------------------
baseline (366d only)          222,166  +36.17   -26.00   1.391    1.331    180    716  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     0 regime 5d (losers only)    -0.92    +0.036    +3.40
2. trail — profit-armed trailing stop      12     1 arm +25% / trail 25%       +0.34    +0.125    +0.60
3. dead — dead-money time stop             24     7 <+5% after 90 bars         +6.44    +0.224    +1.96
4. trend — closes below own MA              9     2 sma200 x 5d                +2.10    +0.128    -0.19
5. atr — volatility-normalised stop         5     0 entry - 4x ATR14           -1.24    +0.019    +6.12
```

## Finalists — trade metrics and exit attribution

11 variant(s) cleared the bar, ordered by Sortino.

```text
variant                       N   Win%    Mean%     Med%     PF  CVaR95%  tSortino  exits by rule
-------------------------------------------------------------------------------------------------
baseline (366d only)        180   71.7   +52.99   +26.96   6.75   -70.34     2.651  time=159
<+5% after 90 bars          246   58.1   +44.22    +3.40   7.52   -47.60     4.181  dead=158, time=65
<+0% after 90 bars          239   39.3   +45.36    -1.15   7.05   -46.78     4.119  dead=144, time=72
<+10% after 120 bars        222   63.1   +50.43    +7.16   7.48   -51.86     3.877  dead=135, time=66
<+10% after 90 bars         255   62.0   +41.32    +5.82   6.78   -52.28     3.665  dead=173, time=60
sma200 x 5d                 298   47.7   +34.45    -1.30   5.63   -35.26     4.136  time=50, trend=225
arm +25% / trail 25%        237   66.7   +38.47   +14.99   6.84   -61.79     2.840  time=103, trail=100
<+5% after 90 bars + sma20  325   52.9   +31.28    +1.00   5.73   -36.12     4.144  dead=87, time=43, trend=173
<+5% after 120 bars         218   61.5   +47.07    +3.91   6.86   -52.98     3.510  dead=123, time=69
<+10% after 150 bars        209   65.6   +46.96    +8.54   6.19   -59.91     2.943  dead=114, time=68
<+5% after 150 bars         205   63.9   +46.61    +4.68   6.14   -58.62     2.938  dead=107, time=71
sma200 x 3d                 308   42.9   +33.89    -2.93   5.41   -34.58     4.152  time=38, trend=251
```

## Finalists — per-year decomposition

An edge concentrated in one year is regime-contingent, not a general improvement.

```text
variant                        2020     2021     2022     2023     2024     2025     2026
-----------------------------------------------------------------------------------------
baseline (366d only)          +78.4    +34.7    -16.0    +28.3    +28.1    +40.5    +58.9
<+5% after 90 bars            +71.2    +48.2    -11.5    +28.7    +36.0    +58.9    +60.0
<+0% after 90 bars            +72.3    +44.8    -11.2    +36.3    +28.9    +54.1    +62.4
<+10% after 120 bars          +79.7    +33.8    -16.1    +36.8    +34.7    +58.1    +66.6
<+10% after 90 bars           +71.2    +49.6    -11.0    +30.1    +31.5    +65.0    +46.7
sma200 x 5d                   +63.1    +34.3    -12.6    +12.4    +57.5    +37.2    +75.9
arm +25% / trail 25%          +59.7    +45.5    -18.1    +25.6    +52.6    +53.9    +34.1
<+5% after 90 bars + sma20    +59.4    +33.1    -12.9    +14.8    +53.7    +45.6    +70.6
<+5% after 120 bars           +79.9    +30.7    -16.4    +36.4    +34.2    +55.3    +58.6
<+10% after 150 bars          +77.6    +34.5    -19.0    +24.7    +49.7    +42.6    +53.6
<+5% after 150 bars           +77.6    +35.6    -19.4    +24.3    +49.8    +43.1    +49.4
sma200 x 3d                   +56.6     +8.6    -11.2    +12.3    +60.4    +45.3    +95.3
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
<+5% after 90 bars               91.8          94.1
<+0% after 90 bars               89.6          91.6
<+10% after 120 bars             89.8          88.4
<+10% after 90 bars              81.2          77.2
sma200 x 5d                      62.2          72.6
arm +25% / trail 25%             52.3          75.3
<+5% after 90 bars + sma20       59.9          70.4
<+5% after 120 bars              79.3          78.6
<+10% after 150 bars             57.9          66.7
<+5% after 150 bars              54.1          57.5
sma200 x 3d                      53.7          55.1
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s20 / 2020-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20   102 |     +8.48     +5.23   -3.26 |    0.584    0.495  -0.089 |   -24.26   -17.54 |  fail
2010-2015    s15   142 |     +9.09     +7.82   -1.27 |    0.516    0.555  +0.038 |   -29.20   -19.16 |  fail
2010-2015    s12   145 |     +8.47     +7.64   -0.83 |    0.488    0.541  +0.053 |   -30.04   -19.55 |  fail
2016-2020    s20   135 |    +27.00    +24.22   -2.78 |    1.124    1.095  -0.029 |   -20.23   -26.99 |  fail
2016-2020    s15   139 |    +33.23    +23.79   -9.43 |    1.397    1.028  -0.369 |   -15.02   -24.37 |  fail
2016-2020    s12   141 |    +28.54    +22.88   -5.66 |    1.276    1.002  -0.275 |   -18.94   -23.52 |  fail
2021-2026    s20   163 |    +32.49    +39.37   +6.88 |    1.185    1.405  +0.220 |   -23.95   -24.04 |  PASS
2021-2026    s15   181 |    +40.04    +40.94   +0.90 |    1.352    1.422  +0.071 |   -24.50   -27.31 |  PASS
2021-2026    s12   180 |    +46.92    +39.87   -7.05 |    1.449    1.374  -0.075 |   -27.95   -30.06 |  fail
```

**2 of 9 cells pass**, on the same bar used for the sweep.

`N` is the baseline trade count, which doubles as a read on how capital-constrained each cell is: the rule's second mechanism is recycling capital into signals that would otherwise go unfunded, so it has less to work with where cash was already idle.

## Audit sample — first 10 rule-driven exits of the top finalist

Every field below is checkable against `turtle.daily_bars`: `exit $` is that symbol's split/dividend-adjusted close on `exit date`, and the rule that fired is named.
Rule: <+5% after 90 bars

```text
symbol     entry date   exit date      entry $    exit $     ret%  calD  rule
-----------------------------------------------------------------------------
PCG.US     2020-01-16   2020-05-27       12.36     10.74   -13.12   132  dead
AER.US     2020-05-28   2020-10-05       33.04     26.39   -20.11   130  dead
AIG.US     2020-05-28   2020-10-05       27.35     25.39    -7.18   130  dead
AL.US      2020-05-28   2020-10-05       28.32     28.61    +1.05   130  dead
AMKR.US    2020-05-28   2020-10-05       10.21     10.67    +4.55   130  dead
ASB.US     2020-05-28   2020-10-05       12.26     10.76   -12.22   130  dead
BCS.US     2020-05-28   2020-10-05        5.03      4.28   -15.07   130  dead
BHF.US     2020-05-28   2020-10-05       32.26     29.72    -7.87   130  dead
BKR.US     2020-05-28   2020-10-05       14.21     11.19   -21.22   130  dead
BXMT.US    2020-05-28   2020-10-05       13.50     12.80    -5.18   130  dead
```

## Limitations

- Single evaluation window; parameters are scored on the same data they were chosen on. The full metric surface, the per-year decomposition and the bootstrap bound that risk but do not remove it.
- The universe filter uses **current** `company.market_cap >= $1.5B`, so the backtest only ever sees companies that are large today. This survivorship bias inflates every absolute figure here, baseline included; relative comparisons are unaffected.
- Exits fill at the day's adjusted close, so stop-based rules are measured optimistically.
