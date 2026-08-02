# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-02 23:39:25 Tallinn time

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

**Ranking gate:** `QullamaggieRanking >= 40` drops 253 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        289,987  +51.32   -32.14   1.597    2.146    181    458   10.1%
3%     ungated      218,594  +43.71   -29.61   1.476    1.906    189    703    8.6%
4%     R>=40        252,895  +47.59   -27.47   1.732    1.929    143    496    9.4%
4%     ungated      208,973  +42.53   -27.82   1.529    1.890    146    746    9.3%
5%     R>=40        280,782  +50.43   -30.67   1.644    2.017    116    523    9.7%
5%     ungated      230,802  +45.14   -30.32   1.489    1.916    115    777    9.7%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 773 signals (0 with no fillable next-day open); ungated drops 0 (2 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        209,519  +42.60   -28.75   1.482    1.846    191    560    8.7%
3%     ungated      161,248  +35.94   -27.16   1.324    1.706    194   1328    7.4%
4%     R>=40        228,051  +44.83   -26.87   1.668    1.903    144    607    8.6%
4%     ungated      182,780  +39.09   -28.50   1.371    1.766    143   1379    7.8%
5%     R>=40        213,855  +43.14   -32.04   1.347    1.787    114    637    9.0%
5%     ungated      212,709  +43.00   -28.12   1.529    1.874    115   1407    7.4%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 1511 signals (0 with no fillable next-day open); ungated drops 0 (3 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        257,159  +48.04   -25.46   1.887    2.099    194    714    7.8%
3%     ungated      173,841  +37.82   -20.50   1.845    1.940    194   2222    5.6%
4%     R>=40        230,107  +45.06   -27.07   1.664    1.963    144    764    8.7%
4%     ungated      210,071  +42.67   -22.27   1.916    2.117    145   2271    5.6%
5%     R>=40        245,644  +46.80   -25.93   1.805    1.969    114    794    9.5%
5%     ungated      247,444  +47.00   -23.65   1.987    2.203    116   2300    5.8%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s20 R>=40             3%     289,987  +51.32   -32.14   1.597    2.146    181    458   10.1%
 2  s20 R>=40             5%     280,782  +50.43   -30.67   1.644    2.017    116    523    9.7%
 3  s12 R>=40             3%     257,159  +48.04   -25.46   1.887    2.099    194    714    7.8%
 4  s20 R>=40             4%     252,895  +47.59   -27.47   1.732    1.929    143    496    9.4%
 5  s12 ungated           5%     247,444  +47.00   -23.65   1.987    2.203    116   2300    5.8%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 ungated           5%     247,444  +47.00   -23.65   1.987    2.203    116   2300    5.8%
 2  s20 R>=40             3%     289,987  +51.32   -32.14   1.597    2.146    181    458   10.1%
 3  s12 ungated           4%     210,071  +42.67   -22.27   1.916    2.117    145   2271    5.6%
 4  s12 R>=40             3%     257,159  +48.04   -25.46   1.887    2.099    194    714    7.8%
 5  s20 R>=40             5%     280,782  +50.43   -30.67   1.644    2.017    116    523    9.7%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=40 3%        2021      46,939  +56.46   -22.51   2.509    2.035     33    104    1.0%
                    2022      54,886  +16.93   -25.46   0.665    0.760     32     66   20.4%
                    2023      75,021  +36.69   -24.05   1.525    2.190     33    164    5.3%
                    2024     107,639  +43.48   -12.29   3.537    2.440     33    127    3.8%
                    2025     229,247 +112.98   -25.11   4.499    4.163     31    204    8.5%
                    2026     257,159  +12.18   -18.37   0.663    1.156     32     49    8.1%
s12 R>=40 4%        2021      46,416  +54.72   -24.82   2.205    1.886     24    113    3.2%
                    2022      56,100  +20.86   -22.26   0.937    0.871     24     74   18.8%
                    2023      77,123  +37.47   -25.12   1.492    2.159     24    173    5.3%
                    2024     108,759  +41.02   -12.99   3.157    2.292     24    136    4.3%
                    2025     205,987  +89.40   -27.07   3.302    3.740     23    212   11.4%
                    2026     230,107  +11.71   -19.27   0.608    1.100     25     56    9.4%
s12 R>=40 5%        2021      48,820  +62.73   -25.93   2.419    2.005     19    118    4.0%
                    2022      54,423  +11.48   -23.06   0.498    0.505     19     79   18.1%
                    2023      71,669  +31.69   -20.75   1.527    1.942     19    178    5.1%
                    2024     106,058  +47.98   -15.44   3.107    2.606     19    141    5.1%
                    2025     218,371 +105.90   -24.55   4.314    3.971     18    217   13.2%
                    2026     245,644  +12.49   -18.85   0.662    1.078     20     61   13.4%
s20 R>=40 3%        2021      46,077  +53.59   -22.73   2.357    1.946     33     69    1.0%
                    2022      50,284   +9.13   -24.78   0.369    0.468     33     30   33.1%
                    2023      65,609  +30.48   -26.07   1.169    1.860     32     98    7.8%
                    2024      96,432  +46.98   -14.95   3.142    2.350     31     85    6.3%
                    2025     220,859 +129.03   -32.14   4.015    3.843     33    138    4.7%
                    2026     289,987  +31.30   -18.16   1.723    2.289     19     38    4.8%
s20 R>=40 5%        2021      48,820  +62.73   -25.93   2.419    2.005     19     83    4.0%
                    2022      57,352  +17.48   -30.67   0.570    0.743     19     44   24.4%
                    2023      71,831  +25.25   -29.51   0.856    1.540     19    111    8.3%
                    2024     106,229  +47.89   -12.16   3.938    2.429     19     97    4.7%
                    2025     248,338 +133.78   -26.15   5.116    4.289     20    151    7.3%
                    2026     280,782  +13.06   -21.71   0.602    1.070     20     37    9.6%
```

## Monthly returns/transactions — s12 R>=40 at each sizing, plus the top 2 by Final$

### s12 R>=40 — size 3%  (Final $257,159)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.6|33   +20.2|0    +1.4|0    +5.0|0   +10.1|0    +5.9|0    -8.9|0    -0.3|0   +12.1|0    +9.2|0    -5.8|0    +5.0|0 |   +56.5    33
 2022 |    +5.2|1    +1.3|8   -1.2|23   -12.8|0    +4.9|0    -7.3|0   +14.8|0    +3.9|0   -11.4|0   +12.7|0    +8.5|0    +1.3|0 |   +16.9    32
 2023 |    +8.1|2    +1.9|4    -3.6|8   -3.3|12   +10.2|7   +12.1|0   +10.0|0    -6.3|0    -8.9|0    -9.8|0   +14.0|0   +11.8|0 |   +36.7    33
 2024 |    -5.2|1   +11.4|4    +2.4|7    -5.6|9   +7.1|12    -5.7|0    +8.7|0    +4.2|0    +6.1|0    +2.6|0    +8.6|0    +4.0|0 |   +43.5    33
 2025 |    -1.1|0    -5.5|4    -5.7|1    +2.2|0   +2.1|19   +13.3|7   +33.4|0   +12.5|0   +13.2|0   +15.7|0    +5.1|0    -1.1|0 |  +113.0    31
 2026 |    +3.4|0    +2.2|1    -8.1|3    +8.1|5    +7.5|9   -0.6|14         ·         ·         ·         ·         ·         · |   +12.2    32
```

### s12 R>=40 — size 4%  (Final $230,107)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.9|24   +22.4|0    -0.1|0    +3.6|0   +10.7|0    +7.7|0   -11.2|0    +0.3|0   +13.4|0    +9.9|0    -7.0|0    +3.3|0 |   +54.7    24
 2022 |    +7.8|1    +1.7|8   -0.8|15   -11.2|0    +7.3|0    -8.0|0   +14.3|0    +1.4|0   -11.2|0   +17.0|0    +8.2|0    -2.7|0 |   +20.9    24
 2023 |    +8.4|1    +3.6|4    -4.3|8   -4.0|11   +10.7|0   +13.3|0    +9.8|0    -6.8|0    -9.7|0    -9.9|0   +12.8|0   +13.0|0 |   +37.5    24
 2024 |    -6.4|1    +9.3|4    +1.1|7   -8.7|10   +10.1|2    -6.8|0    +6.3|0    +3.5|0    +6.7|0    +2.7|0   +14.5|0    +5.7|0 |   +41.0    24
 2025 |    -1.8|0   -11.5|4    -4.2|1    -0.0|0   +0.0|18   +13.2|0   +33.9|0    +9.2|0   +17.2|0   +13.2|0    +4.3|0    -0.7|0 |   +89.4    23
 2026 |    +2.7|0    +1.7|1    -9.3|3    +9.2|5    +5.2|9    +2.5|7         ·         ·         ·         ·         ·         · |   +11.7    25
```

### s12 R>=40 — size 5%  (Final $245,644)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.6|19   +24.6|0    +0.4|0    +2.2|0   +12.7|0    +9.7|0   -12.7|0    +0.6|0   +15.0|0   +11.3|0    -7.7|0    +2.9|0 |   +62.7    19
 2022 |    +9.0|1    +2.1|8   -1.2|10    -9.5|0    +5.3|0   -10.7|0    +9.2|0    -1.2|0   -10.8|0   +19.8|0    +5.1|0    -1.7|0 |   +11.5    19
 2023 |    +8.3|2    -0.7|4    -1.7|9    -5.3|4   +14.2|0   +10.2|0    +3.5|0    -2.1|0    -7.8|0   -10.3|0   +12.5|0   +10.9|0 |   +31.7    19
 2024 |    -1.2|2    +7.2|4    +3.8|8    -7.0|5   +10.9|0    -5.9|0    +4.3|0    +0.4|0    +4.5|0    +5.2|0   +14.7|0    +5.3|0 |   +48.0    19
 2025 |    -2.2|0   -10.5|6    -3.4|1    +4.7|0   +2.5|11   +13.7|0   +36.6|0    +9.3|0   +19.8|0   +14.2|0    +1.2|0    -3.3|0 |  +105.9    18
 2026 |    +1.3|0    +2.7|1    -8.7|3    +6.3|6    +6.9|9    +4.3|1         ·         ·         ·         ·         ·         · |   +12.5    20
```

### s20 R>=40 — size 3%  (Final $289,987)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.7|33   +20.9|0    +0.8|0    +5.1|0   +10.2|0    +6.1|0    -9.8|0    -0.1|0   +11.8|0    +9.1|0    -6.2|0    +4.2|0 |   +53.6    33
 2022 |    +5.9|0    +0.5|2   -1.3|16  -12.1|10    +3.4|0    -4.3|0   +11.4|0    +5.5|0   -10.1|0    +8.1|0    +3.0|0    +1.5|5 |    +9.1    33
 2023 |    +8.3|0    -1.8|2    -4.5|2    -2.4|7   +4.5|10    +8.6|6   +11.2|0   -10.1|0    -7.0|0   -10.3|0   +18.8|0   +17.0|5 |   +30.5    32
 2024 |    -6.6|0    +9.4|2    -0.3|0    -6.2|6    +6.1|8    -3.4|8    +5.8|4    +4.0|0    +7.1|0    +4.7|0   +23.3|0    -1.4|3 |   +47.0    31
 2025 |    +6.9|0    -6.7|1   -10.9|1    +2.2|0   +7.6|10  +19.8|11   +29.6|8   +12.1|0   +18.1|0   +12.2|0    +4.5|0    -2.7|2 |  +129.0    33
 2026 |    +6.8|0    -0.8|1    -4.0|0    +6.9|5    +8.7|6   +11.1|7         ·         ·         ·         ·         ·         · |   +31.3    19
```

### s20 R>=40 — size 5%  (Final $280,782)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.6|19   +24.6|0    +0.4|0    +2.2|0   +12.7|0    +9.7|0   -12.7|0    +0.6|0   +15.0|0   +11.3|0    -7.7|0    +2.9|0 |   +62.7    19
 2022 |    +9.1|0    +0.8|2   -2.1|16   -15.0|1    +4.1|0    -5.5|0   +15.6|0    +6.5|0   -14.0|0   +12.6|0    +6.4|0    +2.9|0 |   +17.5    19
 2023 |    +6.5|0    -3.9|3    -7.0|2    -2.7|7   +10.9|7   +10.5|0   +11.7|0    -9.0|0    -8.3|0   -13.5|0   +20.6|0   +13.5|0 |   +25.2    19
 2024 |    -8.4|0   +13.8|3    +0.7|0    -5.3|6   +10.5|8    -7.7|2    +5.8|0    +9.5|0    +8.0|0    +2.6|0    +9.7|0    +3.5|0 |   +47.9    19
 2025 |    +3.5|0    -4.1|1    -6.1|1    -2.8|0   +1.3|10   +15.3|8   +44.7|0   +17.4|0   +16.3|0   +12.9|0    +1.2|0    -2.1|0 |  +133.8    20
 2026 |    +0.1|0    +4.0|1   -12.9|0    +6.9|5   +10.4|7    +5.5|7         ·         ·         ·         ·         ·         · |   +13.1    20
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 143  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        41-49       14   +1.87    -7.88   0.238    0.572
D2        49-58       14   +4.55    -7.14   0.638    1.392
D3        60-60       14   -0.60   -13.13  -0.045   -0.080
D4        60-62       15   +1.78    -9.87   0.180    0.520
D5        64-66       14   +3.71    -6.64   0.558    0.877
D6        66-66       14   +1.07    -9.98   0.108    0.288
D7        66-73       15   +5.55    -9.09   0.611    1.088
D8        73-83       14   +1.47   -12.77   0.115    0.384
D9        83-87       14  +17.37   -18.77   0.926    1.968
D10       87-100      15  +11.69    -9.89   1.181    1.860
```

### s16  (bk50d_s16_v2.0)

Trades scored: 144  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       14   +1.74    -3.73   0.467    0.690
D2        44-51       14   +3.66    -9.10   0.403    1.056
D3        51-60       15   +5.11    -6.51   0.785    1.540
D4        60-60       14   +0.20   -11.71   0.017    0.091
D5        60-64       15   +3.75    -6.81   0.550    1.127
D6        64-66       14   +1.00    -9.66   0.104    0.260
D7        66-70       14   +4.32    -7.19   0.600    0.978
D8        70-79       15   +3.51    -6.64   0.529    0.843
D9        83-83       14  +13.05   -13.85   0.943    1.828
D10       83-100      15   +9.18   -11.27   0.814    1.509
```

### s12  (bk50d_s12_v2.0)

Trades scored: 144  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-41       14   +3.59    -7.50   0.479    1.183
D2        42-44       14   +0.11    -9.19   0.012    0.068
D3        44-50       15   +4.60    -9.53   0.483    1.105
D4        51-57       14   +6.87    -4.88   1.407    1.789
D5        57-60       15   +1.22    -6.83   0.178    0.426
D6        60-64       14   +3.73    -8.16   0.458    0.916
D7        66-66       14   +1.96    -6.71   0.293    0.489
D8        67-73       15   +6.31    -9.09   0.695    1.269
D9        73-83       14   +0.84   -10.45   0.081    0.259
D10       83-100      15  +16.93   -13.00   1.302    2.086
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
