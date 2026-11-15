# Qullamaggie Exit-Strategy Sweep

Run date: 2026-11-15 15:00:38 Tallinn time

Config: `bk50d_s12_v2.0` | 2021-01-01 – 2026-06-26 | initial $30,000 | sizing 3% of portfolio value | ranking >= 44 | time-cap backstop 366d

830 signals entered the simulation (1483 dropped below the ranking gate, 0 with no entry bar in the window). Exits fill at the day's adjusted close.

## Baseline reconciliation

Signals here and in `qullamaggie-portfolio-sim.py` both come from `turtlex.research.qullamaggie`, and both fund same-day signals best-ranked first, so on the same day's data the two baselines should agree. A divergence means either the harness no longer reproduces portfolio-sim, which would invalidate every comparison below, or the data has moved since the REF_* run: re-run portfolio-sim on the same data before reading it as the former.

```text
source                         Final$   CAGR%   MaxDD%  Sortino
---------------------------------------------------------------
portfolio-sim (2026-11-15)    307,819  +53.22   -31.15    2.210
this harness                  307,819  +53.22   -31.15    2.210
```

CAGR divergence: 0.00pp (within the 1.0pp tolerance).

Pass bar: CAGR > +53.22%, Sortino > 2.210, MaxDD > -36.15%.

## 1. regime — SPY below its 200d SMA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
regime 1d                     113,427  +27.60   -24.88   1.109    1.584    322    508  fail
regime 1d (losers only)       171,209  +37.60   -23.91   1.573    1.923    287    543  fail
regime 3d                     112,096  +27.33   -24.63   1.109    1.558    305    525  fail
regime 3d (losers only)       137,643  +32.21   -24.48   1.316    1.693    262    568  fail
regime 5d                     118,755  +28.68   -23.48   1.221    1.609    291    539  fail
regime 5d (losers only)       143,165  +33.16   -22.57   1.469    1.751    254    576  fail
regime 10d                    171,007  +37.57   -24.05   1.562    1.933    246    584  fail
regime 10d (losers only)      167,021  +36.98   -22.57   1.639    1.885    225    605  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## 2. trail — profit-armed trailing stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 15%          130,189  +30.87   -27.68   1.115    1.902    372    458  fail
arm +15% / trail 20%          175,209  +38.19   -28.60   1.335    2.154    317    513  fail
arm +15% / trail 25%          148,048  +33.99   -23.20   1.465    1.901    275    555  fail
arm +15% / trail 30%          153,401  +34.86   -25.30   1.378    1.851    241    589  fail
arm +25% / trail 15%          137,715  +32.22   -25.49   1.264    1.877    315    515  fail
arm +25% / trail 20%          134,202  +31.60   -29.74   1.062    1.754    279    551  fail
arm +25% / trail 25%          149,320  +34.20   -25.88   1.321    1.847    248    582  fail
arm +25% / trail 30%          142,457  +33.04   -28.00   1.180    1.728    228    602  fail
arm +40% / trail 15%          171,030  +37.58   -25.41   1.479    2.043    264    566  fail
arm +40% / trail 20%          142,587  +33.07   -29.48   1.122    1.767    247    583  fail
arm +40% / trail 25%          146,515  +33.73   -28.31   1.192    1.777    229    601  fail
arm +40% / trail 30%          162,425  +36.28   -25.08   1.447    1.774    213    617  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## 3. dead — dead-money time stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
<+0% after 20 bars            126,279  +30.14   -24.50   1.230    1.655    410    420  fail
<+5% after 20 bars            119,253  +28.78   -21.51   1.338    1.603    489    341  fail
<+10% after 20 bars           133,024  +31.38   -19.57   1.604    1.844    523    307  fail
<+0% after 40 bars            165,444  +36.74   -32.06   1.146    1.687    308    522  fail
<+5% after 40 bars            168,515  +37.20   -32.58   1.142    1.768    345    485  fail
<+10% after 40 bars           195,027  +40.93   -30.50   1.342    1.943    366    464  fail
<+0% after 60 bars            140,757  +32.75   -32.49   1.008    1.549    281    549  fail
<+5% after 60 bars            144,477  +33.39   -33.62   0.993    1.588    301    529  fail
<+10% after 60 bars           143,581  +33.24   -32.55   1.021    1.553    315    515  fail
<+0% after 90 bars            178,716  +38.69   -35.03   1.104    1.806    248    582  fail
<+5% after 90 bars            256,579  +48.19   -34.32   1.404    2.110    248    582  fail
<+10% after 90 bars           250,239  +47.52   -33.25   1.429    2.092    257    573  fail
<+0% after 120 bars           178,149  +38.61   -31.02   1.245    1.767    226    604  fail
<+5% after 120 bars           186,318  +39.75   -31.71   1.254    1.789    233    597  fail
<+10% after 120 bars          196,327  +41.10   -34.52   1.191    1.888    236    594  fail
<+0% after 150 bars           180,526  +38.95   -33.60   1.159    1.740    205    625  fail
<+5% after 150 bars           168,625  +37.22   -31.77   1.171    1.705    213    617  fail
<+10% after 150 bars          156,432  +35.35   -30.62   1.154    1.669    218    612  fail
<+0% after 180 bars           150,354  +34.37   -34.77   0.988    1.541    201    629  fail
<+5% after 180 bars           152,494  +34.71   -35.39   0.981    1.635    203    627  fail
<+10% after 180 bars          168,592  +37.22   -36.38   1.023    1.630    201    629  fail
<+0% after 240 bars           270,574  +49.64   -25.11   1.977    2.153    190    640  fail
<+5% after 240 bars           259,009  +48.45   -25.11   1.930    2.095    190    640  fail
<+10% after 240 bars          260,605  +48.62   -25.11   1.936    2.100    190    640  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## 4. trend — closes below own MA

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
ema20 x 1d                     53,962  +11.36   -21.64   0.525    1.317    735     95  fail
ema20 x 3d                     68,935  +16.47   -19.39   0.849    1.576    649    181  fail
ema20 x 5d                     91,315  +22.63   -21.14   1.071    1.796    582    248  fail
sma50 x 1d                     71,455  +17.24   -25.33   0.681    1.383    580    250  fail
sma50 x 3d                     80,679  +19.88   -25.52   0.779    1.459    527    303  fail
sma50 x 5d                     85,173  +21.08   -21.98   0.959    1.496    481    349  fail
sma200 x 1d                   139,184  +32.48   -23.64   1.374    1.743    371    459  fail
sma200 x 3d                   104,463  +25.69   -25.91   0.992    1.348    329    501  fail
sma200 x 5d                    92,795  +22.99   -23.87   0.963    1.211    307    523  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## 5. atr — volatility-normalised stop

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
entry - 3x ATR14              153,865  +34.94   -23.46   1.489    1.720    286    544  fail
entry - 4x ATR14              146,717  +33.76   -27.59   1.224    1.672    248    582  fail
entry - 5x ATR14              143,311  +33.19   -26.40   1.257    1.635    228    602  fail
entry - 6x ATR14              155,735  +35.23   -24.54   1.436    1.707    212    618  fail
entry - 8x ATR14              216,281  +43.62   -24.78   1.760    1.993    201    629  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## Controls

The four exit modes `qullamaggie-portfolio-sim.py` carried but never selected (`stop30`, `trail25`, `sma200x5`, `dead120`), at the constants it used for them. They were removed from it on 2026-11-15 and are measured only here.

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
stop30 — fixed -30% stop      134,197  +31.60   -26.65   1.185    1.551    214    616  fail
trail25 — 25% from day one     84,001  +20.77   -24.46   0.849    1.382    346    484  fail
sma200 x 5d                    92,795  +22.99   -23.87   0.963    1.211    307    523  fail
dead120 — <+5% after 120 c    178,845  +38.71   -32.57   1.188    1.793    262    568  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## Composed rule

The two best-scoring ideas with non-overlapping mechanisms, run together.

Rule: `arm +15% / trail 20% + <+0% after 240 bars` (name truncated in the table below).

```text
variant                        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip      
-------------------------------------------------------------------------------------------
arm +15% / trail 20% + <+0    145,708  +33.60   -29.56   1.136    1.926    320    510  fail
-------------------------------------------------------------------------------------------
baseline (366d only)          307,819  +53.22   -31.15   1.709    2.210    188    642  fail
```

## Verdict by idea

Deltas are the idea's best-by-Sortino variant against the baseline.

```text
idea                                    cells  pass best variant               dCAGR  dSortino   dMaxDD
-------------------------------------------------------------------------------------------------------
1. regime — SPY below its 200d SMA          8     0 regime 10d                -15.65    -0.277    +7.10
2. trail — profit-armed trailing stop      12     0 arm +15% / trail 20%      -15.03    -0.056    +2.55
3. dead — dead-money time stop             24     0 <+0% after 240 bars        -3.58    -0.058    +6.04
4. trend — closes below own MA              9     0 ema20 x 5d                -30.59    -0.415   +10.01
5. atr — volatility-normalised stop         5     0 entry - 8x ATR14           -9.60    -0.217    +6.37
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
regime 10d                  246   53.7   +30.86    +2.01   4.53   -53.57     2.494  regime=125, time=89
ema20 x 5d                  582   42.6    +7.48    -3.07   2.17   -26.71     2.043  trend=554
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
regime 10d                    +47.3     -7.1    +31.9    +48.9    +73.5    +22.2
ema20 x 5d                     +9.6    -10.3    +20.3     +2.5   +116.4    +16.1
```

## Finalists — bootstrap win rate vs baseline

Stationary block bootstrap, 1,000 resamples of 21-day blocks, paired on day indices. The figure is the fraction of resampled paths on which the variant beats the baseline — near 50% means the difference is indistinguishable from noise.

```text
variant                     CAGR win%  Sortino win%
---------------------------------------------------
arm +15% / trail 20%              6.3          43.9
<+0% after 240 bars              18.1          33.7
entry - 8x ATR14                  1.0           7.7
regime 10d                        7.6          23.4
ema20 x 5d                        1.0          22.2
```

## Robustness matrix — `<+5% after 90 bars` across configs and periods

The winning rule's parameters were chosen on **s12 / 2021-01-01–2026-06-26**. Every other cell below varies the entry threshold, the period, or both, and none of them informed that choice. Each cell re-runs the baseline and the rule on identical signals, so the difference is the exit and nothing else.

```text
period       cfg     N | base CAGR rule CAGR       d | base Srt rule Srt       d |  base DD  rule DD |      
------------------------------------------------------------------------------------------------------------
2010-2015    s20   147 |    +15.48    +13.86   -1.63 |    1.115    1.130  +0.015 |   -25.99   -23.29 |  fail
2010-2015    s16   158 |    +15.72    +15.01   -0.70 |    1.095    1.097  +0.002 |   -27.90   -28.30 |  fail
2010-2015    s12   164 |    +13.01    +14.56   +1.55 |    0.905    1.046  +0.141 |   -28.55   -27.10 |  PASS
2016-2020    s20   139 |    +32.52    +23.55   -8.97 |    1.865    1.401  -0.465 |   -23.63   -31.81 |  fail
2016-2020    s16   140 |    +33.77    +32.81   -0.95 |    1.919    1.853  -0.067 |   -24.39   -27.83 |  fail
2016-2020    s12   141 |    +37.76    +31.91   -5.85 |    2.143    1.863  -0.280 |   -21.73   -25.41 |  fail
2021-2026    s20   181 |    +43.83    +33.29  -10.53 |    1.969    1.630  -0.339 |   -32.97   -33.48 |  fail
2021-2026    s16   182 |    +51.06    +43.04   -8.03 |    2.133    1.927  -0.207 |   -30.87   -34.59 |  fail
2021-2026    s12   188 |    +53.22    +48.19   -5.03 |    2.210    2.110  -0.100 |   -31.15   -34.32 |  fail
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
