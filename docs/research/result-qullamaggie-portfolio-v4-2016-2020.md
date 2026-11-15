# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-11-15 14:42:46 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2016-01-01 – 2020-12-31 |
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
SPY         55,797  +13.24   -34.10   0.388    1.030
QQQ         85,956  +23.47   -28.56   0.822    1.492
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 632 signals (0 with no fillable next-day open); `R>=44` drops 195 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        118,790  +31.74   -36.59   0.867    1.823    118    360   39.4%
3%     R>=44        122,344  +32.52   -23.63   1.376    1.865    139    776   24.7%
3%     ungated      132,419  +34.64   -20.69   1.674    2.003    143    967   22.8%
4%     R>=55        139,752  +36.10   -29.52   1.223    1.988     98    380   32.7%
4%     R>=44        164,719  +40.66   -22.95   1.772    2.171    105    810   23.7%
4%     ungated      128,515  +33.83   -24.70   1.370    1.954    110   1000   21.5%
5%     R>=55        176,722  +42.65   -25.78   1.655    2.209     83    395   29.1%
5%     R>=44        144,242  +36.97   -28.48   1.298    2.001     87    828   22.5%
5%     ungated      144,709  +37.05   -31.59   1.173    1.980     89   1021   19.9%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1217 signals (0 with no fillable next-day open); `R>=44` drops 706 signals (1 with no fillable next-day open); `ungated` drops 0 signals (4 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        123,176  +32.70   -38.26   0.855    1.875    117    361   39.2%
3%     R>=44        128,196  +33.77   -24.39   1.384    1.919    140    848   23.2%
3%     ungated      128,108  +33.75   -41.18   0.820    1.794    157   1534   14.4%
4%     R>=55        170,463  +41.63   -33.57   1.240    2.232     99    379   32.4%
4%     R>=44        135,014  +35.16   -29.76   1.182    1.940    108    880   20.8%
4%     ungated      109,273  +29.56   -47.84   0.618    1.474    123   1568   11.6%
5%     R>=55        201,316  +46.42   -26.40   1.759    2.430     81    397   30.2%
5%     R>=44        137,184  +35.60   -31.93   1.115    1.923     87    901   19.7%
5%     ungated       99,696  +27.20   -41.78   0.651    1.368     97   1594   11.5%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1952 signals (0 with no fillable next-day open); `R>=44` drops 1414 signals (1 with no fillable next-day open); `ungated` drops 0 signals (4 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        130,212  +34.19   -42.09   0.812    1.896    115    357   39.5%
3%     R>=44        148,472  +37.76   -21.73   1.738    2.143    141    868   23.1%
3%     ungated       84,415  +23.03   -43.37   0.531    1.230    163   2257   10.1%
4%     R>=55        155,577  +39.06   -40.25   0.970    2.070     98    374   32.9%
4%     R>=44        151,748  +38.36   -22.56   1.701    2.114    107    902   21.9%
4%     ungated       88,578  +24.22   -44.60   0.543    1.243    123   2297    9.2%
5%     R>=55        179,890  +43.16   -36.62   1.179    2.226     82    390   29.4%
5%     R>=44        134,957  +35.15   -27.07   1.299    1.923     87    922   20.2%
5%     ungated       96,111  +26.27   -44.84   0.586    1.294     96   2324    9.7%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=55             5%     201,316  +46.42   -26.40   1.759    2.430     81    397   30.2%
 2  s12 R>=55             5%     179,890  +43.16   -36.62   1.179    2.226     82    390   29.4%
 3  s20 R>=55             5%     176,722  +42.65   -25.78   1.655    2.209     83    395   29.1%
 4  s16 R>=55             4%     170,463  +41.63   -33.57   1.240    2.232     99    379   32.4%
 5  s20 R>=44             4%     164,719  +40.66   -22.95   1.772    2.171    105    810   23.7%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=55             5%     201,316  +46.42   -26.40   1.759    2.430     81    397   30.2%
 2  s16 R>=55             4%     170,463  +41.63   -33.57   1.240    2.232     99    379   32.4%
 3  s12 R>=55             5%     179,890  +43.16   -36.62   1.179    2.226     82    390   29.4%
 4  s20 R>=55             5%     176,722  +42.65   -25.78   1.655    2.209     83    395   29.1%
 5  s20 R>=44             4%     164,719  +40.66   -22.95   1.772    2.171    105    810   23.7%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2016      44,449  +48.16   -11.05   4.358    2.751     33    158   22.0%
                    2017      52,256  +17.56    -6.59   2.665    1.772     32     15   40.4%
                    2018      63,975  +22.43   -13.04   1.720    1.452     11     18   22.1%
                    2019      86,925  +35.87   -12.22   2.936    2.291     32     47   13.0%
                    2020     148,472  +70.81   -21.73   3.258    2.399     33    630   18.3%
s12 R>=44 4%        2016      43,429  +44.76   -11.54   3.879    2.635     24    167   23.0%
                    2017      52,861  +21.72    -6.62   3.280    2.192     24     23   35.6%
                    2018      61,450  +16.25   -12.75   1.275    1.013     11     18   22.5%
                    2019      83,971  +36.65   -16.22   2.260    2.209     24     55   11.0%
                    2020     151,748  +80.72   -22.51   3.586    2.581     24    639   17.4%
s12 R>=44 5%        2016      42,826  +42.75   -12.41   3.446    2.445     19    172   23.2%
                    2017      51,191  +19.53    -8.21   2.379    1.823     19     28   31.8%
                    2018      57,768  +12.85   -15.81   0.813    0.746     11     18   22.3%
                    2019      73,964  +28.04   -20.71   1.354    1.657     19     60    9.4%
                    2020     134,957  +82.46   -27.07   3.046    2.627     19    644   14.5%
s16 R>=55 5%        2016      48,325  +61.08    -9.14   6.681    2.882     20     83   21.5%
                    2017      55,768  +15.40   -10.22   1.508    1.530     15      3   52.9%
                    2018      76,228  +36.69   -13.75   2.669    2.026      7      4   18.9%
                    2019      91,294  +19.76   -15.18   1.302    1.687     19      5   44.7%
                    2020     201,316 +120.51   -26.40   4.565    3.354     20    302   13.3%
s12 R>=55 5%        2016      48,325  +61.08    -9.14   6.681    2.882     20     79   21.5%
                    2017      55,828  +15.53   -10.22   1.520    1.543     15      3   52.8%
                    2018      74,981  +34.31   -14.58   2.352    1.903      8      3   18.5%
                    2019      84,774  +13.06   -15.19   0.860    1.139     20      3   44.9%
                    2020     179,890 +112.20   -36.62   3.064    3.006     19    302    9.1%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $148,472)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.2|33   +12.8|0    -3.1|0    +3.1|0   +10.1|0    +3.7|0    +4.8|0    -3.1|0   +15.2|0    -1.7|0 |   +48.2    33
 2017 |    +6.3|0    -1.2|0    -0.1|2    +0.2|1    -0.9|2    +2.6|3    -1.1|4    -0.2|5    +2.4|6    -0.1|8    +6.3|1    +2.6|0 |   +17.6    32
 2018 |    -0.4|0    -4.1|0    +1.4|0    +8.3|3   +14.0|2    -0.6|3    +3.9|0   +10.6|1    -0.3|1    -5.4|0    -0.0|0    -4.8|1 |   +22.4    11
 2019 |    +6.0|0   +2.2|14    +0.9|8    -1.2|2    -6.5|2   +16.0|3    +2.1|0    -6.2|2    -1.3|1    +4.9|0    +4.7|0   +11.6|0 |   +35.9    32
 2020 |    -5.0|0    -0.8|1    -7.2|0    +5.9|0   +1.5|25    +4.5|3    +4.6|0   +12.4|2    -5.8|1    -2.6|1   +38.7|0   +16.2|0 |   +70.8    33
```

### s12 R>=44 — size 4%  (Final $151,748)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.8|24   +12.2|0    -3.3|0    +0.8|0    +9.4|0    +4.2|0    +5.3|0    -3.0|0   +16.5|0    -1.7|0 |   +44.8    24
 2017 |    +6.4|0    -1.5|0    +0.4|2    +0.3|1    -1.2|2    +3.5|3    -1.5|4    -0.3|5    +3.3|6    -0.2|1    +7.7|0    +3.5|0 |   +21.7    24
 2018 |    +0.1|0    -2.8|0    +0.3|0    +7.7|3   +14.0|2    -1.8|3    +2.3|0    +6.5|1    -1.2|1    -3.6|0    +1.7|0    -6.5|1 |   +16.2    11
 2019 |    +8.0|0   +3.2|13    +0.2|0    -1.6|2    -9.9|2   +17.6|3    +1.7|0    -6.8|2    +0.8|1    +5.4|0    +5.7|0   +10.2|1 |   +36.6    24
 2020 |    -8.3|0    +1.2|1    -8.5|0    +8.0|0   +2.8|17    +4.7|2    +3.3|0   +14.5|3    -3.4|1    -4.9|0   +41.0|0   +19.6|0 |   +80.7    24
```

### s12 R>=44 — size 5%  (Final $134,957)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.9|19   +10.3|0    -2.7|0    -0.3|0    +9.8|0    +4.8|0    +5.9|0    -1.7|0   +15.8|0    -3.0|0 |   +42.8    19
 2017 |    +5.9|0    -2.5|0    +1.4|2    +0.4|1    -1.5|2    +4.3|3    -1.8|4    -0.4|5    +3.7|2    +0.9|0    +5.2|0    +2.8|0 |   +19.5    19
 2018 |    +0.2|0    -2.0|0    -0.9|0    +7.7|3   +14.1|2    -1.0|3    +1.7|0    +6.4|1    -1.6|1    -4.5|0    +2.2|0    -8.1|1 |   +12.8    11
 2019 |   +10.3|0    +4.6|8    +0.6|0    -2.5|2   -14.4|2   +15.5|3    -0.0|1    -5.9|2    +3.0|1    +2.8|0    +4.1|0   +10.3|0 |   +28.0    19
 2020 |    -8.3|0    -0.3|1    -9.0|0   +10.1|0   +7.2|11    +5.4|3    +9.0|0    +9.6|2    -5.6|2    -8.1|0   +39.8|0   +21.5|0 |   +82.5    19
```

### s16 R>=55 — size 5%  (Final $201,316)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.3|20   +22.3|0    -2.4|0   +10.9|0    +9.8|0    +0.2|0    +4.9|0    -3.4|0   +13.8|0    -4.3|0 |   +61.1    20
 2017 |    +6.5|0    -2.4|0    +0.5|0    -0.0|1    -2.3|1    +1.5|1    +0.3|3    -2.5|2    +0.4|2    +0.7|2    +5.7|1    +6.6|2 |   +15.4    15
 2018 |    +0.5|4    -0.9|0    +2.4|0   +11.9|0   +15.5|1    -4.6|1    +2.6|0   +16.4|0    +1.9|1    -7.5|0    +6.6|0    -9.4|0 |   +36.7     7
 2019 |    +3.0|0    +2.3|2    -1.9|4    +1.6|0    +0.2|1    +6.3|1    +1.5|4   -10.3|2    -1.3|0    +2.4|3    +4.1|2   +11.8|0 |   +19.8    19
 2020 |    -6.9|0    +4.8|1   -12.5|0   +19.3|0    +1.1|9    +3.7|0   +12.8|3   +13.7|2    -4.2|0    -0.9|2   +37.6|3   +23.3|0 |  +120.5    20
```

### s12 R>=55 — size 5%  (Final $179,890)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.3|20   +22.3|0    -2.4|0   +10.9|0    +9.8|0    +0.2|0    +4.9|0    -3.4|0   +13.8|0    -4.3|0 |   +61.1    20
 2017 |    +6.5|0    -2.4|0    +0.5|0    -0.0|1    -2.3|1    +1.5|1    +0.3|3    -2.5|2    +0.4|2    +0.7|2    +5.7|1    +6.7|2 |   +15.5    15
 2018 |    +0.6|4    -0.9|0    +2.4|0   +12.0|0   +15.4|1    -4.6|1    +2.6|0   +16.4|0    +1.9|1    -7.5|0    +6.7|0   -11.1|1 |   +34.3     8
 2019 |    +4.3|0    +3.0|2    -0.7|3    +0.3|0    -3.7|1    +3.3|1    +1.1|4   -10.4|2    +0.3|0    +1.2|3    +2.9|2   +12.4|2 |   +13.1    20
 2020 |    -3.4|0    -1.6|1   -17.1|0   +22.9|0    +5.7|6    +5.6|1   +11.6|3   +14.0|2    -1.3|0    -2.6|2   +34.9|2   +19.0|2 |  +112.2    19
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return. Each config is decomposed once per gated signal set, strictest gate first as in the size sweep: the deciles split the trades that gate's own run took, so each table spans only that gate..100 and reads against the matching size-sweep row.

### s20 R>=55  (bk50d_s20_v2.0)

Trades scored: 98  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57        9   +2.62    -6.96   0.376    1.065
D2        57-61       10   +1.28    -7.98   0.160    0.499
D3        61-61       10   +3.25    -6.71   0.484    1.147
D4        61-64       10   +2.32   -10.48   0.221    0.702
D5        64-65       10   +1.63    -7.46   0.218    0.513
D6        65-65        9   +8.25   -11.64   0.709    1.932
D7        68-75       10   +0.78    -7.92   0.098    0.311
D8        75-93       10   +5.53    -4.80   1.152    1.630
D9        93-100      10   +6.75   -11.14   0.606    1.144
D10      100-100      10   +5.42   -13.85   0.391    1.019
```

### s20 R>=44  (bk50d_s20_v2.0)

Trades scored: 105  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       10   +2.43    -4.07   0.597    1.114
D2        46-47       11   +2.84    -5.29   0.537    1.013
D3        47-51       10   +2.22    -3.67   0.604    0.960
D4        51-54       11   +1.51    -5.24   0.288    0.626
D5        54-61       10   +3.58    -5.16   0.693    1.323
D6        61-65       11   +3.11    -7.05   0.440    1.039
D7        65-75       10   +8.24    -7.21   1.143    2.159
D8        75-96       11   +7.45    -4.40   1.692    1.974
D9        96-100      10   +5.08    -7.95   0.639    1.014
D10      100-100      11   +5.24   -15.31   0.342    0.914
```

### s16 R>=55  (bk50d_s16_v2.0)

Trades scored: 99  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57        9   +2.05   -10.49   0.195    0.758
D2        57-58       10   +3.34    -4.63   0.721    1.474
D3        58-61       10   +3.05    -5.46   0.559    1.067
D4        61-64       10   +3.89    -5.13   0.759    1.301
D5        64-65       10   +1.84    -7.37   0.250    0.605
D6        65-65       10   +9.53   -12.82   0.743    1.787
D7        65-71       10   +1.60    -6.77   0.236    0.552
D8        74-89       10   +4.06    -3.69   1.102    1.581
D9        89-100      10   +6.07    -9.01   0.674    1.187
D10      100-100      10   +7.69   -10.94   0.703    1.414
```

### s16 R>=44  (bk50d_s16_v2.0)

Trades scored: 108  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +3.28    -3.93   0.834    1.179
D2        44-46       11   +1.52    -8.62   0.176    0.489
D3        46-47       11   +3.91    -8.50   0.460    1.371
D4        47-51       11   +0.78    -6.42   0.122    0.339
D5        51-54       11   +2.27    -4.69   0.483    0.879
D6        55-61       10   +4.97    -5.26   0.945    1.744
D7        61-65       11   +0.32   -10.02   0.032    0.143
D8        65-79       11   +6.32    -7.06   0.895    1.974
D9        89-100      11   +6.99    -9.62   0.727    1.527
D10      100-100      11   +5.24   -15.31   0.342    0.914
```

### s12 R>=55  (bk50d_s12_v2.0)

Trades scored: 98  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55        9   +1.13   -12.93   0.088    0.424
D2        57-58       10   +4.30    -3.79   1.135    1.866
D3        58-61       10   +3.05    -5.46   0.559    1.067
D4        61-64       10   +2.36    -8.30   0.284    0.812
D5        64-65       10   +2.09    -7.80   0.268    0.669
D6        65-65        9   +9.22   -10.84   0.850    1.867
D7        65-71       10   +2.41    -8.75   0.275    0.804
D8        71-79       10   +2.01    -6.64   0.302    0.844
D9        89-100      10   +6.26    -8.13   0.770    1.303
D10      100-100      10   +8.11    -9.64   0.841    1.514
```

### s12 R>=44  (bk50d_s12_v2.0)

Trades scored: 107  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +3.90    -2.86   1.364    1.508
D2        44-47       11   +5.02    -9.52   0.527    1.633
D3        47-47       11   +3.71    -5.36   0.693    1.273
D4        47-51       10   +1.49    -5.58   0.267    0.610
D5        51-55       11   +2.59    -5.32   0.487    1.012
D6        55-61       11   +3.92    -6.41   0.612    1.492
D7        61-65       10   -0.59   -10.70  -0.055   -0.223
D8        65-89       11   +6.99    -7.72   0.905    2.062
D9        89-100      11   +6.91   -10.26   0.673    1.446
D10      100-100      11   +5.21   -15.40   0.338    0.881
```

## Findings (2026-07-30 run, 2016-01-01 – 2020-12-31 — tables above regenerate on re-run)

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

Across the 9 config/size cells, R>=55 minus R>=44 CAGR averages **+0.02pp** and wins **3 of 9**
(range −5.01 to +8.21pp); Sortino is better in 3 of 9 and MaxDD in 4 of 9. For the reference
`s12` R>=55 loses at every sizing (−5.01 / −1.88 / −1.52pp at 3/4/5%), and its drawdown roughly
doubles at 3% (−40.77% against −22.66%) — fewer positions means each one weighs more. The wins
are at s16/s20, where the best cell of the window (`s16 R>=55 @5%`, +41.12%, Sortino 2.147) sits
on only 83 trades. Uninvested capital rises from 18.7–24.0% to 26.8–39.2%. **Verdict here: a wash
on average, and worse for the live `s12` config.**

The R>=55 decile tables are equally flat: for `s12` R>=55, D1 (score 55) has the worst
drawdown (−12.93%), and the best CAGR is D6 (score 65-68, +7.37%), not D10 (score 100, +6.80%),
with no order between. In the R>=44 tables
the 44-54 deciles (D1-D5) post +2.3% to +5.2% standalone — no worse than 55-61 — which is why
cutting them costs return here.

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
4. **Every gated cell beats both benchmarks** (SPY +13.24%, QQQ +23.47%) — the only window where
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
