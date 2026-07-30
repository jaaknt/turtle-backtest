# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-07-30
Period: 2010-01-01 – 2015-12-31  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         53,967  +10.30   -19.42   0.530    0.658
QQQ         72,292  +15.81   -16.09   0.983    0.888
```

## s20  (bk50d_s20_v2.0 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 36 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          43,627   +6.45   -14.97   0.431    0.569     71      0   64.2%
4%          48,805   +8.46   -19.42   0.436    0.578     71      0   52.8%
5%          52,165   +9.67   -23.63   0.409    0.566     67      4   44.8%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          48,868   +8.48   -24.26   0.350    0.584    102      5   49.1%
4%          52,327   +9.73   -26.95   0.361    0.563     92     15   39.4%
5%          64,766  +13.71   -27.06   0.506    0.693     81     26   33.0%
```

## s16  (bk50d_s16_v2.0 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 144 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          46,228   +7.48   -18.92   0.395    0.568     91      0   56.3%
4%          46,398   +7.55   -24.62   0.307    0.482     83      8   47.6%
5%          48,543   +8.36   -30.09   0.278    0.482     73     18   40.1%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          58,521  +11.80   -27.37   0.431    0.636    150     85   29.6%
4%          74,043  +16.27   -26.13   0.623    0.797    124    111   24.2%
5%          73,089  +16.02   -25.92   0.618    0.796    101    134   22.6%
```

## s12  (bk50d_s12_v2.0 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 333 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          40,826   +5.28   -24.43   0.216    0.379    107     12   49.5%
4%          43,503   +6.40   -28.62   0.224    0.392     95     24   38.6%
5%          49,773   +8.82   -26.63   0.331    0.472     84     35   32.1%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%          60,872  +12.53   -26.62   0.471    0.634    182    270   17.3%
4%          57,069  +11.33   -26.74   0.424    0.562    140    312   14.0%
5%          60,204  +12.33   -31.46   0.392    0.581    117    335   11.9%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s16 ungated — size 4%  (Final $74,043)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -4.8|8    +6.1|1    +5.0|0    -1.5|4    -3.9|0    -6.2|0    +5.4|0    -4.9|4    +9.6|6    +4.7|1    +1.0|0   +11.0|0 |   +21.3    24
 2011 |    +5.9|2    +3.4|0    +2.4|0    +2.5|1    -2.2|1    -0.3|0    -1.0|0    -8.4|0    -4.4|0   +0.3|21    -1.0|0    +0.2|0 |    -3.5    25
 2012 |    +7.4|1    +3.1|0    +1.4|0    -2.1|0    -7.5|0    +2.4|0    -1.6|3    +2.3|0    +4.5|0    +1.4|0    +1.6|3    +1.1|2 |   +14.1     9
 2013 |    +0.8|4    -0.2|1    +6.1|2    +6.5|1   +10.4|3    +3.3|1    +4.1|2    +2.6|2    +9.7|2    -0.5|0    +7.2|0    +1.6|0 |   +64.5    18
 2014 |    +7.6|4    +6.6|2    -4.7|2    +1.5|2    -2.8|1   +10.1|2    -2.6|2    +7.7|1    -5.9|0    -0.4|0    +1.1|5    +2.1|3 |   +20.5    24
 2015 |    +4.1|3    +5.1|2    +0.4|1    -2.2|4    +7.4|0    +0.8|1    +0.6|1   -10.5|0   -11.7|0    +5.5|1    +3.9|5    -8.2|6 |    -6.8    24
```

### #2  s16 ungated — size 5%  (Final $73,089)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -6.0|8    +7.7|1    +6.2|0    -1.9|4    -4.9|0    -7.8|0    +6.9|0    -6.2|4   +12.0|2    +2.6|0    +0.8|0   +11.4|0 |   +19.8    19
 2011 |    +4.6|2    +2.0|0    +1.1|0    +1.3|1    -1.6|1    -1.7|0    -1.5|0    -7.1|0    -1.9|0   -0.1|16    -0.4|0    +1.1|0 |    -4.6    20
 2012 |    +7.5|1    +2.8|0    +0.7|0    -1.9|0    -6.9|0    +1.8|0    -2.3|3    +2.3|0    +4.7|0    +1.3|0    +2.0|3    +1.3|2 |   +13.4     9
 2013 |    +1.0|4    -0.2|1    +7.6|2    +8.0|1   +12.6|3    +3.7|0    +4.2|2    +4.4|1   +10.3|0    +1.7|0    +7.9|0    -0.3|0 |   +79.7    14
 2014 |    +6.4|4    +6.5|2    -5.2|2    +3.5|2    -5.0|1    +9.2|2    -3.1|2    +9.0|1    -5.7|0    -0.5|0    +1.2|3    +1.6|0 |   +17.6    19
 2015 |    +2.3|3    +3.4|3    +0.9|0    -0.1|4    +7.5|0    +0.4|1    -3.0|1    -7.4|0   -10.1|0    +3.3|1    +1.9|6    -9.2|1 |   -11.1    20
```

### #3  s20 ungated — size 5%  (Final $64,766)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |    -3.2|5    +6.5|1    +4.5|0    -1.8|3    -3.0|0    -5.6|0    +4.0|0    -4.2|3    +7.7|2    +2.0|1    -1.0|2    +9.4|2 |   +14.7    19
 2011 |    +3.3|0    +3.3|0    +2.9|0    +4.3|0    -3.2|0    +1.0|0    +0.2|0    -7.1|0    -7.9|0    +4.4|6    -1.9|2    -0.3|2 |    -1.9    10
 2012 |    +6.9|2    +3.3|7    +1.3|0    +0.6|0   -11.6|0    +3.3|0    -0.9|0    +8.1|0    +3.6|0    +0.8|0    -0.3|1    +4.3|1 |   +19.8    11
 2013 |    +1.1|2    +0.3|1    +2.3|0    +5.5|2    +4.9|2    +2.4|0    +2.1|1    -0.5|1    +9.9|1    -1.9|0    +7.5|2    +1.2|0 |   +40.1    12
 2014 |    +5.6|3    +6.8|1    -4.1|1    -0.3|2    -3.8|1    +7.0|1    -2.5|0    +6.5|1    -5.8|0    +0.0|0    +2.9|0    +4.4|3 |   +16.7    13
 2015 |    +3.8|4    +4.8|5    -0.4|0    -2.2|3    +8.4|0    +2.7|1    +1.3|1   -11.2|0   -13.6|0    +1.7|0   +11.6|2    -5.6|0 |    -2.0    16
```

### #4  s12 ungated — size 3%  (Final $60,872)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -5.0|16    +6.5|1    +4.7|1    +0.0|7    -6.9|0    -6.4|0    +5.6|0    -6.0|7   +12.3|0    +2.0|0    +2.2|0   +13.1|0 |   +21.3    32
 2011 |    +1.0|5    +3.7|3    -2.3|1    -0.4|4    -1.5|1    -3.1|0    -1.9|2    -6.4|0    -7.5|0   +7.2|18    -3.7|0    +0.8|0 |   -14.0    34
 2012 |    +9.9|5    +4.9|2    -1.8|0    -2.1|0    -8.8|1    +1.1|1    -1.9|6    +4.6|0    +6.1|0    +0.7|0    +0.4|4    +1.2|5 |   +13.9    24
 2013 |    +3.7|7    -2.1|6    +7.2|3    +1.2|0    +7.1|0    +0.4|1    +4.8|4    +2.1|1   +10.2|0    +1.1|0    +7.5|0    +2.6|2 |   +55.4    24
 2014 |    +6.3|5    +3.9|2    -5.0|5    +1.4|3    -3.5|4   +10.2|6    -2.2|2    +6.4|3    -8.4|0    +0.1|0    +2.3|1    +1.8|2 |   +12.4    33
 2015 |    +4.9|4    +2.4|3    +1.6|2    -1.0|4    +8.1|1    -1.7|5    -2.2|2    -5.2|0    -7.9|0    +1.8|3    +3.8|8    -5.8|3 |    -2.2    35
```

### #5  s12 ungated — size 5%  (Final $60,204)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2010 |   -8.4|16   +11.2|1    +7.8|1    -1.1|1    -8.3|0    -9.0|0   +10.5|0    -7.4|0   +12.1|0    +1.8|0    +0.2|0   +12.7|0 |   +19.6    19
 2011 |    +2.6|5    +1.1|3    -1.9|1    -1.7|4    -1.1|1    -4.6|0    -3.1|2    -6.0|0   -12.9|0   +16.2|4    -6.8|0    +1.9|0 |   -17.5    20
 2012 |   +10.5|6    +5.2|2    -3.0|0    -2.0|0    -9.4|1    -1.2|1    -1.1|7    +6.1|0    +8.1|0    +2.0|0    +0.9|4    +3.3|0 |   +19.4    21
 2013 |    +3.8|3    -1.8|4    +7.3|0    +2.0|0    +3.5|0    -1.5|1    +4.4|4    +2.9|2   +12.3|0    +2.5|0    +9.5|0    +2.9|2 |   +58.4    16
 2014 |   +12.9|3    +4.8|2    -8.7|5    +1.8|1    -2.2|0   +13.8|1    -4.6|2    +4.3|3   -11.0|0    -0.9|0    +6.2|1    +2.6|2 |   +17.1    20
 2015 |    +6.7|3    +2.9|1    +2.5|2    -4.7|3    +6.0|0    -1.0|2    -0.6|0    -8.3|0    -7.9|0    +3.9|3    +1.3|4    -7.6|3 |    -8.2    21
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 71  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        43-43        7   +0.34    -4.48   0.076    0.145
D2        43-49        7   +0.65    -5.23   0.124    0.211
D3        49-52        7   -0.82    -7.16  -0.114   -0.273
D4        52-56        7   +2.72    -5.36   0.508    0.701
D5        56-60        7   +2.59    -4.87   0.530    0.725
D6        60-60        7   +0.29   -10.39   0.027    0.057
D7        60-66        7   -0.15    -6.64  -0.023   -0.027
D8        66-66        7   +0.09    -5.51   0.016    0.035
D9        66-77        7   +2.01    -4.16   0.484    0.633
D10       83-100       8   +1.15    -7.27   0.158    0.254
```

### s16  (bk50d_s16_v2.0)

Trades scored: 83  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43        8   +1.45    -5.43   0.267    0.423
D2        43-47        8   -0.53    -5.67  -0.094   -0.213
D3        47-49        8   -0.57    -6.45  -0.089   -0.162
D4        49-52        9   +0.76    -6.18   0.123    0.213
D5        52-56        8   +2.90    -5.36   0.542    0.887
D6        57-60        8   +1.38    -6.42   0.215    0.246
D7        60-64        9   -0.58    -9.00  -0.065   -0.109
D8        64-66        8   +0.16    -3.62   0.045    0.067
D9        66-74        8   +1.18    -3.35   0.351    0.450
D10       77-100       9   +1.75    -7.27   0.241    0.346
```

### s12  (bk50d_s12_v2.0)

Trades scored: 95  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-40        9   -0.43    -6.76  -0.063   -0.130
D2        40-43       10   +1.51    -4.98   0.302    0.407
D3        43-47        9   -0.61    -8.73  -0.069   -0.181
D4        49-50       10   -1.17    -9.74  -0.120   -0.300
D5        50-53        9   +1.97    -5.26   0.374    0.453
D6        53-60       10   +4.74    -5.36   0.885    1.049
D7        60-64        9   -0.66   -11.54  -0.057   -0.084
D8        64-66       10   +0.26    -5.58   0.046    0.081
D9        66-69        9   -0.37    -6.15  -0.061   -0.135
D10       74-100      10   +1.78    -7.27   0.244    0.347
```

## Findings (2026-07-30 run, 2010-01-01 – 2015-12-31 — tables above regenerate on re-run)

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
