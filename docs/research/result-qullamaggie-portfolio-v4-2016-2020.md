# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-11-15 01:38:44 Tallinn time

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
SPY         55,797  +13.23   -34.10   0.388    1.030
QQQ         85,956  +23.46   -28.56   0.821    1.492
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 634 signals (0 with no fillable next-day open); `R>=44` drops 196 signals (0 with no fillable next-day open); `ungated` drops 0 signals (0 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        123,179  +32.68   -36.05   0.907    1.863    117    358   39.7%
3%     R>=44        129,815  +34.09   -24.03   1.418    1.934    139    774   24.3%
3%     ungated      130,254  +34.18   -21.78   1.569    1.972    143    966   22.6%
4%     R>=55        141,541  +36.43   -28.33   1.286    2.032     95    380   33.7%
4%     R>=44        151,987  +38.39   -22.73   1.688    2.090    105    808   23.7%
4%     ungated      142,991  +36.71   -25.90   1.417    2.068    110    999   21.0%
5%     R>=55        168,985  +41.35   -21.96   1.883    2.187     81    394   28.1%
5%     R>=44        150,855  +38.18   -26.17   1.459    2.044     88    825   21.7%
5%     ungated      155,565  +39.03   -31.68   1.232    2.056     89   1020   19.6%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1223 signals (0 with no fillable next-day open); `R>=44` drops 711 signals (1 with no fillable next-day open); `ungated` drops 0 signals (4 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        143,067  +36.72   -39.30   0.934    2.039    114    360   39.6%
3%     R>=44        135,694  +35.28   -26.46   1.333    1.959    142    843   22.5%
3%     ungated      137,462  +35.63   -42.26   0.843    1.836    158   1535   13.7%
4%     R>=55        178,539  +42.92   -33.58   1.278    2.316     97    377   33.3%
4%     R>=44        138,957  +35.92   -30.25   1.188    1.967    108    877   20.5%
4%     ungated      126,496  +33.39   -44.54   0.750    1.662    122   1571   11.0%
5%     R>=55        198,596  +46.00   -26.45   1.739    2.433     80    394   29.3%
5%     R>=44        141,041  +36.33   -33.97   1.070    1.964     87    898   19.9%
5%     ungated      116,485  +31.21   -40.66   0.768    1.566     96   1597   11.8%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `R>=55` drops 1956 signals (0 with no fillable next-day open); `R>=44` drops 1419 signals (1 with no fillable next-day open); `ungated` drops 0 signals (4 with no fillable next-day open). Each sizing is listed strictest gate first, so the rows read across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=55        130,201  +34.16   -42.08   0.812    1.903    114    356   39.7%
3%     R>=44        153,167  +38.60   -22.35   1.727    2.183    140    866   22.9%
3%     ungated       94,428  +25.81   -43.80   0.589    1.322    164   2258    9.5%
4%     R>=55        160,768  +39.95   -40.25   0.993    2.121     97    373   33.1%
4%     R>=44        157,925  +39.45   -24.50   1.611    2.194    107    899   22.1%
4%     ungated       91,280  +24.96   -45.41   0.550    1.252    121   2301    9.5%
5%     R>=55        185,127  +43.96   -36.79   1.195    2.270     82    388   28.3%
5%     R>=44        145,623  +37.21   -30.58   1.217    2.016     88    918   20.1%
5%     ungated       98,389  +26.85   -45.54   0.590    1.310     96   2326    9.9%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=55             5%     198,596  +46.00   -26.45   1.739    2.433     80    394   29.3%
 2  s12 R>=55             5%     185,127  +43.96   -36.79   1.195    2.270     82    388   28.3%
 3  s16 R>=55             4%     178,539  +42.92   -33.58   1.278    2.316     97    377   33.3%
 4  s20 R>=55             5%     168,985  +41.35   -21.96   1.883    2.187     81    394   28.1%
 5  s12 R>=55             4%     160,768  +39.95   -40.25   0.993    2.121     97    373   33.1%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=55             5%     198,596  +46.00   -26.45   1.739    2.433     80    394   29.3%
 2  s16 R>=55             4%     178,539  +42.92   -33.58   1.278    2.316     97    377   33.3%
 3  s12 R>=55             5%     185,127  +43.96   -36.79   1.195    2.270     82    388   28.3%
 4  s12 R>=44             4%     157,925  +39.45   -24.50   1.611    2.194    107    899   22.1%
 5  s20 R>=55             5%     168,985  +41.35   -21.96   1.883    2.187     81    394   28.1%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2016      44,449  +48.16   -11.05   4.358    2.751     33    158   22.0%
                    2017      53,440  +20.23    -6.57   3.077    2.070     31     14   41.2%
                    2018      65,970  +23.45   -15.32   1.530    1.498     12     15   20.7%
                    2019      90,047  +36.50   -12.56   2.905    2.327     32     48   12.3%
                    2020     153,167  +70.10   -22.35   3.136    2.391     32    631   18.4%
s12 R>=44 4%        2016      43,429  +44.76   -11.54   3.879    2.635     24    167   23.0%
                    2017      53,905  +24.12    -6.03   3.998    2.395     24     21   35.1%
                    2018      61,102  +13.35   -16.81   0.794    0.860     11     16   22.5%
                    2019      83,583  +36.79   -12.30   2.991    2.254     24     56   12.0%
                    2020     157,925  +88.94   -24.50   3.631    2.789     24    639   18.0%
s12 R>=44 5%        2016      42,826  +42.75   -12.41   3.446    2.445     19    172   23.2%
                    2017      54,846  +28.07    -7.29   3.853    2.622     19     26   31.0%
                    2018      60,017   +9.43   -20.21   0.467    0.538     11     16   21.5%
                    2019      77,957  +29.89   -16.96   1.762    1.841     20     60   10.7%
                    2020     145,623  +86.80   -30.58   2.838    2.644     19    644   14.4%
s16 R>=55 5%        2016      46,136  +53.79   -10.28   5.233    2.748     20     82   21.5%
                    2017      56,211  +21.84    -8.72   2.503    2.241     15      3   50.5%
                    2018      80,123  +42.54   -13.35   3.187    2.304      7      2   19.5%
                    2019      93,204  +16.33   -15.38   1.062    1.319     19      5   41.5%
                    2020     198,596 +113.08   -26.45   4.275    3.230     19    302   13.8%
s12 R>=55 5%        2016      46,136  +53.79   -10.28   5.233    2.748     20     79   21.5%
                    2017      56,271  +21.97    -8.72   2.518    2.254     15      3   50.5%
                    2018      78,837  +40.10   -14.21   2.822    2.180      8      2   19.1%
                    2019      86,325   +9.50   -18.37   0.517    0.773     20      3   41.7%
                    2020     185,127 +114.45   -36.79   3.111    3.039     19    301    9.1%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $153,167)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.2|33   +12.8|0    -3.1|0    +3.1|0   +10.1|0    +3.7|0    +4.8|0    -3.1|0   +15.2|0    -1.7|0 |   +48.2    33
 2017 |    +6.3|0    -1.2|0    -0.1|2    +0.2|0    +0.4|3    +3.4|3    +0.1|3    -0.8|5    +1.0|5    +1.6|8    +4.2|1    +3.6|1 |   +20.2    31
 2018 |    +1.0|0    -4.4|0    +3.3|0    +8.4|3   +13.7|3    -0.8|3    +3.7|0   +12.0|1    +0.0|1    -6.3|0    -1.2|0    -5.9|1 |   +23.4    12
 2019 |    +6.8|0   +2.1|14    +1.2|7    -1.3|2    -7.2|3   +16.3|3    +2.2|0    -6.2|2    -0.3|1    +4.1|0    +4.8|0   +11.3|0 |   +36.5    32
 2020 |    -4.6|0    -0.5|1    -7.5|0    +6.6|0   +1.3|25    +4.5|3    +4.6|0   +12.4|2    -5.8|1    -2.6|0   +37.6|0   +15.6|0 |   +70.1    32
```

### s12 R>=44 — size 4%  (Final $157,925)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.8|24   +12.2|0    -3.3|0    +0.8|0    +9.4|0    +4.2|0    +5.3|0    -3.0|0   +16.5|0    -1.7|0 |   +44.8    24
 2017 |    +6.4|0    -1.5|0    +0.4|2    +0.3|0    +0.6|3    +4.6|3    +0.1|3    -1.0|5    +1.4|5    +1.3|3    +4.8|0    +4.8|0 |   +24.1    24
 2018 |    +1.8|0    -3.4|0    +2.8|0    +8.0|2   +11.9|3    +0.1|3    +2.7|0    +6.0|1    -1.8|1    -4.5|0    -2.9|0    -6.5|1 |   +13.4    11
 2019 |    +7.7|0   +2.1|14    +1.1|1    -1.5|1    -5.3|1   +15.4|3    +2.1|0    -6.4|2    -0.5|1    +3.0|0    +5.2|0   +10.8|1 |   +36.8    24
 2020 |    -5.4|0    +1.0|1    -9.4|0    +8.7|0   +4.6|17    +5.0|2    +3.8|0   +14.1|3    -3.9|1    -4.5|0   +40.7|0   +19.6|0 |   +88.9    24
```

### s12 R>=44 — size 5%  (Final $145,623)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.9|19   +10.3|0    -2.7|0    -0.3|0    +9.8|0    +4.8|0    +5.9|0    -1.7|0   +15.8|0    -3.0|0 |   +42.8    19
 2017 |    +5.9|0    -2.5|0    +1.4|2    +0.4|0    +0.7|3    +5.7|3    +0.1|3    -1.3|5    +1.6|3    +2.4|0    +5.5|0    +5.5|0 |   +28.1    19
 2018 |    +2.4|0    -2.3|0    +1.2|0    +8.9|2   +13.5|3    -2.0|3    +2.0|0    +6.4|1    -1.7|1    -5.4|0    -3.7|0    -8.3|1 |    +9.4    11
 2019 |   +10.0|0    +3.2|9    +0.4|0    -2.5|2   -10.2|1   +13.3|3    +1.2|1    -5.8|2    +0.6|1    +2.3|0    +4.0|0   +12.7|1 |   +29.9    20
 2020 |    -6.1|0    -1.8|1   -10.4|0   +11.7|0   +9.2|11    +5.9|2    +9.5|1    +9.8|2    -6.2|1    -5.8|0   +35.0|0   +22.2|1 |   +86.8    19
```

### s16 R>=55 — size 5%  (Final $198,596)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|20   +19.9|0    -6.7|0    +8.0|0   +13.4|0    +2.0|0    +6.1|0    -3.0|0   +11.3|0    -3.7|0 |   +53.8    20
 2017 |    +8.3|0    -2.1|0    -0.7|0    +0.0|0    -0.1|2    +2.9|1    +2.0|3    -2.5|2    -0.7|2    +2.3|2    +4.6|1    +6.5|2 |   +21.8    15
 2018 |    +0.8|3    -1.7|0    +3.0|0   +13.6|0   +15.2|2    -4.6|1    +3.3|0   +15.9|0    +2.7|1    -6.7|0    +7.2|0    -9.1|0 |   +42.5     7
 2019 |    +3.2|0    +1.9|2    -1.7|4    +1.2|0    -2.8|1    +6.5|1    +1.6|4   -10.4|2    -1.4|0    +2.5|3    +4.1|2   +12.0|0 |   +16.3    19
 2020 |    -6.8|0    +5.0|1   -12.5|0   +19.3|0    +1.1|9    +3.7|0   +12.7|3   +13.6|2    -4.2|0    -0.8|1   +34.6|3   +21.5|0 |  +113.1    19
```

### s12 R>=55 — size 5%  (Final $185,127)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|20   +19.9|0    -6.7|0    +8.0|0   +13.4|0    +2.0|0    +6.1|0    -3.0|0   +11.3|0    -3.7|0 |   +53.8    20
 2017 |    +8.3|0    -2.1|0    -0.7|0    +0.0|0    -0.1|2    +2.9|1    +2.0|3    -2.5|2    -0.7|2    +2.3|2    +4.6|1    +6.7|2 |   +22.0    15
 2018 |    +0.9|3    -1.7|0    +3.1|0   +13.7|0   +15.2|2    -4.6|1    +3.3|0   +15.9|0    +2.7|1    -6.8|0    +7.3|0   -10.8|1 |   +40.1     8
 2019 |    +4.5|0    +2.6|2    -0.5|3    -0.1|0    -6.6|1    +3.4|1    +1.1|4   -10.5|2    +0.3|0    +1.2|3    +2.9|2   +12.5|2 |    +9.5    20
 2020 |    -3.3|0    -1.6|1   -17.2|0   +23.0|0    +5.7|6    +5.6|1   +11.6|3   +14.0|2    -1.3|0    -2.5|1   +35.4|3   +19.5|2 |  +114.5    19
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return. Each config is decomposed once per gated signal set, strictest gate first as in the size sweep: the deciles split the trades that gate's own run took, so each table spans only that gate..100 and reads against the matching size-sweep row.

### s20 R>=55  (bk50d_s20_v2.0)

Trades scored: 95  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57        9   +2.62    -6.96   0.376    1.065
D2        57-61       10   +2.97    -7.97   0.372    1.031
D3        61-61        9   +3.09    -5.65   0.546    1.003
D4        61-64       10   +0.60   -11.51   0.052    0.223
D5        65-65        9   +2.33    -7.34   0.317    0.702
D6        65-68       10   +7.23    -9.70   0.745    1.561
D7        68-75        9   +1.99    -5.75   0.346    0.887
D8        75-93       10   +6.37    -5.11   1.248    1.744
D9        93-100       9   +6.01    -9.67   0.621    1.213
D10      100-100      10   +4.62   -14.24   0.324    0.872
```

### s20 R>=44  (bk50d_s20_v2.0)

Trades scored: 105  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       10   +2.43    -4.07   0.597    1.114
D2        46-47       11   +2.84    -5.29   0.537    1.013
D3        50-51       10   +1.63    -5.89   0.277    0.660
D4        51-54       11   +1.25    -5.15   0.242    0.523
D5        54-61       10   +3.42    -7.34   0.466    1.220
D6        61-65       11   +2.33    -6.30   0.370    0.890
D7        65-75       10   +7.86    -9.90   0.794    2.014
D8        75-96       11   +7.44    -3.88   1.917    1.987
D9        96-100      10   +5.00    -9.31   0.537    1.082
D10      100-100      11   +5.24   -15.31   0.342    0.914
```

### s16 R>=55  (bk50d_s16_v2.0)

Trades scored: 97  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-57        9   +2.05   -10.49   0.195    0.758
D2        57-60       10   +4.86    -7.97   0.609    1.807
D3        61-61       10   +2.08    -5.55   0.375    0.780
D4        61-64        9   +3.72    -7.12   0.522    1.181
D5        64-65       10   +3.76    -7.14   0.526    1.151
D6        65-68       10   +8.01   -10.55   0.760    1.709
D7        68-74        9   +3.06    -6.35   0.482    1.027
D8        75-89       10   +3.91    -3.63   1.077    1.553
D9        89-100      10   +5.90   -10.23   0.577    1.102
D10      100-100      10   +7.13   -10.94   0.651    1.386
```

### s16 R>=44  (bk50d_s16_v2.0)

Trades scored: 108  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +2.81    -4.06   0.692    1.099
D2        44-46       11   +2.70    -9.70   0.278    0.772
D3        46-47       11   +3.01    -9.62   0.313    1.048
D4        47-51       11   +1.20    -6.89   0.174    0.513
D5        51-54       11   +1.88    -5.08   0.371    0.731
D6        55-61       10   +5.46    -4.21   1.295    1.959
D7        61-65       11   +0.30   -10.68   0.028    0.136
D8        65-79       11   +5.96    -8.69   0.685    1.802
D9        89-100      11   +7.84    -8.36   0.938    1.779
D10      100-100      11   +5.24   -15.31   0.342    0.914
```

### s12 R>=55  (bk50d_s12_v2.0)

Trades scored: 97  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        55-55        9   +1.13   -12.93   0.088    0.424
D2        57-58       10   +5.12    -7.97   0.642    1.850
D3        60-61       10   +3.01    -5.55   0.542    1.102
D4        61-64        9   +1.43   -10.97   0.130    0.489
D5        64-65       10   +3.76    -7.14   0.526    1.151
D6        65-68       10   +8.01   -10.55   0.760    1.709
D7        68-71        9   +2.66   -10.09   0.264    0.849
D8        71-89       10   +2.77    -3.69   0.750    1.205
D9        89-100      10   +5.95   -10.22   0.583    1.178
D10      100-100      10   +8.07    -9.64   0.837    1.607
```

### s12 R>=44  (bk50d_s12_v2.0)

Trades scored: 107  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +3.07    -6.65   0.462    1.116
D2        44-46       11   +2.51    -9.00   0.278    0.866
D3        46-47       11   +4.52    -5.60   0.807    1.666
D4        47-51       10   +3.08    -5.63   0.548    1.124
D5        51-55       11   +2.04    -5.19   0.393    0.901
D6        55-61       11   +4.62    -5.33   0.865    1.653
D7        61-65       10   +0.54   -13.12   0.041    0.210
D8        65-89       11   +7.80    -5.26   1.483    2.330
D9        89-100      11   +7.02    -9.36   0.750    1.511
D10      100-100      11   +5.24   -15.31   0.342    0.914
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
