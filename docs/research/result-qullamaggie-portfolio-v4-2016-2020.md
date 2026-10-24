# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-10-24 18:27:38 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2016-01-01 – 2020-12-31 |
| Hold | 366d (calendar) |
| Algorithms | bk50d_s20_v2.0 (%abv_SMA50>20%), bk50d_s16_v2.0 (%abv_SMA50>16%), bk50d_s12_v2.0 (%abv_SMA50>12%) |
| Entry | next trading day's split/dividend-adjusted open |
| Initial equity | $30,000 |
| Position sizing | 3%, 4%, 5% of portfolio per trade |
| Ranking gate | QullamaggieRanking >= 44, reported against an ungated run of the same signals |
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

**Ranking gate:** `QullamaggieRanking >= 44` drops 190 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        118,584  +31.68   -23.84   1.329    1.818    139    772   24.0%
3%     ungated      118,737  +31.71   -25.45   1.246    1.822    144    957   21.9%
4%     R>=44        129,077  +33.93   -27.33   1.242    1.859    107    804   22.6%
4%     ungated      123,224  +32.69   -29.11   1.123    1.837    112    989   19.7%
5%     R>=44        116,564  +31.23   -31.87   0.980    1.717     87    824   21.7%
5%     ungated      139,017  +35.94   -32.06   1.121    1.929     88   1013   19.2%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 699 signals (1 with no fillable next-day open); ungated drops 0 (4 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        145,603  +37.20   -24.68   1.507    2.065    141    842   22.6%
3%     ungated      122,617  +32.56   -44.02   0.740    1.663    159   1520   12.8%
4%     R>=44        121,047  +32.22   -31.21   1.032    1.802    109    874   20.0%
4%     ungated      106,397  +28.85   -47.52   0.607    1.437    123   1556   11.0%
5%     R>=44        124,234  +32.91   -32.20   1.022    1.779     88    895   19.1%
5%     ungated      116,689  +31.25   -42.22   0.740    1.556     97   1582   11.7%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 1404 signals (1 with no fillable next-day open); ungated drops 0 (4 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        139,170  +35.97   -22.66   1.587    2.035    141    866   22.6%
3%     ungated       91,249  +24.95   -46.31   0.539    1.271    164   2244    9.2%
4%     R>=44        146,279  +37.33   -25.13   1.485    2.059    109    898   20.3%
4%     ungated       86,328  +23.57   -46.50   0.507    1.189    121   2287    9.6%
5%     R>=44        156,170  +39.14   -30.09   1.301    2.058     88    919   18.7%
5%     ungated       94,345  +25.78   -49.51   0.521    1.244     96   2312    9.7%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=44             5%     156,170  +39.14   -30.09   1.301    2.058     88    919   18.7%
 2  s12 R>=44             4%     146,279  +37.33   -25.13   1.485    2.059    109    898   20.3%
 3  s16 R>=44             3%     145,603  +37.20   -24.68   1.507    2.065    141    842   22.6%
 4  s12 R>=44             3%     139,170  +35.97   -22.66   1.587    2.035    141    866   22.6%
 5  s20 ungated           5%     139,017  +35.94   -32.06   1.121    1.929     88   1013   19.2%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=44             3%     145,603  +37.20   -24.68   1.507    2.065    141    842   22.6%
 2  s12 R>=44             4%     146,279  +37.33   -25.13   1.485    2.059    109    898   20.3%
 3  s12 R>=44             5%     156,170  +39.14   -30.09   1.301    2.058     88    919   18.7%
 4  s12 R>=44             3%     139,170  +35.97   -22.66   1.587    2.035    141    866   22.6%
 5  s20 ungated           5%     139,017  +35.94   -32.06   1.121    1.929     88   1013   19.2%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2016      43,972  +46.57   -10.45   4.459    2.726     33    155   22.2%
                    2017      51,479  +17.07    -6.95   2.456    1.750     31     14   40.8%
                    2018      61,888  +20.22   -15.33   1.319    1.292     13     16   19.0%
                    2019      80,345  +29.82   -13.88   2.149    1.906     32     50   12.1%
                    2020     139,170  +73.21   -22.66   3.231    2.412     32    631   18.7%
s12 R>=44 4%        2016      44,283  +47.61   -11.81   4.031    2.724     25    163   20.7%
                    2017      52,593  +18.77    -6.75   2.778    1.875     23     22   34.9%
                    2018      60,279  +14.61   -17.24   0.848    0.913     13     16   19.7%
                    2019      80,071  +32.83   -16.37   2.006    2.039     24     58   10.9%
                    2020     146,279  +82.69   -25.13   3.290    2.592     24    639   15.3%
s12 R>=44 5%        2016      42,705  +42.35   -10.78   3.929    2.514     19    169   23.4%
                    2017      52,499  +22.93    -7.37   3.111    2.201     19     26   30.3%
                    2018      58,296  +11.04   -19.02   0.581    0.618     12     17   17.9%
                    2019      72,917  +25.08   -19.48   1.287    1.490     19     63    8.8%
                    2020     156,170 +114.17   -30.09   3.794    3.112     19    644   13.2%
s16 R>=44 3%        2016      43,594  +45.31   -10.71   4.232    2.673     33    143   22.3%
                    2017      50,863  +16.67    -7.30   2.282    1.749     31     12   42.3%
                    2018      63,970  +25.77   -14.68   1.755    1.542     11     16   17.4%
                    2019      86,538  +35.28   -11.75   3.003    2.253     33     45   12.9%
                    2020     145,603  +68.25   -24.68   2.765    2.257     33    626   18.0%
s20 ungated 5%      2016      44,505  +48.35   -11.56   4.183    2.795     19    166   23.6%
                    2017      56,569  +27.11    -9.25   2.929    2.507     19     24   31.2%
                    2018      54,810   -3.11   -23.74  -0.131   -0.225     11     20   17.9%
                    2019      64,587  +17.84   -14.28   1.249    1.082     20     71    9.8%
                    2020     139,017 +115.24   -32.06   3.595    3.111     19    732   13.7%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $139,170)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|33   +13.0|0    -3.1|0    +4.0|0   +10.5|0    +2.6|0    +4.6|0    -3.5|0   +14.3|0    -1.6|0 |   +46.6    33
 2017 |    +6.4|0    -1.4|0    -0.2|2    +0.2|0    +0.4|3    +3.4|3    -0.0|4    +0.1|4    +0.9|5    -0.4|8    +5.5|1    +1.2|1 |   +17.1    31
 2018 |    +0.7|0    -6.7|0    +3.4|0    +7.4|3   +13.3|4    -1.8|3    +6.3|0   +11.9|1    -0.2|1    -6.5|0    -0.0|0    -6.6|1 |   +20.2    13
 2019 |    +6.9|0   +2.2|15    +1.1|5    -1.1|2    -8.2|2   +14.0|3    +1.5|1    -5.6|3    -0.1|0    +2.7|0    +4.1|0   +10.8|1 |   +29.8    32
 2020 |    -5.0|0    -1.3|1    -7.8|0    +7.2|0   +2.0|24    +3.6|3    +4.2|1   +14.2|3    -6.6|0    -1.9|0   +38.6|0   +17.0|0 |   +73.2    32
```

### s12 R>=44 — size 4%  (Final $146,279)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.2|25   +12.3|0    -1.0|0    +0.6|0    +9.4|0    +4.0|0    +4.8|0    -3.8|0   +17.9|0    -1.3|0 |   +47.6    25
 2017 |    +6.3|0    -1.5|0    -0.1|2    +0.3|0    +0.6|3    +4.6|3    -0.1|4    +0.2|4    +1.2|5    -1.3|2    +6.3|0    +1.2|0 |   +18.8    23
 2018 |    +1.8|0    -6.6|0    +2.9|0    +6.8|3   +12.4|4    -0.7|3    +6.0|0    +7.3|1    -1.7|1    -5.2|0    +0.4|0    -7.6|1 |   +14.6    13
 2019 |    +9.5|0   +3.3|11    +0.3|0    -1.4|2   -10.2|3   +16.0|3    +1.1|1    -5.5|2    +0.8|1    +3.4|0    +3.2|0   +10.8|1 |   +32.8    24
 2020 |    -6.7|0    +2.4|1    -9.9|0   +10.0|0   +4.3|16    +5.6|2    +5.2|1    +9.1|2    -6.0|1    -4.3|0   +41.2|0   +19.9|1 |   +82.7    24
```

### s12 R>=44 — size 5%  (Final $156,170)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.1|19   +10.8|0    -2.4|0    +1.2|0   +10.2|0    +3.7|0    +5.9|0    -2.3|0   +15.0|0    -3.2|0 |   +42.4    19
 2017 |    +6.2|0    -2.8|0    +1.3|2    +0.4|0    +0.7|3    +5.7|3    -0.1|4    +0.2|4    +1.4|3    -0.9|0    +7.6|0    +1.6|0 |   +22.9    19
 2018 |    +2.0|0    -5.9|0    +1.1|0    +7.3|3   +13.9|3    -3.4|3    +6.2|0    +7.0|1    -2.0|1    -5.6|0    +1.3|0    -9.1|1 |   +11.0    12
 2019 |   +11.2|0    +4.1|7    +1.0|0    -2.2|2   -13.3|3   +13.2|3    -0.5|1    -6.0|2    +2.6|1    +2.6|0    +3.8|0    +9.0|0 |   +25.1    19
 2020 |    -1.7|0    +1.1|1   -11.3|0   +12.5|0   +7.8|11    +4.4|3    +7.3|1   +10.1|1    -7.3|2    +2.0|0   +40.9|0   +22.0|0 |  +114.2    19
```

### s16 R>=44 — size 3%  (Final $145,603)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.0|33   +12.6|0    -3.5|0    +3.4|0   +11.4|0    +2.5|0    +5.1|0    -3.7|0   +13.6|0    -1.4|0 |   +45.3    33
 2017 |    +6.3|0    -1.7|0    -0.6|2    +0.2|0    +0.4|3    +3.4|3    -0.1|4    +0.0|3    +1.4|5    +0.1|7    +5.0|1    +1.4|3 |   +16.7    31
 2018 |    +3.0|0    -6.3|0    +5.2|0    +9.5|3   +10.7|3    -2.5|3    +5.8|0   +11.7|1    +0.1|1    -7.3|0    +2.3|0    -6.6|0 |   +25.8    11
 2019 |    +5.8|0   +1.7|17    -0.1|5    +0.7|2    -6.3|3   +17.0|3    +3.0|0    -6.5|3    +0.1|0    +3.3|0    +4.1|0    +9.9|0 |   +35.3    33
 2020 |    -4.7|0    -2.9|2    -9.3|0    +7.9|0   +1.9|25    +1.9|3    +4.5|0   +15.0|3    -6.2|0    -2.0|0   +38.6|0   +16.8|0 |   +68.3    33
```

### s20 ungated — size 5%  (Final $139,017)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.0|19    +9.8|0    -1.0|0    -0.8|0   +11.0|0    +5.1|0    +3.8|0    -1.6|0   +18.0|0    -2.2|0 |   +48.3    19
 2017 |    +7.0|0    -3.0|0    -0.1|2    -0.6|0    +0.6|2    +4.7|4    +3.7|4    -3.3|3    +4.3|4    +2.0|0    +7.8|0    +1.9|0 |   +27.1    19
 2018 |    +3.1|0    -5.1|0    +1.9|1    +2.6|1   +10.7|3    +0.7|3    +0.8|1    +6.4|1    +0.7|1   -10.3|0    -0.5|0   -11.9|0 |    -3.1    11
 2019 |    +8.8|0    +8.1|9    -4.1|0    +3.6|2    -9.4|2    +7.9|4    -0.0|1    -5.4|1    +0.4|0    +2.8|1    +2.2|0    +3.4|0 |   +17.8    20
 2020 |    +7.2|0    +0.0|1   -15.0|0    +9.8|0  +10.4|10    +4.0|5    +8.1|0   +12.9|1    -5.6|0    -6.8|2   +42.6|0   +22.2|0 |  +115.2    19
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 107  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-45       10   +1.89    -4.07   0.464    0.851
D2        46-47       11   +2.88    -5.29   0.544    1.016
D3        50-51       11   +1.66    -6.04   0.275    0.657
D4        51-54       10   +1.53    -5.15   0.298    0.677
D5        54-61       11   +2.87    -7.77   0.369    0.996
D6        61-65       11   +1.81    -7.72   0.235    0.632
D7        65-68       10   +8.27    -9.91   0.835    2.030
D8        71-93       11   +3.73    -3.40   1.097    1.207
D9        96-100      11   +5.11   -11.00   0.465    1.034
D10      100-100      11   +5.24   -16.62   0.316    0.928
```

### s16  (bk50d_s16_v2.0)

Trades scored: 109  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +2.81    -4.06   0.692    1.099
D2        44-46       11   +2.42   -12.94   0.187    0.621
D3        46-47       11   +2.50   -10.28   0.243    0.862
D4        47-51       11   +1.09    -7.35   0.149    0.454
D5        51-54       11   +2.02    -4.84   0.418    0.846
D6        55-61       11   +5.27    -5.28   0.999    1.814
D7        61-65       11   +1.37    -7.65   0.179    0.533
D8        65-75       11   +4.71   -11.30   0.417    1.481
D9        79-100      11   +5.08    -7.52   0.675    1.429
D10      100-100      11   +5.76   -16.62   0.347    1.013
```

### s12  (bk50d_s12_v2.0)

Trades scored: 109  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +3.07    -6.65   0.462    1.116
D2        44-46       11   +2.98    -7.32   0.408    1.008
D3        46-47       11   +5.15    -4.60   1.120    1.726
D4        47-50       11   +2.27    -7.54   0.301    0.776
D5        51-55       11   +2.67    -5.93   0.450    1.095
D6        55-61       11   +3.75    -9.08   0.413    1.269
D7        61-65       11   +0.53   -11.64   0.045    0.209
D8        65-89       11   +6.83    -7.63   0.896    2.079
D9        89-100      11   +4.65    -9.36   0.497    1.215
D10      100-100      11   +5.76   -16.62   0.347    1.013
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
