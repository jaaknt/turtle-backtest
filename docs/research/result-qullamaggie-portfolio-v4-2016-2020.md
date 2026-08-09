# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-09 19:03:43 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2016-01-01 – 2020-12-31 |
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
SPY         55,797  +13.23   -34.10   0.388    1.030
QQQ         85,956  +23.46   -28.56   0.821    1.492
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 194 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        173,524  +42.11   -24.20   1.740    2.215    138    803   23.5%
3%     ungated      145,694  +37.22   -25.06   1.485    2.063    143    992   22.1%
4%     R>=44        177,889  +42.82   -29.42   1.455    2.114    107    834   21.9%
4%     ungated      157,720  +39.42   -34.30   1.149    2.007    109   1026   19.9%
5%     R>=44        164,669  +40.62   -35.19   1.155    1.975     88    853   20.2%
5%     ungated      190,402  +44.77   -37.17   1.204    2.126     89   1046   18.0%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 717 signals (1 with no fillable next-day open); ungated drops 0 (4 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        159,755  +39.77   -24.74   1.608    2.106    141    872   22.5%
3%     ungated      174,515  +42.27   -42.41   0.997    1.987    158   1569   12.9%
4%     R>=44        163,907  +40.49   -32.97   1.228    2.040    109    904   20.1%
4%     ungated      138,596  +35.85   -47.79   0.750    1.651    121   1606   11.5%
5%     R>=44        173,819  +42.16   -38.07   1.107    2.001     88    925   18.7%
5%     ungated      143,611  +36.82   -44.09   0.835    1.698     96   1631   11.5%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 1434 signals (1 with no fillable next-day open); ungated drops 0 (4 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44        171,445  +41.76   -21.16   1.974    2.273    140    892   22.6%
3%     ungated      119,492  +31.88   -44.15   0.722    1.524    164   2299    9.2%
4%     R>=44        173,704  +42.14   -24.63   1.711    2.240    109    923   21.0%
4%     ungated      132,263  +34.59   -45.89   0.754    1.578    122   2341    9.0%
5%     R>=44        193,496  +45.24   -33.07   1.368    2.189     88    944   19.0%
5%     ungated      142,521  +36.62   -49.65   0.737    1.572     98   2365    8.9%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=44             5%     193,496  +45.24   -33.07   1.368    2.189     88    944   19.0%
 2  s20 ungated           5%     190,402  +44.77   -37.17   1.204    2.126     89   1046   18.0%
 3  s20 R>=44             4%     177,889  +42.82   -29.42   1.455    2.114    107    834   21.9%
 4  s16 ungated           3%     174,515  +42.27   -42.41   0.997    1.987    158   1569   12.9%
 5  s16 R>=44             5%     173,819  +42.16   -38.07   1.107    2.001     88    925   18.7%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s12 R>=44             3%     171,445  +41.76   -21.16   1.974    2.273    140    892   22.6%
 2  s12 R>=44             4%     173,704  +42.14   -24.63   1.711    2.240    109    923   21.0%
 3  s20 R>=44             3%     173,524  +42.11   -24.20   1.740    2.215    138    803   23.5%
 4  s12 R>=44             5%     193,496  +45.24   -33.07   1.368    2.189     88    944   19.0%
 5  s20 ungated           5%     190,402  +44.77   -37.17   1.204    2.126     89   1046   18.0%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2016      44,449  +48.16   -11.05   4.358    2.751     33    153   22.0%
                    2017      53,584  +20.55    -6.57   3.127    2.082     31     15   40.5%
                    2018      72,661  +35.60   -13.66   2.606    2.105     12     21   19.8%
                    2019      93,955  +29.31   -15.17   1.932    1.784     32     53   12.7%
                    2020     171,445  +82.48   -21.16   3.897    2.703     32    650   18.3%
s12 R>=44 4%        2016      43,429  +44.76   -11.54   3.879    2.635     24    162   23.0%
                    2017      53,936  +24.19    -5.97   4.053    2.384     23     23   35.3%
                    2018      71,359  +32.30   -17.58   1.837    1.800     12     21   19.8%
                    2019     100,615  +41.00   -12.87   3.186    2.397     25     60   11.8%
                    2020     173,704  +72.64   -24.63   2.949    2.424     25    657   15.1%
s12 R>=44 5%        2016      42,826  +42.75   -12.41   3.446    2.445     19    167   23.2%
                    2017      55,217  +28.93    -7.38   3.921    2.641     19     27   30.2%
                    2018      70,824  +28.26   -22.82   1.239    1.445     11     22   18.2%
                    2019      93,153  +31.53   -15.64   2.016    1.735     20     65   11.4%
                    2020     193,496 +107.72   -33.07   3.257    2.923     19    663   12.1%
s20 ungated 5%      2016      43,642  +45.47   -12.12   3.751    2.605     19    168   23.4%
                    2017      57,855  +32.57    -9.77   3.333    2.897     19     26   30.9%
                    2018      70,235  +21.40   -25.41   0.842    1.108     11     24   15.5%
                    2019      88,378  +25.83   -16.12   1.603    1.480     21     75    9.5%
                    2020     190,402 +115.44   -37.17   3.106    2.952     19    753   10.7%
s20 R>=44 4%        2016      45,046  +50.15   -11.12   4.512    2.583     25    132   21.2%
                    2017      54,198  +20.32    -9.02   2.253    1.876     23     11   39.2%
                    2018      75,731  +39.73   -17.76   2.237    2.116     10     20   17.9%
                    2019      94,366  +24.61   -14.68   1.676    1.465     25     50   13.7%
                    2020     177,889  +88.51   -29.42   3.009    2.552     24    621   17.3%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $171,445)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.2|33   +12.8|0    -3.1|0    +3.1|0   +10.1|0    +3.7|0    +4.8|0    -3.1|0   +15.2|0    -1.7|0 |   +48.2    33
 2017 |    +6.3|0    -1.2|0    -0.1|2    +0.2|0    +0.4|3    +3.4|3    -0.0|4    -0.2|5    +1.3|4    +1.6|8    +5.5|2    +2.0|0 |   +20.6    31
 2018 |    +0.0|0    -3.7|0    +2.9|0    +7.1|3   +16.2|4    +1.6|2    +4.1|0   +15.2|1    -1.3|1    -6.1|0    +0.7|0    -3.5|1 |   +35.6    12
 2019 |    +7.0|0   +7.9|14    -0.9|4    -1.4|2    -6.8|2   +14.1|3    +1.7|4    -9.5|2    -0.4|1    +2.4|0    +3.3|0   +11.1|0 |   +29.3    32
 2020 |    -3.0|0    +0.8|1    -7.0|0    +7.1|0   +4.4|23    +4.1|3    +5.4|2   +11.7|2    -6.0|1    -1.6|0   +37.1|0   +15.5|0 |   +82.5    32
```

### s12 R>=44 — size 4%  (Final $173,704)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.8|24   +12.2|0    -3.3|0    +0.8|0    +9.4|0    +4.2|0    +5.3|0    -3.0|0   +16.5|0    -1.7|0 |   +44.8    24
 2017 |    +6.4|0    -1.5|0    +0.4|2    +0.3|0    +0.6|3    +4.6|3    -0.1|4    -0.3|5    +1.7|4    +1.3|2    +6.3|0    +2.5|0 |   +24.2    23
 2018 |    +1.3|0    -3.0|0    +2.0|0    +7.1|3   +16.1|3    +3.6|3    +3.6|0   +13.3|1    -3.0|1    -5.5|0    +0.0|0    -4.9|1 |   +32.3    12
 2019 |    +9.4|0  +11.5|11    -2.2|0    -2.0|2    -3.8|2   +15.5|3    +2.0|3    -7.8|2    -0.2|1    +2.9|0    +1.8|0   +10.5|1 |   +41.0    25
 2020 |    -3.8|0    +1.4|0    -8.0|0   +15.0|0   +3.9|15    +2.4|3    +4.9|2    +8.2|2    -9.5|1    -2.9|0   +39.5|0   +13.0|2 |   +72.6    25
```

### s12 R>=44 — size 5%  (Final $193,496)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.9|19   +10.3|0    -2.7|0    -0.3|0    +9.8|0    +4.8|0    +5.9|0    -1.7|0   +15.8|0    -3.0|0 |   +42.8    19
 2017 |    +5.9|0    -2.5|0    +1.4|2    +0.4|0    +0.7|3    +5.7|3    -0.1|4    -0.4|5    +2.0|2    +2.3|0    +7.6|0    +3.0|0 |   +28.9    19
 2018 |    +1.4|0    -1.6|0    +0.2|0    +8.1|2   +17.8|3    +2.0|3    +4.6|0   +14.8|1    -3.7|1    -6.1|0    -2.3|0    -6.9|1 |   +28.3    11
 2019 |   +10.9|0   +13.9|7    -0.5|0    -1.7|1    -5.7|2   +10.5|3    -0.1|4   -10.1|2    +1.6|1    +1.8|0    +1.4|0    +8.5|0 |   +31.5    20
 2020 |    -0.4|0    +1.1|1   -14.1|0   +12.9|0  +13.6|10    +5.9|2   +11.8|3    +8.9|1    -6.9|2    -6.7|0   +38.0|0   +21.1|0 |  +107.7    19
```

### s20 ungated — size 5%  (Final $190,402)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.2|19    +9.1|0    -2.0|0    -0.4|0   +10.1|0    +5.1|0    +4.5|0    -1.8|0   +17.5|0    -2.3|0 |   +45.5    19
 2017 |    +7.4|0    -3.0|0    +0.9|2    -0.6|0    +0.6|2    +4.7|4    +3.7|4    -3.9|4    +5.2|3    +4.5|0    +6.4|0    +3.2|0 |   +32.6    19
 2018 |    +2.7|0    -2.2|0    +0.6|1    +4.5|1   +15.9|3    +6.1|2    +0.5|2   +15.1|1    +0.2|1   -10.3|0    -1.2|0    -9.0|0 |   +21.4    11
 2019 |   +10.1|0   +17.1|7    -5.1|0    +1.5|2    -6.8|3    +8.0|5    +1.7|2    -9.5|1    +1.0|0    +2.0|1    +2.1|0    +4.0|0 |   +25.8    21
 2020 |    +7.4|0    -0.2|1   -18.3|0   +11.7|0   +10.4|9    +5.1|5    +9.5|1   +13.1|1    -5.0|0    -6.6|2   +41.5|0   +22.1|0 |  +115.4    19
```

### s20 R>=44 — size 4%  (Final $177,889)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.9|25   +15.2|0    -6.1|0    +3.7|0   +12.7|0    +2.4|0    +5.6|0    -2.7|0   +14.1|0    -2.0|0 |   +50.2    25
 2017 |    +7.3|0    -3.0|0    -1.2|2    -0.5|0    +0.5|2    +3.9|2    +2.1|3    -2.7|4    +2.8|3    +3.5|6    +3.1|1    +3.3|0 |   +20.3    23
 2018 |    +1.1|0    -3.9|0    +3.4|0    +8.1|3   +15.1|3    +4.3|2    +3.3|0   +17.6|1    +1.2|1   -10.1|0    +1.8|0    -4.6|0 |   +39.7    10
 2019 |    +6.6|0  +10.4|13    -2.2|0    +2.3|2    -6.4|2   +11.0|3    +2.1|3   -10.5|1    +3.6|0    -1.9|1    +3.3|0    +6.3|0 |   +24.6    25
 2020 |    -1.3|0    +0.3|1   -13.1|0   +12.3|0   +3.7|18    +4.7|3    +3.4|1   +13.7|0    -4.1|0    -6.3|1   +44.9|0   +17.4|0 |   +88.5    24
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 107  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-45       10   +1.72    -5.16   0.333    0.717
D2        46-47       11   +3.01    -4.61   0.654    1.086
D3        47-51       11   +1.33    -7.05   0.189    0.508
D4        53-54       10   +1.99    -8.44   0.235    0.737
D5        55-61       11   +3.34    -4.40   0.760    1.277
D6        61-65       11   +0.30   -13.65   0.022    0.113
D7        65-75       10   +7.80    -7.61   1.025    2.023
D8        75-96       11   +7.84    -3.92   2.001    2.010
D9        96-100      11  +11.06   -10.16   1.089    1.812
D10      100-100      11   +5.22   -16.85   0.310    0.862
```

### s16  (bk50d_s16_v2.0)

Trades scored: 109  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +3.28    -3.93   0.834    1.179
D2        44-46       11   +0.94   -12.88   0.073    0.291
D3        46-47       11   +3.32    -6.71   0.495    1.219
D4        47-53       11   +0.12    -8.06   0.015    0.077
D5        53-57       11   +2.66    -4.76   0.558    0.909
D6        57-61       11   +5.19    -4.50   1.154    1.829
D7        61-65       11   -0.77   -15.31  -0.050   -0.227
D8        65-79       11   +7.56    -5.84   1.294    2.157
D9        89-100      11   +8.38    -8.02   1.044    1.904
D10      100-100      11  +10.20   -16.62   0.614    1.481
```

### s12  (bk50d_s12_v2.0)

Trades scored: 109  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       10   +3.05    -4.61   0.661    1.133
D2        44-46       11   +2.38   -10.80   0.220    0.788
D3        47-47       11   +3.84    -4.54   0.846    1.395
D4        47-51       11   +2.69    -6.23   0.432    0.986
D5        51-57       11   +3.28    -4.43   0.741    1.378
D6        57-61       11   +5.02    -6.14   0.817    1.531
D7        61-65       11   +1.22   -11.60   0.105    0.451
D8        68-89       11   +3.61    -4.58   0.789    1.287
D9        89-100      11   +6.68    -9.35   0.714    1.521
D10      100-100      11  +10.20   -16.62   0.614    1.481
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
