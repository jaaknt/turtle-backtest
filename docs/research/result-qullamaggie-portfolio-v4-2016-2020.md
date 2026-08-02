# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-02 14:21:22 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2016-01-01 – 2020-12-31 |
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
SPY         55,797  +13.23   -34.10   0.388    1.030
QQQ         85,956  +23.46   -28.56   0.821    1.492
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 179 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        108,184  +29.28   -30.62   0.956    1.715    129    506   31.6%
3%     ungated      105,769  +28.70   -22.89   1.254    1.643    139    675   23.7%
4%     R>=40        116,840  +31.29   -26.45   1.183    1.704    102    533   26.0%
4%     ungated      110,384  +29.80   -31.73   0.939    1.688    107    707   22.1%
5%     R>=40        137,756  +35.69   -23.02   1.551    1.910     82    553   24.8%
5%     ungated      112,910  +30.39   -35.77   0.850    1.676     87    727   20.9%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 526 signals (0 with no fillable next-day open); ungated drops 0 (1 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        114,759  +30.82   -29.45   1.046    1.768    132    542   28.2%
3%     ungated      113,035  +30.42   -30.75   0.989    1.722    151   1048   18.2%
4%     R>=40        132,982  +34.73   -25.94   1.339    1.841    103    571   23.7%
4%     ungated      111,067  +29.96   -44.43   0.674    1.508    117   1082   15.1%
5%     R>=40        144,764  +37.04   -26.29   1.409    1.991     83    591   23.3%
5%     ungated       96,831  +26.44   -45.37   0.583    1.335     98   1101   12.6%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 40` drops 934 signals (0 with no fillable next-day open); ungated drops 0 (1 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=40        104,578  +28.41   -26.13   1.087    1.631    143    602   21.4%
3%     ungated      104,991  +28.51   -44.54   0.640    1.465    162   1516   11.2%
4%     R>=40        104,436  +28.37   -29.60   0.959    1.589    111    634   19.6%
4%     ungated      102,116  +27.79   -48.32   0.575    1.374    121   1557   10.4%
5%     R>=40         99,489  +27.13   -45.95   0.590    1.419     92    653   17.0%
5%     ungated       99,022  +27.01   -49.72   0.543    1.310     97   1581    9.6%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=40             5%     144,764  +37.04   -26.29   1.409    1.991     83    591   23.3%
 2  s20 R>=40             5%     137,756  +35.69   -23.02   1.551    1.910     82    553   24.8%
 3  s16 R>=40             4%     132,982  +34.73   -25.94   1.339    1.841    103    571   23.7%
 4  s20 R>=40             4%     116,840  +31.29   -26.45   1.183    1.704    102    533   26.0%
 5  s16 R>=40             3%     114,759  +30.82   -29.45   1.046    1.768    132    542   28.2%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 R>=40             5%     144,764  +37.04   -26.29   1.409    1.991     83    591   23.3%
 2  s20 R>=40             5%     137,756  +35.69   -23.02   1.551    1.910     82    553   24.8%
 3  s16 R>=40             4%     132,982  +34.73   -25.94   1.339    1.841    103    571   23.7%
 4  s16 R>=40             3%     114,759  +30.82   -29.45   1.046    1.768    132    542   28.2%
 5  s16 ungated           3%     113,035  +30.42   -30.75   0.989    1.722    151   1048   18.2%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=40 3%        2016      41,434  +38.11   -10.87   3.506    2.265     33    110   22.3%
                    2017      48,970  +18.19    -7.30   2.490    1.820     27      9   39.8%
                    2018      54,550  +11.40   -19.12   0.596    0.652     19      3   15.9%
                    2019      63,730  +16.83   -20.89   0.806    1.047     32     22   12.4%
                    2020     104,578  +64.10   -25.02   2.562    2.226     32    458   16.8%
s12 R>=40 4%        2016      41,521  +38.40   -12.00   3.201    2.235     25    118   20.9%
                    2017      51,189  +23.28    -6.45   3.612    2.203     23     13   29.1%
                    2018      51,663   +0.93   -20.72   0.045    0.014     15      7   22.9%
                    2019      61,248  +18.55   -20.29   0.914    1.090     24     30   10.6%
                    2020     104,436  +70.51   -27.88   2.529    2.364     24    466   14.6%
s12 R>=40 5%        2016      43,797  +45.99   -10.97   4.194    2.610     19    124   23.3%
                    2017      53,731  +22.68    -6.67   3.402    1.983     19     17   23.5%
                    2018      54,497   +1.43   -25.04   0.057    0.058     15      7   18.6%
                    2019      58,087   +6.59   -29.75   0.221    0.465     20     34   10.9%
                    2020      99,489  +71.28   -35.40   2.014    2.162     19    471    8.8%
s16 R>=40 5%        2016      43,046  +43.49   -12.15   3.580    2.339     20    104   20.7%
                    2017      55,648  +29.27    -6.33   4.624    2.607     18      8   30.4%
                    2018      64,142  +15.26   -12.31   1.240    0.975      7      6   33.7%
                    2019      78,473  +22.34   -16.14   1.384    1.411     19     23   14.6%
                    2020     144,764  +84.48   -26.29   3.213    2.622     19    450   17.4%
s20 R>=40 5%        2016      44,214  +47.38   -11.74   4.037    2.513     20     94   21.2%
                    2017      54,874  +24.11    -7.46   3.233    2.245     17      4   39.4%
                    2018      66,040  +20.35   -13.84   1.471    1.157      6      7   26.0%
                    2019      75,333  +14.07   -17.96   0.784    0.963     19     17   16.7%
                    2020     137,756  +82.86   -23.02   3.600    2.517     20    431   20.6%
```

## Monthly returns/transactions — s12 R>=40 at each sizing, plus the top 2 by Final$

### s12 R>=40 — size 3%  (Final $104,578)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.2|33   +13.3|0    -3.7|0    +3.5|0   +10.1|0    +0.5|0    +4.9|0    -3.7|0   +11.7|0    -2.3|0 |   +38.1    33
 2017 |    +6.6|0    -0.3|0    -0.1|4    -0.2|0    +0.2|5    +3.1|2    +1.3|4    +0.3|4    +1.7|2    +1.2|3    +1.5|0    +1.7|3 |   +18.2    27
 2018 |    +4.3|4    -6.4|0    +5.4|1    +5.0|4    +9.4|3    -2.1|1    +3.0|2    +5.9|2    +2.6|0    -7.4|0    +4.0|0   -10.4|2 |   +11.4    19
 2019 |   +10.7|0   +3.0|10    -1.8|8    -0.2|2   -11.6|1   +14.4|3    +0.5|4   -12.9|1    -1.7|2    +3.2|0    +7.6|0    +8.1|1 |   +16.8    32
 2020 |   -10.1|0    +0.4|1   -10.4|0    +6.0|0   +1.1|21   +12.3|3    +6.0|3    +8.3|1    -5.2|3    -0.5|0   +32.4|0   +17.5|0 |   +64.1    32
```

### s12 R>=40 — size 4%  (Final $104,436)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.8|25   +11.8|0    -1.2|0    +1.0|0    +9.3|0    +2.6|0    +4.5|0    -4.9|0   +15.4|0    -2.8|0 |   +38.4    25
 2017 |    +7.1|0    -0.0|0    +0.8|4    -0.2|0    +0.2|5    +4.2|2    +1.7|4    +0.4|4    +2.2|2    +1.2|2    +2.2|0    +1.6|0 |   +23.3    23
 2018 |    +4.1|0    -7.0|0    +4.0|1    +1.7|4    +8.8|3    -0.0|1    +2.8|2    +3.8|2    +1.8|0    -6.0|0    -2.2|0    -9.2|2 |    +0.9    15
 2019 |   +11.9|0    +4.3|9    -1.9|1    +0.7|1   -11.2|1   +15.2|3    +0.4|4   -15.0|1    -0.3|2    +2.5|1    +5.3|0    +9.3|1 |   +18.6    24
 2020 |   -10.4|0    +1.2|1   -13.7|0    +9.7|0   +5.5|12   +11.4|3    +9.3|3    +8.6|1    -5.8|3    -2.8|1   +29.5|0   +20.2|0 |   +70.5    24
```

### s12 R>=40 — size 5%  (Final $99,489)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.1|19   +14.6|0    -2.4|0    +2.5|0    +8.4|0    +3.2|0    +5.9|0    -4.1|0   +17.3|0    -3.5|0 |   +46.0    19
 2017 |    +6.8|0    -1.7|0    +0.5|4    -0.3|0    +0.3|5    +5.2|2    +2.2|4    +0.5|4    +3.1|0    +1.1|0    +2.1|0    +1.2|0 |   +22.7    19
 2018 |    +5.1|0    -6.2|0    +5.0|1    +1.3|4    +9.0|3    +0.9|1    +2.2|2    +5.5|2    +2.1|0    -7.2|0    -2.8|0   -11.5|2 |    +1.4    15
 2019 |   +15.3|0    +6.7|4    -0.8|1    -0.8|1   -14.2|1   +10.8|3    -0.5|5   -19.6|1    +0.7|2    +3.1|0    +3.6|0    +7.8|2 |    +6.6    20
 2020 |   -11.5|0    +1.0|1   -16.6|0   +13.9|0    +9.2|6    +7.5|2    +9.5|5    +8.8|1    -4.6|3    -3.2|0   +30.0|0   +20.3|1 |   +71.3    19
```

### s16 R>=40 — size 5%  (Final $144,764)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -1.1|20   +12.7|0    -2.0|0    +1.5|0   +11.5|0    +2.8|0    +5.4|0    -5.3|0   +17.0|0    -3.4|0 |   +43.5    20
 2017 |    +7.4|0    -2.1|0    +0.4|3    -0.4|0    +0.5|3    +5.9|2    +1.5|4    +0.6|2    +3.8|2    +4.1|2    +3.1|0    +1.6|0 |   +29.3    18
 2018 |    +4.9|0    -7.9|0    +4.2|1    +3.0|2    +9.1|1    -1.5|0    +2.8|1    +5.6|1    +0.7|0    -0.8|0    +1.0|0    -5.7|1 |   +15.3     7
 2019 |    +6.7|0    +2.4|7    -1.0|4    -0.3|1   -10.6|1   +20.4|3    +1.9|0   -10.5|1    -2.2|1    +4.3|0    +4.4|0    +8.5|1 |   +22.3    19
 2020 |    -5.2|0    -0.3|1   -12.3|0    +5.5|0   +3.7|13    +8.4|2    +8.2|0   +12.6|1    -6.2|2    -0.8|0   +33.9|0   +23.6|0 |   +84.5    19
```

### s20 R>=40 — size 5%  (Final $137,756)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|20   +14.5|0    -2.6|0    +1.9|0   +13.4|0    +0.9|0    +5.4|0    -4.2|0   +15.9|0    -3.3|0 |   +47.4    20
 2017 |    +8.5|0    -2.5|0    -0.3|2    -0.6|0    +0.6|2    +4.5|2    +3.3|3    -2.7|2    +3.4|2    +3.6|2    +2.3|0    +2.3|2 |   +24.1    17
 2018 |    +8.9|1    -5.4|0    +4.6|1    +6.1|1    +6.6|1    -4.3|0    +3.4|1    +6.6|1    +3.7|0    -7.9|0    +5.5|0    -7.0|0 |   +20.3     6
 2019 |    +1.8|0    +1.0|7    -3.6|6    +0.8|2   -10.2|1   +16.9|0    +3.3|1    -9.0|1    -3.6|0    +2.5|1    +9.3|0    +7.2|0 |   +14.1    19
 2020 |    -8.1|0    +0.4|1   -11.7|0    +4.8|0   -1.6|16    +8.7|0    +6.8|0   +13.7|1    -3.6|0    -0.6|1   +42.0|1   +21.1|0 |   +82.9    20
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
