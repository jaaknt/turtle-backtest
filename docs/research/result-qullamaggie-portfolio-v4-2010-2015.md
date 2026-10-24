# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-10-24 22:53:04 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2010-01-01 – 2015-12-31 |
| Hold | 366d (calendar) |
| Algorithms | bk50d_s20_v2.0 (%abv_SMA50>20%), bk50d_s16_v2.0 (%abv_SMA50>16%), bk50d_s12_v2.0 (%abv_SMA50>12%) |
| Entry | next trading day's split/dividend-adjusted open |
| Initial equity | $30,000 |
| Position sizing | 3%, 4%, 5% of portfolio per trade |
| Ranking gate | QullamaggieRanking >= 55 and >= 44, reported against an ungated run of the same signals |
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
SPY         53,967  +10.30   -19.42   0.530    0.981
QQQ         72,292  +15.81   -16.09   0.983    1.327
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 142 signals (0 with no fillable next-day open); `R>=44` drops 34 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55         52,604   +9.83   -18.16   0.541    0.962    102      0   50.3%
3%     R>=44         74,047  +16.28   -25.89   0.629    1.169    146     64   29.9%
3%     ungated       73,081  +16.02   -27.42   0.584    1.176    151     93   27.9%
4%     R>=55         56,583  +11.17   -23.38   0.478    0.915     94      8   39.9%
4%     R>=44         76,323  +16.86   -28.04   0.601    1.167    120     90   24.4%
4%     ungated       70,694  +15.38   -23.72   0.648    1.082    123    121   22.9%
5%     R>=55         60,046  +12.28   -25.51   0.481    0.904     87     15   31.5%
5%     R>=44         70,870  +15.43   -26.93   0.573    1.040    101    109   21.7%
5%     ungated       70,527  +15.33   -24.08   0.637    1.025    102    142   21.2%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 433 signals (0 with no fillable next-day open); `R>=44` drops 268 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55         47,636   +8.02   -19.93   0.402    0.781    104      2   49.7%
3%     R>=44         70,220  +15.25   -27.31   0.558    1.070    158    113   24.4%
3%     ungated       81,826  +18.23   -24.13   0.756    1.193    184    355   13.8%
4%     R>=55         52,456   +9.77   -23.42   0.417    0.800     96     10   38.8%
4%     R>=44         74,018  +16.27   -26.44   0.615    1.081    126    145   20.8%
4%     ungated       65,466  +13.91   -26.98   0.516    0.927    142    397   11.9%
5%     R>=55         57,789  +11.56   -27.39   0.422    0.826     88     18   29.3%
5%     R>=44         64,573  +13.65   -29.73   0.459    0.914    102    169   18.8%
5%     ungated       67,070  +14.37   -34.08   0.422    0.918    117    422   11.0%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 928 signals (0 with no fillable next-day open); `R>=44` drops 732 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55         51,794   +9.54   -19.93   0.479    0.909    104      0   49.0%
3%     R>=44         62,974  +13.17   -27.99   0.471    0.912    164    136   22.4%
3%     ungated       61,045  +12.59   -34.47   0.365    0.839    196    836    6.2%
4%     R>=55         58,633  +11.83   -23.93   0.495    0.937     96      8   37.7%
4%     R>=44         64,735  +13.70   -32.56   0.421    0.913    127    173   19.2%
4%     ungated       70,599  +15.35   -34.97   0.439    0.959    148    884    4.7%
5%     R>=55         64,992  +13.77   -27.39   0.503    0.957     88     16   28.4%
5%     R>=44         62,494  +13.03   -33.72   0.386    0.863    101    199   18.6%
5%     ungated       73,591  +16.16   -35.19   0.459    0.991    119    913    3.8%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      81,826  +18.23   -24.13   0.756    1.193    184    355   13.8%
 2  s20 R>=44             4%      76,323  +16.86   -28.04   0.601    1.167    120     90   24.4%
 3  s20 R>=44             3%      74,047  +16.28   -25.89   0.629    1.169    146     64   29.9%
 4  s16 R>=44             4%      74,018  +16.27   -26.44   0.615    1.081    126    145   20.8%
 5  s12 ungated           5%      73,591  +16.16   -35.19   0.459    0.991    119    913    3.8%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      81,826  +18.23   -24.13   0.756    1.193    184    355   13.8%
 2  s20 ungated           3%      73,081  +16.02   -27.42   0.584    1.176    151     93   27.9%
 3  s20 R>=44             3%      74,047  +16.28   -25.89   0.629    1.169    146     64   29.9%
 4  s20 R>=44             4%      76,323  +16.86   -28.04   0.601    1.167    120     90   24.4%
 5  s20 ungated           4%      70,694  +15.38   -23.72   0.648    1.082    123    121   22.9%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2010      34,647  +15.49   -15.84   0.978    1.367     33     28   43.6%
                    2011      32,430   -6.40   -27.33  -0.234   -0.282     33     22   29.0%
                    2012      36,841  +13.60   -19.32   0.704    0.941     11     64   16.1%
                    2013      57,337  +55.63    -9.22   6.033    3.776     24      0   28.0%
                    2014      67,774  +18.20   -15.89   1.146    1.155     33      7   10.8%
                    2015      62,974   -7.08   -27.99  -0.253   -0.084     30     15    6.9%
s12 R>=44 4%        2010      34,228  +14.09   -20.82   0.677    1.068     25     36   32.5%
                    2011      31,033   -9.33   -27.85  -0.335   -0.521     24     31   37.8%
                    2012      35,492  +14.37   -20.53   0.700    0.945     12     63   15.1%
                    2013      60,131  +69.42   -10.19   6.811    3.944     18      6   18.0%
                    2014      74,158  +23.33   -16.61   1.405    1.337     24     16    6.4%
                    2015      64,735  -12.71   -32.56  -0.390   -0.325     24     21    5.5%
s12 R>=44 5%        2010      33,104  +10.35   -23.74   0.436    0.757     19     42   25.4%
                    2011      29,735  -10.18   -25.81  -0.394   -0.665     20     35   47.2%
                    2012      34,958  +17.56   -17.64   0.995    1.117     11     64   14.6%
                    2013      61,498  +75.92   -10.89   6.973    3.966     14     10   13.9%
                    2014      67,886  +10.39   -20.06   0.518    0.681     19     21    5.0%
                    2015      62,494   -7.94   -33.72  -0.236   -0.077     18     27    5.3%
s16 ungated 3%      2010      37,555  +25.18   -21.59   1.167    1.375     32     97   12.2%
                    2011      33,642  -10.42   -22.92  -0.455   -0.595     34     60   34.9%
                    2012      40,945  +21.71   -14.95   1.452    1.528     28     94   14.0%
                    2013      71,185  +73.85    -7.33  10.081    4.097     25     18    7.2%
                    2014      85,247  +19.75   -16.09   1.228    1.285     32     26    8.4%
                    2015      81,826   -4.01   -24.13  -0.166   -0.067     33     60    5.9%
s20 R>=44 4%        2010      33,532  +11.77   -19.53   0.603    0.891     24     25   30.2%
                    2011      30,334   -9.54   -28.04  -0.340   -0.547     25     10   38.1%
                    2012      37,751  +24.45   -15.16   1.613    1.732     10     44   18.1%
                    2013      59,607  +57.90    -6.42   9.012    4.114     18      0   28.4%
                    2014      73,917  +24.01   -12.70   1.890    1.509     24      0   13.9%
                    2015      76,323   +3.25   -24.72   0.132    0.377     19     11   17.8%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $62,974)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.0|7    +3.4|3    +1.6|0    +0.6|5    -4.0|0    -4.3|0    +3.1|1    -8.5|6   +12.4|7    +5.3|4    +0.6|0    +9.2|0 |   +15.5    33
 2011 |    +1.7|1    +6.7|1    +3.7|1    +3.7|0    +0.1|0    -1.4|1    -2.6|1    -9.1|0    -6.3|0   +2.3|28    -3.0|0    -1.4|0 |    -6.4    33
 2012 |   +10.2|1    +3.2|0    +1.2|0    -3.3|0   -11.5|0    +5.6|3    -0.4|1    +3.9|0    +3.6|0    -1.1|0    +2.1|2    +1.0|4 |   +13.6    11
 2013 |    +2.3|1    +0.6|3    +2.6|3    +3.6|2   +11.5|6    +6.0|2    +4.2|1    +3.4|2    +5.8|1    -3.2|1    +7.6|1    +1.4|1 |   +55.6    24
 2014 |    +3.2|5    +3.2|6    -3.3|5    +1.6|1    -0.3|1    +8.3|3    -0.6|2    +6.1|2    -2.2|2    -5.1|1    -0.4|3    +7.1|2 |   +18.2    33
 2015 |    +0.2|2   +11.5|6    -0.1|4    -3.0|3    +6.1|1    +0.7|1    +1.5|4   -12.1|0   -12.7|0    +5.8|1    +5.2|5    -7.4|3 |    -7.1    30
```

### s12 R>=44 — size 4%  (Final $64,735)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.0|7    +4.6|3    +2.1|0    +0.8|5    -5.3|0    -5.8|0    +4.3|1   -11.5|6   +16.6|3    +4.8|0    +0.6|0    +9.1|0 |   +14.1    25
 2011 |    +2.1|1    +5.8|1    +3.5|1    +1.8|0    -1.9|0    -1.6|1    -1.9|1    -7.8|0    -4.3|0   +0.4|19    -4.0|0    -0.9|0 |    -9.3    24
 2012 |   +10.7|1    +2.0|0    +0.8|1    -2.0|0   -13.3|0    +6.2|3    -0.8|1    +3.9|0    +4.8|0    -1.5|0    +3.0|2    +1.8|4 |   +14.4    12
 2013 |    +3.6|1    +0.8|3    +3.4|3    +4.7|2   +14.8|4    +6.8|0    +4.2|1    +2.4|2    +7.0|1    -3.0|0    +8.4|0    +1.8|1 |   +69.4    18
 2014 |    +5.5|5    +4.0|6    -5.7|3    +0.1|1    +0.9|1    +8.2|3    -2.3|2   +10.8|1    -4.4|0    -2.5|1    -0.8|1    +9.0|0 |   +23.3    24
 2015 |    -0.7|3   +10.6|6    -0.7|2    -2.7|3    +7.6|0    -0.4|1    -0.3|5   -13.7|0   -15.4|0    +4.3|1    +9.4|3    -7.6|0 |   -12.7    24
```

### s12 R>=44 — size 5%  (Final $62,494)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -5.0|7    +5.8|3    +2.6|0    +1.0|5    -6.6|0    -7.3|0    +5.5|1   -12.6|3   +17.7|0    +2.7|0    +1.0|0    +8.8|0 |   +10.3    19
 2011 |    +1.5|1    +4.7|1    +3.6|1    +1.4|0    -1.9|0    -1.4|1    -0.5|1    -5.5|0    -4.5|0   +1.4|14    -6.2|0    -2.6|1 |   -10.2    20
 2012 |   +11.4|1    +2.5|0    +1.6|0    -1.9|0   -10.7|0    +5.8|3    -0.8|1    +2.8|0    +3.8|0    -1.6|0    +3.4|2    +1.5|4 |   +17.6    11
 2013 |    +3.7|1    +0.9|3    +4.2|3    +5.9|2   +17.2|0    +8.0|0    +3.8|1    +2.1|2    +7.1|0    -3.3|0    +7.8|1    +1.6|1 |   +75.9    14
 2014 |    +5.9|4    +1.5|6    -4.7|3    +0.9|1    -2.0|1    +7.9|1    -0.3|0   +10.6|1    -7.3|1    -5.0|0    -4.5|0    +8.8|1 |   +10.4    19
 2015 |    -1.5|4    +7.9|5    +6.8|2    -4.3|3    +9.1|1    +4.9|1    +1.1|0   -15.7|0   -16.1|0    +4.1|1    +8.3|1    -8.3|0 |    -7.9    18
```

### s16 ungated — size 3%  (Final $81,826)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -5.7|16    +6.8|5    +5.9|2    +3.2|9    -6.5|0    -8.9|0    +9.6|0    -9.4|0   +15.7|0    +4.1|0    +3.9|0    +7.5|0 |   +25.2    32
 2011 |    +1.2|8    +1.4|1    +0.9|3    +0.6|3    -1.0|3    -3.5|1    -0.6|1    -4.8|0    -7.8|0   +7.9|14    -4.0|0    -0.4|0 |   -10.4    34
 2012 |    +9.3|8    +3.1|0    -0.0|0    -1.5|0    -9.7|0    +4.8|1   +1.2|11    +1.8|0    +5.1|0    -1.5|0    +4.2|3    +4.3|5 |   +21.7    28
 2013 |    +3.7|8    +0.9|4    +6.0|0    +4.0|0   +15.3|0    +3.0|2    +6.0|3    +4.3|3    +7.8|2    -1.6|1    +6.9|1    +1.1|1 |   +73.9    25
 2014 |    +4.2|6    +5.1|4    -3.9|7    +1.0|3    -0.8|0    +9.8|1    -1.6|3    +5.3|2    -3.0|1    -2.8|1    +1.3|3    +4.6|1 |   +19.8    32
 2015 |    +2.0|5    +5.6|5    +0.5|6    -1.7|5    +5.7|0    +0.7|0    -0.3|2    -9.9|1    -9.5|0    +7.1|3    +4.2|6    -6.5|0 |    -4.0    33
```

### s20 R>=44 — size 4%  (Final $76,323)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.7|7    +4.9|3    +2.9|0    +0.3|7    -5.1|0    -6.6|0    +4.1|0    -9.0|5   +14.1|2    +2.1|0    +0.8|0    +8.8|0 |   +11.8    24
 2011 |    +1.3|1    +7.2|1    +2.6|1    +3.9|2    -2.3|0    -2.4|1    -1.9|1    -6.2|0    -6.2|0   +1.5|17    -4.3|1    -2.3|0 |    -9.5    25
 2012 |   +10.6|1    +3.5|0    +2.1|0    -0.6|0    -9.4|0    +4.5|1    +0.4|4    +4.8|0    +4.8|0    -0.6|0    +1.0|1    +2.1|3 |   +24.5    10
 2013 |    +2.4|2    +0.4|2    +5.6|0    +6.1|2    +7.0|3    +5.7|2    +4.5|1    -0.0|2    +9.6|1    -2.4|1    +8.0|1    +0.5|1 |   +57.9    18
 2014 |    +5.7|3    +5.6|2    -2.0|4    +1.8|3    -1.7|1    +6.8|2    +0.4|2    +3.8|1    -2.1|1    -3.7|1    +3.0|2    +4.9|2 |   +24.0    24
 2015 |    +3.8|2   +10.9|2    +1.1|1    -4.4|3    +6.6|2    +3.4|1    +3.0|2   -11.1|0   -11.0|0    +0.7|0    +8.6|3    -5.5|3 |    +3.3    19
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return. Each config is decomposed once per gated signal set, strictest gate first as in the size sweep: the deciles split the trades that gate's own run took, so each table spans only that gate..100 and reads against the matching size-sweep row.

### s20 R>=55  (bk50d_s20_v2.0)

Trades scored: 94  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55        9   +2.54    -5.64   0.451    1.103
D2        55-57        9   +2.15    -5.83   0.369    1.032
D3        58-58       10   +0.02    -5.05   0.004    0.030
D4        58-61        9   +0.41   -10.46   0.039    0.168
D5        61-61       10   +3.83    -7.01   0.545    1.150
D6        61-65        9   -0.43    -7.98  -0.054   -0.209
D7        65-65        9   +0.56    -6.49   0.086    0.264
D8        65-75       10   -0.44    -6.24  -0.070   -0.194
D9        75-82        9   +0.96    -6.05   0.159    0.427
D10       86-100      10   +2.35    -5.38   0.437    0.814
```

### s20 R>=44  (bk50d_s20_v2.0)

Trades scored: 120  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       12   +1.06    -7.45   0.143    0.467
D2        46-47       12   +0.72    -8.47   0.085    0.311
D3        47-50       12   +3.54    -4.96   0.712    1.405
D4        50-54       12   +6.10    -5.46   1.116    2.323
D5        54-55       12   +2.85   -10.73   0.266    0.787
D6        55-58       12   +1.47    -5.39   0.273    0.667
D7        58-61       12   +1.23    -6.61   0.185    0.544
D8        61-65       12   +0.32    -7.50   0.042    0.153
D9        65-75       12   -0.18    -6.14  -0.029   -0.054
D10       79-100      12   +1.49    -8.08   0.184    0.494
```

### s16 R>=55  (bk50d_s16_v2.0)

Trades scored: 96  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55        9   +2.05    -5.98   0.343    0.880
D2        57-57       10   +2.09    -5.41   0.386    0.856
D3        57-58        9   -0.22    -6.95  -0.031   -0.067
D4        58-61       10   -0.04    -5.36  -0.007   -0.002
D5        61-61       10   +3.72    -6.21   0.599    1.085
D6        61-61        9   +0.46    -7.96   0.057    0.248
D7        65-65       10   +0.31    -6.49   0.048    0.156
D8        65-75        9   -0.85    -8.51  -0.099   -0.448
D9        75-82       10   +0.68    -6.05   0.112    0.288
D10       86-100      10   +2.35    -5.38   0.437    0.814
```

### s16 R>=44  (bk50d_s16_v2.0)

Trades scored: 126  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-45       12   +1.62    -5.51   0.294    0.695
D2        46-47       13   +1.51    -7.39   0.204    0.539
D3        47-49       12   +4.44    -5.66   0.785    1.491
D4        50-51       13   +3.27    -5.21   0.628    1.154
D5        51-54       13   +2.11    -8.72   0.242    0.879
D6        54-57       12   +1.51    -8.02   0.188    0.482
D7        57-61       13   +1.37    -4.89   0.280    0.554
D8        61-65       12   +0.74    -5.20   0.142    0.368
D9        65-75       13   +0.43    -6.68   0.064    0.180
D10       75-100      13   +1.16    -8.16   0.143    0.377
```

### s12 R>=55  (bk50d_s12_v2.0)

Trades scored: 96  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57        9   +3.47    -7.40   0.469    1.305
D2        57-57       10   +2.09    -4.87   0.428    0.861
D3        57-58        9   +0.07    -5.05   0.014    0.054
D4        58-61       10   -0.22    -7.32  -0.030   -0.079
D5        61-61       10   +2.83    -6.10   0.464    0.932
D6        61-65        9   +0.26    -7.19   0.036    0.158
D7        65-65       10   +0.51    -6.65   0.076    0.241
D8        68-75        9   -1.08    -9.91  -0.109   -0.522
D9        75-86       10   +1.03    -6.05   0.170    0.420
D10       86-100      10   +3.64    -8.21   0.444    1.015
```

### s12 R>=44  (bk50d_s12_v2.0)

Trades scored: 127  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       12   +0.63    -6.40   0.099    0.289
D2        44-46       13   +1.00    -7.14   0.140    0.393
D3        47-47       13   +1.61    -6.93   0.233    0.595
D4        47-50       12   +4.46    -7.24   0.616    1.660
D5        50-51       13   +3.15    -7.38   0.426    1.149
D6        51-55       13   +0.89    -9.68   0.092    0.301
D7        55-58       12   +2.00    -5.21   0.384    0.774
D8        58-61       13   +0.92    -6.17   0.150    0.405
D9        65-75       13   -0.26    -6.57  -0.040   -0.063
D10       75-100      13   +1.52    -7.64   0.199    0.488
```

## Findings (2026-07-30 run, 2010-01-01 – 2015-12-31 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.
>
> **2026-10-24:** the tables now carry three rows per sizing — `R>=55`, `R>=44` and ungated — and
> the gate is `MIN_RANKING >= 44`, not the `>= 40` the text below refers to. The R>=55 comparison
> is summarised in the next subsection; everything after it is the original 2026-07-30 text.

### R>=55 against R>=44 (2026-10-24 run)

Across the 9 config/size cells, R>=55 minus R>=44 CAGR averages **−3.99pp** and wins **1 of 9**
(range −7.23 to +0.74pp); Sortino is better in only 2 of 9. For the reference `s12` the deltas at
3/4/5% sizing are −3.63 / −1.87 / +0.74pp. The stricter gate removes signals from a window that
already has too few, so uninvested capital rises from 18.6–29.9% at R>=44 to 28.4–50.3%. Its
MaxDD is shallower in all 9 cells, but that is cash, not better trades — the same artifact as
point 5 below. **Verdict here: R>=55 costs return and buys only idle-cash safety.**

The R>=55 decile tables (9-10 trades per decile) show no ordering inside 55..100: for `s12`, D1 (score
55-57, +3.47%) and D10 (86-100, +3.64%) lead while D4 (58-61, −0.22%) and D8 (68-75, −1.08%) are
negative. Nothing in 55..100
separates better than the 44..54 deciles of the R>=44 tables do, so dropping 44-54 removes
trades of similar quality rather than the weak tail.

**What changed in this run.** Each config is now reported twice — through the `MIN_RANKING >= 40`
gate and with no ranking condition. This is also the first portfolio run on the 40/35/25
`QullamaggieRanking` weights (changed 2026-07-29), so the gated figures moved against the previously
committed tables. The bar load is now bounded at the eval-window end, which for this window excludes
585 symbols that previously satisfied the 300-bar `MIN_HISTORY` check on bars printed *after* 2015;
that bound changes nothing measurable, verified by a control run reproducing the report
byte-for-byte. The limit-order entry comparison was removed from the script.

1. **The ranking gate loses in all nine cells here** — mean −4.86pp CAGR, worst −8.72pp
   (s16 @4%: +7.55% gated against +16.27% ungated). This is the exact opposite of 2021-2026, where
   the same gate wins all nine by +12.09pp on average. Whatever the score is picking up, it is not
   present in this tape.
2. **The reason is signal scarcity, not signal quality.** Gated runs leave 32-64% of capital
   uninvested with near-zero skip counts (0-35 across the nine cells) — the portfolio is idle because
   nothing qualifies, not because cash ran out. Removing the gate roughly doubles the trade count
   (s12: 107 → 182 at 3%) and puts that idle cash to work. In a window this thin, any additional
   filter costs more in foregone compounding than it saves in trade quality.
3. **Even ungated, this is the weakest of the three windows.** The best cell is ungated `s16 @4%` at
   +16.27% CAGR, marginally above QQQ buy & hold (+15.81%); every gated cell trails both QQQ and,
   at 3% sizing, SPY (+10.30%) as well. Sortino never exceeds 0.797.
4. **Ungated, looser thresholds do win** — at 3% sizing s12 +12.53% > s16 +11.80% > s20 +8.48%. That
   ordering inverts under the gate (s20 +6.45% > s16 +7.48%... s12 +5.28% worst), another sign the
   gate is mis-selecting in this period rather than merely being redundant.
5. **The gate's milder drawdowns are a cash artifact.** Gated s20 shows −14.97% against ungated
   −24.26%, but that is a portfolio half in cash, not better exits.
6. **The ranking deciles are unreadable at this sample size**: 7-10 trades each, four of s12's ten
   deciles negative, and D10 (+1.78%) barely above D2 (+1.51%).

**How to read this window:** it is the control that stops 2021-2026 being mistaken for the general
case — and it now also contradicts the gate. The strategy's edge and the ranking's edge are both
regime-dependent; in a flat tape with the regime filter on, the strategy mostly does not trade, and
filtering the little it does find makes matters worse.
