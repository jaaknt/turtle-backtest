# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-09 19:03:28 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2010-01-01 – 2015-12-31 |
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
SPY         53,967  +10.30   -19.42   0.530    0.981
QQQ         72,292  +15.81   -16.09   0.983    1.327
```

## s20  (bk50d_s20_v2.0 / 366d)

`%abv_SMA50 > 20%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 35 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44         72,310  +15.82   -27.00   0.586    1.139    146     69   29.6%
3%     ungated       77,078  +17.06   -27.45   0.621    1.220    152     98   27.0%
4%     R>=44         73,445  +16.12   -30.00   0.537    1.131    120     95   24.2%
4%     ungated       72,597  +15.89   -24.26   0.655    1.126    122    128   23.3%
5%     R>=44         67,681  +14.54   -28.78   0.505    0.997    100    115   22.1%
5%     ungated       67,589  +14.52   -26.10   0.556    0.990    101    149   21.9%
```

## s16  (bk50d_s16_v2.0 / 366d)

`%abv_SMA50 > 16%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 278 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44         72,968  +15.99   -28.53   0.561    1.109    157    117   24.7%
3%     ungated       85,181  +19.03   -25.51   0.746    1.229    183    369   13.8%
4%     R>=44         74,570  +16.41   -27.59   0.595    1.100    125    149   20.9%
4%     ungated       65,174  +13.82   -27.73   0.499    0.927    143    409   12.4%
5%     R>=44         61,328  +12.67   -30.26   0.419    0.867    101    173   19.5%
5%     ungated       70,490  +15.32   -34.97   0.438    0.953    114    438   10.9%
```

## s12  (bk50d_s12_v2.0 / 366d)

`%abv_SMA50 > 12%` — every other filter is in the Configuration table above.

**Ranking gate:** `QullamaggieRanking >= 44` drops 753 signals (0 with no fillable next-day open); ungated drops 0 (0 with no fillable open). Each sizing is listed gated then ungated, so the pair reads across — a gated run alone cannot show whether the signals it removed would have compounded better.

```text
size   gate          Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
-----------------------------------------------------------------------------------
3%     R>=44         62,562  +13.05   -29.00   0.450    0.908    164    140   22.8%
3%     ungated       63,626  +13.37   -34.19   0.391    0.878    196    861    6.4%
4%     R>=44         68,563  +14.79   -29.79   0.497    0.978    126    178   19.6%
4%     ungated       74,259  +16.33   -34.94   0.467    1.006    148    909    5.1%
5%     R>=44         56,250  +11.06   -33.72   0.328    0.763    101    203   18.7%
5%     ungated       80,495  +17.91   -33.80   0.530    1.067    119    938    4.6%
```

## Top 5 by Final$

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      85,181  +19.03   -25.51   0.746    1.229    183    369   13.8%
 2  s12 ungated           5%      80,495  +17.91   -33.80   0.530    1.067    119    938    4.6%
 3  s20 ungated           3%      77,078  +17.06   -27.45   0.621    1.220    152     98   27.0%
 4  s16 R>=44             4%      74,570  +16.41   -27.59   0.595    1.100    125    149   20.9%
 5  s12 ungated           4%      74,259  +16.33   -34.94   0.467    1.006    148    909    5.1%
```

## Top 5 by Sortino

```text
 #  algo                size      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
------------------------------------------------------------------------------------------------
 1  s16 ungated           3%      85,181  +19.03   -25.51   0.746    1.229    183    369   13.8%
 2  s20 ungated           3%      77,078  +17.06   -27.45   0.621    1.220    152     98   27.0%
 3  s20 R>=44             3%      72,310  +15.82   -27.00   0.586    1.139    146     69   29.6%
 4  s20 R>=44             4%      73,445  +16.12   -30.00   0.537    1.131    120     95   24.2%
 5  s20 ungated           4%      72,597  +15.89   -24.26   0.655    1.126    122    128   23.3%
```

## Yearly results

Portfolio value at each year end against the previous year end — `Final$` is the equity on the last trading day of that year, `CAGR%` its year-over-year return. `MaxDD%`, `Calmar`, `Sortino` and `Uninv%` are re-derived on that calendar year's daily slice, and `taken`/`skip` count only that year's signals; none is a slice of the whole-period figure.

```text
algo                year      Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------------------------
s12 R>=44 3%        2010      34,915  +16.38   -14.76   1.110    1.484     33     25   45.3%
                    2011      32,569   -6.72   -28.28  -0.238   -0.283     33     24   28.5%
                    2012      37,618  +15.50   -19.34   0.801    1.040     10     70   16.4%
                    2013      58,485  +55.47    -9.22   6.013    3.774     24      0   28.1%
                    2014      69,651  +19.09   -15.89   1.202    1.208     33      7   10.7%
                    2015      62,562  -10.18   -29.00  -0.351   -0.264     31     14    7.7%
s12 R>=44 4%        2010      34,270  +14.23   -19.40   0.734    1.117     25     33   34.4%
                    2011      31,376   -8.44   -28.86  -0.293   -0.438     24     33   37.3%
                    2012      36,688  +16.93   -20.89   0.811    1.067     11     69   15.3%
                    2013      62,064  +69.16   -10.20   6.781    3.941     18      6   18.2%
                    2014      76,353  +23.02   -16.61   1.386    1.332     24     16    6.4%
                    2015      68,563  -10.20   -29.79  -0.342   -0.228     24     21    5.7%
s12 R>=44 5%        2010      31,988   +6.63   -23.56   0.281    0.559     20     38   25.2%
                    2011      27,149  -15.13   -28.60  -0.529   -1.006     19     38   47.8%
                    2012      31,335  +15.42   -19.78   0.779    0.935     11     69   15.5%
                    2013      55,355  +76.66   -10.88   7.048    3.982     14     10   13.5%
                    2014      61,103  +10.38   -20.06   0.518    0.681     19     21    4.9%
                    2015      56,250   -7.94   -33.72  -0.236   -0.077     18     27    5.3%
s16 ungated 3%      2010      37,304  +24.35   -20.89   1.166    1.350     32     97   12.3%
                    2011      32,604  -12.60   -25.51  -0.494   -0.739     35     62   35.7%
                    2012      40,456  +24.09   -14.65   1.644    1.624     28    103   13.8%
                    2013      71,655  +77.12    -7.24  10.648    4.277     23     20    7.4%
                    2014      86,108  +20.17   -16.96   1.190    1.295     31     28    8.5%
                    2015      85,181   -1.08   -23.45  -0.046    0.109     34     59    5.1%
s12 ungated 5%      2010      39,418  +31.39   -21.45   1.464    1.628     19    225    4.4%
                    2011      34,137  -13.40   -33.80  -0.396   -0.421     20    179    5.9%
                    2012      44,946  +31.66   -21.55   1.469    1.702     20    218    2.1%
                    2013      81,492  +81.31    -7.02  11.588    4.352     20     65    4.8%
                    2014      88,223   +8.26   -18.72   0.441    0.736     20     91    6.4%
                    2015      80,495   -8.76   -26.94  -0.325   -0.284     20    160    3.7%
```

## Monthly returns/transactions — s12 R>=44 at each sizing, plus the top 2 by Final$

### s12 R>=44 — size 3%  (Final $62,562)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.0|7    +3.4|3    +1.6|0    +0.5|4    -3.2|0    -4.6|0    +3.6|1    -8.2|6   +10.2|7    +5.7|5    +0.8|0   +10.3|0 |   +16.4    33
 2011 |    +1.9|0    +6.9|1    +3.8|1    +2.6|0    +0.3|0    -0.7|1    -2.3|1    -9.6|0    -6.5|0   +2.1|29    -2.9|0    -1.4|0 |    -6.7    33
 2012 |   +10.9|0    +2.7|0    +1.6|0    -3.7|0   -11.0|0    +5.8|3    -0.1|1    +4.1|0    +3.5|0    -0.8|0    +2.0|2    +1.0|4 |   +15.5    10
 2013 |    +2.2|1    +0.6|3    +2.5|3    +3.6|2   +11.5|6    +6.0|2    +4.2|1    +3.4|2    +5.8|1    -3.2|1    +7.6|1    +1.4|1 |   +55.5    24
 2014 |    +3.2|5    +3.2|6    -3.3|5    +1.6|1    -0.3|1    +8.3|3    -0.6|2    +6.1|2    -2.2|2    -5.1|1    +0.0|3    +7.5|2 |   +19.1    33
 2015 |    +0.3|2   +11.0|6    +0.1|3    -2.5|4    +5.9|1    -0.2|0    +1.0|5   -13.3|0   -12.3|0    +6.1|1    +4.3|5    -8.1|4 |   -10.2    31
```

### s12 R>=44 — size 4%  (Final $68,563)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.0|7    +4.6|3    +2.1|0    +0.6|4    -4.2|0    -6.2|0    +4.9|1   -11.0|6   +13.5|4    +4.7|0    +0.2|0   +10.9|0 |   +14.2    25
 2011 |    +2.3|0    +7.9|1    +2.3|1    +2.6|0    -0.9|0    -1.7|1    -2.9|1    -8.1|0    -3.4|0   -1.0|20    -3.9|0    -1.0|0 |    -8.4    24
 2012 |   +11.7|0    +1.4|0    +1.2|1    -2.5|0   -12.7|0    +6.6|3    -0.4|1    +4.1|0    +4.7|0    -1.0|0    +2.9|2    +1.7|4 |   +16.9    11
 2013 |    +3.4|1    +0.8|3    +3.3|3    +4.7|2   +14.8|4    +6.8|0    +4.2|1    +2.4|2    +7.0|1    -3.0|0    +8.4|0    +1.8|1 |   +69.2    18
 2014 |    +5.5|5    +4.0|6    -5.7|3    +0.1|1    +0.9|1    +8.2|3    -2.3|2   +10.8|1    -4.4|0    -2.5|1    -0.7|1    +8.5|0 |   +23.0    24
 2015 |    -0.9|3   +10.7|6    +0.2|2    -1.9|3    +6.6|0    +0.4|1    +0.4|5   -13.3|0   -13.5|0    +3.1|1    +8.2|3    -7.4|0 |   -10.2    24
```

### s12 R>=44 — size 5%  (Final $56,250)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -5.0|7    +5.8|3    +2.6|0    +0.8|4    -5.2|0    -7.8|0    +6.2|1   -13.6|5   +14.6|0    +2.9|0    -2.7|0   +11.6|0 |    +6.6    20
 2011 |    +2.3|0    +3.8|1    +1.5|1    +1.1|0    -1.8|0    -1.8|1    -0.6|1    -7.0|0    -4.0|0   -0.3|15    -6.2|0    -2.6|0 |   -15.1    19
 2012 |   +11.7|0    +1.4|0    +1.6|1    -2.1|0   -12.0|0    +5.5|3    -0.3|1    +2.4|0    +4.1|0    -2.1|0    +3.7|2    +2.2|4 |   +15.4    11
 2013 |    +4.3|1    +1.0|3    +4.2|3    +5.8|2   +17.2|0    +8.0|0    +3.8|1    +2.1|2    +7.1|0    -3.3|0    +7.8|1    +1.6|1 |   +76.7    14
 2014 |    +5.9|4    +1.5|6    -4.7|3    +0.9|1    -2.0|1    +7.9|1    -0.3|0   +10.6|1    -7.3|1    -5.0|0    -4.5|0    +8.8|1 |   +10.4    19
 2015 |    -1.5|4    +7.9|5    +6.8|2    -4.3|3    +9.1|1    +4.9|1    +1.1|0   -15.7|0   -16.1|0    +4.1|1    +8.3|1    -8.3|0 |    -7.9    18
```

### s16 ungated — size 3%  (Final $85,181)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -5.7|16    +6.8|5    +5.9|2    +2.8|9    -5.7|0    -9.3|0   +10.0|0    -9.3|0   +13.9|0    +4.1|0    +3.0|0    +8.8|0 |   +24.3    32
 2011 |    +1.3|7    +0.9|1    +0.2|3    -0.0|4    -1.6|3    -3.6|1    -1.2|1    -4.6|0    -7.7|0   +7.0|14    -4.3|1    +1.0|0 |   -12.6    35
 2012 |   +10.0|6    +2.7|1    +0.9|0    -2.6|0    -8.0|0    +5.4|1   +0.8|11    +1.6|0    +5.3|0    -1.1|0    +4.2|3    +3.7|6 |   +24.1    28
 2013 |    +4.7|7    +1.1|4    +6.9|0    +4.1|0   +15.2|0    +3.0|1    +5.9|3    +3.6|3    +7.4|2    -1.6|2    +6.8|0    +2.2|1 |   +77.1    23
 2014 |    +4.4|6    +5.5|4    -3.1|7    +0.6|3    -0.4|0    +9.9|1    -1.8|3    +5.0|2    -4.2|1    -3.0|1    +1.5|3    +5.2|0 |   +20.2    31
 2015 |    +2.5|6    +5.5|5    -0.0|5    -1.6|6    +7.3|0    +1.0|0    +0.0|2    -9.8|1    -8.6|0    +6.4|3    +3.9|6    -5.9|0 |    -1.1    34
```

### s12 ungated — size 5%  (Final $80,495)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -9.0|19   +11.4|0    +8.9|0    -0.4|0    -6.2|0    -9.5|0   +11.2|0    -5.7|0   +12.1|0    +5.0|0    +5.1|0    +8.5|0 |   +31.4    19
 2011 |   +1.3|12    +0.2|7    +0.5|1    -1.8|0    -1.1|0    -1.1|0    -2.2|0   -11.3|0   -14.5|0   +18.2|0    -1.9|0    +3.0|0 |   -13.4    20
 2012 |   +9.3|12    +8.1|6    -0.3|1    -3.5|0   -10.6|0    +7.4|1    +2.8|0    +3.4|0    +4.3|0    -3.5|0    +4.4|0    +7.9|0 |   +31.7    20
 2013 |   +6.5|11    +1.6|7    +7.0|1    +2.2|0   +11.3|0    +7.2|1    +5.9|0    +0.4|0   +11.8|0    -2.0|0    +7.1|0    +2.9|0 |   +81.3    20
 2014 |    +2.6|3    +0.8|9    -4.9|7    +1.8|0    +1.1|0   +12.5|0    -3.7|0    +5.5|0    -8.6|0    -4.3|1    +2.5|0    +4.2|0 |    +8.3    20
 2015 |    -0.9|2    +4.3|8    +3.0|7    -1.9|1    +6.7|0    -2.0|0    -1.3|0   -11.0|1   -10.0|0   +10.3|0    +2.7|0    -6.7|1 |    -8.8    20
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 120  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-46       12   +1.06    -7.45   0.143    0.467
D2        46-47       12   +1.02    -6.95   0.146    0.469
D3        47-50       12   +3.98    -4.96   0.802    1.580
D4        50-54       12   +4.84    -5.82   0.833    1.826
D5        54-55       12   +3.08    -6.50   0.474    1.024
D6        55-58       12   +1.58    -5.83   0.271    0.680
D7        58-61       12   +1.37    -6.38   0.214    0.668
D8        61-65       12   -0.87    -8.73  -0.100   -0.307
D9        65-79       12   +0.33    -6.43   0.052    0.170
D10       79-100      12   +1.49    -8.08   0.184    0.494
```

### s16  (bk50d_s16_v2.0)

Trades scored: 125  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-45       12   +1.62    -5.51   0.294    0.695
D2        46-47       13   +1.97    -6.73   0.292    0.690
D3        47-50       12   +4.53    -5.66   0.800    1.538
D4        50-51       13   +6.02    -5.56   1.084    2.088
D5        51-54       12   -0.17    -8.09  -0.021   -0.029
D6        54-57       13   +2.56    -6.62   0.386    0.860
D7        57-61       12   +0.43    -6.71   0.064    0.215
D8        61-65       13   +0.66    -6.69   0.099    0.309
D9        65-75       12   -0.79    -7.86  -0.101   -0.285
D10       75-100      13   +1.31    -8.16   0.160    0.407
```

### s12  (bk50d_s12_v2.0)

Trades scored: 126  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        44-44       12   +1.63    -7.61   0.215    0.615
D2        44-47       13   +1.02    -6.16   0.165    0.422
D3        47-47       12   +1.44    -6.93   0.208    0.544
D4        47-50       13   +4.44    -7.24   0.613    1.569
D5        50-53       13   +3.13    -6.02   0.521    1.180
D6        53-55       12   +1.10    -8.74   0.125    0.367
D7        55-58       13   +2.20    -5.21   0.422    0.821
D8        61-65       12   +0.65    -6.88   0.095    0.319
D9        65-75       13   +0.18    -6.57   0.028    0.092
D10       75-100      13   +1.24    -7.64   0.162    0.393
```

## Findings (2026-07-30 run, 2010-01-01 – 2015-12-31 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.

**What changed in this run.** Each config is now reported twice — through the `MIN_RANKING >= 40`
gate and with no ranking condition. This is also the first portfolio run on the 40/35/25
`QullamaggieRanking` weights (changed 2026-07-29), so the gated figures moved against the previously
committed tables. The bar load is now bounded at the eval-window end, which for this window excludes
585 symbols that previously satisfied the 300-bar `MIN_HISTORY` check on bars printed *after* 2015;
that bound changes nothing measurable, verified by a control run reproducing the report
byte-for-byte. The limit-order entry comparison was removed from the script.

1. **The ranking gate loses in all nine cells here** — mean −4.86pp CAGR, worst −8.72pp
   (s16 @4%: +7.55% gated against +16.27% ungated). This is the exact opposite of 2021-2026, where
   the same gate wins all nine by +12.09pp on average. Whatever the score is picking up, it is not
   present in this tape.
2. **The reason is signal scarcity, not signal quality.** Gated runs leave 32-64% of capital
   uninvested with near-zero skip counts (0-35 across the nine cells) — the portfolio is idle because
   nothing qualifies, not because cash ran out. Removing the gate roughly doubles the trade count
   (s12: 107 → 182 at 3%) and puts that idle cash to work. In a window this thin, any additional
   filter costs more in foregone compounding than it saves in trade quality.
3. **Even ungated, this is the weakest of the three windows.** The best cell is ungated `s16 @4%` at
   +16.27% CAGR, marginally above QQQ buy & hold (+15.81%); every gated cell trails both QQQ and,
   at 3% sizing, SPY (+10.30%) as well. Sortino never exceeds 0.797.
4. **Ungated, looser thresholds do win** — at 3% sizing s12 +12.53% > s16 +11.80% > s20 +8.48%. That
   ordering inverts under the gate (s20 +6.45% > s16 +7.48%... s12 +5.28% worst), another sign the
   gate is mis-selecting in this period rather than merely being redundant.
5. **The gate's milder drawdowns are a cash artifact.** Gated s20 shows −14.97% against ungated
   −24.26%, but that is a portfolio half in cash, not better exits.
6. **The ranking deciles are unreadable at this sample size**: 7-10 trades each, four of s12's ten
   deciles negative, and D10 (+1.78%) barely above D2 (+1.51%).

**How to read this window:** it is the control that stops 2021-2026 being mistaken for the general
case — and it now also contradicts the gate. The strategy's edge and the ranking's edge are both
regime-dependent; in a flat tape with the regime filter on, the strategy mostly does not trade, and
filtering the little it does find makes matters worse.
