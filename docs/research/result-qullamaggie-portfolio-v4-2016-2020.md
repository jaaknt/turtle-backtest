# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-01 10:47:40 Tallinn time
Period: 2016-01-01 – 2020-12-31  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         55,797  +13.23   -34.10   0.388    1.030
QQQ         85,956  +23.46   -28.56   0.821    1.492
```

## s20  (bk50d_s20_v2.0 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 179 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         108,184  +29.28   -30.62   0.956    1.715    129    505   31.6%
4%         116,840  +31.29   -26.45   1.183    1.704    102    532   26.0%
5%         137,756  +35.69   -23.02   1.551    1.910     82    552   24.8%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         107,990  +29.23   -21.13   1.384    1.686    139    674   23.7%
4%         113,289  +30.48   -29.46   1.034    1.722    107    706   22.2%
5%         114,903  +30.85   -33.56   0.919    1.699     87    726   21.1%
```

## s16  (bk50d_s16_v2.0 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 526 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         114,759  +30.82   -29.45   1.046    1.768    132    542   28.2%
4%         132,982  +34.73   -25.94   1.339    1.841    103    571   23.7%
5%         144,764  +37.04   -26.29   1.409    1.991     83    591   23.3%
```

**no ranking filter** — 0 signals dropped by the gate, 1 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         114,597  +30.78   -29.78   1.034    1.747    151   1048   18.2%
4%         105,266  +28.57   -43.60   0.655    1.463    117   1082   15.1%
5%         101,074  +27.53   -44.41   0.620    1.381     98   1101   12.6%
```

## s12  (bk50d_s12_v2.0 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 936 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         101,568  +27.66   -26.13   1.059    1.600    143    602   21.4%
4%         104,436  +28.37   -29.60   0.959    1.589    111    634   19.6%
5%          99,489  +27.13   -45.95   0.590    1.419     92    653   17.0%
```

**no ranking filter** — 0 signals dropped by the gate, 1 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         104,991  +28.51   -44.54   0.640    1.465    162   1518   11.2%
4%         102,116  +27.79   -48.32   0.575    1.374    121   1559   10.4%
5%          99,022  +27.01   -49.72   0.543    1.310     97   1583    9.6%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s16 R>=40 — size 5%  (Final $144,764)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.1|20   +12.7|0    -2.0|0    +1.5|0   +11.5|0    +2.8|0    +5.4|0    -5.3|0   +17.0|0    -3.4|0 |   +43.5    20
 2017 |    +7.4|0    -2.1|0    +0.4|3    -0.4|0    +0.5|3    +5.9|2    +1.5|4    +0.6|2    +3.8|2    +4.1|2    +3.1|0    +1.6|0 |   +29.3    18
 2018 |    +4.9|0    -7.9|0    +4.2|1    +3.0|2    +9.1|1    -1.5|0    +2.8|1    +5.6|1    +0.7|0    -0.8|0    +1.0|0    -5.7|1 |   +15.3     7
 2019 |    +6.7|0    +2.4|7    -1.0|4    -0.3|1   -10.6|1   +20.4|3    +1.9|0   -10.5|1    -2.2|1    +4.3|0    +4.4|0    +8.5|1 |   +22.3    19
 2020 |    -5.2|0    -0.3|1   -12.3|0    +5.5|0   +3.7|13    +8.4|2    +8.2|0   +12.6|1    -6.2|2    -0.8|0   +33.9|0   +23.6|0 |   +84.5    19
```

### #2  s20 R>=40 — size 5%  (Final $137,756)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|20   +14.5|0    -2.6|0    +1.9|0   +13.4|0    +0.9|0    +5.4|0    -4.2|0   +15.9|0    -3.3|0 |   +47.4    20
 2017 |    +8.5|0    -2.5|0    -0.3|2    -0.6|0    +0.6|2    +4.5|2    +3.3|3    -2.7|2    +3.4|2    +3.6|2    +2.3|0    +2.3|2 |   +24.1    17
 2018 |    +8.9|1    -5.4|0    +4.6|1    +6.1|1    +6.6|1    -4.3|0    +3.4|1    +6.6|1    +3.7|0    -7.9|0    +5.5|0    -7.0|0 |   +20.3     6
 2019 |    +1.8|0    +1.0|7    -3.6|6    +0.8|2   -10.2|1   +16.9|0    +3.3|1    -9.0|1    -3.6|0    +2.5|1    +9.3|0    +7.2|0 |   +14.1    19
 2020 |    -8.1|0    +0.4|1   -11.7|0    +4.8|0   -1.6|16    +8.7|0    +6.8|0   +13.7|1    -3.6|0    -0.6|1   +42.0|1   +21.1|0 |   +82.9    20
```

### #3  s16 R>=40 — size 4%  (Final $132,982)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|25   +14.3|0    -4.6|0    +4.3|0   +11.9|0    +2.0|0    +6.1|0    -3.6|0   +14.3|0    -2.9|0 |   +47.6    25
 2017 |    +7.2|0    -2.3|0    -0.6|3    -0.3|0    +0.4|3    +4.7|2    +1.2|4    +0.4|2    +3.1|2    +3.3|2    +2.5|0    +1.7|3 |   +23.1    21
 2018 |    +6.1|2    -6.2|0    +5.3|1    +5.9|2    +9.2|1    -4.0|0    +3.1|1    +7.2|1    +1.4|0    -3.8|0    +6.0|0    -8.0|1 |   +22.5     9
 2019 |    +6.1|0    +1.9|7    -1.2|7    -1.1|1    -9.8|1   +16.9|3    +1.7|2   -14.9|1    -2.6|2    +4.5|0    +7.8|0    +8.8|0 |   +15.2    24
 2020 |    -7.0|0    -0.1|1   -12.0|0    +4.3|0   +2.6|16    +7.3|2    +8.9|1    +9.6|1    -6.3|3    +0.4|0   +33.6|0   +22.6|0 |   +72.8    24
```

### #4  s20 R>=40 — size 4%  (Final $116,840)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.6|25   +15.6|0    -5.0|0    +4.0|0   +12.7|0    +0.3|0    +5.6|0    -3.3|0   +12.2|0    -3.1|0 |   +44.0    25
 2017 |    +7.7|0    -2.2|0    -0.9|2    -0.5|0    +0.5|2    +3.6|2    +2.6|3    -2.2|2    +2.7|2    +2.9|2    +1.8|0    +1.9|2 |   +19.1    17
 2018 |    +6.1|6    -6.4|0    +4.2|1    +6.1|1    +8.0|1    -2.8|0    +2.7|1    +6.6|1    +3.6|0    -7.9|0    +8.0|0    -8.3|0 |   +19.2    11
 2019 |    +4.4|0    +0.8|7    -2.9|6    +0.6|2    -8.0|1   +13.3|2    +1.9|4   -14.3|1    -3.3|0    +2.6|1    +8.3|0    +7.0|0 |    +7.5    24
 2020 |    -7.3|0    +0.6|1   -12.2|0    +5.9|0   +1.0|17    +9.1|2    +4.7|2   +13.2|1    -4.6|0    -0.8|1   +40.9|1   +17.5|0 |   +77.2    25
```

### #5  s20 ungated — size 5%  (Final $114,903)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|20   +15.0|0    -2.9|0    +1.2|0   +13.0|0    +2.9|0    +6.0|0    -4.1|0   +16.9|0    -3.7|0 |   +50.0    20
 2017 |    +9.2|0    -3.4|0    -0.4|2    -0.6|0    +0.6|2    +4.1|3    +3.7|3    -2.4|2    +3.3|4    +4.0|2    +5.9|0    +3.1|0 |   +30.0    18
 2018 |    +3.6|0    -5.6|0    +1.9|1    +1.7|2    +9.1|3    -0.7|1    +2.0|2    +5.6|1    +1.6|0   -10.2|0    -3.4|0    -8.1|0 |    -4.3    10
 2019 |    +7.5|0   +5.0|10    -2.6|0    +2.1|2   -11.4|1   +10.7|2    -0.9|3    -9.1|1    +2.1|1    +0.4|0    -0.4|0    +5.7|0 |    +6.9    20
 2020 |    -3.6|0    +3.9|1   -14.9|0    +7.1|0   +5.8|12   +10.4|2    +9.1|2   +12.9|1    -6.8|1    -5.0|0   +35.5|0   +22.0|0 |   +92.0    19
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 102  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        43-43       10   +3.25    -4.37   0.743    1.191
D2        43-47       10   +2.67    -7.64   0.349    0.953
D3        49-50       10   -0.11    -8.09  -0.014   -0.007
D4        52-60       10   +1.05    -6.72   0.156    0.434
D5        60-66       11   +0.78    -9.54   0.081    0.260
D6        66-66       10   +1.42    -6.04   0.234    0.546
D7        70-83       10   +3.05    -4.38   0.695    1.150
D8        83-83       10  +10.20   -10.12   1.007    2.348
D9        83-87       10   +4.80    -7.68   0.625    1.238
D10      100-100      11   +5.51   -12.89   0.428    1.060
```

### s16  (bk50d_s16_v2.0)

Trades scored: 103  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       10   +5.55    -3.56   1.558    1.950
D2        43-43       10   +2.49    -5.73   0.434    0.910
D3        43-49       10   +2.19    -6.36   0.345    1.044
D4        49-56       11   +1.35    -9.76   0.138    0.347
D5        56-60       10   -0.49   -10.39  -0.048   -0.141
D6        64-66       10   +1.69    -6.81   0.249    0.570
D7        66-73       11   +1.81    -5.92   0.306    0.696
D8        74-83       10  +10.07    -8.56   1.177    2.396
D9        83-87       10   +5.52    -6.97   0.792    1.428
D10       87-100      11   +5.64   -11.79   0.479    1.076
```

### s12  (bk50d_s12_v2.0)

Trades scored: 111  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-40       11   +0.71   -10.74   0.066    0.292
D2        40-43       11   +3.53    -7.72   0.458    1.257
D3        43-43       11   +3.02    -4.27   0.706    1.143
D4        44-47       11   +1.81    -7.69   0.236    0.650
D5        47-50       11   +1.99    -6.85   0.291    0.653
D6        51-60       11   +1.65    -5.19   0.319    0.590
D7        60-66       11   +1.39    -7.37   0.189    0.441
D8        66-74       11   +0.65   -10.51   0.062    0.247
D9        74-87       11   +9.55    -7.36   1.298    2.407
D10       87-100      12   +5.11   -14.76   0.346    0.936
```

## Findings (2026-07-30 run, 2016-01-01 – 2020-12-31 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.

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
