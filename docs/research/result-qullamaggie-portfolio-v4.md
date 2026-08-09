# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-09 19:04:03 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2021-01-01 – 2026-06-26 |
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
SPY         59,301  +13.25   -25.36   0.522    1.192
QQQ         68,525  +16.28   -35.62   0.457    1.131
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 190 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        231,265  +45.20   -31.94   1.415    1.959    186    535    9.7%
3%     ungated      202,291  +41.69   -28.99   1.438    1.838    192    719    9.0%
4%     R>=44        166,413  +36.73   -27.47   1.337    1.621    142    579    9.0%
4%     ungated      157,481  +35.36   -27.47   1.287    1.599    145    766    8.9%
5%     R>=44        218,205  +43.66   -30.67   1.424    1.817    116    605    9.5%
5%     ungated      235,503  +45.68   -30.67   1.489    1.887    117    794    9.3%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 701 signals (0 with no fillable next-day open); ungated drops 0 (2 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        232,197  +45.30   -27.37   1.655    1.933    191    663    8.0%
3%     ungated      161,339  +35.96   -27.61   1.302    1.693    194   1359    7.2%
4%     R>=44        207,336  +42.33   -29.39   1.440    1.813    146    708    8.4%
4%     ungated      182,440  +39.04   -24.65   1.584    1.767    145   1408    7.4%
5%     R>=44        191,101  +40.23   -30.55   1.317    1.731    116    738    8.1%
5%     ungated      207,319  +42.33   -26.27   1.612    1.854    116   1437    7.5%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 1550 signals (0 with no fillable next-day open); ungated drops 0 (3 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
3%     ungated      150,240  +34.20   -21.38   1.600    1.779    194   2253    5.9%
4%     R>=44        263,361  +48.68   -28.27   1.722    2.021    145    755    8.3%
4%     ungated      149,827  +34.13   -22.27   1.532    1.767    146   2301    6.2%
5%     R>=44        246,762  +46.93   -26.39   1.778    1.956    115    785    8.6%
5%     ungated      198,072  +41.15   -23.38   1.760    1.966    116   2331    6.0%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=44             3%     285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
 2  s12 R>=44             4%     263,361  +48.68   -28.27   1.722    2.021    145    755    8.3%
 3  s12 R>=44             5%     246,762  +46.93   -26.39   1.778    1.956    115    785    8.6%
 4  s20 ungated           5%     235,503  +45.68   -30.67   1.489    1.887    117    794    9.3%
 5  s16 R>=44             3%     232,197  +45.30   -27.37   1.655    1.933    191    663    8.0%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=44             3%     285,404  +50.88   -28.01   1.817    2.129    190    710    8.1%
 2  s12 R>=44             4%     263,361  +48.68   -28.27   1.722    2.021    145    755    8.3%
 3  s12 ungated           5%     198,072  +41.15   -23.38   1.760    1.966    116   2331    6.0%
 4  s20 R>=44             3%     231,265  +45.20   -31.94   1.415    1.959    186    535    9.7%
 5  s12 R>=44             5%     246,762  +46.93   -26.39   1.778    1.956    115    785    8.6%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2021      46,306  +54.35   -22.30   2.437    1.963     33    111    0.9%
                    2022      58,853  +27.10   -25.28   1.072    1.117     32     57   20.1%
                    2023      75,072  +27.56   -28.01   0.984    1.729     33    164    6.2%
                    2024      99,789  +32.92   -13.14   2.506    1.822     32    127    5.5%
                    2025     242,395 +142.91   -24.49   5.835    4.584     33    200    8.4%
                    2026     285,404  +17.74   -19.09   0.929    1.429     27     51    7.0%
s12 R>=44 4%        2021      45,212  +50.71   -24.52   2.068    1.800     24    120    3.3%
                    2022      53,901  +19.22   -27.86   0.690    0.788     24     65   18.6%
                    2023      70,018  +29.90   -28.27   1.058    1.788     25    172    3.9%
                    2024      93,944  +34.17   -14.88   2.296    1.868     24    135    4.3%
                    2025     228,300 +143.02   -26.72   5.352    4.878     24    209   11.7%
                    2026     263,361  +15.36   -17.45   0.880    1.401     24     54    7.3%
s12 R>=44 5%        2021      44,411  +48.04   -25.21   1.905    1.722     19    125    4.2%
                    2022      56,247  +26.65   -23.49   1.135    1.030     19     70   18.0%
                    2023      75,377  +34.01   -26.15   1.300    1.918     19    178    5.8%
                    2024     103,656  +37.52   -15.32   2.449    1.959     19    140    3.2%
                    2025     230,055 +121.94   -26.39   4.620    4.534     19    214   11.9%
                    2026     246,762   +7.26   -21.94   0.331    0.651     20     58    8.6%
s20 ungated 5%      2021      44,613  +48.71   -24.51   1.987    1.766     19    135    4.1%
                    2022      51,806  +16.12   -30.67   0.526    0.720     19     62   24.6%
                    2023      64,741  +24.97   -29.86   0.836    1.500     20    159    5.8%
                    2024      93,869  +44.99   -16.39   2.745    2.219     19    143    3.7%
                    2025     209,871 +123.58   -29.31   4.216    3.842     20    235    8.1%
                    2026     235,503  +12.21   -20.68   0.591    1.003     20     60    9.6%
s16 R>=44 3%        2021      46,306  +54.35   -22.30   2.437    1.963     33    103    0.9%
                    2022      53,368  +15.25   -26.56   0.574    0.692     32     51   21.3%
                    2023      66,671  +24.93   -26.76   0.932    1.657     32    161    8.1%
                    2024      86,398  +29.59   -14.18   2.087    1.677     32    120    5.9%
                    2025     197,603 +128.71   -27.37   4.702    3.960     34    178    5.0%
                    2026     232,197  +17.51   -20.44   0.856    1.378     28     50    5.7%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $285,404)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.7|33   +24.0|0    +1.3|0    +3.5|0   +10.9|0    +5.9|0   -10.2|0    +1.2|0   +11.0|0    +8.3|0    -6.1|0    +4.5|0 |   +54.4    33
 2022 |    +6.6|1    +2.5|5   +0.3|23   -12.1|3    +7.5|0    -7.6|0   +15.4|0    +5.2|0   -11.0|0   +13.8|0    +6.7|0    +1.4|0 |   +27.1    32
 2023 |    +7.1|1    +1.2|6    -7.8|4    -3.2|9   +8.8|13   +11.8|0   +11.3|0    -8.8|0    -8.8|0   -11.8|0   +16.9|0   +13.5|0 |   +27.6    33
 2024 |    -6.9|0   +10.9|6    -1.3|2    -7.2|8    +9.3|9    -5.9|7    +8.2|0    +5.1|0    +3.9|0    +3.9|0   +10.8|0    +0.4|0 |   +32.9    32
 2025 |    +6.4|0    -7.6|3    -4.7|1    +1.3|0   +4.0|16  +14.5|13   +34.4|0   +14.0|0   +14.4|0   +18.6|0    +3.7|0    -0.4|0 |  +142.9    33
 2026 |    +5.9|0    -0.9|1    -7.2|2    +9.4|4   +11.2|8   -0.7|12         ·         ·         ·         ·         ·         · |   +17.7    27
```

### s12 R>=44 — size 4%  (Final $263,361)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.3|24   +22.4|0    +0.2|0    +2.6|0   +12.1|0    +8.0|0   -12.2|0    +1.2|0   +12.2|0    +9.5|0    -7.2|0    +3.1|0 |   +50.7    24
 2022 |    +8.5|1    +3.3|5   +0.3|18   -14.2|0    +8.6|0    -8.9|0   +16.5|0    +4.5|0   -12.1|0   +14.2|0    +6.7|0    -4.2|0 |   +19.2    24
 2023 |    +8.2|1    +1.3|6    -6.4|5    -4.3|9    +8.7|4   +13.9|0    +9.4|0    -8.5|0   -10.2|0   -11.1|0   +18.6|0   +12.8|0 |   +29.9    25
 2024 |    -6.4|0    +9.6|6    -2.9|3    -7.2|8    +9.9|7    -7.3|0    +8.2|0    +8.3|0    +6.3|0    +1.2|0    +6.7|0    +6.0|0 |   +34.2    24
 2025 |    +2.9|0    -7.1|3    -5.6|1    -0.1|0   -0.1|16   +15.9|4   +43.7|0   +14.3|0   +15.9|0   +17.9|0    +4.5|0    -0.8|0 |  +143.0    24
 2026 |    +2.3|0    +2.2|1    -7.7|2    +9.3|4    +8.2|8    +1.1|9         ·         ·         ·         ·         ·         · |   +15.4    24
```

### s12 R>=44 — size 5%  (Final $246,762)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.8|19   +21.7|0    +0.9|0    +1.3|0   +11.6|0    +7.5|0   -12.7|0    +1.1|0   +12.3|0    +8.7|0    -7.2|0    +3.0|0 |   +48.0    19
 2022 |    +8.5|1    +4.1|5   +0.9|13   -12.3|0   +10.6|0   -10.2|0   +13.6|0    +4.0|0   -12.1|0   +19.7|0    +5.4|0    -2.6|0 |   +26.7    19
 2023 |    +8.0|1    -0.2|6    -6.0|4    -4.7|8    +9.7|0   +15.3|0    +9.8|0    -7.3|0    -8.8|0   -10.7|0   +16.3|0   +14.1|0 |   +34.0    19
 2024 |    -7.7|1    +9.6|6    -1.7|2    -7.8|8    +8.7|2    -6.9|0    +6.3|0   +10.4|0    +7.2|0    +4.6|0    +8.6|0    +3.7|0 |   +37.5    19
 2025 |    +5.6|1   -12.4|3    -3.0|1    -1.3|0   -1.4|14   +15.7|0   +44.1|0   +11.5|0   +17.8|0   +13.4|0    +3.1|0    -0.6|0 |  +121.9    19
 2026 |    +3.1|1    -2.4|1    -9.6|2    +5.6|5    +7.4|9    +4.1|2         ·         ·         ·         ·         ·         · |    +7.3    20
```

### s20 ungated — size 5%  (Final $235,503)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -2.9|19   +21.0|0    +1.1|0    +2.0|0   +11.2|0    +7.2|0   -12.3|0    +1.5|0   +11.7|0    +7.9|0    -7.0|0    +3.1|0 |   +48.7    19
 2022 |    +7.8|0    +0.8|2   -2.1|16   -15.0|1    +4.1|0    -5.5|0   +15.6|0    +6.5|0   -14.0|0   +12.6|0    +6.4|0    +2.9|0 |   +16.1    19
 2023 |    +6.5|0    -4.1|3    -8.3|2    -2.3|8   +11.3|7   +10.6|0   +12.1|0    -9.1|0    -8.6|0   -13.4|0   +22.2|0   +12.4|0 |   +25.0    20
 2024 |    -8.0|0   +14.3|3    +0.6|0    -6.0|7   +10.4|9   -10.5|0    +4.8|0    +8.3|0    +7.7|0    +5.3|0    +8.5|0    +5.7|0 |   +45.0    19
 2025 |    +2.3|0    -4.4|1    -5.7|1    -4.2|0   +3.1|15   +20.3|3   +39.2|0   +13.8|0   +16.6|0   +14.0|0    -0.8|0    -2.3|0 |  +123.6    20
 2026 |    +1.4|0    +3.0|0   -12.2|0    +7.9|6    +5.9|8    +7.1|6         ·         ·         ·         ·         ·         · |   +12.2    20
```

### s16 R>=44 — size 3%  (Final $232,197)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.7|33   +24.0|0    +1.3|0    +3.5|0   +10.9|0    +5.9|0   -10.2|0    +1.2|0   +11.0|0    +8.3|0    -6.1|0    +4.5|0 |   +54.4    33
 2022 |    +6.6|1    +2.0|4   -0.8|19   -13.2|8    +5.6|0    -9.0|0   +13.8|0    +5.9|0   -10.7|0   +13.0|0    +4.5|0    +0.8|0 |   +15.3    32
 2023 |    +9.7|2    -1.7|4    -8.1|3    -2.0|9   +6.0|14    +9.9|0   +13.9|0    -9.0|0    -8.3|0   -10.3|0   +14.8|0   +12.9|0 |   +24.9    32
 2024 |    -6.2|2    +8.7|4    -1.3|0    -6.0|8    +7.3|9    -5.1|9    +5.6|0    +8.3|0    +3.1|0    +3.8|0   +10.7|0    -0.7|0 |   +29.6    32
 2025 |    +5.9|2    -7.2|2    -6.4|1    -0.5|0   +8.4|15  +17.1|12   +31.4|2   +10.9|0   +16.4|0   +13.4|0    +3.7|0    -1.3|0 |  +128.7    34
 2026 |    +5.4|1    -2.9|1    -6.7|1    +8.5|5    +6.7|7   +6.1|13         ·         ·         ·         ·         ·         · |   +17.5    28
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 142  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-47       14   +1.78    -4.68   0.381    0.673
D2        47-51       14   +1.92    -8.14   0.236    0.596
D3        51-54       14   +3.83    -4.71   0.813    1.140
D4        54-54       14   +1.38    -6.87   0.201    0.533
D5        55-61       15   +4.18    -5.70   0.733    1.001
D6        61-64       14   -0.10   -12.25  -0.008    0.005
D7        64-68       14   +5.79   -14.46   0.400    0.859
D8        75-79       14   +6.86   -11.94   0.574    1.177
D9        79-89       14   +5.54    -9.20   0.602    1.159
D10       89-100      15   +6.71    -7.63   0.879    1.309
```

### s16  (bk50d_s16_v2.0)

Trades scored: 146  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       14   +4.54    -4.52   1.006    1.503
D2        46-50       15   +1.41    -8.17   0.172    0.498
D3        50-51       14   +3.31    -8.06   0.411    0.898
D4        51-54       15   +1.14    -4.98   0.229    0.398
D5        54-57       15   +3.45    -7.93   0.436    0.947
D6        58-61       14   +1.85    -7.40   0.250    0.468
D7        61-68       15  +12.03   -14.25   0.844    1.849
D8        69-79       14   +6.27    -9.93   0.631    1.196
D9        79-89       15   +5.64    -8.52   0.662    1.177
D10       89-100      15   +5.92    -7.93   0.746    1.155
```

### s12  (bk50d_s12_v2.0)

Trades scored: 145  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-47       14   +3.54    -5.07   0.699    1.243
D2        47-50       15   +7.07   -12.46   0.567    1.252
D3        50-51       14   +4.80    -7.01   0.684    1.241
D4        51-54       15   +1.91    -5.84   0.328    0.629
D5        54-58       14   +2.59    -6.47   0.401    0.803
D6        58-61       15   +1.90    -8.18   0.232    0.475
D7        61-68       14  +13.52   -12.76   1.060    1.996
D8        68-79       15   +5.96    -9.98   0.597    1.097
D9        79-89       14   +5.02    -8.52   0.589    1.081
D10       89-100      15   +5.84    -7.93   0.736    1.135
```

## Findings (2026-07-30 run, 2021-01-01 – 2026-06-26 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.

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
