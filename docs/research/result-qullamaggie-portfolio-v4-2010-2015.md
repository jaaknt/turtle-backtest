# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-11-15 14:40:29 Tallinn time

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
QQQ         72,292  +15.82   -16.09   0.983    1.327
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 143 signals (0 with no fillable next-day open); `R>=44` drops 35 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55         52,194   +9.69   -17.11   0.566    0.964    101      0   50.8%
3%     R>=44         71,041  +15.48   -25.99   0.596    1.115    147     62   29.6%
3%     ungated       72,661  +15.92   -27.75   0.574    1.160    153     91   27.1%
4%     R>=55         56,001  +10.99   -21.83   0.503    0.916     93      8   40.6%
4%     R>=44         71,520  +15.61   -30.21   0.517    1.090    121     88   23.9%
4%     ungated       69,311  +15.01   -24.61   0.610    1.067    123    121   23.0%
5%     R>=55         60,046  +12.29   -25.51   0.482    0.904     87     14   31.5%
5%     R>=44         70,618  +15.37   -27.56   0.558    1.041    101    108   21.4%
5%     ungated       68,066  +14.66   -26.10   0.562    0.991    102    142   21.2%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 427 signals (0 with no fillable next-day open); `R>=44` drops 263 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55         47,484   +7.97   -19.93   0.400    0.794    102      2   50.6%
3%     R>=44         71,903  +15.72   -27.90   0.563    1.095    158    110   24.3%
3%     ungated       90,230  +20.19   -23.59   0.856    1.305    182    349   14.2%
4%     R>=55         53,333  +10.09   -22.64   0.445    0.835     95      9   39.2%
4%     R>=44         70,617  +15.37   -27.23   0.564    1.033    126    142   20.8%
4%     ungated       72,168  +15.79   -25.45   0.620    1.025    141    390   12.1%
5%     R>=55         56,980  +11.31   -26.70   0.423    0.822     88     16   30.0%
5%     R>=44         57,188  +11.38   -30.26   0.376    0.797    102    166   19.0%
5%     ungated       70,827  +15.43   -31.08   0.496    0.964    115    416   11.3%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 919 signals (0 with no fillable next-day open); `R>=44` drops 725 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55         51,629   +9.49   -19.92   0.476    0.926    102      0   49.9%
3%     R>=44         62,415  +13.01   -28.55   0.456    0.905    164    132   22.4%
3%     ungated       64,028  +13.50   -35.07   0.385    0.881    195    826    6.3%
4%     R>=55         58,404  +11.77   -23.40   0.503    0.957     94      8   38.9%
4%     R>=44         66,957  +14.35   -31.59   0.454    0.952    127    169   19.1%
4%     ungated       72,380  +15.84   -34.96   0.453    0.973    149    872    4.4%
5%     R>=55         64,077  +13.51   -26.49   0.510    0.955     88     14   29.0%
5%     R>=44         56,387  +11.11   -32.67   0.340    0.771    102    194   18.1%
5%     ungated       77,393  +17.15   -35.18   0.487    1.028    119    902    3.6%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      90,230  +20.19   -23.59   0.856    1.305    182    349   14.2%
 2  s12 ungated           5%      77,393  +17.15   -35.18   0.487    1.028    119    902    3.6%
 3  s20 ungated           3%      72,661  +15.92   -27.75   0.574    1.160    153     91   27.1%
 4  s12 ungated           4%      72,380  +15.84   -34.96   0.453    0.973    149    872    4.4%
 5  s16 ungated           4%      72,168  +15.79   -25.45   0.620    1.025    141    390   12.1%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      90,230  +20.19   -23.59   0.856    1.305    182    349   14.2%
 2  s20 ungated           3%      72,661  +15.92   -27.75   0.574    1.160    153     91   27.1%
 3  s20 R>=44             3%      71,041  +15.48   -25.99   0.596    1.115    147     62   29.6%
 4  s16 R>=44             3%      71,903  +15.72   -27.90   0.563    1.095    158    110   24.3%
 5  s20 R>=44             4%      71,520  +15.61   -30.21   0.517    1.090    121     88   23.9%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2010      34,444  +14.81   -15.21   0.974    1.353     33     25   45.5%
                    2011      32,805   -4.76   -27.77  -0.171   -0.176     33     23   26.6%
                    2012      37,269  +13.61   -19.32   0.704    0.941     11     63   16.1%
                    2013      58,003  +55.63    -9.22   6.033    3.776     24      0   28.0%
                    2014      68,562  +18.20   -15.89   1.146    1.155     33      6   10.8%
                    2015      62,415   -8.97   -28.55  -0.314   -0.203     30     15    7.6%
s12 R>=44 4%        2010      33,649  +12.16   -20.00   0.608    0.976     25     33   34.7%
                    2011      31,703   -5.78   -28.37  -0.204   -0.273     24     32   34.6%
                    2012      36,262  +14.38   -20.54   0.700    0.946     12     62   15.0%
                    2013      61,435  +69.42   -10.19   6.811    3.944     18      6   18.0%
                    2014      75,766  +23.33   -16.61   1.405    1.337     24     15    6.4%
                    2015      66,957  -11.63   -31.59  -0.368   -0.304     24     21    5.6%
s12 R>=44 5%        2010      31,237   +4.12   -24.31   0.170    0.412     20     38   25.4%
                    2011      27,572  -11.73   -28.01  -0.419   -0.750     19     37   44.2%
                    2012      30,926  +12.16   -19.27   0.631    0.777     12     62   15.3%
                    2013      54,746  +77.02   -10.86   7.089    3.986     14     10   13.3%
                    2014      60,430  +10.38   -20.06   0.518    0.681     19     20    4.9%
                    2015      56,387   -6.69   -32.67  -0.205   -0.043     18     27    5.3%
s16 ungated 3%      2010      38,179  +27.26   -19.25   1.416    1.513     32     92   15.4%
                    2011      36,479   -4.45   -23.57  -0.189   -0.228     34     61   32.6%
                    2012      44,113  +20.93   -15.84   1.321    1.466     27     93   14.5%
                    2013      77,587  +75.88    -7.32  10.372    4.204     24     18    8.5%
                    2014      88,566  +14.15   -16.66   0.850    0.989     32     25    8.6%
                    2015      90,230   +1.88   -23.59   0.080    0.273     33     60    5.5%
s12 ungated 5%      2010      38,908  +29.69   -22.69   1.308    1.530     19    212    4.1%
                    2011      33,961  -12.72   -35.18  -0.361   -0.371     20    176    5.2%
                    2012      46,088  +35.71   -20.18   1.769    1.907     20    207    1.4%
                    2013      84,480  +83.30    -7.12  11.707    4.346     20     62    3.6%
                    2014      85,510   +1.22   -21.72   0.056    0.315     20     89    4.6%
                    2015      77,393   -9.49   -25.73  -0.369   -0.353     20    156    2.9%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $62,415)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.0|7    +3.4|3    +1.6|0    +0.1|4    -3.1|0    -4.3|0    +2.6|1    -7.9|6   +10.4|7    +5.5|5    +0.8|0    +9.5|0 |   +14.8    33
 2011 |    +2.8|1    +7.4|1    +4.4|1    +2.7|0    +0.1|0    -0.8|1    -2.6|1    -9.5|0    -6.9|0   +3.2|28    -3.0|0    -1.4|0 |    -4.8    33
 2012 |   +10.2|1    +3.2|0    +1.2|0    -3.3|0   -11.5|0    +5.6|3    -0.4|1    +3.9|0    +3.6|0    -1.1|0    +2.1|2    +1.0|4 |   +13.6    11
 2013 |    +2.3|1    +0.6|3    +2.6|3    +3.6|2   +11.5|6    +6.0|2    +4.2|1    +3.4|2    +5.8|1    -3.2|1    +7.6|1    +1.4|1 |   +55.6    24
 2014 |    +3.2|5    +3.2|6    -3.3|5    +1.6|1    -0.3|1    +8.3|3    -0.6|2    +6.1|2    -2.2|2    -5.1|1    -0.4|3    +7.1|2 |   +18.2    33
 2015 |    +0.2|2   +11.5|6    +0.4|3    -3.1|4    +6.5|1    -0.0|0    +0.6|5   -12.3|0   -12.7|0    +7.9|1    +3.0|4    -8.2|4 |    -9.0    30
```

### s12 R>=44 — size 4%  (Final $66,957)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.0|7    +4.6|3    +2.1|0    +0.1|4    -4.2|0    -5.8|0    +3.6|1   -10.7|6   +13.8|4    +4.5|0    +0.3|0    +9.7|0 |   +12.2    25
 2011 |    +3.6|1    +8.5|1    +3.1|1    +2.8|0    -1.2|0    -1.9|1    -3.4|1    -8.0|0    -3.9|0   +0.4|19    -4.0|0    -0.9|0 |    -5.8    24
 2012 |   +10.7|1    +2.0|0    +0.8|1    -2.0|0   -13.4|0    +6.2|3    -0.8|1    +3.9|0    +4.8|0    -1.5|0    +3.0|2    +1.8|4 |   +14.4    12
 2013 |    +3.6|1    +0.8|3    +3.4|3    +4.7|2   +14.8|4    +6.8|0    +4.2|1    +2.4|2    +7.0|1    -3.0|0    +8.4|0    +1.8|1 |   +69.4    18
 2014 |    +5.5|5    +4.0|6    -5.7|3    +0.1|1    +0.9|1    +8.2|3    -2.3|2   +10.8|1    -4.4|0    -2.5|1    -0.8|1    +9.0|0 |   +23.3    24
 2015 |    -0.7|3   +10.6|6    -0.7|2    -2.7|3    +8.1|0    -0.9|1    -1.9|5   -12.3|0   -14.3|0    +3.5|1    +9.6|3    -7.0|0 |   -11.6    24
```

### s12 R>=44 — size 5%  (Final $56,387)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -5.0|7    +5.8|3    +2.6|0    +0.1|4    -5.2|0    -7.2|0    +4.5|1   -13.2|5   +15.1|0    +2.6|0    -2.6|0    +9.9|0 |    +4.1    20
 2011 |    +3.9|1    +4.6|1    +2.7|1    +1.4|0    -2.1|0    -2.0|1    -1.1|1    -7.0|0    -4.7|0   +1.5|14    -6.3|0    -2.5|0 |   -11.7    19
 2012 |   +10.5|1    +2.2|0    +1.1|1    -1.4|0   -12.9|0    +5.0|3    -0.8|1    +2.0|0    +4.2|0    -2.8|0    +3.8|2    +2.3|4 |   +12.2    12
 2013 |    +4.5|1    +1.0|3    +4.2|3    +5.8|2   +17.2|0    +8.0|0    +3.8|1    +2.1|2    +7.1|0    -3.3|0    +7.8|1    +1.6|1 |   +77.0    14
 2014 |    +5.9|4    +1.5|6    -4.7|3    +0.9|1    -2.0|1    +7.9|1    -0.3|0   +10.6|1    -7.3|1    -5.0|0    -4.5|0    +8.8|1 |   +10.4    19
 2015 |    -1.5|4    +7.9|5    +6.8|2    -4.3|3    +9.8|1    +4.3|1    -0.8|0   -14.2|0   -14.8|0    +3.1|1    +8.7|1    -7.6|0 |    -6.7    18
```

### s16 ungated — size 3%  (Final $90,230)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -4.7|13    +6.1|5    +5.2|2   +2.2|11    -4.3|0    -8.2|0    +7.8|0    -7.7|1   +14.2|0    +4.2|0    +3.1|0    +9.2|0 |   +27.3    32
 2011 |    +1.9|7    +4.4|1    +4.0|3    +1.2|3    -1.9|3    -3.3|1    -0.3|1    -5.1|0    -7.5|0   +7.3|15    -3.8|0    -0.5|0 |    -4.5    34
 2012 |    +9.3|7    +3.0|0    -0.2|0    -1.8|0   -10.0|0    +5.1|1   +1.2|11    +1.7|0    +5.6|0    -1.2|0    +3.9|3    +3.9|5 |   +20.9    27
 2013 |    +4.0|7    +1.0|4    +6.6|1    +4.5|0   +15.8|0    +2.7|1    +6.1|3    +3.5|3    +7.4|2    -1.8|1    +7.7|1    +1.4|1 |   +75.9    24
 2014 |    +3.3|6    +5.5|4    -3.7|7    +1.2|3    -1.2|1    +9.6|0    -1.4|3    +5.3|2    -5.2|1    -3.0|1    +0.5|3    +3.5|1 |   +14.2    32
 2015 |    +1.7|5    +4.1|6    +1.5|6    -1.2|6    +8.8|0    +2.9|0    +0.1|0    -9.5|1    -9.6|0    +8.0|3    +3.5|6    -6.2|0 |    +1.9    33
```

### s12 ungated — size 5%  (Final $77,393)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -8.0|19   +12.2|0    +9.4|0    -2.2|0    -5.5|0   -10.2|0   +10.4|0    -8.9|0   +13.9|0    +5.8|0    +4.0|0    +9.6|0 |   +29.7    19
 2011 |   +2.4|13    +0.6|6    +0.6|0    -3.5|1    -1.8|0    -1.9|0    -3.3|0   -10.3|0   -13.9|0   +19.5|0    -2.3|0    +3.8|0 |   -12.7    20
 2012 |   +8.9|13    +8.3|5    +0.9|1    -2.1|0    -9.4|1    +6.2|0    +2.4|0    +2.7|0    +2.3|0    -2.1|0    +6.2|0    +8.2|0 |   +35.7    20
 2013 |   +7.1|11    +2.4|7    +6.0|1    +1.1|0   +12.3|1    +4.9|0    +6.7|0    -0.5|0   +12.6|0    -2.1|0    +8.4|0    +4.4|0 |   +83.3    20
 2014 |    +2.2|3    +1.3|9    -5.1|7    +3.2|0    -0.9|1   +12.6|0    -3.8|0    +4.4|0   -10.6|0    -6.1|0    +2.0|0    +4.2|0 |    +1.2    20
 2015 |    -0.2|2    +2.7|8    +1.2|9    -0.5|0    +6.7|0    -0.3|0    -2.3|0    -9.2|1    -9.7|0    +8.7|0    +1.2|0    -6.5|0 |    -9.5    20
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return. Each config is decomposed once per gated signal set, strictest gate first as in the size sweep: the deciles split the trades that gate's own run took, so each table spans only that gate..100 and reads against the matching size-sweep row.

### s20 R>=55  (bk50d_s20_v2.0)

Trades scored: 93  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55        9   +2.54    -5.64   0.451    1.103
D2        55-57        9   +2.15    -5.83   0.369    1.032
D3        58-58        9   +0.10    -5.05   0.020    0.071
D4        58-61       10   +0.07    -8.51   0.009    0.053
D5        61-61        9   +3.90    -6.11   0.638    1.255
D6        61-65        9   -0.43    -7.98  -0.054   -0.209
D7        65-65       10   +0.51    -6.65   0.076    0.241
D8        68-75        9   -0.38    -6.24  -0.061   -0.170
D9        75-82        9   +0.96    -6.05   0.159    0.427
D10       86-100      10   +2.35    -5.38   0.437    0.814
```

### s20 R>=44  (bk50d_s20_v2.0)

Trades scored: 121  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       12   +1.06    -7.45   0.143    0.467
D2        46-47       12   +0.72    -8.47   0.085    0.311
D3        47-50       12   +3.54    -4.96   0.713    1.405
D4        50-54       12   +5.32    -5.46   0.975    2.039
D5        54-55       12   +2.53   -10.32   0.246    0.728
D6        55-58       12   +1.93    -5.08   0.380    0.835
D7        58-61       12   +0.43    -6.38   0.067    0.220
D8        61-65       12   +0.32    -7.50   0.042    0.153
D9        65-75       12   +0.24    -6.85   0.034    0.124
D10       75-100      13   +1.27    -8.07   0.158    0.420
```

### s16 R>=55  (bk50d_s16_v2.0)

Trades scored: 95  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55        9   +2.05    -5.98   0.343    0.880
D2        57-57       10   +2.09    -5.41   0.386    0.856
D3        57-58        9   +0.25    -5.05   0.049    0.135
D4        58-61       10   -0.22    -7.32  -0.030   -0.079
D5        61-61        9   +3.71    -6.20   0.600    1.212
D6        61-65       10   +0.21    -7.96   0.027    0.124
D7        65-65        9   +0.56    -6.49   0.086    0.264
D8        65-75       10   -1.13    -9.91  -0.114   -0.543
D9        75-82        9   +0.96    -6.05   0.159    0.427
D10       86-100      10   +2.35    -5.38   0.437    0.814
```

### s16 R>=44  (bk50d_s16_v2.0)

Trades scored: 126  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       12   +1.57    -5.50   0.286    0.680
D2        46-47       13   +1.88    -6.82   0.277    0.645
D3        47-50       12   +4.53    -5.66   0.800    1.538
D4        50-51       13   +2.98    -5.56   0.535    1.091
D5        51-54       13   +1.27   -10.42   0.122    0.532
D6        54-57       12   +1.50    -9.52   0.157    0.446
D7        57-61       13   +1.30    -5.18   0.251    0.515
D8        61-65       12   +0.74    -5.20   0.142    0.368
D9        65-75       13   +0.43    -6.68   0.064    0.180
D10       75-100      13   +1.16    -8.16   0.143    0.377
```

### s12 R>=55  (bk50d_s12_v2.0)

Trades scored: 94  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57        9   +3.47    -7.40   0.469    1.305
D2        57-57        9   +2.00    -4.87   0.411    0.864
D3        57-58       10   +0.46    -5.05   0.092    0.234
D4        58-61        9   -0.44    -8.36  -0.053   -0.182
D5        61-61       10   +3.32    -6.07   0.546    1.131
D6        61-65        9   -0.08    -7.22  -0.011   -0.025
D7        65-65        9   +0.20    -6.65   0.031    0.113
D8        68-75       10   -1.13   -10.18  -0.111   -0.504
D9        75-86        9   +1.08    -6.05   0.179    0.464
D10       86-100      10   +3.65    -8.21   0.444    1.015
```

### s12 R>=44  (bk50d_s12_v2.0)

Trades scored: 127  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       12   +1.64    -7.61   0.215    0.615
D2        44-46       13   +0.79    -7.14   0.110    0.310
D3        46-47       13   +2.11    -5.06   0.417    0.786
D4        47-50       12   +3.34    -7.24   0.461    1.295
D5        50-51       13   +3.50    -6.37   0.549    1.249
D6        51-54       13   +0.23    -8.90   0.026    0.101
D7        55-58       12   +2.76    -5.21   0.529    0.985
D8        58-61       13   +0.92    -6.17   0.150    0.405
D9        65-75       13   -0.26    -6.57  -0.040   -0.063
D10       75-100      13   +1.52    -7.64   0.199    0.488
```

## Findings (2026-07-30 run, 2010-01-01 – 2015-12-31 — tables above regenerate on re-run)

*The tables above were regenerated on 2026-11-15, on the shared `qm` signal path and on hetzner data that has drifted since the earlier runs. Numbers quoted below come from the run each subsection names, not from those tables.*

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
55-57, +3.47%) and D10 (86-100, +3.65%) lead while D4 (58-61, −0.22%) and D8 (68-75, −1.08%) are
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
   +16.27% CAGR, marginally above QQQ buy & hold (+15.82%); every gated cell trails both QQQ and,
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
