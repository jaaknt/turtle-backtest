# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-07-30
Period: 2016-01-01 – 2020-12-31  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         55,797  +13.23   -34.10   0.388    0.681
QQQ         85,956  +23.46   -28.56   0.821    0.965
```

## s20  (bk50d_s20_v2.0 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 137 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         105,884  +28.72   -25.98   1.106    1.224    112    335   41.0%
4%         117,685  +31.48   -33.37   0.943    1.213     93    354   34.1%
5%         120,686  +32.14   -29.85   1.077    1.227     77    370   31.8%
```

**no ranking filter** — 0 signals dropped by the gate, 1 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         102,761  +27.96   -20.23   1.382    1.102    135    448   25.8%
4%         107,430  +29.10   -22.80   1.276    1.100    103    480   24.0%
5%         100,027  +27.27   -31.47   0.866    1.039     83    500   24.7%
```

## s16  (bk50d_s16_v2.0 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 390 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         122,392  +32.51   -30.44   1.068    1.256    121    357   35.5%
4%         135,825  +35.31   -31.34   1.127    1.290    101    377   28.8%
5%         137,170  +35.57   -28.98   1.227    1.266     81    397   26.3%
```

**no ranking filter** — 0 signals dropped by the gate, 3 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         114,266  +30.70   -22.92   1.340    1.208    143    722   22.3%
4%         128,585  +33.83   -27.38   1.236    1.247    110    755   20.1%
5%         120,939  +32.20   -37.11   0.868    1.139     90    775   18.4%
```

## s12  (bk50d_s12_v2.0 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 714 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         117,314  +31.39   -33.74   0.930    1.195    133    388   29.9%
4%         122,974  +32.64   -26.24   1.244    1.205    105    416   23.5%
5%         120,324  +32.06   -23.63   1.357    1.218     85    436   23.0%
```

**no ranking filter** — 0 signals dropped by the gate, 3 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         105,758  +28.69   -45.23   0.634    0.968    158   1074   14.7%
4%          90,430  +24.72   -47.10   0.525    0.851    120   1112   12.7%
5%         112,292  +30.25   -43.71   0.692    0.992     96   1136   11.5%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s16 R>=40 — size 5%  (Final $137,170)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.3|16    +7.6|4    -1.2|0    +3.0|0   +10.0|0    +0.8|0    +3.5|0    -5.6|0    +9.6|0    +0.1|0 |   +29.6    20
 2017 |    +5.9|0    +2.4|0    +2.4|2    -0.3|0    -0.3|3    +5.0|2    +2.0|4    -0.3|2    +4.8|2    +3.1|1    +3.8|0    +1.8|2 |   +34.6    18
 2018 |    +6.9|0    -7.2|0    +4.8|0    +3.8|2    +8.1|0    -1.6|0    +3.1|0    +4.2|1    -0.2|0    -1.8|0    +0.3|0    -5.2|1 |   +14.8     4
 2019 |    +6.0|0    +1.5|7    -0.0|2    -0.7|1    -4.9|0   +14.1|2    -0.1|5   -17.3|1    -2.5|1    +2.5|0    +6.1|0    +8.5|1 |   +10.0    20
 2020 |    -8.7|0    +6.5|1   -12.5|0   +10.5|0   +3.9|10   +11.7|1   +13.6|4   +14.5|0    +1.1|2    -8.9|0   +34.9|0   +17.7|1 |  +107.5    19
```

### #2  s16 R>=40 — size 4%  (Final $135,825)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|16   +10.4|8    -1.9|0    +4.6|0    +9.1|0    -0.9|0    +3.6|0    -6.2|0    +8.4|0    -0.5|0 |   +27.9    24
 2017 |    +6.1|0    +0.8|0    +2.3|2    -0.2|0    -0.3|3    +4.0|2    +1.6|4    -0.2|2    +3.8|2    +2.6|1    +3.1|0    +1.7|3 |   +28.2    19
 2018 |    +5.9|4    -6.5|0    +6.2|0    +6.1|2    +9.3|0    -3.5|0    +2.9|0    +5.9|1    +1.6|0    -4.2|0    +7.6|0    -6.8|1 |   +25.2     8
 2019 |    +7.1|0    +1.1|7    -0.1|2    -0.5|1    -3.9|0   +11.1|2    -0.1|5   -13.8|1    -2.0|1    +1.8|4    +7.1|0    +6.7|2 |   +12.6    25
 2020 |    -9.9|0    +3.6|1   -16.7|0   +14.8|0   +2.7|10   +10.4|2   +13.6|4   +16.5|1    +0.5|1    -3.1|3   +32.6|1   +13.2|2 |   +95.8    25
```

### #3  s16 ungated — size 4%  (Final $128,585)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.0|24    +0.4|0    -0.6|1    -2.9|0    +5.3|0    +5.4|0    +4.5|0    -3.2|0   +14.6|0    -1.7|0 |   +21.3    25
 2017 |    +5.0|0    +1.3|0    +1.8|2    -0.8|0    -0.6|3    +4.0|4    +2.1|8    -0.4|2    +3.8|4    +3.9|0    +6.5|0    +2.8|0 |   +33.6    23
 2018 |    +3.8|0    -3.5|0    +4.7|0    +2.9|3   +12.5|3    -0.8|1    +0.5|3    +5.0|1    -3.4|0    -6.5|0    -0.3|0    -6.6|2 |    +6.9    13
 2019 |   +10.5|0   +7.1|11    -3.5|0    +3.0|1   -15.9|1    +9.1|3    -2.4|5    -9.9|2    +6.1|1    +6.2|0    +8.0|0    +4.0|2 |   +20.2    26
 2020 |    -5.9|0    +6.0|2   -13.5|0   +12.0|0   +7.9|11    +8.8|3   +12.1|4   +10.8|2    -3.5|1    -3.9|0   +33.1|0   +18.4|0 |  +105.8    23
```

### #4  s12 R>=40 — size 4%  (Final $122,974)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.1|21    +7.2|4    -0.6|0    +2.2|0    +8.5|0    +0.7|0    +2.7|0    -4.6|0    +8.3|0    +0.3|0 |   +26.3    25
 2017 |    +5.9|0    +4.3|0    +2.6|2    -0.3|0    -0.3|3    +4.0|2    +1.7|4    -0.0|4    +2.5|2    +1.8|1    +3.5|0    +2.0|3 |   +31.3    21
 2018 |    +6.4|2    -6.1|0    +5.0|0    +6.1|3    +9.0|2    -2.7|1    +4.3|0    +4.3|2    +2.5|0    -7.4|0    +3.4|0    -8.1|1 |   +15.7    11
 2019 |    +9.2|0    +2.3|9    -1.2|1    +0.2|3    -5.7|0   +13.1|2    +0.0|5   -13.3|1    -1.6|1    +4.2|2    +6.9|0    +6.7|0 |   +19.6    24
 2020 |    -9.4|1    +5.2|1   -13.9|0    +9.6|0   +4.2|13   +10.2|2    +8.0|3   +10.2|1    -5.1|1    -2.6|2   +32.0|0   +19.0|0 |   +78.6    24
```

### #5  s16 R>=40 — size 3%  (Final $122,392)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|16  +14.1|17    -3.6|0    +8.5|0   +12.0|0    -3.5|0    +2.5|0    -6.0|0    +7.8|0    -1.6|0 |   +31.6    33
 2017 |    +6.3|0    +0.4|0    +1.7|2    -0.4|0    -0.2|3    +3.0|2    +1.2|4    -0.2|2    +2.9|2    +2.0|1    +2.4|0    +1.3|3 |   +22.2    19
 2018 |    +4.4|5    -5.6|0    +4.4|1    +4.2|2    +8.5|0    -1.9|0    +2.0|0    +5.1|1    +1.6|0    -3.7|0    +5.4|0    -5.7|1 |   +19.1    10
 2019 |    +6.1|0    +0.8|7    -0.1|2    -0.4|1    -3.0|0    +8.2|2    -0.1|5   -10.4|1    -1.5|1    +1.3|4    +5.2|0    +5.0|2 |   +10.3    25
 2020 |    -7.6|3    +1.6|3   -16.8|0   +15.2|0   +3.6|14    +9.4|2    +9.9|3   +16.5|1    -1.5|1    -2.3|3   +35.6|1   +13.4|3 |   +93.2    34
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 93  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        43-43        9   +3.01    -4.37   0.689    0.671
D2        43-47        9   +2.78    -2.91   0.954    0.936
D3        49-52        9   +0.12    -8.79   0.013    0.038
D4        52-60       10   +1.53    -8.46   0.181    0.449
D5        60-66        9   +2.18    -7.81   0.280    0.406
D6        66-66        9   +2.17    -5.55   0.390    0.423
D7        66-70       10   +3.81    -8.92   0.427    0.648
D8        70-83        9   +3.37    -5.07   0.666    0.721
D9        83-87        9   +8.99   -10.55   0.852    1.194
D10       87-100      10   +5.42   -10.55   0.514    0.331
```

### s16  (bk50d_s16_v2.0)

Trades scored: 101  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       10   +4.44    -3.56   1.248    1.006
D2        43-43       10   +3.31    -4.42   0.749    0.799
D3        46-47       10   +1.78    -8.76   0.203    0.420
D4        49-51       10   +0.87    -7.72   0.113    0.171
D5        52-60       10   +1.34    -7.44   0.180    0.395
D6        60-64       10   +2.27    -7.77   0.293    0.452
D7        64-66       10   +2.46    -5.55   0.443    0.513
D8        66-70       10   +3.52    -5.23   0.674    0.851
D9        73-83       10  +10.44    -5.69   1.834    1.507
D10       83-100      11   +6.49   -10.50   0.619    0.508
```

### s12  (bk50d_s12_v2.0)

Trades scored: 105  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-40       10   +1.18    -6.58   0.180    0.284
D2        41-43       11   +5.33    -3.27   1.632    1.086
D3        43-47       10   +2.82    -2.96   0.953    0.763
D4        47-50       11   +0.47   -12.24   0.038    0.113
D5        50-53       10   +2.81    -6.28   0.448    0.543
D6        56-60       11   +1.77    -7.40   0.240    0.506
D7        60-66       10   +2.53    -7.71   0.329    0.430
D8        66-70       11   +1.64    -8.61   0.191    0.344
D9        73-83       10  +10.30    -4.83   2.131    1.514
D10       83-100      11   +4.44   -13.77   0.322    0.328
```

## Findings (2026-07-30 run, 2016-01-01 – 2020-12-31 — tables above regenerate on re-run)

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
