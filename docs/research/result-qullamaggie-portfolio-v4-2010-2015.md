# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-02 23:38:50 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2010-01-01 – 2015-12-31 |
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
SPY         53,967  +10.30   -19.42   0.530    0.981
QQQ         72,292  +15.81   -16.09   0.983    1.327
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 82 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40         67,183  +14.40   -27.10   0.531    1.028    137     32   32.4%
3%     ungated       75,866  +16.75   -27.47   0.610    1.217    151    100   27.7%
4%     R>=40         72,854  +15.96   -28.29   0.564    1.080    113     56   26.6%
4%     ungated       75,710  +16.71   -23.36   0.715    1.170    122    129   23.2%
5%     R>=40         69,724  +15.11   -31.11   0.486    0.998     95     74   23.2%
5%     ungated       70,112  +15.22   -25.27   0.602    1.027    101    150   21.7%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 326 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40         61,289  +12.66   -26.48   0.478    0.908    147     75   29.2%
3%     ungated       78,801  +17.49   -24.83   0.704    1.148    183    365   14.0%
4%     R>=40         68,304  +14.72   -28.26   0.521    0.975    119    103   24.2%
4%     ungated       65,144  +13.82   -27.73   0.498    0.921    142    406   12.4%
5%     R>=40         51,222   +9.34   -33.06   0.282    0.689     98    124   22.8%
5%     ungated       71,886  +15.70   -34.97   0.449    0.988    116    432   11.0%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 749 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40         61,246  +12.65   -28.45   0.445    0.893    165    139   21.1%
3%     ungated       63,568  +13.35   -34.71   0.385    0.874    196    857    6.3%
4%     R>=40         62,187  +12.94   -29.91   0.433    0.893    126    178   18.9%
4%     ungated       72,148  +15.77   -33.21   0.475    0.975    148    905    4.8%
5%     R>=40         57,428  +11.45   -29.86   0.383    0.802    100    204   18.0%
5%     ungated       78,118  +17.32   -34.76   0.498    1.035    118    935    4.3%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      78,801  +17.49   -24.83   0.704    1.148    183    365   14.0%
 2  s12 ungated           5%      78,118  +17.32   -34.76   0.498    1.035    118    935    4.3%
 3  s20 ungated           3%      75,866  +16.75   -27.47   0.610    1.217    151    100   27.7%
 4  s20 ungated           4%      75,710  +16.71   -23.36   0.715    1.170    122    129   23.2%
 5  s20 R>=40             4%      72,854  +15.96   -28.29   0.564    1.080    113     56   26.6%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s20 ungated           3%      75,866  +16.75   -27.47   0.610    1.217    151    100   27.7%
 2  s20 ungated           4%      75,710  +16.71   -23.36   0.715    1.170    122    129   23.2%
 3  s16 ungated           3%      78,801  +17.49   -24.83   0.704    1.148    183    365   14.0%
 4  s20 R>=40             4%      72,854  +15.96   -28.29   0.564    1.080    113     56   26.6%
 5  s12 ungated           5%      78,118  +17.32   -34.76   0.498    1.035    118    935    4.3%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=40 3%        2010      36,487  +21.62   -16.39   1.319    1.687     32     23   42.0%
                    2011      32,747  -10.25   -27.25  -0.376   -0.504     33     19   30.4%
                    2012      38,851  +18.64   -18.74   0.995    1.282     10     62   16.0%
                    2013      60,184  +54.91    -7.88   6.965    3.528     25      6   17.7%
                    2014      69,514  +15.50   -16.00   0.969    1.129     33      7   13.5%
                    2015      61,246  -11.89   -28.45  -0.418   -0.405     32     22    6.7%
s12 R>=40 4%        2010      35,683  +18.94   -21.37   0.886    1.248     24     31   30.0%
                    2011      29,010  -18.70   -29.91  -0.625   -1.229     25     27   41.8%
                    2012      34,223  +17.97   -18.80   0.956    1.197     10     62   15.4%
                    2013      56,364  +64.69    -8.44   7.663    3.644     18     13   12.5%
                    2014      67,890  +20.45   -18.32   1.116    1.270     25     15    6.8%
                    2015      62,187   -8.40   -26.38  -0.318   -0.230     24     30    6.6%
s12 R>=40 5%        2010      34,355  +14.52   -25.98   0.559    0.903     19     36   20.3%
                    2011      28,523  -16.98   -27.20  -0.624   -1.265     20     32   50.6%
                    2012      34,901  +22.36   -16.97   1.318    1.485     10     62   15.1%
                    2013      57,942  +66.02    -8.44   7.821    3.539     13     18    7.4%
                    2014      61,938   +6.90   -17.52   0.394    0.582     19     21    9.0%
                    2015      57,428   -7.28   -29.86  -0.244   -0.122     19     35    5.7%
s16 ungated 3%      2010      38,037  +26.79   -21.22   1.263    1.449     32     96   12.2%
                    2011      32,761  -13.87   -24.83  -0.559   -0.819     35     62   35.6%
                    2012      39,706  +21.20   -14.06   1.507    1.477     29     99   14.1%
                    2013      69,991  +76.27    -6.83  11.173    4.217     23     20    7.2%
                    2014      81,132  +15.92   -17.51   0.909    1.084     31     29    8.5%
                    2015      78,801   -2.87   -23.10  -0.124    0.008     33     59    6.7%
s12 ungated 5%      2010      39,418  +31.39   -21.45   1.464    1.628     19    225    4.4%
                    2011      33,726  -14.44   -34.76  -0.415   -0.463     20    178    4.8%
                    2012      43,908  +30.19   -21.62   1.396    1.639     19    217    3.8%
                    2013      77,723  +77.01    -7.05  10.929    4.083     20     64    3.7%
                    2014      81,108   +4.36   -19.87   0.219    0.500     20     92    5.3%
                    2015      78,118   -3.69   -25.14  -0.147   -0.018     20    159    4.0%
```

## Monthly returns/transactions — s12 R>=40 at each sizing, plus the top 2 by Final$

### s12 R>=40 — size 3%  (Final $61,246)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -2.1|7    +3.4|3    +2.1|0    +2.6|7    -4.2|0    -5.3|0    +3.8|1    -7.8|3    +8.9|4    +5.3|7    +3.6|0   +11.2|0 |   +21.6    32
 2011 |    +0.1|0    +5.4|1    +3.7|2    +1.0|0    -0.8|0    +0.4|1    -0.1|1    -7.5|0   -10.6|0   +4.3|28    -2.9|0    -2.5|0 |   -10.3    33
 2012 |   +10.9|0    +3.9|1    +2.5|0    -3.1|0   -10.9|0    +4.8|2    -0.4|2    +3.8|0    +4.4|0    +1.4|0    -0.1|1    +1.6|4 |   +18.6    10
 2013 |    +1.7|6    +0.9|2    +2.4|4    +1.7|2   +14.2|7    +5.6|1    +3.1|2    +3.4|1    +6.3|0    -2.1|0    +7.0|0    +1.3|0 |   +54.9    25
 2014 |    -1.2|5    +1.0|6    -2.3|6    +3.1|3    -3.0|2    +6.6|3    +0.7|2    +6.8|1    -2.8|2    -4.5|1    +1.6|2    +9.5|0 |   +15.5    33
 2015 |    +1.3|3    +9.3|4    -1.1|4    -2.9|7    +6.7|1    -1.1|3    -0.9|3   -11.1|0   -11.1|0    +3.6|2    +3.5|4    -6.7|1 |   -11.9    32
```

### s12 R>=40 — size 4%  (Final $62,187)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -2.8|7    +4.6|3    +2.8|0    +3.5|7    -5.5|0    -7.1|0    +5.2|1   -10.5|3   +12.3|3    +4.2|0    +2.9|0   +10.5|0 |   +18.9    24
 2011 |    -1.0|0    +4.3|1    +2.0|2    +0.7|0    -2.4|0    -0.9|1    -1.6|1    -6.6|0    -6.9|0   +0.0|20    -5.2|0    -2.3|0 |   -18.7    25
 2012 |   +12.9|0    +2.8|1    +2.1|0    -3.2|0   -11.0|0    +5.3|2    -0.3|2    +3.6|0    +4.8|0    -0.1|0    -0.1|1    +1.4|4 |   +18.0    10
 2013 |    +1.3|6    +1.7|2    +3.3|4    +1.9|2   +18.0|1    +7.2|0    +2.3|1    +1.9|2    +7.7|0    -2.7|0    +7.6|0    +2.3|0 |   +64.7    18
 2014 |    +0.8|5    +0.5|6    -3.6|6    +1.9|2    -2.3|2    +9.1|1    +2.6|1    +8.3|0    -3.5|2    -4.4|0    +0.9|0    +9.9|0 |   +20.5    25
 2015 |    -0.6|2    +9.5|5    +1.4|4    -4.0|6    +7.9|1    -0.3|2    +2.0|1   -10.1|0   -11.5|0    +4.0|2    +2.1|1    -6.7|0 |    -8.4    24
```

### s12 R>=40 — size 5%  (Final $57,428)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.5|7    +5.8|3    +3.5|0    +4.4|7    -6.8|0    -8.9|0    +6.6|1   -13.5|1   +13.2|0    +2.4|0    +1.4|0   +13.0|0 |   +14.5    19
 2011 |    -0.3|0    +4.1|1    +0.7|2    -0.7|0    -1.1|0    -1.8|1    -0.1|1    -4.2|0    -5.8|0   +0.2|15    -5.8|0    -3.1|0 |   -17.0    20
 2012 |   +12.0|0    +1.2|1    +2.4|0    -2.5|0   -10.0|0    +4.9|2    +1.3|2    +3.7|0    +5.2|0    +1.1|0    -0.2|1    +2.6|4 |   +22.4    10
 2013 |    +2.7|6    +1.5|2    +4.4|2    +3.2|0   +17.8|0    +5.9|0    +2.8|2    +2.3|1    +6.7|0    -3.1|0    +6.5|0    +2.4|0 |   +66.0    13
 2014 |    +1.4|5    -1.0|6    -4.6|6    +3.4|0    -3.8|0   +10.9|0    -0.3|1    +5.3|1    -6.4|0    -5.3|0    +2.2|0    +6.4|0 |    +6.9    19
 2015 |    -0.8|3   +10.4|6    -0.2|4    -3.0|4   +10.7|0    +0.6|0    +2.1|1   -11.8|0   -13.1|0    +5.1|1    +1.9|0    -6.4|0 |    -7.3    19
```

### s16 ungated — size 3%  (Final $78,801)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -5.7|16    +6.8|5    +5.9|2    +3.6|9    -6.5|0    -9.2|0   +10.6|0    -9.7|0   +15.4|0    +4.2|0    +3.8|0    +8.4|0 |   +26.8    32
 2011 |    +0.3|7    +0.9|1    +0.2|3    +0.5|4    -1.6|3    -3.6|1    -1.2|1    -4.6|0    -7.7|0   +7.0|15    -3.9|0    -0.4|0 |   -13.9    35
 2012 |    +9.4|6    +3.3|1    +0.8|0    -2.4|0    -8.0|0    +4.4|1   +1.1|11    +1.3|0    +4.8|0    -1.7|0    +4.2|3    +3.2|7 |   +21.2    29
 2013 |    +5.4|7    +1.3|2    +7.4|1    +3.6|0   +15.6|0    +2.1|1    +5.7|3    +3.7|3    +5.7|2    -0.4|2    +6.6|1    +2.2|1 |   +76.3    23
 2014 |    +2.0|6    +5.1|4    -3.3|7    +0.3|2    -0.4|0    +9.7|0    -1.5|3    +4.6|2    -4.6|2    -2.6|1    +1.8|3    +4.8|1 |   +15.9    31
 2015 |    +1.2|5    +5.0|6    +1.4|5    -0.6|5    +8.0|0    +0.6|0    +0.0|0    -9.7|1    -7.8|0    +6.9|3    +0.6|7    -6.7|1 |    -2.9    33
```

### s12 ungated — size 5%  (Final $78,118)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -9.0|19   +11.4|0    +8.9|0    -0.4|0    -6.2|0    -9.5|0   +11.2|0    -5.7|0   +12.1|0    +5.0|0    +5.1|0    +8.5|0 |   +31.4    19
 2011 |   +1.0|13    +0.8|7    +0.2|0    -0.8|0    -1.3|0    -2.5|0    -3.2|0   -10.9|0   -15.0|0   +18.8|0    -3.4|0    +4.4|0 |   -14.4    20
 2012 |   +8.2|13    +7.9|6    -1.1|0    -3.5|0   -10.1|0    +6.0|0    +3.1|0    +4.7|0    +2.8|0    -1.6|0    +4.5|0    +7.4|0 |   +30.2    19
 2013 |   +5.3|11    +1.3|8    +4.8|1    +1.0|0   +13.0|0    +5.8|0    +6.0|0    +1.4|0   +12.5|0    -3.1|0    +8.4|0    +3.3|0 |   +77.0    20
 2014 |    +3.0|2    +0.3|9    -4.8|9    +3.9|0    -2.1|0   +13.1|0    -2.1|0    +3.6|0   -10.3|0    -6.1|0    +4.3|0    +3.6|0 |    +4.4    20
 2015 |    +0.1|1    +6.3|8   +3.4|10    -1.7|0    +6.6|0    -1.7|0    -0.4|0    -8.7|0   -10.7|0    +8.9|1    +2.5|0    -6.1|0 |    -3.7    20
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 113  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        43-43       11   +1.33    -8.69   0.153    0.443
D2        43-46       11   +2.94    -4.97   0.592    1.208
D3        49-56       11   +3.25    -4.92   0.661    1.223
D4        56-56       12   +4.99    -5.68   0.880    1.701
D5        60-64       11   +1.29   -12.60   0.102    0.357
D6        64-66       11   -0.81    -8.97  -0.090   -0.295
D7        66-66       12   +1.18    -7.44   0.159    0.510
D8        66-70       11   +1.69    -4.81   0.353    0.848
D9        70-83       11   -0.13    -8.32  -0.016   -0.021
D10       83-100      12   +0.87    -4.58   0.191    0.340
```

### s16  (bk50d_s16_v2.0)

Trades scored: 119  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       11   +2.73    -6.87   0.398    0.873
D2        43-46       12   +3.24    -4.97   0.651    1.307
D3        46-49       12   +0.28    -5.70   0.050    0.149
D4        49-56       12   +3.00    -7.36   0.407    1.065
D5        56-60       12   +2.13    -6.36   0.335    0.793
D6        60-64       12   +0.70   -12.60   0.055    0.206
D7        64-66       12   -0.04    -7.91  -0.005    0.014
D8        66-69       12   +1.39    -5.14   0.271    0.724
D9        69-83       12   +1.47    -5.21   0.282    0.545
D10       83-100      12   +0.72    -5.90   0.123    0.263
```

### s12  (bk50d_s12_v2.0)

Trades scored: 126  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-40       12   +1.39    -7.77   0.178    0.526
D2        40-41       13   +1.52    -5.40   0.281    0.584
D3        43-46       12   +1.73    -8.79   0.197    0.647
D4        46-50       13   +1.86    -4.78   0.388    0.773
D5        50-56       13   +1.94    -6.41   0.303    0.692
D6        56-60       12   +4.93    -4.17   1.182    1.756
D7        60-64       13   -1.15   -13.63  -0.084   -0.289
D8        64-66       12   -0.01    -7.26  -0.002    0.020
D9        67-83       13   +1.07    -6.08   0.176    0.437
D10       83-100      13   +1.35    -5.70   0.237    0.446
```

## Findings (2026-07-30 run, 2010-01-01 – 2015-12-31 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.

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
