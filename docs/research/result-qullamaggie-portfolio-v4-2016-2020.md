# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-02 23:39:06 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2016-01-01 – 2020-12-31 |
| Hold | 366d (calendar) |
| Algorithms | bk50d_s20_v2.0 (%abv_SMA50>20%), bk50d_s16_v2.0 (%abv_SMA50>16%), bk50d_s12_v2.0 (%abv_SMA50>12%) |
| Entry | next trading day's split/dividend-adjusted open |
| Initial equity | $30,000 |
| Position sizing | 3%, 4%, 5% of portfolio per trade |
| Ranking gate | QullamaggieRanking >= 40, reported against an ungated run of the same signals |
| Fixed filters | breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100% (no tight_range) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Cash competition | same-day signals funded best-ranked first |

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         55,797  +13.23   -34.10   0.388    1.030
QQQ         85,956  +23.46   -28.56   0.821    1.492
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 267 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        139,714  +36.07   -25.23   1.429    1.972    138    721   24.6%
3%     ungated      131,730  +34.48   -22.82   1.511    1.989    142    984   22.6%
4%     R>=40        168,677  +41.30   -20.10   2.055    2.220    106    753   22.6%
4%     ungated      135,081  +35.16   -26.71   1.316    1.979    108   1018   21.2%
5%     R>=40        136,370  +35.41   -33.32   1.063    1.886     87    772   21.6%
5%     ungated      134,569  +35.05   -33.78   1.038    1.862     88   1038   19.7%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 799 signals (1 with no fillable next-day open); ungated drops 0 (4 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        158,733  +39.59   -22.92   1.727    2.155    140    778   22.9%
3%     ungated      128,924  +33.90   -39.81   0.851    1.742    158   1556   13.5%
4%     R>=40        175,297  +42.40   -27.07   1.566    2.249    107    811   21.1%
4%     ungated      111,793  +30.13   -43.99   0.685    1.475    122   1592   11.5%
5%     R>=40        162,725  +40.29   -39.18   1.028    1.954     88    830   19.4%
5%     ungated       90,956  +24.87   -41.87   0.594    1.261     96   1618   11.1%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 1430 signals (1 with no fillable next-day open); ungated drops 0 (4 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        132,960  +34.73   -26.94   1.289    1.895    149    873   18.8%
3%     ungated      105,093  +28.53   -43.73   0.652    1.422    164   2285    9.1%
4%     R>=40        134,458  +35.03   -36.37   0.963    1.733    118    904   14.9%
4%     ungated       97,026  +26.49   -44.60   0.594    1.310    121   2328    9.3%
5%     R>=40        117,954  +31.54   -44.94   0.702    1.489     96    926   12.8%
5%     ungated      104,655  +28.42   -47.91   0.593    1.353     96   2353    9.5%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=40             4%     175,297  +42.40   -27.07   1.566    2.249    107    811   21.1%
 2  s20 R>=40             4%     168,677  +41.30   -20.10   2.055    2.220    106    753   22.6%
 3  s16 R>=40             5%     162,725  +40.29   -39.18   1.028    1.954     88    830   19.4%
 4  s16 R>=40             3%     158,733  +39.59   -22.92   1.727    2.155    140    778   22.9%
 5  s20 R>=40             3%     139,714  +36.07   -25.23   1.429    1.972    138    721   24.6%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=40             4%     175,297  +42.40   -27.07   1.566    2.249    107    811   21.1%
 2  s20 R>=40             4%     168,677  +41.30   -20.10   2.055    2.220    106    753   22.6%
 3  s16 R>=40             3%     158,733  +39.59   -22.92   1.727    2.155    140    778   22.9%
 4  s20 ungated           3%     131,730  +34.48   -22.82   1.511    1.989    142    984   22.6%
 5  s20 ungated           4%     135,081  +35.16   -26.71   1.316    1.979    108   1018   21.2%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=40 3%        2016      43,267  +44.22   -10.88   4.064    2.549     33    150   22.2%
                    2017      54,670  +26.35    -7.09   3.717    2.554     31     17   31.7%
                    2018      55,483   +1.49   -21.97   0.068    0.069     21     10   17.6%
                    2019      66,698  +20.21   -19.36   1.044    1.179     32     49    9.1%
                    2020     132,960  +99.35   -26.94   3.688    2.980     32    647   13.6%
s12 R>=40 4%        2016      42,679  +42.26   -11.50   3.674    2.426     25    158   20.7%
                    2017      54,779  +28.35    -6.62   4.284    2.572     24     24   24.0%
                    2018      54,538   -0.44   -25.46  -0.017   -0.036     20     11   14.6%
                    2019      63,207  +15.90   -22.20   0.716    0.888     25     56    7.1%
                    2020     134,458 +112.72   -36.37   3.100    2.819     24    655    8.3%
s12 R>=40 5%        2016      44,099  +47.00   -10.49   4.482    2.659     19    164   23.2%
                    2017      55,294  +25.39    -7.58   3.351    2.274     19     29   20.5%
                    2018      51,333   -7.16   -32.45  -0.221   -0.347     19     12    7.4%
                    2019      61,186  +19.19   -25.92   0.740    0.985     20     61    7.9%
                    2020     117,954  +92.78   -41.84   2.218    2.274     19    660    5.2%
s16 R>=40 4%        2016      44,313  +47.71   -10.98   4.345    2.701     25    126   21.2%
                    2017      60,000  +35.40    -6.65   5.323    3.361     23     13   30.0%
                    2018      68,508  +14.18   -14.01   1.012    0.924     11      7   27.3%
                    2019      88,508  +29.19   -15.29   1.909    1.681     24     43   10.7%
                    2020     175,297  +98.06   -27.07   3.623    2.920     24    622   16.5%
s20 R>=40 4%        2016      43,817  +46.06   -11.20   4.112    2.437     25    112   21.5%
                    2017      54,659  +24.74    -8.81   2.809    2.288     22      5   39.6%
                    2018      68,569  +25.45   -16.78   1.517    1.437     10      8   19.0%
                    2019      85,234  +24.30   -16.30   1.491    1.490     24     34   13.3%
                    2020     168,677  +97.90   -20.10   4.870    3.099     25    594   19.9%
```

## Monthly returns/transactions — s12 R>=40 at each sizing, plus the top 2 by Final$

### s12 R>=40 — size 3%  (Final $132,960)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|33   +13.3|0    -3.7|0    +3.5|0   +10.3|0    +2.7|0    +4.8|0    -3.2|0   +13.7|0    -2.1|0 |   +44.2    33
 2017 |    +7.3|0    -0.4|0    -0.1|4    -0.2|0    +0.3|6    +3.7|3    +1.3|5    +0.3|5    +2.7|3    +2.0|5    +4.5|0    +2.5|0 |   +26.4    31
 2018 |    +1.6|0    -4.2|0    +3.4|1    +4.3|4   +10.3|4    -1.2|4    +1.3|2    +7.2|2    +0.2|1    -7.6|1    +0.3|0   -12.0|2 |    +1.5    21
 2019 |    +9.9|0   +6.4|12    -2.5|1    +2.6|2   -11.1|2   +14.2|4    +2.5|6   -13.9|2    +1.4|2    +1.1|0    +2.8|0    +8.8|1 |   +20.2    32
 2020 |    -6.1|0    +1.7|1    -8.5|0   +16.7|0   +4.0|18    +5.3|3    +6.9|5   +10.2|1    -7.1|3    +0.8|0   +35.7|0   +19.2|1 |   +99.3    32
```

### s12 R>=40 — size 4%  (Final $134,458)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.7|25   +13.6|0    -2.7|0    +1.5|0    +9.7|0    +2.5|0    +4.6|0    -3.7|0   +16.5|0    -2.4|0 |   +42.3    25
 2017 |    +7.9|0    -0.9|0    -0.1|4    -0.2|0    +0.4|6    +4.9|3    +1.7|5    +0.4|5    +3.7|1    +2.5|0    +2.7|0    +2.6|0 |   +28.4    24
 2018 |    +2.4|0    -2.6|0    +4.2|1    +3.8|3    +9.2|4    -0.4|4    +0.5|2    +6.6|2    +0.7|1    -8.1|1    +1.0|0   -15.2|2 |    -0.4    20
 2019 |   +13.1|0    +8.9|5    -2.2|0    +2.7|2   -12.0|2   +10.7|4    +2.6|6   -16.1|2    +1.4|2    +1.2|0    +2.3|0    +6.4|2 |   +15.9    25
 2020 |    -1.9|0    +0.2|1   -12.7|0   +24.7|0    +7.6|9    +4.5|3    +8.5|5    +9.7|2    -5.8|2    -0.7|0   +32.2|0   +20.1|2 |  +112.7    24
```

### s12 R>=40 — size 5%  (Final $117,954)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.7|19   +14.5|0    -4.3|0    +2.4|0   +10.2|0    +3.5|0    +5.7|0    -3.0|0   +17.1|0    -2.8|0 |   +47.0    19
 2017 |    +7.5|0    -2.1|0    -0.1|4    -0.3|0    +0.5|6    +6.2|3    +2.1|5    +0.2|1    +5.7|0    +0.4|0    +3.5|0    -0.3|0 |   +25.4    19
 2018 |    +3.1|0    -5.7|0    +6.4|1    +1.5|4   +10.3|4    +0.1|4    +0.8|2    +8.2|2    +1.1|1   -11.7|1    +0.5|0   -18.2|0 |    -7.2    19
 2019 |   +15.8|0   +10.2|0    -0.7|1    +2.5|2    -9.4|2   +10.0|4    +1.3|6   -17.1|2    -3.5|2    +3.6|1    +1.8|0    +7.6|0 |   +19.2    20
 2020 |    +0.5|0    -4.2|0   -13.3|0   +24.9|0   +10.8|6    +4.1|3    +6.8|6    +7.9|1    -7.6|3    +1.9|0   +28.1|0   +15.4|0 |   +92.8    19
```

### s16 R>=40 — size 4%  (Final $175,297)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.8|25   +14.0|0    -2.8|0    +3.1|0   +12.4|0    +2.0|0    +5.2|0    -4.0|0   +15.4|0    -2.5|0 |   +47.7    25
 2017 |    +7.9|0    -1.6|0    +0.1|3    -0.3|0    +0.5|4    +5.4|3    +1.2|5    +0.4|3    +4.5|3    +4.0|2    +6.3|0    +2.7|0 |   +35.4    23
 2018 |    +1.8|0    -3.1|0    +4.0|1    +4.5|2   +10.6|2    -1.6|1    +0.6|2    +8.8|1    -0.6|1    -2.7|0    +1.7|0    -9.2|1 |   +14.2    11
 2019 |    +6.4|0   +3.6|11    +0.3|2    +2.1|2   -11.5|2   +15.5|2    +4.1|2   -11.1|2    +2.1|1    +1.8|0    +5.1|0   +10.7|0 |   +29.2    24
 2020 |    -0.9|0    -4.5|1    -7.8|0   +11.4|0   +2.6|18    +5.5|1    +8.3|1    +8.3|1    -6.4|2    +2.9|0   +39.1|0   +20.0|0 |   +98.1    24
```

### s20 R>=40 — size 4%  (Final $168,677)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.3|25   +15.3|0    -5.6|0    +4.0|0   +13.1|0    +0.9|0    +5.7|0    -2.7|0   +12.7|0    -2.7|0 |   +46.1    25
 2017 |    +8.1|0    -2.3|0    -1.5|2    -0.5|0    +0.5|2    +4.0|3    +2.6|4    -3.5|3    +3.7|2    +4.7|3    +4.0|1    +3.1|2 |   +24.7    22
 2018 |    +4.0|1    -2.2|0    +3.6|1    +9.2|1    +9.7|2    -3.4|1    +1.2|2   +13.3|1    +4.4|1    -9.2|0    +5.0|0    -9.8|0 |   +25.5    10
 2019 |    +2.3|0   +2.3|11    -3.5|6    +6.5|1    -7.3|0   +15.7|2    +3.5|2    -7.8|1    -1.2|0    +2.3|1    +4.6|0    +7.1|0 |   +24.3    24
 2020 |    -2.4|0    +0.2|1    -4.6|0    +9.2|0   +0.2|18    +6.6|3    +3.7|1   +13.6|0    -5.9|0    -0.6|1   +39.3|1   +18.7|0 |   +97.9    25
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 106  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        43-43       10   +3.58    -4.37   0.818    1.300
D2        43-46       11   +1.64    -6.34   0.259    0.590
D3        46-50       10   +2.01    -5.49   0.366    0.811
D4        52-60       11   +1.40    -6.06   0.230    0.553
D5        60-66       11   +2.38    -5.70   0.417    0.827
D6        66-70       10   +3.63    -6.13   0.593    1.344
D7        70-83       11   +4.16    -6.47   0.642    1.202
D8        83-87       10   +9.59    -8.37   1.146    2.182
D9        87-100      11   +8.30    -5.35   1.551    1.970
D10      100-100      11   +5.24   -16.62   0.316    0.928
```

### s16  (bk50d_s16_v2.0)

Trades scored: 107  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       10   +4.81    -3.43   1.402    1.679
D2        43-44       11   +3.13    -4.64   0.675    1.143
D3        46-49       11   +3.34    -4.96   0.673    1.475
D4        49-56       10   +1.13    -9.35   0.121    0.336
D5        57-64       11   +4.33    -4.78   0.905    1.422
D6        64-70       11   +2.65    -8.73   0.303    0.852
D7        70-77       10   +2.75    -5.28   0.522    0.926
D8        83-83       11   +6.59   -12.33   0.535    1.797
D9        87-100      11   +8.46    -5.28   1.602    1.998
D10      100-100      11   +5.22   -16.85   0.310    0.862
```

### s12  (bk50d_s12_v2.0)

Trades scored: 118  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-40       11   +0.64    -8.86   0.073    0.267
D2        40-43       12   +4.60    -7.62   0.604    1.473
D3        43-44       12   +1.33    -8.98   0.148    0.471
D4        46-49       12   +2.96    -8.74   0.339    1.018
D5        50-56       12   +2.35    -7.84   0.300    0.762
D6        56-60       11   +2.71    -4.95   0.548    1.150
D7        60-66       12   +1.62   -11.11   0.145    0.488
D8        66-74       12   +2.37    -8.68   0.273    0.724
D9        77-87       12  +11.36    -7.49   1.516    2.318
D10       87-100      12   +6.47   -14.40   0.449    1.177
```

## Findings (2026-07-30 run, 2016-01-01 – 2020-12-31 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.

**What changed in this run.** Each config is now reported twice — through the `MIN_RANKING >= 40`
gate and with no ranking condition. This is also the first portfolio run on the 40/35/25
`QullamaggieRanking` weights (changed 2026-07-29), so the gated figures moved against the previously
committed tables. The bar load bound added in the same pass has no measurable effect (verified
byte-for-byte on the 2010-2015 window), and the limit-order entry comparison was removed.

1. **The ranking gate wins all nine cells, but modestly** — mean +3.01pp CAGR, range +0.76 to
   +7.92pp. This sits exactly between the two other windows (−4.86pp in 2010-2015, +12.09pp in
   2021-2026), and it is the middle term of a monotone progression: the gate's value tracks how
   recent the window is, not how many signals it has.
2. **Here the gate's real contribution is drawdown, not return.** At s12 it cuts MaxDD from
   −45.23% / −47.10% / −43.71% (ungated, 3/4/5%) to −33.74% / −26.24% / −23.63%. A ~20pp reduction
   at roughly equal CAGR is the strongest single argument for the gate anywhere in this study — and
   it does *not* reproduce in 2021-2026, where gated s12 drawdown is the worse of the two.
3. **s16 is the best config gated** (+35.57% at 5%), s16 also ungated (+33.83% at 4%). The clean
   s12 > s16 > s20 ordering of 2021-2026 does not survive this window under either treatment, so
   "looser is better" remains a property of the recent tape.
4. **Every gated cell beats both benchmarks** (SPY +13.23%, QQQ +23.46%) — the only window where
   that is true of all nine.
5. **23-41% of capital sits uninvested gated**, against 11-26% ungated, alongside skip counts far
   below 2021-2026's: signal supply is still closer to the binding constraint than liquidity.
6. **The deciles are non-monotone at the top**: s12's D9 returns +10.30% standalone with Calmar
   2.131, against D10's +4.44% and 0.322. On 10-11 trades per decile that is not evidence the score
   inverts, only that it does not resolve at this sample size.

**How to read this window:** its absolute figures are the most flattering of the three and the least
trustworthy — the universe is fixed by a 2026 market-cap snapshot, and the 366d holds on 2020 signals
exit into 2021, a year outside the window. Its most useful contribution is the drawdown result in
point 2, which is the one gate benefit that is not a pure bull-market amplifier.
