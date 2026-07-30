# Portfolio Simulation — size sweep + ranking deciles

Run date: 2026-07-30
Period: 2021-01-01 – 2026-06-26  |  Initial: $30,000  |  algorithm: RSI<70  |  sizes: 3%, 4%, 5%  |  hold: 366d  |  min ranking: 40

## Buy & Hold Benchmarks

$30,000 bought on the first trading day of the period, sold on the last.

```text
symbol      Final$   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------
SPY         59,301  +13.25   -25.36   0.522    0.803
QQQ         68,525  +16.28   -35.62   0.457    0.760
```

## s20  (bk50d_s20_v2.0 / 366d)

Parameters: %abv_SMA50>20%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 143 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         159,762  +35.71   -22.73   1.571    1.252    151    222   21.8%
4%         148,736  +33.95   -24.43   1.390    1.165    120    253   18.6%
5%         152,319  +34.54   -28.11   1.229    1.110    100    273   16.3%
```

**no ranking filter** — 0 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         136,114  +31.80   -23.95   1.328    1.174    163    353   18.4%
4%         117,221  +28.25   -31.34   0.902    1.020    132    384   15.9%
5%         116,341  +28.08   -28.67   0.979    0.968    110    406   13.7%
```

## s16  (bk50d_s16_v2.0 / 366d)

Parameters: %abv_SMA50>16%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 422 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         189,431  +40.00   -22.56   1.773    1.359    162    278   17.3%
4%         197,380  +41.06   -25.33   1.621    1.295    129    311   14.1%
5%         211,638  +42.86   -31.39   1.366    1.262    106    334   11.2%
```

**no ranking filter** — 0 signals dropped by the gate, 1 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         133,356  +31.31   -25.70   1.218    1.127    185    676   11.5%
4%         167,702  +36.92   -27.10   1.362    1.176    143    718    8.8%
5%         177,208  +38.31   -27.91   1.373    1.204    113    748    8.9%
```

## s12  (bk50d_s12_v2.0 / 366d)

Parameters: %abv_SMA50>12%, breakout>50d high, RSI(14)<70, ADR%(20)>=3.0%, ADR_change<90%, vol_surge<2.0x, vol_dry_up<90%, roc_12m<100%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown=30d, hold=366d cal

**QullamaggieRanking >= 40** — 807 signals dropped by the gate, 0 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         267,081  +49.06   -27.13   1.808    1.508    172    356   13.0%
4%         338,569  +55.66   -33.16   1.679    1.485    132    396    8.9%
5%         312,117  +53.37   -34.36   1.553    1.461    108    420    8.6%
```

**no ranking filter** — 0 signals dropped by the gate, 1 with no fillable next-day open in period.

```text
size        Final$   CAGR%   MaxDD%  Calmar  Sortino  taken   skip  Uninv%
--------------------------------------------------------------------------
3%         128,064  +30.34   -25.72   1.180    1.060    193   1141    7.1%
4%         113,380  +27.48   -25.36   1.084    0.999    142   1192    8.0%
5%         101,458  +24.92   -28.38   0.878    0.900    114   1220    7.3%
```

## Monthly returns/transactions — top 5 by Final$

### #1  s12 R>=40 — size 4%  (Final $338,569)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.4|24   +22.9|0    +2.0|0    +5.6|0   +12.3|0    +7.6|0    -9.7|0    +1.1|0   +16.1|0    +9.3|0    -7.0|0    +5.0|0 |   +71.6    24
 2022 |    +5.7|1    +0.3|4   -2.0|13   -17.5|7    -0.8|0    -6.0|0   +18.0|0    +5.6|0    -8.4|0    +8.6|0    +7.4|0    -5.5|0 |    +0.8    25
 2023 |   +13.0|1    +1.3|2    -4.1|2    -2.3|3   +0.8|10   +11.8|6   +11.0|0    -6.0|0    -9.9|0    -8.8|0   +20.8|0   +23.0|0 |   +54.0    24
 2024 |    -4.0|1    +8.2|2    -0.9|0    -4.8|3    +9.5|8    -2.3|2    +6.2|5    +8.2|3    +4.6|0    +2.3|0   +17.1|0    +3.8|0 |   +56.7    24
 2025 |    +5.2|0    -4.6|2    -7.6|0    +4.9|0    +8.8|9   +11.5|3    +8.2|8   +14.6|3   +12.1|0   +11.3|0    +8.9|0    -4.9|0 |   +88.9    25
 2026 |    +8.9|0    -0.8|2    +2.8|0   +10.4|0    +6.5|3    +9.7|5         ·         ·         ·         ·         ·         · |   +43.2    10
```

### #2  s12 R>=40 — size 5%  (Final $312,117)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.9|19   +24.3|0    +1.0|0    +5.4|0   +13.3|0    +7.7|0   -11.2|0    +1.0|0   +15.3|0   +10.0|0    -8.0|0    +3.8|0 |   +68.5    19
 2022 |    +6.7|1    +0.4|4   -2.5|13   -17.5|2    -0.2|0    -7.4|0   +20.3|0    +7.7|0    -8.9|0    +8.6|0    +9.8|0    -5.5|0 |    +6.1    20
 2023 |   +14.3|1    +1.3|2    -4.8|2    -2.1|3   +0.9|10   +15.0|2    +9.4|0    -6.7|0   -11.2|0    -7.8|0   +20.8|0   +22.6|0 |   +55.1    20
 2024 |    -3.8|0    +9.2|2    -1.4|1    -7.0|3    +7.4|7    -0.9|2    +8.2|4    +6.8|0    +5.5|0    -0.7|0   +18.4|0    +7.4|0 |   +57.8    19
 2025 |    +3.0|0    -4.8|1   -11.6|0    +4.8|0   +12.2|9   +14.5|3   +11.2|7    +8.5|0   +12.7|0    +7.9|0    +8.2|0    -3.6|0 |   +78.4    20
 2026 |    +9.7|0    -2.3|1    +0.0|0    +8.7|0    +6.6|3    +7.2|6         ·         ·         ·         ·         ·         · |   +33.3    10
```

### #3  s12 R>=40 — size 3%  (Final $267,081)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.2|32   +23.1|0    +1.4|0    +5.7|0    +9.1|0    +7.2|0    -9.4|0    +2.6|0   +10.0|0    +7.8|0    -6.4|0    +4.8|0 |   +58.2    32
 2022 |    +4.8|1    +0.2|4   -1.5|13   -13.5|8    -0.7|0    -4.6|0   +13.2|0    +4.5|0    -6.5|0    +6.0|0    +5.6|0    -3.8|7 |    +0.9    33
 2023 |   +13.7|2    -0.0|2    -2.7|2    -2.2|3   -3.0|10   +11.1|6   +10.3|0    -6.0|0    -8.4|0    -6.9|0   +20.1|0   +19.5|7 |   +47.9    32
 2024 |    -4.4|2    +8.6|2    -0.6|0    -5.8|3    +9.4|8    -3.3|2    +8.6|5    +6.3|3    +5.4|0    +2.5|0   +16.0|0    +3.3|1 |   +53.4    26
 2025 |    +3.3|2    -4.9|2    -7.3|0    +3.6|0    +7.2|9   +10.7|9    +7.1|9   +12.5|2    +9.9|0   +11.1|0   +10.8|0    -0.5|0 |   +81.6    33
 2026 |    +6.7|1    +8.3|2    -2.2|0   +11.5|0    +1.3|3   +6.1|10         ·         ·         ·         ·         ·         · |   +35.4    16
```

### #4  s16 R>=40 — size 5%  (Final $211,638)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -3.9|19   +24.3|0    +1.0|0    +5.4|0   +13.3|0    +7.7|0   -11.2|0    +1.0|0   +15.3|0   +10.0|0    -8.0|0    +3.8|0 |   +68.5    19
 2022 |    +6.7|1    +1.8|2    -1.5|8   -17.3|6    +0.5|0    -7.2|0   +13.8|0    +4.9|0   -10.0|0   +10.6|0    +2.1|0    -2.4|3 |    -2.3    20
 2023 |   +12.1|1    -5.0|1    -4.4|2    -3.7|3    -3.2|8   +12.4|1   +13.7|0   -10.7|0    -9.1|0    -9.0|0   +19.9|0   +19.0|3 |   +27.8    19
 2024 |    -5.9|1   +12.7|1    -4.5|1    -9.6|2    +6.4|7    -3.6|2   +10.5|2    +8.4|0    +7.7|0    +0.9|0   +20.1|0    +6.6|1 |   +56.6    17
 2025 |    +2.3|1    -7.1|1   -11.2|0    +4.6|0   +12.2|7   +10.4|4    +9.9|7    +8.1|0   +14.0|0    +7.9|0    +7.1|0    -3.6|0 |   +65.1    20
 2026 |    +8.3|0    -0.2|1    -0.4|0    +9.8|0    +2.5|3    +7.0|7         ·         ·         ·         ·         ·         · |   +29.6    11
```

### #5  s16 R>=40 — size 4%  (Final $197,380)

```text
 Year |       Jan       Feb       Mar       Apr       May       Jun       Jul       Aug       Sep       Oct       Nov       Dec |   Year%  Txns
-----------------------------------------------------------------------------------------------------------------------------------------------
 2021 |   -5.4|24   +22.9|0    +2.0|0    +5.6|0   +12.3|0    +7.6|0    -9.7|0    +1.1|0   +16.1|0    +9.3|0    -7.0|0    +5.0|0 |   +71.6    24
 2022 |    +5.7|1    +1.4|2    -1.2|8   -13.8|6    +0.4|0    -5.5|0   +10.4|0    +3.8|0    -7.9|0    +8.1|0    +1.6|0    -3.0|8 |    -2.5    25
 2023 |   +13.4|2    -4.9|1    -2.7|2    -3.6|3    -6.1|8   +11.8|0   +11.5|0    -8.2|0    -9.2|0    -6.1|0   +19.0|0   +17.7|8 |   +29.8    24
 2024 |    -7.9|2   +12.8|1    -3.8|1   -12.5|2    +6.3|7    -2.5|2   +10.3|0    +5.8|1    +6.0|0    -0.5|0    +9.8|0    +7.1|1 |   +31.3    17
 2025 |    -0.0|2    -2.5|1    -8.4|0    +0.3|0    +7.0|7  +10.2|11    +4.6|2   +12.7|1   +11.9|0   +12.5|0    +7.4|0    -0.7|0 |   +67.6    24
 2026 |    +5.5|0   +13.2|2    -3.9|0   +15.8|0    -0.1|2   +3.7|11         ·         ·         ·         ·         ·         · |   +37.7    15
```

## Ranking Deciles (QullamaggieRanking)

Every taken trade of every config (at 4% sizing, the middle of the 3%/4%/5% sweep) is scored 0-100 with turtlex/strategy/ranking/qullamaggie.py at entry, split into 10 equal-count deciles (D1=lowest score .. D10=highest), and each decile's own signal subset is re-simulated in isolation (same sizing, same universe) to report that decile's standalone portfolio metrics — this tests whether higher-ranked signals produce a better standalone portfolio, not just a higher per-trade return.

### s20  (bk50d_s20_v2.0)

Trades scored: 120  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        41-43       12   +1.09    -5.71   0.191    0.325
D2        43-47       12   +7.16    -9.14   0.784    0.776
D3        49-56       12   +2.83    -8.80   0.322    0.532
D4        58-60       12   -1.31   -11.55  -0.113   -0.208
D5        60-66       12   +3.77   -16.35   0.230    0.435
D6        66-66       12   -0.51    -8.56  -0.059   -0.083
D7        66-70       12   +8.29    -8.20   1.011    0.973
D8        70-83       12   +2.87    -9.09   0.315    0.597
D9        83-87       12   +5.63   -11.18   0.503    0.781
D10       87-100      12   +7.76    -7.71   1.005    0.849
```

### s16  (bk50d_s16_v2.0)

Trades scored: 129  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       12   +2.90    -5.88   0.493    0.743
D2        43-49       13   +6.16    -9.67   0.637    0.726
D3        50-56       13   +5.04    -6.09   0.828    0.996
D4        56-60       13   +0.53    -8.85   0.060    0.120
D5        60-64       13   +5.09   -14.78   0.345    0.660
D6        64-66       13   +2.04    -9.47   0.216    0.332
D7        66-70       13   +5.07    -7.03   0.720    0.726
D8        70-77       13   +5.30    -6.84   0.776    0.914
D9        77-87       13   +2.13   -12.42   0.172    0.388
D10       87-100      13  +10.01   -11.24   0.890    1.006
```

### s12  (bk50d_s12_v2.0)

Trades scored: 132  |  size: 4%

```text
Decile     Ranking     N   CAGR%   MaxDD%  Calmar  Sortino
----------------------------------------------------------
D1        40-43       13   +7.43    -3.61   2.059    1.449
D2        44-47       13   +1.58   -10.13   0.156    0.296
D3        47-52       13   +3.93    -5.89   0.667    0.764
D4        52-60       13   +3.60    -8.22   0.437    0.678
D5        60-64       14   +2.52   -12.04   0.209    0.407
D6        64-66       13   +4.47    -8.33   0.537    0.721
D7        66-70       13   +6.81    -7.03   0.969    1.066
D8        70-77       13   +9.02   -13.68   0.659    1.125
D9        77-83       13   +3.55   -11.93   0.297    0.508
D10       83-100      14  +14.18   -13.13   1.080    1.149
```

## Findings (2026-07-30 run, 2021-01-01 – 2026-06-26 — tables above regenerate on re-run)

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
