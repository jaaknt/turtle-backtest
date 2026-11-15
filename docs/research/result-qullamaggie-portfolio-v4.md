# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-11-15 01:37:26 Tallinn time

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

**Ranking gate:** `R>=55` drops 472 signals (0 with no fillable next-day open); `R>=44` drops 177 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        219,825  +43.86   -23.78   1.845    2.050    161    211   18.2%
3%     R>=44        191,181  +40.24   -30.68   1.311    1.814    180    487    9.8%
3%     ungated      211,922  +42.90   -29.89   1.435    1.856    181    663    8.9%
4%     R>=55        252,419  +47.54   -34.64   1.372    1.997    132    240   13.7%
4%     R>=44        237,003  +45.85   -28.91   1.586    1.926    141    526    9.1%
4%     ungated      215,258  +43.31   -27.47   1.576    1.882    145    699    9.1%
5%     R>=55        286,642  +51.00   -33.21   1.535    2.007    108    264   11.9%
5%     R>=44        224,900  +44.46   -30.67   1.450    1.858    116    551    9.3%
5%     ungated      221,850  +44.10   -30.67   1.438    1.857    117    727    9.4%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1057 signals (0 with no fillable next-day open); `R>=44` drops 659 signals (0 with no fillable next-day open); `ungated` drops 0 signals (2 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        279,542  +50.31   -30.18   1.667    2.163    171    214   14.4%
3%     R>=44        268,827  +49.24   -30.37   1.621    2.067    185    598    8.1%
3%     ungated      150,243  +34.20   -25.22   1.356    1.645    192   1248    7.8%
4%     R>=55        330,543  +54.98   -32.07   1.714    2.105    132    253   10.7%
4%     R>=44        211,742  +42.88   -28.46   1.507    1.829    145    638    8.7%
4%     ungated      164,431  +36.43   -24.62   1.479    1.692    145   1295    7.5%
5%     R>=55        338,203  +55.63   -32.84   1.694    2.032    110    275    9.6%
5%     R>=44        206,190  +42.19   -27.89   1.512    1.778    117    666    8.4%
5%     ungated      189,431  +40.00   -26.27   1.523    1.786    114   1326    7.8%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1927 signals (0 with no fillable next-day open); `R>=44` drops 1487 signals (0 with no fillable next-day open); `ungated` drops 0 signals (3 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        307,368  +52.94   -34.35   1.541    2.192    175    211   12.8%
3%     R>=44        292,095  +51.52   -29.53   1.744    2.153    189    637    8.4%
3%     ungated      163,670  +36.31   -22.03   1.649    1.856    195   2115    6.0%
4%     R>=55        336,434  +55.48   -32.41   1.712    2.093    133    253    9.8%
4%     R>=44        241,509  +46.35   -26.80   1.730    1.947    145    681    8.0%
4%     ungated      163,436  +36.28   -21.45   1.691    1.874    145   2165    6.4%
5%     R>=55        360,641  +57.47   -31.55   1.822    2.061    108    278    9.2%
5%     R>=44        241,165  +46.31   -27.36   1.693    1.922    115    711    8.4%
5%     ungated      218,479  +43.70   -25.13   1.739    2.090    115   2195    6.1%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=55             5%     360,641  +57.47   -31.55   1.822    2.061    108    278    9.2%
 2  s16 R>=55             5%     338,203  +55.63   -32.84   1.694    2.032    110    275    9.6%
 3  s12 R>=55             4%     336,434  +55.48   -32.41   1.712    2.093    133    253    9.8%
 4  s16 R>=55             4%     330,543  +54.98   -32.07   1.714    2.105    132    253   10.7%
 5  s12 R>=55             3%     307,368  +52.94   -34.35   1.541    2.192    175    211   12.8%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=55             3%     307,368  +52.94   -34.35   1.541    2.192    175    211   12.8%
 2  s16 R>=55             3%     279,542  +50.31   -30.18   1.667    2.163    171    214   14.4%
 3  s12 R>=44             3%     292,095  +51.52   -29.53   1.744    2.153    189    637    8.4%
 4  s16 R>=55             4%     330,543  +54.98   -32.07   1.714    2.105    132    253   10.7%
 5  s12 R>=55             4%     336,434  +55.48   -32.41   1.712    2.093    133    253    9.8%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2021      43,300  +44.33   -22.73   1.951    1.718     32    100    3.2%
                    2022      56,539  +30.58   -24.12   1.267    1.244     32     54   20.2%
                    2023      74,726  +32.17   -24.29   1.325    2.005     33    156    7.4%
                    2024     107,846  +44.32   -15.21   2.915    2.335     33    106    6.2%
                    2025     242,529 +124.88   -29.53   4.229    3.930     33    176    5.8%
                    2026     292,095  +20.44   -18.91   1.081    1.653     26     45    7.0%
s12 R>=44 4%        2021      46,552  +55.17   -24.84   2.221    1.898     24    108    3.1%
                    2022      55,947  +20.18   -26.24   0.769    0.830     24     62   18.8%
                    2023      73,849  +32.00   -26.80   1.194    1.901     25    164    5.0%
                    2024      99,591  +34.86   -14.41   2.419    1.884     24    115    4.7%
                    2025     214,884 +115.77   -24.41   4.742    4.101     24    185    7.2%
                    2026     241,509  +12.39   -18.42   0.673    1.107     24     47   10.0%
s12 R>=44 5%        2021      45,343  +51.14   -26.51   1.929    1.744     19    113    4.0%
                    2022      57,623  +27.08   -24.07   1.125    1.040     19     67   18.1%
                    2023      72,522  +25.86   -27.36   0.945    1.664     20    169    4.2%
                    2024      97,633  +34.63   -17.17   2.017    1.812     19    120    5.1%
                    2025     226,492 +131.98   -26.92   4.902    4.420     19    190    8.8%
                    2026     241,165   +6.48   -19.47   0.333    0.609     19     52   12.0%
s12 R>=55 5%        2021      51,733  +72.44   -23.68   3.059    2.255     19     39    3.9%
                    2022      63,049  +21.87   -31.55   0.693    0.878     19     26   20.5%
                    2023      90,163  +43.01   -30.54   1.408    2.290     19     69   13.0%
                    2024     118,865  +31.83   -19.04   1.672    1.535     19     51    5.5%
                    2025     244,209 +105.45   -30.63   3.443    2.992     20     76    4.2%
                    2026     360,641  +47.68   -23.29   2.047    2.782     12     17    6.5%
s16 R>=55 5%        2021      51,733  +72.44   -23.68   3.059    2.255     19     38    3.9%
                    2022      56,450   +9.12   -30.84   0.296    0.464     19     24   20.9%
                    2023      77,603  +37.47   -28.08   1.335    2.081     19     69   12.2%
                    2024     102,588  +32.20   -19.54   1.647    1.529     19     52    6.4%
                    2025     280,823 +173.74   -32.84   5.290    4.182     20     75    4.1%
                    2026     338,203  +20.43   -20.83   0.981    1.502     14     17   11.0%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $292,095)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.0|32   +21.6|0    +0.8|0    +3.3|0    +9.2|0    +5.3|0   -10.4|0    +0.3|0    +9.7|0    +8.2|0    -5.5|0    +3.4|0 |   +44.3    32
 2022 |    +6.7|1    +2.5|5   -0.2|21   -11.2|5    +7.7|0    -7.8|0   +15.8|0    +4.6|0   -11.3|0   +13.4|0    +8.0|0    +3.2|0 |   +30.6    32
 2023 |    +6.2|1    +0.2|6    -6.2|4    -3.0|6   +5.6|14   +12.8|2   +10.9|0    -6.8|0    -9.1|0    -8.9|0   +16.8|0   +14.6|0 |   +32.2    33
 2024 |    -5.9|0    +9.4|6    +0.5|2    -5.3|5    +5.7|8   -2.4|10    +8.2|2    +4.2|0    +5.9|0    +6.4|0   +10.7|0    +1.5|0 |   +44.3    33
 2025 |    +5.7|0    -4.2|3    -9.1|1    +3.7|0   +2.3|14  +17.5|10   +28.9|5   +13.7|0   +17.9|0   +11.6|0    +4.0|0    -2.3|0 |  +124.9    33
 2026 |    +2.7|0    +3.1|0    -8.5|2    +9.3|6    +9.8|9    +3.5|9         ·         ·         ·         ·         ·         · |   +20.4    26
```

### s12 R>=44 — size 4%  (Final $241,509)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.4|24   +22.7|0    +0.2|0    +2.6|0   +12.0|0    +8.0|0   -12.1|0    +1.0|0   +12.2|0   +10.8|0    -7.2|0    +3.8|0 |   +55.2    24
 2022 |    +8.2|1    +3.3|5   -0.5|18   -13.9|0    +9.4|0    -8.7|0   +15.8|0    +3.4|0   -12.1|0   +15.0|0    +7.2|0    -3.1|0 |   +20.2    24
 2023 |    +8.9|1    +1.3|6    -6.0|5    -3.7|6    +6.6|7   +13.4|0   +11.3|0    -7.7|0    -9.8|0   -10.4|0   +18.2|0   +11.5|0 |   +32.0    25
 2024 |    -8.4|1    +8.9|6    -2.9|2    -5.4|5    +8.3|8    -5.9|2    +9.7|0   +10.5|0    +4.6|0    +1.8|0    +6.2|0    +5.2|0 |   +34.9    24
 2025 |    -0.2|1    -4.0|3    -6.1|1    +1.7|0   +0.4|15   +15.7|4   +34.6|0   +14.3|0   +16.6|0   +13.8|0    +1.0|0    -1.5|0 |  +115.8    24
 2026 |    +0.6|0    +2.1|0   -10.0|2    +8.1|7    +9.7|9    +2.5|6         ·         ·         ·         ·         ·         · |   +12.4    24
```

### s12 R>=44 — size 5%  (Final $241,165)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.6|19   +21.7|0    +0.6|0    +2.1|0   +12.9|0    +8.1|0   -13.2|0    +0.2|0   +13.8|0    +9.5|0    -8.1|0    +3.2|0 |   +51.1    19
 2022 |    +9.3|1    +4.1|5   +0.0|13   -12.4|0   +11.7|0    -8.9|0   +15.0|0    +2.7|0   -13.1|0   +18.1|0    +6.0|0    -2.5|0 |   +27.1    19
 2023 |    +7.5|1    -1.7|6    -4.8|4    -4.6|6    +4.8|3   +13.9|0    +9.0|0    -8.8|0   -10.3|0    -9.6|0   +20.5|0   +13.3|0 |   +25.9    20
 2024 |    -8.1|1   +11.0|6    -4.8|1    -6.4|5    +5.6|6    -4.3|0   +11.5|0   +10.8|0    +4.8|0    +2.0|0    +5.0|0    +5.7|0 |   +34.6    19
 2025 |    +2.6|1    -4.2|3    -6.7|1    +1.9|0   -0.5|14   +16.3|0   +43.9|0   +11.2|0   +18.7|0   +11.8|0    +2.2|0    -1.2|0 |  +132.0    19
 2026 |    +0.7|0    +0.6|0    -9.9|2    +8.1|7    +7.8|8    +0.2|2         ·         ·         ·         ·         ·         · |    +6.5    19
```

### s12 R>=55 — size 5%  (Final $360,641)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.9|19   +27.8|0    +1.0|0    +4.7|0   +11.1|0    +9.3|0   -11.7|0    +1.7|0   +13.6|0   +12.0|0    -6.7|0    +3.8|0 |   +72.4    19
 2022 |    +7.5|1    +3.5|1   -0.2|12   -15.5|5    +6.1|0    -8.8|0   +21.6|0    +9.4|0   -13.7|0   +13.5|0    +9.0|0    -5.4|0 |   +21.9    19
 2023 |    +9.9|1    -0.9|1    -3.7|1    -2.6|3    +5.5|8    +8.5|5   +12.7|0   -10.4|0   -11.8|0   -10.3|0   +24.4|0   +23.1|0 |   +43.0    19
 2024 |    -4.8|1    +9.7|1    -2.0|0    -6.5|3    +4.7|6    -2.7|6    +6.9|2    +1.6|0    +4.6|0    +4.1|0   +17.4|0    -2.6|0 |   +31.8    19
 2025 |   +11.6|0    -4.5|2   -10.4|0    +3.6|0    +5.4|6   +17.6|6    +6.2|6   +18.4|0   +24.5|0   +10.9|0    +3.0|0    -6.3|0 |  +105.5    20
 2026 |   +13.5|0    +2.0|0    -9.7|0   +10.8|1   +11.4|5   +14.5|6         ·         ·         ·         ·         ·         · |   +47.7    12
```

### s16 R>=55 — size 5%  (Final $338,203)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.9|19   +27.8|0    +1.0|0    +4.7|0   +11.1|0    +9.3|0   -11.7|0    +1.7|0   +13.6|0   +12.0|0    -6.7|0    +3.8|0 |   +72.4    19
 2022 |    +7.5|1    +3.5|1   -0.2|11   -16.1|6    +4.8|0    -8.4|0   +18.2|0    +6.6|0   -14.1|0   +14.9|0    +6.2|0    -7.6|0 |    +9.1    19
 2023 |   +11.5|1    -3.7|1    -4.1|2    -2.9|3    +6.0|8    +9.1|4   +10.9|0    -8.9|0   -11.2|0    -9.0|0   +20.6|0   +20.9|0 |   +37.5    19
 2024 |    -5.2|1   +11.2|1    -2.7|0    -7.5|4    +4.1|6    -1.8|6    +6.6|1    +1.5|0    +4.5|0    +3.8|0   +18.2|0    -1.8|0 |   +32.2    19
 2025 |   +10.4|0    -5.2|2   -12.5|1    +4.1|0    +6.7|6   +21.1|6   +36.0|5   +17.4|0   +20.8|0   +13.3|0    +5.3|0    -3.5|0 |  +173.7    20
 2026 |    +3.8|0    +3.2|0   -10.5|0    +8.6|5   +11.7|5    +3.6|4         ·         ·         ·         ·         ·         · |   +20.4    14
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return. Each config is decomposed once per gated signal set, strictest gate first as in the size sweep: the deciles split the trades that gate's own run took, so each table spans only that gate..100 and reads against the matching size-sweep row.

### s20 R>=55  (bk50d_s20_v2.0)

Trades scored: 132  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-58       13   +0.98    -6.02   0.162    0.357
D2        58-61       13   +3.98    -9.42   0.422    0.942
D3        61-61       13   -0.21    -9.22  -0.023   -0.034
D4        61-65       13   +2.20    -8.93   0.246    0.614
D5        65-65       14  +13.60   -17.50   0.777    1.890
D6        65-75       13   +5.95   -12.40   0.480    1.185
D7        75-79       13   +5.71    -7.59   0.753    1.197
D8        79-82       13   +7.89    -8.33   0.947    1.821
D9        82-93       13   +2.95   -11.52   0.256    0.767
D10       96-100      14  +10.14    -8.88   1.141    1.665
```

### s20 R>=44  (bk50d_s20_v2.0)

Trades scored: 141  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-49       14   +2.61    -5.45   0.478    0.909
D2        50-51       14   +0.24    -9.08   0.026    0.105
D3        51-54       14   +2.05    -6.15   0.333    0.683
D4        54-58       14   +1.22    -8.51   0.143    0.420
D5        58-63       14   +0.97    -9.66   0.101    0.282
D6        64-65       14  +15.33   -15.28   1.003    2.059
D7        65-75       14   +5.92   -12.40   0.478    1.177
D8        75-79       14   +5.88    -8.96   0.657    1.256
D9        79-93       14   +4.45   -12.04   0.370    1.018
D10       93-100      15  +10.34    -9.42   1.098    1.656
```

### s16 R>=55  (bk50d_s16_v2.0)

Trades scored: 132  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57       13  +10.85   -11.03   0.983    2.274
D2        58-61       13   +4.27    -5.98   0.715    1.070
D3        61-61       13   +1.88    -6.72   0.280    0.620
D4        63-65       13   +1.86   -11.51   0.162    0.446
D5        65-68       14   +8.62   -18.78   0.459    1.138
D6        68-75       13   +5.70   -12.40   0.460    1.184
D7        75-79       13   +4.89    -9.19   0.532    1.001
D8        79-82       13   +6.68    -7.82   0.854    1.696
D9        82-96       13   +1.20   -13.11   0.091    0.341
D10       96-100      14  +12.33   -10.42   1.184    1.850
```

### s16 R>=44  (bk50d_s16_v2.0)

Trades scored: 145  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       14   +0.95    -3.09   0.307    0.424
D2        47-50       15   +2.90    -8.17   0.354    0.829
D3        50-51       14   +2.22    -8.59   0.258    0.649
D4        51-54       15   +0.50    -7.57   0.066    0.204
D5        54-61       14   +4.21    -6.28   0.671    0.955
D6        61-65       15   +0.64   -13.25   0.049    0.205
D7        65-68       14  +12.57   -14.93   0.842    1.824
D8        68-79       15   +8.37   -10.82   0.774    1.408
D9        79-89       14   +7.99    -8.52   0.937    1.428
D10       89-100      15   +5.67    -9.41   0.603    1.131
```

### s12 R>=55  (bk50d_s12_v2.0)

Trades scored: 133  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57       13  +11.51   -11.46   1.005    2.202
D2        57-61       13   +4.23    -5.72   0.741    1.164
D3        61-63       13   +0.55    -8.65   0.063    0.195
D4        63-65       14   +5.06   -13.90   0.364    0.944
D5        65-68       13   +5.52   -18.70   0.295    0.806
D6        68-75       13   +7.99   -12.40   0.644    1.510
D7        75-79       14   +5.04   -10.59   0.476    1.010
D8        79-82       13   +4.15    -8.57   0.484    0.987
D9        82-96       13   +1.58    -9.76   0.162    0.460
D10       96-100      14  +11.98   -10.65   1.125    1.871
```

### s12 R>=44  (bk50d_s12_v2.0)

Trades scored: 145  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-47       14   +1.11    -4.17   0.266    0.474
D2        47-50       15   +2.39    -8.34   0.287    0.668
D3        51-51       14   +4.86    -5.61   0.867    1.406
D4        51-54       15   +0.78    -7.57   0.103    0.297
D5        54-61       14   +4.95    -5.59   0.884    1.177
D6        61-65       15   +1.75    -5.13   0.341    0.509
D7        65-68       14  +12.16   -14.32   0.849    1.782
D8        69-79       15   +8.15   -10.82   0.753    1.354
D9        79-89       14   +4.94    -8.52   0.580    1.179
D10       93-100      15   +6.05    -9.13   0.663    1.174
```

## Findings (2026-07-30 run, 2021-01-01 – 2026-06-26 — tables above regenerate on re-run)

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
