# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-07-29
Period: 2010-01-01 – 2015-12-31  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         53,967  +10.30   -19.42   0.530    0.658
QQQ         72,292  +15.81   -16.09   0.983    0.888
```

## s20  (bk50d_s20_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (0 signals dropped below it, 0 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          48,868   +8.48   -24.26   0.350    0.584    102      5   49.1%
4%          52,327   +9.73   -26.95   0.361    0.563     92     15   39.4%
5%          64,802  +13.72   -27.06   0.507    0.691     81     26   33.0%
```

## s16  (bk50d_s16_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (92 signals dropped below it, 0 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          47,523   +7.98   -24.97   0.320    0.502    122     21   41.6%
4%          58,542  +11.80   -25.53   0.462    0.620    104     39   31.9%
5%          75,777  +16.72   -24.72   0.677    0.778     91     52   26.1%
```

## s12  (bk50d_s12_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (247 signals dropped below it, 0 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          47,821   +8.09   -29.38   0.275    0.470    145     60   31.6%
4%          53,490  +10.13   -29.41   0.345    0.536    122     83   24.3%
5%          55,316  +10.75   -29.02   0.370    0.552    104    101   21.2%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s16 — size 5%  (Final $75,777)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.1|6    +6.9|1    +5.3|0    -2.1|3    -4.4|0    -5.8|0    +7.0|0    -6.0|3   +10.0|1    +1.3|1    -2.1|3   +11.6|1 |   +16.7    19
 2011 |    +5.4|2    +1.0|0    +2.6|0    +3.1|0    -2.0|0    +1.0|0    -2.9|0    -9.0|0    -7.3|0    +4.5|7    -2.0|3    +1.2|3 |    -5.4    15
 2012 |    +9.1|4    +4.3|3    +1.3|0    -1.8|0    -9.2|0    +3.2|0    +1.4|0    +8.2|0    +2.2|0    +3.5|0    +2.4|2    +4.0|1 |   +31.2    10
 2013 |    +3.0|2    +0.5|1    +3.6|0    +3.4|1    +3.2|3    +2.3|0    +2.2|2    +3.7|2    +8.6|1    -0.9|0    +6.4|2    +1.2|0 |   +43.5    14
 2014 |    +8.8|3    +8.3|2    -6.8|1    +1.0|2    -5.3|1   +11.0|2    -4.5|0    +8.0|1    -7.7|0    -0.1|0    +3.0|2    +4.5|2 |   +19.2    16
 2015 |    +5.1|6    +6.6|1    -0.3|0    -2.6|3    +8.5|0    +3.8|2    +2.9|1   -10.4|0   -12.1|0    +1.5|1    +6.4|0    -4.9|3 |    +2.0    17
```

### #2  s20 — size 5%  (Final $64,802)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.2|5    +6.5|1    +4.5|0    -1.8|3    -3.0|0    -5.6|0    +4.0|0    -4.2|3    +7.7|2    +2.0|1    -1.0|2    +9.4|2 |   +14.8    19
 2011 |    +4.2|0    +1.9|0    +2.9|0    +5.1|0    -1.5|0    +1.0|0    -0.6|0    -7.2|0    -8.1|0    +4.1|6    -2.4|2    -0.4|2 |    -2.0    10
 2012 |    +6.9|2    +3.3|7    +1.3|0    +0.6|0   -11.6|0    +3.3|0    -0.9|0    +8.1|0    +3.6|0    +0.8|0    -0.3|1    +4.3|1 |   +19.8    11
 2013 |    +1.1|2    +0.3|1    +2.3|0    +5.5|2    +4.9|2    +2.4|0    +2.1|1    -0.5|1    +9.9|1    -1.9|0    +7.5|2    +1.2|0 |   +40.1    12
 2014 |    +5.6|3    +6.8|1    -4.1|1    -0.3|2    -3.8|1    +7.0|1    -2.5|0    +6.5|1    -5.8|0    +0.0|0    +2.9|0    +4.4|3 |   +16.7    13
 2015 |    +3.8|4    +4.8|5    -0.4|0    -2.2|3    +8.4|0    +2.7|1    +1.3|1   -11.2|0   -13.6|0    +1.7|0   +11.6|2    -5.6|0 |    -2.0    16
```

### #3  s16 — size 4%  (Final $58,542)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.3|6    +5.5|1    +4.3|0    -1.7|3    -3.6|0    -4.6|0    +5.5|0    -4.8|3    +7.9|1    +1.0|1    -1.7|3    +9.7|5 |   +13.7    23
 2011 |    +3.0|2    +1.6|0    +2.5|0    +3.2|0    -1.1|0    -0.7|0    -2.0|0    -8.4|0   -10.0|0    +5.6|7    -2.6|3    +0.1|3 |    -9.5    15
 2012 |    +7.4|4    +3.1|7    +1.3|0    -1.2|0   -10.1|0    +2.2|0    +0.4|0    +9.0|0    +1.3|0    +2.0|0    +1.8|2    +4.4|1 |   +22.4    14
 2013 |    +2.4|2    +0.8|1    +2.9|0    +2.7|1    +2.5|3    +1.9|0    +1.8|2    +3.0|2    +7.0|1    -0.7|0    +5.2|2    +0.9|0 |   +34.9    14
 2014 |    +7.3|3    +6.9|2    -5.6|1    +0.7|2    -4.3|1    +9.0|2    -3.7|0    +6.4|1    -6.3|0    -0.1|0    +2.4|2    +3.6|2 |   +15.7    16
 2015 |    +4.1|6    +4.7|6    +1.2|0    -1.4|3    +8.6|0    +2.0|2    +0.1|1   -10.5|0   -11.2|0    +2.0|1    +7.7|0    -5.7|3 |    -0.7    22
```

### #4  s12 — size 5%  (Final $55,316)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.9|9    +7.6|1    +6.2|0    -0.7|3    -6.6|0    -7.3|0    +8.9|0    -8.3|4   +11.9|1    +3.0|1    -1.3|0   +14.0|0 |   +21.1    19
 2011 |    +4.0|2    +2.1|2    +0.7|0    +0.0|2    -2.6|1    -4.4|0    -3.7|0    -9.3|0    -5.2|0   +3.5|13    -1.2|0    +2.3|0 |   -13.8    20
 2012 |    +9.6|0    +3.2|4    -1.1|0    -2.3|0    -6.3|0    -0.7|1    +0.6|2    -0.4|0    +1.7|0    -1.0|0    +2.3|2    +2.7|3 |    +7.6    12
 2013 |    +2.0|3    -0.2|1    +4.3|2    +3.3|1    +6.7|3    +2.6|0    +3.6|2    +3.5|1    +9.4|0    -0.1|0    +6.4|1    -0.4|0 |   +48.9    14
 2014 |    +4.5|2    +5.0|2    -7.1|2    +3.7|2    -7.1|2    +9.6|4    -3.7|0    +8.0|1    -6.5|0    -1.2|0    +3.9|2    +3.7|2 |   +11.4    19
 2015 |    +4.3|2    +7.2|1    +0.5|1    -4.5|3   +10.7|0    -1.4|3    -1.8|1    -8.3|0   -10.2|0    +0.6|1    +8.8|5    -4.7|3 |    -1.0    20
```

### #5  s12 — size 4%  (Final $53,490)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.0|9    +6.0|1    +5.0|0    -0.5|3    -5.3|0    -5.8|0    +7.0|0    -6.6|4    +9.4|1    +2.8|3    -1.7|2   +12.7|1 |   +18.0    24
 2011 |    +4.5|2    +1.6|2    +1.1|0    +2.2|2    -2.2|1    -3.0|0    -2.7|0   -10.3|0    -9.3|0   +7.2|15    -3.3|2    +2.8|1 |   -12.1    25
 2012 |   +10.5|0    +3.7|4    -0.9|0    -2.4|0    -8.2|0    +0.6|1    -0.3|2    +0.8|0    +2.3|0    +0.9|0    +1.5|2    +2.2|3 |   +10.2    12
 2013 |    +1.6|3    -0.2|1    +3.4|2    +2.6|1    +5.4|3    +2.1|0    +2.9|2    +2.6|2    +8.4|1    -1.8|0    +6.1|2    +1.2|0 |   +39.9    17
 2014 |    +6.0|2    +6.0|2    -6.9|2    +1.2|2    -5.2|2   +10.3|4    -3.2|0    +8.0|1    -6.7|0    -0.0|0    +3.0|2    +3.1|3 |   +14.4    20
 2015 |    +4.8|6    +7.3|1    +0.1|1    -2.9|3    +7.0|0    -0.8|3    -1.2|1    -8.2|0   -10.2|0    +1.4|1    +6.0|4    -4.0|4 |    -2.5    24
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v1.3_roc100)

Trades scored: 92  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        46-52        9   +1.45    -5.46   0.266    0.448
D2        52-55        9   +1.70    -4.97   0.343    0.519
D3        55-57        9   -0.39    -8.47  -0.046   -0.123
D4        57-58        9   +0.20    -4.22   0.047    0.074
D5        59-61       10   +2.06    -6.97   0.296    0.449
D6        61-63        9   +0.51    -7.43   0.069    0.134
D7        63-66        9   -0.79    -6.61  -0.120   -0.169
D8        67-68        9   +3.14    -3.46   0.906    0.831
D9        69-73        9   -0.57    -5.43  -0.106   -0.186
D10       73-95       10   +2.80    -7.47   0.375    0.569
```

### s16  (bk50d_s16_v1.3_roc100)

Trades scored: 104  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-42       10   +1.71    -4.60   0.372    0.604
D2        42-46       10   +0.57    -5.27   0.109    0.150
D3        46-51       11   +0.98    -6.24   0.157    0.302
D4        51-54       10   +1.00    -6.89   0.145    0.293
D5        54-58       11   +0.57    -4.11   0.138    0.154
D6        58-61       10   +1.95    -6.27   0.311    0.482
D7        61-64       10   +0.10    -9.01   0.011    0.040
D8        64-68       11   +3.12    -5.96   0.524    0.624
D9        68-72       10   -0.39    -6.17  -0.063   -0.094
D10       73-95       11   +2.61    -7.47   0.349    0.535
```

### s12  (bk50d_s12_v1.3_roc100)

Trades scored: 122  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-42       12   +2.15    -4.26   0.504    0.633
D2        42-43       12   -0.45    -6.71  -0.068   -0.124
D3        43-45       12   +2.83    -4.10   0.691    0.914
D4        45-48       12   +0.09    -6.34   0.014    0.040
D5        48-52       13   -0.10    -9.07  -0.011   -0.008
D6        52-56       12   +0.75    -7.84   0.096    0.225
D7        57-60       12   +1.56    -6.25   0.249    0.482
D8        61-64       12   -0.17   -10.38  -0.017   -0.020
D9        64-70       12   +1.57    -9.12   0.172    0.295
D10       71-95       13   +2.78    -6.34   0.438    0.590
```

## Findings (2026-07-29 run, 2010-01-01 – 2015-12-31 — tables above regenerate on re-run)

1. **The strategy loses to buy & hold in this window.** At 3% sizing all three configs return
   roughly +8% (s20 +8.48, s12 +8.09, s16 +7.98) against SPY's +10.30% and QQQ's +15.81%. Not one
   of the nine cells clears QQQ's Calmar of 0.983 — the best is s16 @5% at 0.677. Only s16 @5%
   (+16.72%) beats QQQ on absolute CAGR, and it pays −24.72% MaxDD to QQQ's −16.09%. Any
   conclusion drawn from the 2016-2020 or 2021-2026 windows should be checked here first.
2. **Signal supply, not capital, is the binding constraint — the reverse of the later periods.**
   s20 @3% leaves 49.1% of the portfolio in cash and skips just 5 signals in six years; s12 @3%
   skips 60. In 2021-2026 the same configs skip 353 and 602. There is simply not enough that
   passes the filters, because far fewer $1.5B+ liquid names existed in the early 2010s.
3. **So raising position size is close to free return here.** From 3% to 5%, s20 goes +8.48 →
   +13.72 and s16 +7.98 → +16.72, while MaxDD barely moves (−24.26 → −27.06 and −24.97 → −24.72).
   Calmar roughly doubles for both. 5% is best in every config — the opposite of 2021-2026, where
   3% wins for s20 and s12. **Position size should track candidate supply rather than be fixed.**
   Note 5% is the top of the swept range, so the true optimum here is likely larger still and
   outside what this sweep can see.
4. **The ranking neither gates nor orders usefully in this period.** `MIN_RANKING = 40` removes 0
   s20 signals, 92 s16 and 247 s12, yet the decile tables show no predictive power: for s16 and
   s12 the *lowest* decile out-Sortinos the highest (D1 0.604 vs D10 0.535, and D1 0.633 vs D10
   0.590). Rank-preference funding cannot add anything when the score does not separate outcomes,
   which is consistent with the near-zero effect measured for it on 2021-2026.
5. **No config conclusion should be drawn from this window.** At 3% the three thresholds sit
   within 0.5pp of each other (+7.98 to +8.48) and their ordering reverses at 5% (s16 +16.72 >
   s20 +13.72 > s12 +10.75). The `s12 > s16 > s20` ordering that holds in both later periods is
   simply absent here.

**How to improve performance in a regime like this:** the lever is candidate supply, not exit or
ranking logic. Either size up (5%+ when skip counts are in single digits) or loosen the entry
filters / widen the universe — see the relaxation sweep prompt. Tuning the ranking or the exit is
wasted effort in a window where half the portfolio never gets deployed.
