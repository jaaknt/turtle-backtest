# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-08-01 10:49:33 Tallinn time
Period: 2021-01-01 – 2026-06-26  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         59,301  +13.25   -25.36   0.522    1.192
QQQ         68,525  +16.28   -35.62   0.457    1.131
```

## s20  (bk50d_s20_v2.0 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 184 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         188,451  +39.87   -28.24   1.412    1.785    175    335   13.8%
4%         206,548  +42.23   -28.01   1.508    1.769    135    375   11.3%
5%         250,869  +47.37   -31.43   1.507    1.800    110    400    9.8%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         151,102  +34.34   -27.66   1.242    1.625    184    510   11.6%
4%         191,828  +40.32   -28.54   1.413    1.710    139    555    9.5%
5%         169,102  +37.13   -29.20   1.272    1.609    114    580    9.7%
```

## s16  (bk50d_s16_v2.0 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 562 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         172,561  +37.64   -30.71   1.226    1.647    184    421   10.4%
4%         191,224  +40.24   -30.95   1.300    1.653    142    463    8.8%
5%         165,030  +36.52   -30.77   1.187    1.543    114    491    9.4%
```

**no ranking filter** — 0 signals dropped by the gate, 2 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         192,240  +40.38   -23.53   1.716    1.820    192    973    7.7%
4%         158,994  +35.59   -25.86   1.376    1.594    142   1023    8.2%
5%         179,977  +38.70   -28.23   1.371    1.642    112   1053    8.9%
```

## s12  (bk50d_s12_v2.0 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 1064 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         342,332  +55.98   -25.59   2.187    2.265    189    546    8.1%
4%         222,576  +44.18   -26.00   1.700    1.865    143    592    8.7%
5%         221,218  +44.02   -26.55   1.658    1.808    115    620    8.7%
```

**no ranking filter** — 0 signals dropped by the gate, 2 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         123,721  +29.52   -23.75   1.243    1.512    194   1603    6.5%
4%         132,902  +31.23   -25.66   1.217    1.545    145   1652    6.0%
5%         123,840  +29.55   -24.09   1.226    1.500    116   1681    5.9%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s12 R>=40 — size 3%  (Final $342,332)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.9|33   +21.1|0    +2.4|0    +5.6|0   +10.5|0    +7.6|0    -9.8|0    +2.1|0   +11.4|0    +8.6|0    -6.5|0    +5.1|0 |   +60.4    33
 2022 |    +5.3|1    +1.1|7   -0.8|21   -11.1|3    +4.8|0    -9.0|0   +16.0|0    +4.4|0    -8.3|0   +13.3|0    +8.7|0    -3.3|0 |   +18.3    32
 2023 |    +7.1|2    +1.9|3    -1.1|6    -3.4|6   +7.7|12   +14.1|3   +11.5|0    -4.0|0    -9.5|0    -9.8|0   +17.6|0   +15.2|0 |   +51.7    32
 2024 |    -5.2|1   +12.2|3    -0.2|6    -7.1|5   +8.5|11    -3.8|7    +7.8|0    +3.9|0    +6.3|0    +3.7|0   +16.9|0    +2.7|0 |   +52.5    33
 2025 |    +2.2|0    -5.8|3    -6.6|0    +2.4|0   +5.2|18  +16.8|10    +8.1|1    +9.0|0   +19.7|0   +13.1|0    +3.0|0    -1.0|0 |   +84.1    32
 2026 |   +13.6|0    +3.4|1    -6.3|2   +11.7|0    +7.8|8   +6.5|16         ·         ·         ·         ·         ·         · |   +41.2    27
```

### #2  s20 R>=40 — size 5%  (Final $250,869)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.0|19   +23.8|0    +1.8|0    +4.4|0   +12.4|0    +9.0|0   -12.1|0    +1.2|0   +16.3|0   +11.2|0    -7.8|0    +3.3|0 |   +69.5    19
 2022 |    +8.3|0    +0.8|2   -2.2|14   -13.9|3    +4.8|0    -7.8|0   +14.0|0    +3.2|0   -11.7|0   +11.1|0    +3.3|0    -7.3|0 |    -1.9    19
 2023 |    +7.1|0    -2.1|3    -4.6|2    -3.9|3    +7.1|8   +13.0|3   +15.0|0    -9.0|0   -11.1|0   -12.5|0   +25.3|0   +20.7|0 |   +43.2    19
 2024 |    -8.1|0    +7.1|3    -3.2|0    -5.2|4    +8.5|8    -3.5|3    +3.9|0   +11.1|0   +12.6|0    +6.4|0   +13.6|0    +1.2|0 |   +50.5    18
 2025 |    +7.1|0    -6.6|1    -6.9|0    -0.5|0   +5.2|10   +18.4|9    +9.0|0   +10.1|0   +24.9|0   +14.4|0    -4.8|0    -4.1|0 |   +80.9    20
 2026 |   +15.7|0    -4.9|1   -13.3|0   +10.8|0   +17.1|7    +4.2|7         ·         ·         ·         ·         ·         · |   +28.9    15
```

### #3  s12 R>=40 — size 4%  (Final $222,576)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.5|24   +20.7|0    +2.2|0    +5.7|0   +11.8|0    +6.8|0    -9.7|0    +1.5|0   +14.3|0    +9.9|0    -7.2|0    +4.2|0 |   +65.6    24
 2022 |    +5.7|1    +1.5|7   -0.6|16   -11.4|0    +4.6|0    -9.1|0   +13.7|0    +1.8|0   -10.8|0   +15.8|0    +6.0|0    -4.2|0 |    +9.2    24
 2023 |    +7.6|2    +1.2|3    -3.4|6    -4.6|6    +9.8|7   +14.1|0   +13.2|0    -4.4|0   -10.5|0   -11.8|0   +17.6|0   +13.4|0 |   +43.1    24
 2024 |    -7.0|2   +16.7|3    -0.9|5    -9.6|5    +9.5|9    -5.4|0    +8.2|0    +5.8|0    +6.1|0    +0.4|0   +12.3|0    +7.1|0 |   +47.6    24
 2025 |    -2.2|0    -4.2|6    -6.7|0    +2.4|0   +5.3|17   +13.8|0    +5.8|0    +9.1|0   +23.8|0   +10.1|0    -3.1|0    -4.4|0 |   +56.3    23
 2026 |   +10.5|0    +0.3|1    -9.3|3   +12.1|2    +7.4|9    +2.7|9         ·         ·         ·         ·         ·         · |   +24.3    24
```

### #4  s12 R>=40 — size 5%  (Final $221,218)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.0|19   +23.8|0    +1.8|0    +4.4|0   +12.4|0    +9.0|0   -12.1|0    +1.2|0   +16.3|0   +11.2|0    -7.8|0    +3.3|0 |   +69.5    19
 2022 |    +8.3|1    +1.8|7   -0.5|11    -9.0|0    +5.4|0   -10.1|0   +10.3|0    -0.2|0   -11.5|0   +19.3|0    +5.3|0    -3.0|0 |   +12.4    19
 2023 |    +6.8|2    -1.5|3    -1.3|6    -5.8|6    +8.5|2   +14.5|0   +12.5|0    -2.4|0   -10.2|0   -10.0|0   +14.7|0   +13.3|0 |   +40.0    19
 2024 |    -9.7|2   +15.4|3    -1.6|6    -9.1|5   +14.0|4    -5.6|0    +5.9|0    +4.9|0    +9.2|0    -0.8|0   +13.7|0   +10.6|0 |   +51.8    20
 2025 |    -4.2|0    -2.2|4    -4.3|0    +1.6|0   +1.1|14   +15.7|0    +6.8|0   +10.3|0   +22.1|0    +8.7|0    -3.7|0    -7.5|0 |   +48.5    18
 2026 |   +12.4|0    -0.4|1   -11.3|3    +7.8|1   +10.9|9    +3.3|6         ·         ·         ·         ·         ·         · |   +22.7    20
```

### #5  s20 R>=40 — size 4%  (Final $206,548)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -4.9|24   +22.5|0    +2.1|0    +5.3|0   +12.5|0    +7.6|0   -11.5|0    +0.7|0   +15.8|0   +10.4|0    -8.0|0    +4.6|0 |   +66.4    24
 2022 |    +7.4|0    +0.7|2   -1.8|14   -11.7|4    +3.5|0    -6.6|0   +11.6|0    +3.0|0    -9.7|0    +8.2|0    +2.7|0    -4.5|5 |    -0.0    25
 2023 |    +9.8|0    -3.4|2    -2.4|2    -4.1|3    +2.4|8   +11.4|3   +14.9|0    -9.3|0    -8.7|0   -10.6|0   +24.1|0   +17.2|5 |   +39.9    23
 2024 |    -8.4|0    +8.1|3    -5.3|0    -6.6|4    +7.2|8    -4.3|3    +7.9|1    +9.0|0    +9.6|0    +4.5|0   +13.0|0    +0.6|3 |   +37.5    22
 2025 |    +7.8|0    -7.7|1    -8.3|0    -0.9|0   +6.6|10  +15.9|10    +7.3|1   +12.9|0   +21.4|0   +13.1|0    -4.2|0    -3.7|2 |   +71.3    24
 2026 |   +14.7|0    -5.3|1    -9.9|0    +7.5|0   +14.4|7    +4.4|9         ·         ·         ·         ·         ·         · |   +25.6    17
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 135  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        41-49       13   +4.93    -6.61   0.746    1.259
D2        49-58       14   +3.40    -6.16   0.552    1.060
D3        60-60       13   -0.43    -9.01  -0.048   -0.070
D4        60-64       14   +2.81    -8.03   0.349    0.915
D5        64-66       13   +1.98   -11.89   0.167    0.470
D6        66-69       14   +3.10    -8.81   0.352    0.800
D7        69-73       13   +5.25    -9.09   0.578    1.087
D8        73-83       14   +0.78   -12.33   0.063    0.213
D9        83-87       13  +11.25   -23.73   0.474    1.246
D10       87-100      14  +11.22   -11.24   0.998    1.702
```

### s16  (bk50d_s16_v2.0)

Trades scored: 142  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-46       14   +2.04    -7.50   0.272    0.775
D2        47-52       14   +3.74    -7.42   0.504    0.994
D3        52-60       14   +1.26    -7.37   0.171    0.398
D4        60-60       14   +0.98   -11.19   0.087    0.307
D5        62-66       15   +3.51    -6.24   0.563    0.894
D6        66-66       14   +1.20   -10.13   0.118    0.325
D7        66-73       14   +4.93    -9.09   0.542    1.051
D8        73-83       14   +2.50    -9.55   0.262    0.638
D9        83-83       14  +11.03   -21.75   0.507    1.183
D10       87-100      15  +10.49   -11.59   0.905    1.577
```

### s12  (bk50d_s12_v2.0)

Trades scored: 143  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       14   +5.64    -7.16   0.788    1.710
D2        43-46       14   +0.73   -10.79   0.068    0.324
D3        47-52       14   +5.11    -7.56   0.676    1.280
D4        52-58       15   +7.87    -5.94   1.327    1.956
D5        60-62       14   -0.34    -7.48  -0.046   -0.075
D6        62-66       14   +3.09    -7.00   0.442    0.730
D7        66-67       15   +3.15    -7.83   0.402    0.812
D8        69-73       14   +4.41    -9.09   0.485    0.929
D9        73-83       14   +2.70   -11.70   0.231    0.634
D10       83-100      15  +12.07   -18.55   0.651    1.412
```

## Findings (2026-07-30 run, 2021-01-01 – 2026-06-26 — tables above regenerate on re-run)

> **⚠ These findings predate the tables above.** They were written against the 2026-07-30 run;
> the tables were regenerated 2026-08-01 after `vol_dry_up` was retired from the strategy, which
> added ~45% more signals. Figures quoted below no longer match — e.g. the ranking gate's CAGR
> advantage is now **+7.92pp winning 7 of 9 cells**, not +12.09pp winning 9 of 9. Treat the
> reasoning as still useful and every number as superseded.

**What changed in this run.** Each config is now reported twice — through the `MIN_RANKING >= 40`
gate and with no ranking condition — so the gate's value can be read in portfolio terms rather than
inferred. This is also the first portfolio run on the 40/35/25 `QullamaggieRanking` weights
(changed 2026-07-29); the previously committed tables predated them, which is why the gated figures
moved. Two other changes moved nothing: the bar load is now bounded at the eval-window end (a
control run with the bound removed reproduces this report byte-for-byte), and the limit-order entry
comparison was removed.

1. **The ranking gate is worth +12.09pp of CAGR on average here, and it wins all nine cells.** The
   effect grows as the entry threshold loosens: +3.91 to +6.46pp at s20, +4.14 to +8.69pp at s16,
   and **+18.72 to +28.45pp at s12**. The mechanism is visible in the `skip` column — ungated s12
   generates 1,141-1,220 skipped signals against 356-420 gated. Without the gate the portfolio
   spends its cash on whatever arrives first; with it, the same cash buys a better-scoring subset.
2. **Without the gate, the SMA threshold barely matters.** Ungated at 3% sizing: s20 +31.80%,
   s16 +31.31%, s12 +30.34% — flat within noise. Gated at 3%: +35.71%, +40.00%, +49.06% — strongly
   increasing. The "looser thresholds win" conclusion is *entirely* a gate effect. A looser
   threshold is only better because it gives the ranking more candidates to choose from; on its own
   it just adds mediocre trades.
3. **Best cell is gated `s12 @4%`** — $338,569, +55.66% CAGR, Calmar 1.679, Sortino 1.485. Best
   risk-adjusted is gated `s12 @3%` (Calmar 1.808, Sortino 1.508). All nine gated cells beat buy &
   hold comfortably (SPY +13.25%, QQQ +16.28%), though s12's −27% to −34% drawdown is worse than
   SPY's −25.36%.
4. **The gate does not buy safety here, only return.** Gated drawdowns are similar to or worse than
   ungated at s12 (−33.16% vs −25.36% at 4%). It concentrates capital into higher-scoring names,
   which is a return-seeking move, not a defensive one. Contrast 2016-2020, where the same gate cut
   s12's drawdown by ~20pp.
5. **The ranking separates on return but not on risk** within the gated set. D10 is the top decile
   by CAGR in all three configs (+14.18% standalone for s12), yet s12's *D1* carries the best Calmar
   of any decile (2.059 against D10's 1.080) on the same 13-14 trades. The middle is unordered —
   D2 +1.58, D5 +2.52, D9 +3.55 against D7 +6.81 and D8 +9.02.

**How to improve performance:** prefer gated `s12` at 3-4%, keep the next-day-open entry, and keep
the plain 366d time cap.

### The ranking gate across all three windows

Gated minus ungated CAGR, all 9 config/size cells per window:

```text
window       mean delta   gate wins   range
2010-2015      -4.86pp       0 / 9    -8.72 .. -1.27
2016-2020      +3.01pp       9 / 9    +0.76 .. +7.92
2021-2026     +12.09pp       9 / 9    +3.91 .. +28.45
```

**The gate's value is regime-dependent and reverses sign.** In 2010-2015 it loses in every single
cell — it removes signals from a window that already has too few, leaving 32-64% of capital idle.
By 2016-2020 it wins every cell but modestly, and its main contribution there is drawdown: it cuts
s12's from ~−45% to ~−28%. In 2021-2026 it dominates.

Note this is *not* explained by which era the weights were fitted on: the 40/35/25 split was derived
from 2010-2020 signals (see `docs/research/result-qullamaggie-ranking-weights.md`), and 2010-2015 is
the window where the gate performs worst. The fit was on year-demeaned cross-sectional returns,
which strips exactly the time effect the portfolio sim is exposed to — so the two are not in
contradiction, but the gate should be treated as a bull-regime amplifier rather than a universally
positive filter.

### Exit variations, across all three windows

Mean CAGR delta against the plain 366d time cap, 9 config/size cells per window. Carried over from
`docs/research/result-qullamaggie-exit-sweep.md`; **these figures predate the re-weighting** and have
not been regenerated.

```text
variation      2010-2015   2016-2020   2021-2026   cells won (CAGR, of 27)
sma200x5        -2.13       -9.20       -1.91             6
dead120         -2.59       -9.70       -0.76             4
```

Neither wins a majority of cells and both change magnitude sharply between periods. The 366d time
cap remains the rule to beat.

**Entry variations are no longer measured here.** The limit-order comparison this doc used to carry
was removed from the script on 2026-07-30; that dimension belongs to
`docs/research/result-qullamaggie-cohorts-limit-order.md` and
`docs/research/result-qullamaggie-limit-fill-rate.md`, both of which need a re-run on the current
weights before their numbers can be quoted against this table.
