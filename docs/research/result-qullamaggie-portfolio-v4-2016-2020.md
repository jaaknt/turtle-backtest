# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-07-29
Period: 2016-01-01 – 2020-12-31  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         55,797  +13.23   -34.10   0.388    0.681
QQQ         85,956  +23.46   -28.56   0.821    0.965
```

## s20  (bk50d_s20_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (0 signals dropped below it, 1 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         102,352  +27.85   -20.23   1.377    1.101    135    448   25.8%
4%         105,207  +28.56   -22.51   1.269    1.085    103    480   24.1%
5%          99,263  +27.07   -31.47   0.860    1.038     83    500   24.7%
```

## s16  (bk50d_s16_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (204 signals dropped below it, 3 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         106,753  +28.94   -22.28   1.299    1.146    138    523   23.6%
4%         106,657  +28.91   -26.91   1.074    1.128    106    555   22.4%
5%         123,287  +32.71   -31.21   1.048    1.209     88    573   20.2%
```

## s12  (bk50d_s12_v1.3_roc100 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal, QullamaggieRanking>=40 (419 signals dropped below it, 3 with no fillable next-day open in period)

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         111,992  +30.18   -20.85   1.448    1.258    141    672   23.3%
4%         116,649  +31.24   -21.63   1.444    1.235    110    703   21.3%
5%         104,004  +28.26   -32.90   0.859    1.093     88    725   20.6%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s16 — size 5%  (Final $123,287)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|19    +2.3|1    +1.0|0    -1.5|0    +8.3|0    +6.0|0    +3.5|0    -4.5|0   +14.6|0    +0.0|0 |   +32.5    20
 2017 |    +6.0|0    +3.2|0    +1.4|1    -0.0|0    -0.1|3    +4.2|3    +3.0|5    -1.7|2    +4.1|3    +3.7|2    +7.6|0    +2.7|0 |   +39.5    19
 2018 |    +3.5|0    -6.9|0    +2.8|0    +2.7|1   +11.1|3    +0.9|2    -0.9|2    +3.9|1    -4.1|0    -6.1|0    -1.6|0    -5.9|1 |    -1.9    10
 2019 |   +12.2|0    +5.5|9    -2.5|0    +1.6|1   -15.4|0    +9.9|2    -2.6|5   -13.7|1    +4.1|1    +2.4|1    +4.1|0    +6.1|0 |    +7.9    20
 2020 |    -5.5|0    +6.5|2   -13.8|0   +11.0|0    +6.3|9   +10.5|2   +13.3|4   +13.4|0    -0.1|1    -7.6|1   +33.2|0   +17.4|0 |  +109.9    19
```

### #2  s12 — size 4%  (Final $116,649)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   -0.2|25    -0.3|0    -1.1|0    -2.4|0    +7.7|0    +6.4|0    +3.1|0    -3.3|0   +12.0|0    +0.5|0 |   +23.5    25
 2017 |    +5.7|0    +2.9|0    +0.2|1    +0.2|0    -0.1|3    +3.4|3    +1.7|6    +0.1|5    +2.5|5    +2.8|0    +5.9|0    +2.1|0 |   +30.8    23
 2018 |    +3.1|0    -6.0|0    +4.4|0    +2.9|2   +13.2|3    +0.4|2    +1.9|2    +3.1|3    -0.4|0    -8.1|0    -3.2|0    -7.4|1 |    +2.1    13
 2019 |   +10.8|0   +5.1|13    -3.8|0    +5.0|1   -13.0|0   +10.2|2    -0.7|4    -8.6|1    +1.2|2    +0.7|2    +3.8|0    +4.5|0 |   +13.1    25
 2020 |    -3.5|0    +4.5|2    -8.2|0    +8.3|0   +5.9|13   +10.1|2    +7.6|2   +10.7|1    -4.8|1    -3.4|3   +37.6|0   +18.3|0 |  +108.4    24
```

### #3  s12 — size 3%  (Final $111,992)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.3|33    +1.0|0    -0.7|0    -2.9|0    +8.0|0    +4.1|0    +2.4|0    -3.7|0    +9.6|0    -0.1|0 |   +18.7    33
 2017 |    +5.3|0    +4.4|0    +1.0|1    +0.1|0    -0.0|3    +2.5|3    +1.3|6    +0.0|5    +1.9|5    +2.3|3    +4.9|2    +2.1|3 |   +28.9    31
 2018 |    +3.0|0    -5.0|0    +5.7|0    +4.2|2   +11.5|3    +0.2|1    +2.8|2    +3.6|3    -1.9|0    -7.9|0    -2.7|0    -6.8|1 |    +5.1    12
 2019 |    +7.2|0   +3.4|22    -2.6|0    +3.8|1   -13.0|0   +11.7|2    +0.2|4    -5.0|1    +3.9|2    +3.5|1    +2.7|0    +4.4|0 |   +19.5    33
 2020 |    -4.1|0    +5.0|2    -5.3|0    +5.6|0   +2.1|22    +9.5|2    +5.3|3   +10.1|1    -7.1|1    +0.8|1   +35.2|0   +17.3|0 |   +94.1    32
```

### #4  s16 — size 3%  (Final $106,753)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|25    +5.8|8    -1.9|0    +1.8|0   +10.5|0    -0.1|0    +2.9|0    -4.0|0    +7.1|0    -1.1|0 |   +22.0    33
 2017 |    +7.7|0    +1.8|0    +1.5|1    +0.4|0    -0.0|3    +2.5|3    +1.8|5    -1.0|2    +2.5|3    +2.2|3    +5.1|2    +1.9|4 |   +29.4    26
 2018 |    +2.9|4    -5.0|0    +4.8|0    +6.0|2    +9.9|3    -1.4|2    +0.8|2    +5.4|1    -2.3|0    -9.0|0    +3.0|0    -8.6|1 |    +4.7    15
 2019 |    +8.8|0   +2.4|20    -2.9|2    +4.1|1   -12.4|0   +13.7|2    +0.3|4    -9.9|1    +2.6|1    +3.0|1    +2.9|0    +7.8|0 |   +18.9    32
 2020 |    -4.5|0    +4.4|2    -7.9|0    +4.6|0   +0.7|24    +8.9|2    +6.4|2    +9.8|1    -4.8|0    +0.8|1   +33.6|0   +14.8|0 |   +81.1    32
```

### #5  s16 — size 4%  (Final $106,657)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2016 |    +0.0|0    +0.0|0   +0.1|25    +2.1|0    +0.2|0    -3.6|0    +8.4|0    +5.0|0    +3.3|0    -3.0|0   +11.5|0    -0.9|0 |   +24.3    25
 2017 |    +5.7|0    +4.6|0    +0.5|1    +0.0|0    -0.1|3    +3.4|3    +2.4|5    -1.4|2    +3.3|3    +2.8|3    +6.7|2    +2.7|1 |   +35.0    23
 2018 |    +2.9|0    -5.9|0    +4.5|0    +3.2|2   +10.4|3    -0.0|1    +0.7|2    +5.5|1    -5.0|0    -7.6|0    -2.2|0    -5.9|1 |    -1.3    10
 2019 |    +8.9|0   +4.2|15    -2.4|0    +2.4|1   -16.4|0   +12.3|2    -0.4|3    -9.6|1    +6.1|1    +3.0|1    +1.7|0    +6.6|1 |   +13.8    25
 2020 |    -4.8|0    +4.8|2   -10.9|0    +6.9|0   +2.7|15    +9.9|2    +8.6|2   +11.8|1    -5.0|0    -0.6|1   +32.3|0   +16.1|0 |   +88.6    23
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v1.3_roc100)

Trades scored: 103  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        48-52       10   +0.94    -5.17   0.182    0.268
D2        52-55       10   +3.45    -5.26   0.655    0.696
D3        55-57       10   +0.39    -8.16   0.048    0.112
D4        57-63       11   +3.05    -4.27   0.714    0.717
D5        63-67       10   +1.54    -8.06   0.192    0.330
D6        67-68       10   +2.34    -6.30   0.371    0.481
D7        68-73       11   +0.75   -10.73   0.070    0.157
D8        73-83       10   +9.00    -5.36   1.681    1.591
D9        83-88       10   +4.47    -8.85   0.505    0.558
D10       88-99       11   +4.12   -15.67   0.263    0.182
```

### s16  (bk50d_s16_v1.3_roc100)

Trades scored: 106  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       10   +1.48    -7.07   0.209    0.365
D2        43-48       11   +4.88    -5.57   0.875    1.089
D3        48-50       10   +0.96    -6.70   0.143    0.231
D4        50-54       11   +1.64    -7.72   0.213    0.512
D5        54-56       11   +3.49    -5.84   0.598    0.750
D6        57-63       10   +1.60    -5.04   0.318    0.449
D7        63-68       11   +0.92   -10.78   0.085    0.224
D8        68-73       10   +1.86    -7.17   0.260    0.456
D9        73-88       11   +8.80    -6.09   1.445    1.481
D10       88-99       11   +4.12   -15.67   0.263    0.182
```

### s12  (bk50d_s12_v1.3_roc100)

Trades scored: 110  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-42       11   -0.12    -8.09  -0.015   -0.027
D2        42-45       11   +5.10   -11.84   0.431    0.917
D3        45-47       11   +0.69    -7.40   0.093    0.179
D4        47-50       11   +3.58    -3.81   0.939    0.834
D5        51-55       11   +3.32    -3.88   0.855    0.894
D6        55-57       11   +2.96    -6.87   0.431    0.506
D7        57-64       11   +2.11    -3.97   0.530    0.590
D8        65-72       11   -0.16   -12.58  -0.013   -0.008
D9        73-88       11  +10.68    -4.16   2.566    1.602
D10       88-99       11   +4.12   -15.67   0.263    0.182
```

## Findings (2026-07-29 run, 2016-01-01 – 2020-12-31 — tables above regenerate on re-run)

1. **Every cell beats both benchmarks.** The worst of the nine (s12 @5%, +28.26%, Calmar 0.859)
   still clears QQQ (+23.46%, Calmar 0.821) and more than doubles SPY's Calmar (0.388). This is
   the strategy's natural habitat — a long trending bull punctuated by one sharp, quickly-reversed
   drawdown — and it is the friendliest of the three windows run so far.
2. **Looser thresholds win, agreeing with 2021-2026.** At 3%: s12 (+30.18%, Calmar 1.448) > s16
   (+28.94%) > s20 (+27.85%). That is the same ordering as 2021-2026 (s12 +45.96 > s16 +35.24 >
   s20 +32.17). Two of the three periods now agree that looser is better, and the dissenter
   (2010-2015) is also the period where the strategy fails outright — so `s12` is the better
   default than the historical `s20` preference.
3. **3-4% sizing is right here, unlike 2010-2015.** Calmar decays with size for s20 (1.377 →
   1.269 → 0.860) and s12 (1.448 → 1.444 → 0.859). Skip counts of 448-725 confirm capital, not
   signal supply, is binding — the reverse of 2010-2015, where 5% was best and skips were in
   single digits. s16 is the exception: it keeps gaining CAGR out to 5% (+32.71%, the best
   absolute cell) while its Calmar still falls, so that gain is bought with drawdown.
4. **Best risk-adjusted cell is s12 @3%** (Calmar 1.448, Sortino 1.258, +30.18%); best absolute is
   s16 @5% (+32.71%) at a materially worse Calmar (1.048) and MaxDD (−31.21%).
5. **The ranking's top decile earns more but rides far worse, and it is not config-specific.**
   D10 returns +4.12% standalone in all three configs against +0.94 / +1.48 / −0.12 for D1, but
   carries −15.67% MaxDD against −5.17 / −7.07 / −8.09, so D10's Sortino (0.182) sits *below*
   D1's (0.268 / 0.365). Note D10 is numerically identical across s20, s16 and s12 — same N=11,
   same 88-99 score range, same metrics. The ranking is dominated by the %-above-SMA50 term (50 of
   its 100 points), so the top-ranked signals are the most extended names, which clear all three
   thresholds and form one shared cohort.

**How to improve performance:** prefer `s12` at 3-4%. Treat rank-preference funding with caution —
point 5 shows the score selects for extension, which lifts return and drawdown together, so it is
the wrong lever if Sortino or Calmar is the objective. The measured effect of enabling it was
+0.21pp mean CAGR across nine 2021-2026 cells, i.e. indistinguishable from noise.
