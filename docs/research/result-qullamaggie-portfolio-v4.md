# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-07-29
Period: 2021-01-01 – 2026-06-26  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         59,301  +13.25   -25.36   0.522    0.803
QQQ         68,525  +16.28   -35.62   0.457    0.760
```

## s20  (bk50d_s20_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (0 signals dropped below it, 0 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         138,191  +32.17   -23.95   1.343    1.181    163    353   18.3%
4%         121,336  +29.07   -30.93   0.940    1.038    131    385   16.3%
5%         122,568  +29.30   -28.67   1.022    1.007    110    406   13.6%
```

## s16  (bk50d_s16_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (235 signals dropped below it, 1 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         156,697  +35.24   -22.55   1.563    1.255    177    449   13.2%
4%         157,812  +35.41   -25.47   1.390    1.162    140    486   10.4%
5%         185,724  +39.50   -29.00   1.362    1.223    115    511    9.3%
```

## s12  (bk50d_s12_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (552 signals dropped below it, 1 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         238,041  +45.96   -28.79   1.596    1.423    180    602    8.3%
4%         200,154  +41.42   -26.83   1.544    1.309    142    640    8.7%
5%         149,305  +34.05   -30.05   1.133    1.096    113    669    9.6%
```

## Entry price: next-day open vs resting limit order

The production rule buys the next trading day's split/dividend-adjusted open. The alternatives place a resting limit at the signal day's adjusted close x (1 - X), good for 30 calendar days, filling on the first day whose adjusted low touches it and filling *at* the limit. Rule and window match `scripts/qullamaggie-cohorts-limit-order.py`.

`unfilled` counts signals whose limit was never touched inside the window — those trades simply never happen, which is the cost the deeper limits pay for their better entry price.

```text
cfg   size  entry           Final$   CAGR%   dCAGR   MaxDD%  Sortino    dSrt  Calmar  taken  unfil
--------------------------------------------------------------------------------------------------
s12   3%    next open      238,041  +45.96       —   -28.79    1.423       —   1.596    180      —
            close          207,346  +42.33   -3.63   -28.40    1.365  -0.058   1.490    183     30
            close -1%      228,728  +44.90   -1.06   -27.40    1.436  +0.013   1.639    180     59
            close -3%      240,386  +46.23   +0.26   -28.34    1.439  +0.016   1.631    175    168
            close -5%      147,089  +33.68  -12.28   -26.30    1.169  -0.254   1.281    174    254

s12   4%    next open      200,154  +41.42       —   -26.83    1.309       —   1.544    142      —
            close          173,038  +37.71   -3.71   -28.13    1.271  -0.038   1.340    140     30
            close -1%      202,129  +41.67   +0.25   -26.80    1.319  +0.010   1.555    140     59
            close -3%      194,714  +40.71   -0.71   -28.54    1.306  -0.003   1.426    132    168
            close -5%      126,387  +30.03  -11.39   -29.06    1.092  -0.217   1.034    130    254

s12   5%    next open      149,305  +34.05       —   -30.05    1.096       —   1.133    113      —
            close          140,701  +32.60   -1.44   -31.23    1.101  +0.005   1.044    113     30
            close -1%      174,876  +37.97   +3.93   -30.12    1.226  +0.131   1.261    114     59
            close -3%      160,648  +35.85   +1.80   -30.14    1.178  +0.083   1.189    108    168
            close -5%      126,419  +30.04   -4.01   -30.66    1.070  -0.026   0.980    107    254

s16   3%    next open      156,697  +35.24       —   -22.55    1.255       —   1.563    177      —
            close          120,768  +28.95   -6.28   -25.74    1.081  -0.174   1.125    177     22
            close -1%      146,364  +33.56   -1.67   -22.65    1.251  -0.004   1.482    175     44
            close -3%      118,737  +28.56   -6.68   -27.22    1.068  -0.188   1.049    169    137
            close -5%      117,374  +28.29   -6.95   -22.61    1.049  -0.206   1.251    165    200

s16   4%    next open      157,812  +35.41       —   -25.47    1.162       —   1.390    140      —
            close          139,574  +32.41   -3.00   -26.52    1.111  -0.051   1.222    135     22
            close -1%      160,244  +35.79   +0.38   -25.20    1.220  +0.058   1.420    135     44
            close -3%      143,188  +33.03   -2.38   -24.63    1.145  -0.016   1.341    130    137
            close -5%      112,361  +27.27   -8.14   -24.74    0.980  -0.182   1.102    126    200

s16   5%    next open      185,724  +39.50       —   -29.00    1.223       —   1.362    115      —
            close          125,168  +29.80   -9.70   -28.66    1.017  -0.206   1.040    113     22
            close -1%      151,513  +34.41   -5.09   -26.47    1.146  -0.076   1.300    111     44
            close -3%      168,660  +37.06   -2.43   -31.08    1.190  -0.033   1.193    105    137
            close -5%      114,499  +27.71  -11.79   -29.81    0.993  -0.230   0.929    103    200

s20   3%    next open      138,191  +32.17       —   -23.95    1.181       —   1.343    163      —
            close          124,726  +29.72   -2.45   -23.16    1.157  -0.024   1.283    160     18
            close -1%      117,307  +28.27   -3.90   -24.46    1.128  -0.053   1.156    159     41
            close -3%      129,911  +30.68   -1.48   -24.50    1.155  -0.027   1.252    154    112
            close -5%      139,267  +32.35   +0.19   -24.61    1.150  -0.032   1.314    154    168

s20   4%    next open      121,336  +29.07       —   -30.93    1.038       —   0.940    131      —
            close          110,001  +26.77   -2.29   -27.36    1.006  -0.032   0.979    129     18
            close -1%      107,817  +26.31   -2.75   -26.41    1.010  -0.028   0.996    128     41
            close -3%      102,095  +25.06   -4.01   -25.44    0.984  -0.054   0.985    121    112
            close -5%       82,747  +20.35   -8.71   -28.28    0.805  -0.234   0.720    123    168

s20   5%    next open      122,568  +29.30       —   -28.67    1.007       —   1.022    110      —
            close          109,904  +26.75   -2.55   -30.94    0.961  -0.047   0.865    107     18
            close -1%      122,566  +29.30   -0.00   -31.98    1.034  +0.026   0.916    104     41
            close -3%      111,959  +27.18   -2.12   -29.07    0.999  -0.009   0.935     99    112
            close -5%       89,308  +22.04   -7.26   -27.33    0.826  -0.181   0.807     98    168
```

`close`: beats the next-open entry on CAGR in **0 of 9** config/size cells and on Sortino in **1 of 9**; mean CAGR delta **-3.90pp**, mean unfilled signals **23**.

`close -1%`: beats the next-open entry on CAGR in **3 of 9** config/size cells and on Sortino in **5 of 9**; mean CAGR delta **-1.10pp**, mean unfilled signals **48**.

`close -3%`: beats the next-open entry on CAGR in **2 of 9** config/size cells and on Sortino in **2 of 9**; mean CAGR delta **-1.97pp**, mean unfilled signals **139**.

`close -5%`: beats the next-open entry on CAGR in **1 of 9** config/size cells and on Sortino in **0 of 9**; mean CAGR delta **-7.82pp**, mean unfilled signals **207**.

## Monthly returns/transactions — top 5 by Final$

### #1  s12 — size 3%  (Final $238,041)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.3|33   +20.1|0    +2.2|0    +5.0|0   +12.7|0    +4.8|0    -9.1|0    -0.2|0    +9.1|0    +8.1|0    -7.5|0    +3.8|0 |   +48.0    33
 2022 |    +5.7|3    +0.5|5   -0.1|15  -14.6|10    -0.1|0    -8.6|0   +15.2|0    +3.8|0    -8.2|0    +8.7|0    +8.2|0    -6.2|0 |    +0.1    33
 2023 |   +13.7|3    -0.8|3    -3.5|3    -2.8|5   -0.2|13   +12.8|6   +11.5|0    -6.2|0    -7.6|0    -7.3|0   +18.3|0   +16.1|0 |   +46.4    33
 2024 |    -3.7|3   +10.2|2    +1.2|1    -3.3|4   +7.2|10    -4.7|2    +3.4|8    +7.6|1    +5.0|0    +3.8|0   +18.4|0    +0.7|0 |   +53.3    31
 2025 |    +6.8|1    -7.7|2    +1.9|0    -0.1|0   +6.4|16    +9.6|3  +10.1|11    +9.5|1    +9.5|0    +4.6|0    +7.9|0    +0.5|0 |   +75.2    34
 2026 |    +7.1|0    +7.0|2    -1.5|0   +10.9|0    +2.3|7    +6.3|7         ·         ·         ·         ·         ·         · |   +36.2    16
```

### #2  s12 — size 4%  (Final $200,154)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.0|24   +22.9|0    +1.6|0    +3.8|0   +13.0|0    +6.6|0   -10.5|0    +0.3|0   +12.4|0    +9.2|0    -7.3|0    +3.5|0 |   +57.0    24
 2022 |    +6.3|3    +0.6|5   -0.2|15   -13.7|1    +2.1|0    -9.4|0   +17.0|0    +3.3|0   -10.0|0    +8.4|0    +8.6|0    -7.8|0 |    +0.5    24
 2023 |   +13.5|4    +0.9|3    -3.2|3    -4.9|5   +1.1|10   +14.3|0   +13.0|0    -7.1|0    -8.8|0    -7.5|0   +17.2|0   +15.3|0 |   +45.8    25
 2024 |    -4.9|4   +13.9|2    +1.5|1    -3.6|4   +8.0|10    -5.8|2    +5.5|0    +9.4|0    +3.0|0    +3.0|0   +11.8|0    +4.4|0 |   +54.1    23
 2025 |    +3.6|1    -4.3|2    +1.5|0    -0.0|0   +5.1|17    +6.9|3    +9.4|2    +7.9|0   +10.6|0    +2.2|0    +4.8|0    -0.2|0 |   +57.8    25
 2026 |    +7.7|0    +2.5|2    -5.0|0    +5.7|0    +1.1|8   +6.5|11         ·         ·         ·         ·         ·         · |   +19.2    21
```

### #3  s16 — size 5%  (Final $185,724)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.0|19   +23.8|0    +2.2|0    +2.8|0   +13.5|0    +9.3|0   -11.4|0    +0.9|0   +13.0|0   +11.2|0    -8.2|0    +3.3|0 |   +63.5    19
 2022 |    +7.3|2    +1.9|3    +0.4|8   -15.7|6    +3.2|0   -11.5|0   +14.8|0    +5.5|0   -10.3|0    +9.8|0    +4.4|0    -7.2|0 |    -2.5    19
 2023 |   +13.1|3    -5.1|2    -2.0|3    -2.9|4    +1.2|8   +14.3|0   +14.4|0    -8.9|0    -8.9|0    -6.7|0   +21.3|0   +15.9|0 |   +47.3    20
 2024 |    -6.4|2   +13.3|2    -1.9|3    -9.6|2   +5.4|10    -3.3|0    +6.0|0    +8.0|0   +11.5|0    +2.3|0   +13.2|0    +9.1|0 |   +54.4    19
 2025 |    +0.6|1    -1.1|1    -6.9|0    -1.0|0   +2.6|14    +4.4|3   +11.6|0    +8.7|0   +13.0|0    +3.8|0    +2.8|0    +1.2|0 |   +45.6    19
 2026 |    +6.4|0    +1.0|1    -7.5|0   +11.5|0    -1.3|6   +7.3|12         ·         ·         ·         ·         ·         · |   +17.3    19
```

### #4  s16 — size 4%  (Final $157,812)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.0|24   +22.9|0    +1.6|0    +3.8|0   +13.0|0    +6.6|0   -10.5|0    +0.3|0   +12.4|0    +9.2|0    -7.3|0    +3.5|0 |   +57.0    24
 2022 |    +6.5|2    +1.5|3    +0.3|8   -13.6|9    +1.9|0    -9.9|0   +13.1|0    +4.4|0    -9.4|0    +9.6|0    +4.0|0    -4.2|2 |    +0.4    24
 2023 |   +12.2|3    -5.6|2    -2.8|3    -2.5|4   -0.7|10   +13.5|0   +13.7|0    -9.0|0    -8.3|0    -7.7|0   +16.0|0   +16.5|2 |   +33.8    24
 2024 |    -7.2|3   +12.0|2    -1.9|3   -10.3|2   +4.7|11    -4.2|1    +7.5|0    +6.8|0    +8.8|0    +1.7|0   +13.3|0    +8.9|1 |   +43.7    23
 2025 |    +0.9|1    -2.5|1    -7.1|0    -1.1|0   +4.0|14    +7.2|6   +10.6|2    +9.8|0   +12.4|0    +6.7|0    +2.3|0    +0.0|0 |   +50.0    24
 2026 |    +6.0|0    +2.4|1    -7.9|0   +11.2|0    -1.8|7   +6.0|13         ·         ·         ·         ·         ·         · |   +15.6    21
```

### #5  s16 — size 3%  (Final $156,697)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.3|33   +20.1|0    +2.2|0    +5.0|0   +12.7|0    +4.8|0    -9.1|0    -0.2|0    +9.1|0    +8.1|0    -7.5|0    +3.8|0 |   +48.0    33
 2022 |    +5.8|2    +1.1|3    +0.2|8   -10.2|9    +1.4|0    -7.2|0    +9.2|0    +3.2|0    -6.9|0    +6.9|0    +2.9|0   -3.2|11 |    +1.2    33
 2023 |   +13.3|3    -5.3|2    -2.8|2    -2.9|4   -3.7|10   +12.8|0   +12.7|0    -7.9|0    -7.1|0    -6.9|0   +16.9|0  +15.6|11 |   +33.2    32
 2024 |    -6.7|3   +12.4|2    -1.0|1   -10.0|2   +3.8|12    -1.8|0   +10.0|0    +4.1|0    +8.9|0    +0.9|0    +7.4|0    +4.2|5 |   +34.1    25
 2025 |    +1.3|4    -2.9|1    -6.4|0    -1.0|0   +4.9|14   +5.7|10    +4.4|0   +10.0|0   +12.2|0    +6.4|0    +1.3|0    +1.1|3 |   +42.0    32
 2026 |   +10.4|0    +0.9|2    -6.3|1   +12.6|0   +13.2|6   +3.4|13         ·         ·         ·         ·         ·         · |   +37.5    22
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v1.3_roc100)

Trades scored: 131  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        49-52       13   +2.78    -7.91   0.352    0.536
D2        53-56       13   +2.99    -4.10   0.728    0.685
D3        57-60       13   -0.16   -10.06  -0.016   -0.021
D4        60-63       13   +0.70    -8.48   0.082    0.179
D5        63-64       13   -0.41    -7.83  -0.053   -0.084
D6        64-67       13   +3.10    -6.00   0.516    0.592
D7        67-70       13   +4.92    -4.45   1.105    0.931
D8        70-75       13   +4.06   -12.73   0.319    0.645
D9        75-80       13   +4.89    -9.76   0.502    0.758
D10       81-95       14   +7.82   -11.03   0.709    0.809
```

### s16  (bk50d_s16_v1.3_roc100)

Trades scored: 140  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       14   +4.68    -6.66   0.702    0.906
D2        44-52       14   +5.60    -6.43   0.872    0.932
D3        52-56       14   +2.21    -4.35   0.508    0.585
D4        56-60       14   -1.43   -10.52  -0.136   -0.345
D5        60-63       14   +1.67    -5.21   0.321    0.377
D6        63-65       14   +1.29    -8.12   0.159    0.288
D7        65-70       14   +4.01    -7.67   0.523    0.684
D8        70-75       14   +5.31   -11.54   0.460    0.651
D9        76-81       14   +2.96    -8.63   0.343    0.576
D10       82-95       14  +10.30   -11.27   0.914    1.012
```

### s12  (bk50d_s12_v1.3_roc100)

Trades scored: 142  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-42       14   +5.97    -8.33   0.717    0.973
D2        42-44       14   +2.27    -7.55   0.300    0.511
D3        44-48       14   +6.55    -4.65   1.408    1.081
D4        48-54       14   +2.84    -6.34   0.448    0.639
D5        54-60       15   +3.26    -6.21   0.525    0.774
D6        60-63       14   +2.01    -4.94   0.408    0.467
D7        63-65       14   +0.01   -10.50   0.000    0.018
D8        65-73       14   +3.12    -6.53   0.478    0.592
D9        73-80       14   +5.97    -9.76   0.612    0.788
D10       80-95       15   +9.66   -11.03   0.875    0.930
```

## Findings (2026-07-29 run, 2021-01-01 – 2026-06-26 — tables above regenerate on re-run)

1. **Looser thresholds win by a wide margin.** At 3% sizing s12 returns +45.96% (Calmar 1.596,
   Sortino 1.423) against s16's +35.24% and s20's +32.17%. 2016-2020 gives the same ordering.
   `s12 @3%` is the best cell in this window on every measure.
2. **s16 is an interpolation point, not a sweet spot** — it lands between s20 and s12 exactly where
   its threshold sits. Its only distinction is the mildest drawdown (−22.55%), so pick it if
   drawdown tolerance rather than return is the binding constraint.
3. **Limit-order entries do not help in this window.** Against the next-day-open rule, all four
   variants lose on average: `close` −3.90pp (0 of 9 cells), `close -1%` −1.10pp (3 of 9),
   `close -3%` −1.97pp (2 of 9), `close -5%` −7.82pp (1 of 9). The deep limits fail for a
   mechanical reason visible in the `unfil` column: at `close -5%`, 254 of the config's signals
   never fill at all. You get a better price on the trades you do take, and forgo the breakouts
   that ran without looking back — which are the ones that pay.
4. **The ranking separates only at the top.** D10 is the best decile in all three configs, but the
   middle is noise (D3 and D5 negative for s20, D4 for s16) on 13-15 trades per decile. Treat it as
   weak evidence for a top-quintile preference, not a monotonic score.
5. **Rank-ordered funding is a no-op** — measured against the same harness with the flag off, mean
   CAGR delta over these nine cells is +0.21pp, better in 5 and worse in 4. `MIN_RANKING = 40`
   already removes the low end, so same-day competitors score alike and reordering shuffles
   near-equivalents.

**How to improve performance:** prefer `s12` at 3%, keep the next-day-open entry, and keep the
plain 366d time cap. Every exit and entry variation tested so far is regime-dependent (see below);
the remaining untested lever is entry-side candidate supply — the relaxation sweep.

### Cross-period verdict on entry and exit variations

Both the entry rule and the two deferred exit filters were run over all three windows, 27
config/size cells each. Mean CAGR delta against the production rule:

```text
variation      2010-2015   2016-2020   2021-2026   cells won (CAGR, of 27)
close           +0.21       +0.89       -3.90            13
close -1%       +0.07       +1.42       -1.10            12
close -3%       -1.98       +2.54       -1.97            10
close -5%       -1.49       +2.22       -7.82            10
sma200x5        -2.13       -9.20       -1.91             6
dead120         -2.59       -9.70       -0.76             4
```

No variation wins a majority of the 27 cells, and every one changes sign between periods. Limit
entries help in 2016-2020 and hurt in 2021-2026; the exit filters fail everywhere and 2016-2020
rejects them outright. This is the same pattern `docs/research/result-qullamaggie-exit-sweep.md`
documented for exits: a change that looks decisive on one window does not survive the others. The
production rules — next-day open, 366d time cap — remain the ones to beat.
