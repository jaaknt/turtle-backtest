# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-10-24 22:55:43 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2021-01-01 – 2026-06-26 |
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
SPY         59,301  +13.25   -25.36   0.522    1.192
QQQ         68,525  +16.28   -35.62   0.457    1.131
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 491 signals (0 with no fillable next-day open); `R>=44` drops 189 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        246,367  +46.88   -24.19   1.938    2.197    156    211   19.0%
3%     R>=44        249,647  +47.24   -33.63   1.405    2.074    179    490   11.2%
3%     ungated      230,171  +45.07   -30.81   1.463    1.955    180    678    9.6%
4%     R>=55        260,120  +48.35   -30.04   1.609    2.009    126    241   15.1%
4%     R>=44        268,515  +49.21   -29.94   1.643    2.013    139    530    9.5%
4%     ungated      209,240  +42.57   -27.12   1.570    1.889    145    713    9.4%
5%     R>=55        289,794  +51.30   -31.08   1.651    2.029    105    262   12.5%
5%     R>=44        236,738  +45.82   -28.35   1.616    1.934    115    554   10.0%
5%     ungated      222,373  +44.16   -28.35   1.558    1.881    116    742    9.9%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1092 signals (0 with no fillable next-day open); `R>=44` drops 679 signals (0 with no fillable next-day open); `ungated` drops 0 signals (2 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        270,236  +49.38   -27.69   1.784    2.160    164    219   16.0%
3%     R>=44        268,640  +49.22   -32.34   1.522    2.063    181    615    8.7%
3%     ungated      152,535  +34.57   -25.77   1.341    1.667    193   1280    7.2%
4%     R>=55        307,232  +52.93   -30.07   1.760    2.106    131    252   12.2%
4%     R>=44        215,504  +43.34   -27.40   1.581    1.882    145    651    8.8%
4%     ungated      158,716  +35.55   -26.20   1.357    1.653    144   1329    7.4%
5%     R>=55        358,568  +57.30   -32.19   1.780    2.090    108    275    9.8%
5%     R>=44        205,447  +42.09   -27.89   1.509    1.790    117    679    8.5%
5%     ungated      195,013  +40.75   -27.46   1.484    1.827    115   1358    7.0%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1967 signals (0 with no fillable next-day open); `R>=44` drops 1512 signals (0 with no fillable next-day open); `ungated` drops 0 signals (3 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        316,042  +53.72   -28.62   1.877    2.263    167    216   14.4%
3%     R>=44        352,259  +56.79   -30.27   1.876    2.345    186    652    8.2%
3%     ungated      146,566  +33.59   -23.19   1.449    1.787    196   2151    6.3%
4%     R>=55        406,015  +60.91   -33.61   1.813    2.272    132    251   11.1%
4%     R>=44        243,714  +46.59   -28.53   1.633    1.977    145    693    8.1%
4%     ungated      151,989  +34.48   -22.94   1.503    1.817    145   2202    6.5%
5%     R>=55        440,427  +63.32   -33.83   1.872    2.224    107    276    9.8%
5%     R>=44        241,726  +46.37   -28.71   1.615    1.958    114    724    8.6%
5%     ungated      191,691  +40.31   -24.38   1.653    1.986    116   2231    6.2%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=55             5%     440,427  +63.32   -33.83   1.872    2.224    107    276    9.8%
 2  s12 R>=55             4%     406,015  +60.91   -33.61   1.813    2.272    132    251   11.1%
 3  s16 R>=55             5%     358,568  +57.30   -32.19   1.780    2.090    108    275    9.8%
 4  s12 R>=44             3%     352,259  +56.79   -30.27   1.876    2.345    186    652    8.2%
 5  s12 R>=55             3%     316,042  +53.72   -28.62   1.877    2.263    167    216   14.4%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=44             3%     352,259  +56.79   -30.27   1.876    2.345    186    652    8.2%
 2  s12 R>=55             4%     406,015  +60.91   -33.61   1.813    2.272    132    251   11.1%
 3  s12 R>=55             3%     316,042  +53.72   -28.62   1.877    2.263    167    216   14.4%
 4  s12 R>=55             5%     440,427  +63.32   -33.83   1.872    2.224    107    276    9.8%
 5  s20 R>=55             3%     246,367  +46.88   -24.19   1.938    2.197    156    211   19.0%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2021      45,123  +50.41   -21.27   2.370    1.895     32    110    3.1%
                    2022      58,930  +30.60   -24.57   1.245    1.232     32     54   20.2%
                    2023      78,384  +33.01   -24.98   1.321    2.047     33    159    7.0%
                    2024     124,643  +59.02   -14.70   4.015    2.936     32    107    6.9%
                    2025     281,022 +125.46   -30.27   4.145    3.956     33    178    4.4%
                    2026     352,259  +25.35   -13.46   1.884    2.278     24     44    7.0%
s12 R>=44 4%        2021      43,912  +46.37   -24.40   1.901    1.695     24    118    3.2%
                    2022      53,534  +21.91   -26.25   0.835    0.884     24     62   18.8%
                    2023      67,595  +26.26   -28.53   0.920    1.702     25    167    5.4%
                    2024      96,470  +42.72   -15.05   2.839    2.306     24    115    4.9%
                    2025     223,220 +131.39   -23.28   5.643    4.555     24    187    7.4%
                    2026     243,714   +9.18   -19.07   0.482    0.821     24     44    9.4%
s12 R>=44 5%        2021      43,899  +46.33   -25.17   1.841    1.690     19    123    4.0%
                    2022      56,514  +28.74   -22.74   1.264    1.116     19     67   18.1%
                    2023      69,936  +23.75   -28.71   0.827    1.537     20    172    3.7%
                    2024      96,328  +37.74   -18.36   2.056    1.963     18    121    6.0%
                    2025     230,994 +139.80   -25.15   5.558    4.732     19    192   10.5%
                    2026     241,726   +4.65   -18.38   0.253    0.422     19     49   10.2%
s12 R>=55 5%        2021      49,380  +64.60   -25.58   2.525    2.072     19     42    3.7%
                    2022      57,522  +16.49   -31.31   0.527    0.700     19     26   20.7%
                    2023      81,583  +41.83   -31.65   1.322    2.205     19     70   12.6%
                    2024     123,614  +51.52   -19.12   2.695    2.231     18     51    6.9%
                    2025     350,962 +183.92   -33.83   5.436    4.308     20     73    3.8%
                    2026     440,427  +25.49   -18.44   1.383    1.781     12     14   12.2%
s12 R>=55 4%        2021      50,966  +69.89   -23.71   2.948    2.231     24     37    3.1%
                    2022      57,217  +12.26   -27.50   0.446    0.582     24     21   30.3%
                    2023      80,021  +39.86   -29.33   1.359    2.182     24     65   10.5%
                    2024     127,167  +58.92   -18.36   3.209    2.524     22     47    6.2%
                    2025     322,013 +153.22   -33.61   4.559    3.952     24     69    4.9%
                    2026     406,015  +26.09   -17.80   1.465    1.942     14     12   11.9%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $352,259)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.3|32   +22.7|0    +1.0|0    +4.1|0   +10.4|0    +5.8|0    -9.7|0    +1.5|0    +9.3|0    +7.7|0    -5.9|0    +3.8|0 |   +50.4    32
 2022 |    +6.0|1    +2.5|5   -0.4|21   -12.4|5    +8.2|0    -9.2|0   +15.1|0    +5.9|0   -10.4|0   +14.3|0    +7.6|0    +4.4|0 |   +30.6    32
 2023 |    +6.7|1    +1.4|7    -6.8|3    -3.0|8   +6.3|14   +12.2|0   +12.0|0    -6.4|0    -9.8|0    -9.5|0   +16.1|0   +14.7|0 |   +33.0    33
 2024 |    -4.8|1    +9.6|6    -1.4|0    -4.1|5    +7.1|8    -1.2|8    +7.0|4    +6.8|0    +6.6|0    +6.9|0   +15.9|0    +0.9|0 |   +59.0    32
 2025 |    +5.4|1    -1.2|3   -10.8|1    +3.3|0   +4.4|12   +17.3|9   +28.1|7   +13.3|0   +16.6|0   +12.1|0    +5.1|0    -3.8|0 |  +125.5    33
 2026 |    +2.6|1    +3.4|0    -4.0|2    +7.2|6    +4.8|8    +9.4|7         ·         ·         ·         ·         ·         · |   +25.3    24
```

### s12 R>=44 — size 4%  (Final $243,714)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.3|24   +21.7|0    +0.6|0    +3.8|0   +11.6|0    +7.4|0   -11.6|0    +0.2|0   +10.7|0    +8.3|0    -7.5|0    +3.2|0 |   +46.4    24
 2022 |    +8.1|1    +3.3|5   -0.5|18   -13.4|0    +9.6|0    -9.0|0   +15.8|0    +2.9|0   -12.1|0   +16.0|0    +7.4|0    -2.6|0 |   +21.9    24
 2023 |    +8.7|1    +1.8|7    -7.0|3    -4.0|8    +5.2|6   +12.1|0    +9.9|0    -8.7|0   -10.9|0   -10.4|0   +19.4|0   +13.3|0 |   +26.3    25
 2024 |    -6.0|1    +7.3|7    -4.3|0    -4.1|5    +7.4|8    -3.9|3    +8.9|0   +10.1|0    +6.0|0    +2.7|0   +10.2|0    +3.9|0 |   +42.7    24
 2025 |    +4.7|1    -4.7|3    -5.6|1    +1.7|0   +1.4|14   +15.0|5   +34.9|0   +14.4|0   +16.1|0   +13.7|0    +2.6|0    -0.9|0 |  +131.4    24
 2026 |    +1.9|1    +2.7|0    -9.8|2    +7.1|6    +5.3|8    +2.6|7         ·         ·         ·         ·         ·         · |    +9.2    24
```

### s12 R>=44 — size 5%  (Final $241,726)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.7|19   +21.0|0    +1.6|0    +3.3|0   +10.6|0    +7.5|0   -12.1|0    -0.1|0   +11.0|0    +7.5|0    -6.9|0    +3.2|0 |   +46.3    19
 2022 |    +7.9|1    +4.1|5   +0.1|13   -11.8|0   +11.6|0    -9.1|0   +14.2|0    +2.0|0   -12.3|0   +20.9|0    +5.5|0    -1.8|0 |   +28.7    19
 2023 |    +6.8|1    -0.4|7    -5.8|3    -5.0|8    +7.2|1   +13.2|0   +10.0|0    -7.7|0   -11.4|0   -11.3|0   +17.7|0   +14.1|0 |   +23.8    20
 2024 |    -7.9|1    +8.0|7    -5.8|0    -5.8|5    +8.1|5    -3.0|0    +8.3|0   +11.0|0    +6.4|0    +1.3|0    +8.1|0    +6.4|0 |   +37.7    18
 2025 |    +2.6|1    -4.3|3    -6.5|1    +2.0|0   +0.7|14   +14.7|0   +44.5|0   +12.1|0   +17.1|0   +14.0|0    +3.4|0    -0.9|0 |  +139.8    19
 2026 |    +1.4|1    +0.7|0    -8.9|2    +7.0|6    +2.7|8    +2.3|2         ·         ·         ·         ·         ·         · |    +4.6    19
```

### s12 R>=55 — size 5%  (Final $440,427)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.2|19   +25.7|0    +1.2|0    +5.8|0   +11.1|0   +10.0|0   -12.0|0    -0.8|0   +13.6|0   +11.2|0    -7.9|0    +4.0|0 |   +64.6    19
 2022 |    +8.2|1    +3.5|1   -0.2|12   -17.2|5    +7.9|0   -10.9|0   +20.8|0    +7.9|0   -13.7|0   +12.2|0    +9.3|0    -5.2|0 |   +16.5    19
 2023 |    +9.5|1    -0.2|1    -3.3|1    -3.6|4    +7.4|9    +9.3|3   +12.6|0   -10.2|0   -13.1|0   -10.3|0   +22.1|0   +23.3|0 |   +41.8    19
 2024 |    -3.3|1   +11.0|1    -5.0|0    -6.8|3    +6.7|6    -0.5|5    +5.5|2    +2.7|0    +8.0|0    +5.9|0   +24.4|0    -2.5|0 |   +51.5    18
 2025 |    +8.2|0    -1.3|2   -14.8|1    +3.8|0    +8.2|6   +22.0|6   +40.0|5   +15.3|0   +22.5|0   +15.1|0    +2.6|0    -2.5|0 |  +183.9    20
 2026 |    +5.3|0    +2.3|0    -6.6|0    +8.7|5   +10.8|3    +3.6|4         ·         ·         ·         ·         ·         · |   +25.5    12
```

### s12 R>=55 — size 4%  (Final $406,015)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -6.2|24   +27.4|0    +2.5|0    +6.0|0   +10.7|0    +7.8|0   -10.7|0    +0.2|0   +14.0|0    +9.4|0    -6.4|0    +5.0|0 |   +69.9    24
 2022 |    +7.1|1    +2.8|1   -0.2|12   -15.3|7    +4.6|0    -8.1|0   +16.6|0    +6.3|0   -11.7|0   +10.1|0    +7.0|0    -2.6|3 |   +12.3    24
 2023 |   +10.0|1    -1.5|1    -3.0|1    -2.6|4    +3.9|9    +8.5|5   +15.2|0   -10.1|0   -10.9|0   -10.2|0   +21.5|0   +20.5|3 |   +39.9    24
 2024 |    -5.0|1   +10.9|1    -4.1|0    -5.8|3    +8.7|6    -2.5|5    +5.1|5    +2.8|0    +9.3|0    +4.4|0   +31.6|0    -2.9|1 |   +58.9    22
 2025 |    +8.7|0    -5.9|2   -14.0|1    +5.5|0    +9.0|6   +22.8|6   +34.6|9   +12.4|0   +19.1|0   +13.0|0    +3.9|0    -3.5|0 |  +153.2    24
 2026 |    +4.9|0    +1.8|0    -6.1|0    +9.5|6   +10.5|3    +3.9|5         ·         ·         ·         ·         ·         · |   +26.1    14
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return. Each config is decomposed once per gated signal set, strictest gate first as in the size sweep: the deciles split the trades that gate's own run took, so each table spans only that gate..100 and reads against the matching size-sweep row.

### s20 R>=55  (bk50d_s20_v2.0)

Trades scored: 126  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-58       12   +1.38    -5.99   0.230    0.463
D2        58-61       13   +2.93    -6.67   0.439    0.763
D3        61-61       12   -0.22    -9.15  -0.024   -0.037
D4        61-64       13   +1.53    -7.58   0.202    0.493
D5        64-65       13  +14.75   -14.36   1.027    2.021
D6        65-75       12   +3.02   -11.65   0.259    0.715
D7        75-77       13   +6.50    -9.54   0.681    1.210
D8        78-79       12   +4.72    -7.49   0.630    1.166
D9        79-89       13   +8.34   -10.53   0.792    1.413
D10       93-100      13  +10.47   -10.64   0.984    1.726
```

### s20 R>=44  (bk50d_s20_v2.0)

Trades scored: 139  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-49       13   +2.79    -5.57   0.501    0.982
D2        49-51       14   +1.22    -6.13   0.199    0.379
D3        51-54       14   +4.16    -4.36   0.955    1.364
D4        54-57       14   +0.59   -11.03   0.053    0.223
D5        58-61       14   +2.05    -7.44   0.276    0.509
D6        61-65       14   +2.91    -7.75   0.375    0.768
D7        65-68       14  +15.45   -20.53   0.752    2.007
D8        68-79       14   +6.20    -9.79   0.634    1.115
D9        79-89       14   +6.34   -10.69   0.593    1.240
D10       89-100      14  +10.40   -10.36   1.003    1.667
```

### s16 R>=55  (bk50d_s16_v2.0)

Trades scored: 131  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57       13   +1.90    -7.10   0.268    0.561
D2        57-61       13   +4.33    -6.65   0.652    1.036
D3        61-61       13   +0.55    -6.15   0.090    0.197
D4        61-65       13   +2.08    -8.31   0.250    0.617
D5        65-65       13  +15.77   -16.20   0.974    2.163
D6        65-75       13   +3.78   -11.65   0.325    0.907
D7        75-77       13   +6.32    -9.54   0.663    1.179
D8        77-79       13   +6.06    -8.33   0.727    1.371
D9        79-96       13   +4.42   -10.85   0.407    1.022
D10       96-100      14  +11.78    -9.40   1.253    1.819
```

### s16 R>=44  (bk50d_s16_v2.0)

Trades scored: 145  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-47       14   +2.67    -4.50   0.594    1.011
D2        47-50       15   +2.66    -8.58   0.311    0.857
D3        50-51       14   +2.52    -8.67   0.291    0.724
D4        51-54       15   +1.48    -5.20   0.285    0.484
D5        54-57       14   +2.64    -6.91   0.382    0.751
D6        57-61       15   +3.82    -5.76   0.663    0.875
D7        61-68       14  +12.98   -13.03   0.996    1.989
D8        68-78       15   +4.82   -10.53   0.458    0.959
D9        79-89       14   +6.20    -8.52   0.727    1.268
D10       89-100      15   +5.74   -10.45   0.549    1.136
```

### s12 R>=55  (bk50d_s12_v2.0)

Trades scored: 132  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55       13   +9.08    -9.82   0.925    1.991
D2        57-58       13   +2.62    -7.46   0.351    0.713
D3        58-61       13   +3.42    -5.99   0.571    0.866
D4        61-65       13   +1.45   -14.36   0.101    0.373
D5        65-65       14  +17.65   -16.29   1.084    2.283
D6        65-75       13   +4.35   -12.40   0.351    1.025
D7        75-75       13   +8.62    -9.54   0.904    1.428
D8        75-79       13   +4.23    -7.49   0.565    1.120
D9        79-93       13   +3.52   -11.10   0.317    0.819
D10       96-100      14  +11.11    -9.64   1.153    1.771
```

### s12 R>=44  (bk50d_s12_v2.0)

Trades scored: 145  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       14   +2.95    -4.32   0.683    1.284
D2        46-50       15   +0.98    -5.08   0.194    0.393
D3        50-51       14   +5.54    -8.47   0.654    1.240
D4        51-54       15   +2.17    -8.98   0.242    0.746
D5        54-57       14   +0.73   -10.36   0.071    0.259
D6        57-61       15   +4.22    -7.31   0.578    0.934
D7        61-65       14  +15.03   -13.26   1.133    2.258
D8        65-75       15   +4.59    -8.40   0.547    0.916
D9        75-82       14   +5.71    -7.56   0.756    1.285
D10       82-100      15   +6.15   -10.23   0.601    1.057
```

## Findings (2026-07-30 run, 2021-01-01 – 2026-06-26 — tables above regenerate on re-run)

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

Across the 9 config/size cells, R>=55 minus R>=44 CAGR averages **+6.38pp** and wins **6 of 9**
(range −3.07 to +16.95pp); Sortino is better in 7 of 9 but MaxDD in only 3 of 9. For the reference
`s12` the deltas at 3/4/5% sizing are −3.07 / **+14.32 / +16.95pp** — R>=55 leads the Final$
leaderboard (`s12 @5%`, $440,427, +63.32%) while the best Sortino is still `s12 R>=44 @3%`
(2.345). Uninvested capital still rises — 8.1–11.2% at R>=44 to 9.8–19.0% at R>=55, nearly
doubling at 3% sizing (`s20` 11.2% → 19.0%, `s12` 8.2% → 14.4%) — but far less than the 27–50% of
the earlier windows, because this one has signals to spare. The gain is sizing-dependent (it reverses at 3%), which points at which trades happen to
get funded rather than a robust edge.

**Across the three windows** the R>=55 delta runs −3.99pp → +0.02pp → +6.38pp: the same
bull-regime amplification the R>=44 gate shows in the section below, one step stronger. It wins
only where signals are plentiful, and the 2021–2026 leaderboards it now tops are the in-sample
window. **Keep `MIN_RANKING >= 44` as the reference gate**; R>=55 is a comparison row, not a
candidate replacement.

**R>=55 deciles.** Within 55..100 the score does not order the deciles: for `s12`, D5 (score
65) returns +17.65% standalone and D10 (96-100) +11.11%, but D1 (score 55) is +9.08% while D4
(61-65) is +1.45%. The same score-65 spike is D7 in the R>=44 table (+15.03%), so R>=55's
2021-2026 edge comes from funding more of that band. The 44-54 trades it drops are not a uniformly
weak tail either: the R>=44 deciles lying wholly inside 44-54 (D1-D4) return +0.98% to +5.54%,
overlapping R>=55's own 55-61 deciles (D1-D3, +2.62% to +9.08%) rather than sitting below them.

**What changed in this run.** Each config is now reported twice — through the `MIN_RANKING >= 40`
gate and with no ranking condition — so the gate's value can be read in portfolio terms rather than
inferred. This is also the first portfolio run on the 40/35/25 `QullamaggieRanking` weights
(changed 2026-07-29); the previously committed tables predated them, which is why the gated figures
moved. Two other changes moved nothing: the bar load is now bounded at the eval-window end (a
control run with the bound removed reproduces this report byte-for-byte), and the limit-order entry
comparison was removed.

1. **The ranking gate is worth +12.09pp of CAGR on average here, and it wins all nine cells.** The
   effect grows as the entry threshold loosens: +3.91 to +6.46pp at s20, +4.14 to +8.69pp at s16,
   and **+18.72 to +28.45pp at s12**. The mechanism is visible in the `skip` column — ungated s12
   generates 1,141-1,220 skipped signals against 356-420 gated. Without the gate the portfolio
   spends its cash on whatever arrives first; with it, the same cash buys a better-scoring subset.
2. **Without the gate, the SMA threshold barely matters.** Ungated at 3% sizing: s20 +31.80%,
   s16 +31.31%, s12 +30.34% — flat within noise. Gated at 3%: +35.71%, +40.00%, +49.06% — strongly
   increasing. The "looser thresholds win" conclusion is *entirely* a gate effect. A looser
   threshold is only better because it gives the ranking more candidates to choose from; on its own
   it just adds mediocre trades.
3. **Best cell is gated `s12 @4%`** — $338,569, +55.66% CAGR, Calmar 1.679, Sortino 1.485. Best
   risk-adjusted is gated `s12 @3%` (Calmar 1.808, Sortino 1.508). All nine gated cells beat buy &
   hold comfortably (SPY +13.25%, QQQ +16.28%), though s12's −27% to −34% drawdown is worse than
   SPY's −25.36%.
4. **The gate does not buy safety here, only return.** Gated drawdowns are similar to or worse than
   ungated at s12 (−33.16% vs −25.36% at 4%). It concentrates capital into higher-scoring names,
   which is a return-seeking move, not a defensive one. Contrast 2016-2020, where the same gate cut
   s12's drawdown by ~20pp.
5. **The ranking separates on return but not on risk** within the gated set. D10 is the top decile
   by CAGR in all three configs (+14.18% standalone for s12), yet s12's *D1* carries the best Calmar
   of any decile (2.059 against D10's 1.080) on the same 13-14 trades. The middle is unordered —
   D2 +1.58, D5 +2.52, D9 +3.55 against D7 +6.81 and D8 +9.02.

**How to improve performance:** prefer gated `s12` at 3-4%, keep the next-day-open entry, and keep
the plain 366d time cap.

### The ranking gate across all three windows

Gated minus ungated CAGR, all 9 config/size cells per window:

```text
window       mean delta   gate wins   range
2010-2015      -4.86pp       0 / 9    -8.72 .. -1.27
2016-2020      +3.01pp       9 / 9    +0.76 .. +7.92
2021-2026     +12.09pp       9 / 9    +3.91 .. +28.45
```

**The gate's value is regime-dependent and reverses sign.** In 2010-2015 it loses in every single
cell — it removes signals from a window that already has too few, leaving 32-64% of capital idle.
By 2016-2020 it wins every cell but modestly, and its main contribution there is drawdown: it cuts
s12's from ~−45% to ~−28%. In 2021-2026 it dominates.

Note this is *not* explained by which era the weights were fitted on: the 40/35/25 split was derived
from 2010-2020 signals (see `docs/research/result-qullamaggie-ranking-weights.md`), and 2010-2015 is
the window where the gate performs worst. The fit was on year-demeaned cross-sectional returns,
which strips exactly the time effect the portfolio sim is exposed to — so the two are not in
contradiction, but the gate should be treated as a bull-regime amplifier rather than a universally
positive filter.

### Exit variations, across all three windows

Mean CAGR delta against the plain 366d time cap, 9 config/size cells per window. Carried over from
`docs/research/result-qullamaggie-exit-sweep.md`; **these figures predate the re-weighting** and have
not been regenerated.

```text
variation      2010-2015   2016-2020   2021-2026   cells won (CAGR, of 27)
sma200x5        -2.13       -9.20       -1.91             6
dead120         -2.59       -9.70       -0.76             4
```

Neither wins a majority of cells and both change magnitude sharply between periods. The 366d time
cap remains the rule to beat.

**Entry variations are no longer measured here.** The limit-order comparison this doc used to carry
was removed from the script on 2026-07-30; that dimension belongs to
`docs/research/result-qullamaggie-cohorts-limit-order.md` and
`docs/research/result-qullamaggie-limit-fill-rate.md`, both of which need a re-run on the current
weights before their numbers can be quoted against this table.
