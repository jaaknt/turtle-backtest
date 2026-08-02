# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-02 14:15:55 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2021-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Algorithms | bk50d_s20_v2.0 (%abv_SMA50>20%), bk50d_s16_v2.0 (%abv_SMA50>16%), bk50d_s12_v2.0 (%abv_SMA50>12%) |
| Entry | next trading day's split/dividend-adjusted open |
| Initial equity | $30,000 |
| Position sizing | 3%, 4%, 5% of portfolio per trade |
| Ranking gate | QullamaggieRanking >= 40, reported against an ungated run of the same signals |
| Fixed filters | breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100% (no tight_range) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
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

**Ranking gate:** `QullamaggieRanking >= 40` drops 184 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        170,522  +37.34   -29.50   1.266    1.687    177    339   13.5%
3%     ungated      147,880  +33.81   -26.24   1.289    1.605    186    514   11.8%
4%     R>=40        175,642  +38.08   -30.19   1.261    1.616    140    376   11.0%
4%     ungated      179,126  +38.58   -26.86   1.436    1.710    143    557   10.1%
5%     R>=40        234,830  +45.60   -33.34   1.368    1.745    115    401    9.5%
5%     ungated      172,036  +37.56   -30.73   1.222    1.614    114    586    9.8%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 566 signals (0 with no fillable next-day open); ungated drops 0 (2 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        169,175  +37.14   -33.08   1.123    1.641    185    425   10.3%
3%     ungated      194,149  +40.63   -23.54   1.726    1.850    193    981    7.6%
4%     R>=40        215,766  +43.37   -30.69   1.413    1.760    143    467    8.8%
4%     ungated      162,968  +36.21   -25.86   1.400    1.615    142   1032    8.3%
5%     R>=40        183,921  +39.25   -30.11   1.304    1.608    114    496    9.2%
5%     ungated      203,434  +41.84   -28.23   1.482    1.708    110   1064    8.1%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 1067 signals (0 with no fillable next-day open); ungated drops 0 (2 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        307,178  +52.92   -28.01   1.889    2.159    191    548    7.9%
3%     ungated      142,774  +32.96   -23.18   1.422    1.631    194   1610    6.3%
4%     R>=40        235,095  +45.63   -24.92   1.831    1.912    145    594    8.5%
4%     ungated      131,860  +31.04   -27.09   1.146    1.531    145   1659    6.3%
5%     R>=40        221,009  +44.00   -26.82   1.641    1.803    115    624    8.7%
5%     ungated      112,845  +27.37   -24.09   1.136    1.418    115   1689    6.3%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=40             3%     307,178  +52.92   -28.01   1.889    2.159    191    548    7.9%
 2  s12 R>=40             4%     235,095  +45.63   -24.92   1.831    1.912    145    594    8.5%
 3  s20 R>=40             5%     234,830  +45.60   -33.34   1.368    1.745    115    401    9.5%
 4  s12 R>=40             5%     221,009  +44.00   -26.82   1.641    1.803    115    624    8.7%
 5  s16 R>=40             4%     215,766  +43.37   -30.69   1.413    1.760    143    467    8.8%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=40             3%     307,178  +52.92   -28.01   1.889    2.159    191    548    7.9%
 2  s12 R>=40             4%     235,095  +45.63   -24.92   1.831    1.912    145    594    8.5%
 3  s16 ungated           3%     194,149  +40.63   -23.54   1.726    1.850    193    981    7.6%
 4  s12 R>=40             5%     221,009  +44.00   -26.82   1.641    1.803    115    624    8.7%
 5  s16 R>=40             4%     215,766  +43.37   -30.69   1.413    1.760    143    467    8.8%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=40 3%        2021      48,133  +60.44   -21.77   2.777    2.154     33     68    1.3%
                    2022      56,940  +18.30   -24.05   0.761    0.803     32     47   20.6%
                    2023      86,309  +51.58   -23.16   2.227    2.795     32    115    8.7%
                    2024     133,570  +54.76   -13.74   3.986    2.856     34     91    5.1%
                    2025     236,064  +76.73   -28.01   2.739    2.720     32    176    5.7%
                    2026     307,178  +30.12   -22.20   1.357    2.043     28     51    3.5%
s12 R>=40 4%        2021      49,668  +65.56   -22.52   2.911    2.224     24     77    3.2%
                    2022      54,237   +9.20   -24.85   0.370    0.455     24     55   19.2%
                    2023      78,879  +45.43   -23.37   1.944    2.526     24    123    7.6%
                    2024     112,582  +42.73   -12.29   3.476    2.424     25    100    6.5%
                    2025     180,202  +60.06   -21.92   2.740    2.389     23    185    6.9%
                    2026     235,095  +30.46   -24.92   1.222    2.098     25     54    6.4%
s12 R>=40 5%        2021      50,852  +69.51   -25.28   2.749    2.173     19     82    3.8%
                    2022      57,168  +12.42   -22.01   0.564    0.559     19     60   18.5%
                    2023      82,395  +44.13   -21.81   2.023    2.381     19    128    6.8%
                    2024     120,576  +46.34   -14.25   3.251    2.513     20    105    6.3%
                    2025     178,784  +48.28   -24.40   1.979    1.980     18    190    9.6%
                    2026     221,009  +23.62   -26.82   0.881    1.568     20     59    6.3%
s20 R>=40 5%        2021      50,852  +69.51   -25.28   2.749    2.173     19     54    3.8%
                    2022      49,901   -1.87   -29.51  -0.063    0.029     19     33   24.7%
                    2023      69,945  +40.17   -30.91   1.300    2.087     19     74    8.9%
                    2024     106,727  +52.59   -13.52   3.891    2.480     19     71    4.7%
                    2025     184,584  +72.95   -26.84   2.718    2.318     20    135    7.7%
                    2026     234,830  +27.22   -33.34   0.816    1.436     19     34    4.8%
s16 R>=40 4%        2021      49,668  +65.56   -22.52   2.911    2.224     24     62    3.2%
                    2022      51,226   +3.14   -28.35   0.111    0.236     24     38   20.8%
                    2023      67,482  +31.73   -30.69   1.034    1.802     24     99    7.9%
                    2024      93,665  +38.80   -13.82   2.808    2.036     24     78    6.1%
                    2025     177,334  +89.33   -27.05   3.302    2.759     24    147    7.2%
                    2026     215,766  +21.67   -25.12   0.863    1.378     23     43    6.1%
```

## Monthly returns/transactions — s12 R>=40 at each sizing, plus the top 2 by Final$

### s12 R>=40 — size 3%  (Final $307,178)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.9|33   +21.1|0    +2.4|0    +5.6|0   +10.5|0    +7.6|0    -9.8|0    +2.1|0   +11.4|0    +8.6|0    -6.5|0    +5.1|0 |   +60.4    33
 2022 |    +5.3|1    +1.1|7   -0.8|21   -11.1|3    +4.8|0    -9.0|0   +16.0|0    +4.4|0    -8.3|0   +13.3|0    +8.7|0    -3.3|0 |   +18.3    32
 2023 |    +7.1|2    +1.9|3    -1.1|6    -3.2|7  +10.7|13   +14.4|1   +11.8|0    -4.5|0    -8.7|0   -10.4|0   +15.5|0   +13.7|0 |   +51.6    32
 2024 |    -5.0|1   +14.8|3    +1.5|6    -8.0|5   +8.5|11    -3.6|8    +8.1|0    +3.5|0    +5.8|0    +4.0|0   +15.6|0    +2.2|0 |   +54.8    34
 2025 |    +2.5|0    -6.2|3    -8.8|0    +2.9|0   +6.4|17  +19.1|11    +7.7|1   +11.3|0   +17.8|0   +11.7|0    +0.9|0    -2.8|0 |   +76.7    32
 2026 |   +13.8|0    -2.8|1    -6.9|2    +8.9|0    +8.6|9   +6.8|16         ·         ·         ·         ·         ·         · |   +30.1    28
```

### s12 R>=40 — size 4%  (Final $235,095)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.5|24   +20.7|0    +2.2|0    +5.7|0   +11.8|0    +6.8|0    -9.7|0    +1.5|0   +14.3|0    +9.9|0    -7.2|0    +4.2|0 |   +65.6    24
 2022 |    +5.7|1    +1.5|7   -0.6|16   -11.4|0    +4.6|0    -9.1|0   +13.7|0    +1.8|0   -10.8|0   +15.8|0    +6.0|0    -4.2|0 |    +9.2    24
 2023 |    +7.6|2    +1.2|3    -3.4|6    -4.4|7   +11.7|6   +14.5|0   +11.0|0    -4.7|0    -8.7|0   -10.8|0   +16.6|0   +12.5|0 |   +45.4    24
 2024 |    -7.4|1   +15.5|3    +0.8|6    -9.8|5   +8.5|10    -4.9|0    +8.3|0    +3.6|0    +7.7|0    -0.9|0   +11.8|0    +6.2|0 |   +42.7    25
 2025 |    -1.1|0    -3.4|4    -4.4|0    +1.0|0   +2.0|17   +16.7|2    +5.7|0   +10.9|0   +21.7|0    +9.6|0    -2.9|0    -4.0|0 |   +60.1    23
 2026 |   +11.1|0    +1.1|1   -11.2|3   +12.9|0    +9.8|9   +5.4|12         ·         ·         ·         ·         ·         · |   +30.5    25
```

### s12 R>=40 — size 5%  (Final $221,009)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.0|19   +23.8|0    +1.8|0    +4.4|0   +12.4|0    +9.0|0   -12.1|0    +1.2|0   +16.3|0   +11.2|0    -7.8|0    +3.3|0 |   +69.5    19
 2022 |    +8.3|1    +1.8|7   -0.5|11    -9.0|0    +5.4|0   -10.1|0   +10.3|0    -0.2|0   -11.5|0   +19.3|0    +5.3|0    -3.0|0 |   +12.4    19
 2023 |    +6.8|2    -1.5|3    -1.3|6    -5.5|7   +12.5|1   +14.7|0   +11.7|0    -2.6|0    -9.2|0   -10.7|0   +14.2|0   +13.0|0 |   +44.1    19
 2024 |    -9.5|1   +17.5|3    +0.4|6   -11.9|5    +9.4|5    -5.8|0    +6.6|0    +4.1|0    +9.1|0    -0.1|0   +13.5|0   +10.0|0 |   +46.3    20
 2025 |    -2.9|0    -2.0|3    -6.1|0    -1.0|0   +1.5|15   +14.6|0    +8.0|0    +9.5|0   +21.8|0    +8.8|0    -2.0|0    -6.2|0 |   +48.3    18
 2026 |   +12.3|0    -0.5|1   -11.7|3    +8.8|0   +10.5|9    +4.3|7         ·         ·         ·         ·         ·         · |   +23.6    20
```

### s20 R>=40 — size 5%  (Final $234,830)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.0|19   +23.8|0    +1.8|0    +4.4|0   +12.4|0    +9.0|0   -12.1|0    +1.2|0   +16.3|0   +11.2|0    -7.8|0    +3.3|0 |   +69.5    19
 2022 |    +8.3|0    +0.8|2   -2.2|14   -13.9|3    +4.8|0    -7.8|0   +14.0|0    +3.2|0   -11.7|0   +11.1|0    +3.3|0    -7.3|0 |    -1.9    19
 2023 |    +7.1|0    -2.1|3    -4.6|2    -3.5|4   +12.0|9   +14.2|1   +13.4|0   -10.0|0    -9.3|0   -13.3|0   +21.0|0   +16.9|0 |   +40.2    19
 2024 |    -8.1|0   +12.5|3    -0.9|0    -5.1|4    +8.8|8    -5.3|4    +5.4|0   +12.1|0    +8.7|0    +5.2|0   +12.9|0    -0.2|0 |   +52.6    19
 2025 |    +5.3|0    -5.9|1    -6.6|0    -1.3|0   +9.0|10   +17.6|9   +10.3|0   +13.0|0   +21.0|0   +14.6|0    -8.5|0    -6.7|0 |   +72.9    20
 2026 |   +16.0|0    -7.7|1   -13.5|0    +8.8|0   +19.7|7   +5.5|11         ·         ·         ·         ·         ·         · |   +27.2    19
```

### s16 R>=40 — size 4%  (Final $215,766)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.5|24   +20.7|0    +2.2|0    +5.7|0   +11.8|0    +6.8|0    -9.7|0    +1.5|0   +14.3|0    +9.9|0    -7.2|0    +4.2|0 |   +65.6    24
 2022 |    +5.7|1    +2.5|3   -1.0|15   -13.8|5    +4.5|0    -9.7|0   +13.0|0    +2.7|0   -11.0|0   +16.3|0    +3.1|0    -4.4|0 |    +3.1    24
 2023 |    +8.0|2    -2.0|2    -4.4|3    -4.1|6   +6.6|11   +14.3|0   +15.0|0   -10.7|0    -9.0|0   -13.1|0   +18.7|0   +15.5|0 |   +31.7    24
 2024 |   -10.9|2   +11.4|2    -1.2|1    -8.2|4    +6.1|9    -5.2|6    +6.1|0   +10.6|0    +6.1|0    +7.0|0   +13.9|0    +1.0|0 |   +38.8    24
 2025 |    +7.7|0    -8.3|3    -7.7|0    +1.2|0   +9.9|13   +20.5|8   +10.0|0   +10.4|0   +21.7|0   +13.2|0    -2.9|0    -4.6|0 |   +89.3    24
 2026 |   +11.0|0    -2.6|1    -9.6|1    +7.2|1   +10.4|6   +5.1|14         ·         ·         ·         ·         ·         · |   +21.7    23
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 140  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        41-49       14   +0.18    -9.31   0.020    0.098
D2        49-58       14   +4.33    -6.30   0.687    1.217
D3        58-60       14   -0.65    -9.01  -0.073   -0.132
D4        60-64       14   +2.97    -8.92   0.333    0.930
D5        64-66       14   +0.71    -6.24   0.114    0.216
D6        66-69       14   +2.44    -9.72   0.251    0.638
D7        70-77       14   +4.83    -9.09   0.532    0.965
D8        77-83       14   +3.15   -12.27   0.256    0.714
D9        83-87       14  +11.47   -25.34   0.453    1.181
D10       87-100      14  +10.20   -11.59   0.880    1.726
```

### s16  (bk50d_s16_v2.0)

Trades scored: 143  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-46       14   +2.14    -6.66   0.322    0.864
D2        46-51       14   +3.44   -10.39   0.331    0.871
D3        51-58       14   +4.10    -7.96   0.515    1.161
D4        60-60       15   +1.07    -7.76   0.137    0.316
D5        60-64       14   +3.50    -6.24   0.561    0.981
D6        64-66       14   -0.51   -10.04  -0.051   -0.096
D7        66-70       15   +6.36    -7.03   0.905    1.328
D8        73-83       14   +4.36    -9.55   0.456    1.072
D9        83-87       14   +9.60   -21.84   0.439    1.062
D10       87-100      15  +11.08   -11.33   0.978    1.839
```

### s12  (bk50d_s12_v2.0)

Trades scored: 145  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-42       14   +5.54    -7.16   0.775    1.710
D2        43-46       15   +0.91   -10.61   0.086    0.377
D3        47-52       14   +5.87    -7.03   0.835    1.400
D4        52-60       15   +5.84    -5.94   0.984    1.512
D5        60-62       14   -0.37    -7.48  -0.050   -0.089
D6        62-66       15   +3.32    -8.25   0.403    0.736
D7        66-69       14   +3.16    -7.17   0.441    0.854
D8        69-74       15   +6.24    -9.09   0.687    1.219
D9        77-83       14   +6.73   -21.21   0.317    0.926
D10       87-100      15   +8.85   -11.27   0.785    1.435
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
