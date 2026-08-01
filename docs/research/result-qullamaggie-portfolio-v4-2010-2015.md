# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-01 10:46:47 Tallinn time
Period: 2010-01-01 – 2015-12-31  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         53,967  +10.30   -19.42   0.530    0.981
QQQ         72,292  +15.81   -16.09   0.983    1.327
```

## s20  (bk50d_s20_v2.0 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 62 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          49,048   +8.55   -23.90   0.358    0.785    104     12   48.0%
4%          54,401  +10.44   -30.86   0.338    0.799     97     19   36.0%
5%          60,517  +12.42   -30.86   0.403    0.875     85     31   30.0%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          58,587  +11.82   -25.61   0.462    0.932    133     45   34.3%
4%          66,901  +14.32   -25.09   0.571    1.036    110     68   28.7%
5%          70,284  +15.27   -23.04   0.663    1.075     93     85   26.0%
```

## s16  (bk50d_s16_v2.0 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 210 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          44,395   +6.76   -30.29   0.223    0.607    119     31   41.7%
4%          48,311   +8.28   -30.97   0.267    0.667    100     50   34.8%
5%          46,987   +7.78   -33.88   0.229    0.613     87     63   30.0%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          73,478  +16.13   -24.81   0.650    1.156    170    190   21.9%
4%          63,049  +13.20   -26.39   0.500    0.934    131    229   19.0%
5%          63,730  +13.40   -29.31   0.457    0.905    106    254   16.4%
```

## s12  (bk50d_s12_v2.0 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 469 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          47,507   +7.97   -26.42   0.302    0.656    138     56   33.0%
4%          48,391   +8.31   -26.38   0.315    0.657    114     80   27.5%
5%          56,414  +11.12   -24.78   0.448    0.817     96     98   24.6%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          57,093  +11.34   -29.76   0.381    0.803    194    469   11.2%
4%          52,204   +9.69   -39.96   0.242    0.685    149    514    9.9%
5%          60,486  +12.42   -40.73   0.305    0.814    119    544    8.4%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s16 ungated — size 3%  (Final $73,478)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -4.3|10    +5.1|3    +4.5|1    -1.7|7    -3.5|0    -6.8|0    +6.6|0    -7.0|8   +13.6|3    +5.5|0    +2.3|0    +8.2|0 |   +22.3    32
 2011 |    +2.4|4    +3.6|1    +0.9|1    +2.7|3    -2.0|1    -2.2|0    -0.7|0    -7.5|0    -4.7|0   +1.4|24    -2.0|0    +0.5|0 |    -7.8    34
 2012 |    +8.7|1    +3.1|3    +1.6|0    -3.9|0    -7.8|0    +2.6|1    -0.1|5    +5.0|0    +3.0|0    +1.7|0    +1.7|3    +3.3|3 |   +19.7    16
 2013 |    +1.7|4    +0.1|2    +6.5|3    +5.1|1    +6.0|5    +2.4|2    +4.4|2    +1.1|3    +8.2|2    -1.2|0    +7.6|0    +2.9|1 |   +54.4    25
 2014 |    +5.2|4    +5.2|2    -3.4|3    +2.3|2    -2.5|2    +8.4|2    -1.4|2    +6.5|2    -5.7|1    -2.1|1    +0.9|7    +2.2|4 |   +15.5    32
 2015 |    +5.6|4    +3.5|2    +0.7|2    -3.1|3    +8.2|0    +2.9|2    +2.5|3   -10.2|0    -9.7|0    +3.0|3    +6.5|5    -6.1|7 |    +1.8    31
```

### #2  s20 ungated — size 5%  (Final $70,284)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.3|7    +7.3|2    +5.3|1    -3.0|5    -3.4|0    -8.2|0    +7.5|0    -9.0|4   +14.4|0    +2.0|0    +0.0|0    +8.4|0 |   +15.3    19
 2011 |    +1.7|0    +2.5|1    +0.4|0    +2.3|2    -2.8|0    -0.4|0    -1.2|0    -3.8|0    -4.1|0   -0.4|11    -4.8|4    -0.2|2 |   -10.8    20
 2012 |   +11.9|0    +6.4|0    +1.9|1    -0.5|0   -10.4|0    +1.6|1    -2.6|0    +8.3|0    +4.2|0    +3.5|0    +0.9|1    +1.7|2 |   +28.1     5
 2013 |    +2.4|2    -0.1|2    +4.5|0    +7.4|2    +6.9|2    +6.3|1    +1.7|1    -0.6|2   +10.7|1    -2.8|1   +11.6|0    +0.8|1 |   +59.6    15
 2014 |    +5.2|3    +7.3|1    -3.2|3    +1.7|2    -2.3|1    +9.1|1    -1.7|0    +4.7|1    -5.9|1    -4.5|1    +2.7|1    +4.4|4 |   +17.4    19
 2015 |    +5.7|3    +3.3|1    -3.6|2    -2.5|3    +6.1|0    +1.7|0    +0.2|2    -9.2|0    -9.3|0    +2.0|0    +7.0|2    -5.0|2 |    -5.1    15
```

### #3  s20 ungated — size 4%  (Final $66,901)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.4|7    +5.8|2    +4.3|1    -2.4|5    -2.7|0    -6.5|0    +5.9|0    -7.1|5   +11.7|2    +4.5|2    +0.0|0    +7.5|0 |   +16.6    24
 2011 |    +3.1|0    +3.0|1    +1.6|0    +5.0|2    -3.5|0    +0.4|0    +1.1|0    -6.9|0    -7.5|0   +1.8|11    -3.9|4    -0.3|3 |    -6.9    21
 2012 |   +11.0|4    +6.7|0    +1.9|1    -0.3|0   -10.2|0    +3.5|1    -2.8|0    +8.6|0    +5.7|0    +2.3|0    +0.3|1    +2.9|2 |   +31.8     9
 2013 |    +2.9|2    -0.0|2    +3.6|0    +5.8|2    +5.6|2    +5.2|1    +1.4|1    -0.5|2    +9.0|1    -2.3|1    +9.6|2    +1.0|1 |   +48.9    17
 2014 |    +4.0|3    +5.6|1    -2.8|3    +1.5|2    -3.5|1    +7.6|1    -1.3|0    +5.1|1    -5.4|1    -3.4|1    +2.1|1    +3.4|7 |   +12.6    22
 2015 |    +6.6|5    +2.9|1    -3.1|2    -1.0|3    +5.5|0    +2.5|0    -0.2|2    -9.8|0   -10.7|0    +2.3|0    +5.1|2    -5.4|2 |    -7.0    17
```

### #4  s16 ungated — size 5%  (Final $63,730)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -7.1|10    +8.7|3    +7.4|1    -3.0|5    -5.9|0   -10.5|0   +12.8|0   -10.5|0   +18.1|0    +3.5|0    +3.9|0    +8.7|0 |   +23.4    19
 2011 |    +0.7|4    +1.5|1    -0.4|1    +1.9|3    -1.4|1    -3.6|0    -1.7|0    -4.6|0    -7.5|0   +5.3|11    -5.7|0    +1.6|0 |   -13.7    21
 2012 |    +9.5|1    +3.3|3    +2.4|0    -4.5|0    -7.0|0    +1.9|1    +0.7|4    +5.7|0    +2.6|0    +0.7|0    +3.0|3    +5.0|3 |   +24.5    15
 2013 |    +2.7|4    +0.0|2   +10.2|2    +8.1|0    +8.4|0    +2.2|0    +4.2|2    +1.7|2    +9.4|0    -0.4|0    +7.4|0    +1.2|1 |   +70.4    13
 2014 |    +7.8|4    +5.1|2    -5.6|3    +4.4|2    -6.2|2   +10.5|1    -2.1|1    +8.6|2    -9.5|1    -2.7|0    +0.3|0    +1.2|1 |    +9.9    19
 2015 |    +4.9|4    -2.4|2    -1.9|3    +0.1|3    +7.7|0    +4.7|2    -2.7|1   -10.1|0   -10.2|0    +1.5|3    +0.9|1    -6.1|0 |   -14.5    19
```

### #5  s16 ungated — size 4%  (Final $63,049)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -5.7|10    +6.9|3    +6.0|1    -2.2|7    -4.6|0    -9.1|0    +9.1|0    -9.7|3   +16.2|0    +2.6|0    +0.9|0    +8.7|0 |   +16.8    24
 2011 |    +2.3|4    +2.6|1    -0.2|1    +2.2|3    -1.8|1    -2.9|0    -2.4|0    -5.0|0    -6.0|0   +3.2|16    -3.1|0    +0.3|0 |   -10.9    26
 2012 |    +9.3|1    +3.5|3    +0.7|0    -4.7|0    -7.4|0    +2.2|1    +1.0|4    +6.2|0    +3.5|0    +2.0|0    +2.4|3    +4.0|3 |   +23.6    15
 2013 |    +2.2|4    +0.0|2    +8.1|3    +6.6|1    +7.8|2    +2.1|0    +3.4|2    +2.3|2    +9.0|0    -0.1|0    +7.9|1    +0.9|1 |   +62.4    18
 2014 |    +4.5|4    +4.5|2    -4.6|3    +3.5|2    -6.0|2    +8.6|2    -1.8|2    +8.6|2    -6.5|1    -3.4|1    +1.0|1    +3.0|2 |   +10.4    24
 2015 |    +4.8|3    +0.8|3    -0.4|2    -1.7|3   +10.2|0    +1.5|2    -1.3|3   -10.2|0   -10.7|0    +2.5|3    +4.6|3    -7.3|2 |    -9.0    24
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 97  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        43-43        9   -0.00    -8.94  -0.000    0.019
D2        43-46       10   +1.03    -8.68   0.119    0.448
D3        49-56       10   +0.86    -6.92   0.125    0.364
D4        56-60        9   +4.68    -6.72   0.696    1.718
D5        60-64       10   +0.46   -12.27   0.038    0.158
D6        64-66       10   +0.91    -6.10   0.148    0.381
D7        66-66        9   -0.44    -7.62  -0.058   -0.214
D8        66-69       10   +1.72    -4.76   0.362    0.806
D9        69-83       10   +1.32    -5.14   0.257    0.567
D10       83-100      10   +0.79   -10.18   0.077    0.248
```

### s16  (bk50d_s16_v2.0)

Trades scored: 100  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       10   +1.04    -6.68   0.156    0.507
D2        43-47       10   +0.32    -5.16   0.062    0.185
D3        47-52       10   -0.12   -10.38  -0.012   -0.034
D4        52-57       10   +4.17    -7.53   0.554    1.427
D5        60-64       10   +0.53   -12.16   0.044    0.178
D6        64-66       10   -0.83    -7.76  -0.107   -0.364
D7        66-66       10   +0.49    -6.53   0.076    0.247
D8        66-69       10   +1.59    -6.56   0.242    0.798
D9        70-83       10   +1.39    -5.11   0.271    0.588
D10       83-100      10   +0.79   -10.18   0.077    0.248
```

### s12  (bk50d_s12_v2.0)

Trades scored: 114  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-40       11   -1.30   -14.21  -0.092   -0.484
D2        40-43       11   +1.58    -4.77   0.330    0.827
D3        43-47       12   +1.70    -6.00   0.283    0.732
D4        47-51       11   -1.06   -10.02  -0.106   -0.493
D5        51-56       12   +3.02    -6.64   0.455    1.017
D6        56-60       11   +2.65   -11.10   0.238    0.729
D7        64-66       11   -0.98    -9.06  -0.108   -0.401
D8        66-66       12   +0.73    -6.13   0.119    0.305
D9        66-70       11   +0.88    -4.55   0.193    0.460
D10       77-100      12   +1.83    -9.09   0.201    0.529
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
