# Qullamaggie Backtest v4 — Results

Run date: 2026-07-05

## Configuration

| Parameter | Value |
|---|---|
| Breakout | 50d high |
| SMA thresh sweep | 12%, 15%, 17%, 20% |
| Tight range | 20% (fixed) |
| Hold sweep | 91d, 184d, 366d (calendar) |
| Capacity limits | unconstrained, 30, 20 concurrent (FIFO) |
| vol_dry_up | avg_vol_10 < 80% × avg_vol_50 |
| vol_surge | volume/avg_vol_50 < 2.0× (no lower bound) |
| roc_12m_cap | 12m ROC < 100% |
| RSI | RSI(14) < 70 |
| ADR | mean((high-low)/low, last 20d, shift-1) ≥ 3.0% |
| ADR change | ADR%(10d) / ADR%(50d) < 90% |
| SMA alignment | disabled (commented out) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | ≥ 500K |
| Min history | ≥ 300 trading days |
| Cooldown | 30 calendar days |
| Eval period | 2021-01-01 – 2026-07-05 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```
Period: 2021-01-01 – 2026-07-05  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_tr20_v1.2_roc100       366d   243   67.1   +52.50    +52.33   +22.32   +71.52   6.99    2.864    39.71   -57.79    3.7    4/4  ✓
   2  bk50d_s15_tr20_v1.2_roc100       366d   460   66.3   +42.20    +42.06   +19.23   +58.38   5.92    2.338    37.68   -57.34    7.0    5/5  ✓
   3  bk50d_s17_tr20_v1.2_roc100       366d   353   65.2   +42.46    +42.32   +18.17   +61.03   5.66    2.269    38.87   -58.64    5.3    5/5  ✓
   4  bk50d_s20_tr20_v1.2_roc100       184d   243   65.0   +22.66    +49.94   +14.07   +42.76   4.27    2.150    29.90   -47.09    3.7    4/4  ✓
   5  bk50d_s12_tr20_v1.2_roc100       366d   631   64.5   +36.93    +36.81   +15.57   +53.48   5.21    2.046    37.09   -56.60    9.6    5/5  ✓
   6  bk50d_s20_tr20_v1.2_roc100        91d   243   64.6    +9.81    +45.56    +7.42   +22.38   2.75    1.629    21.41   -38.24    3.7    4/4  ✓
   7  bk50d_s17_tr20_v1.2_roc100       184d   353   62.0   +17.14    +36.86   +10.94   +33.80   3.28    1.603    29.53   -46.31    5.3    4/4  ✓
   8  bk50d_s15_tr20_v1.2_roc100       184d   460   61.7   +16.42    +35.19    +9.61   +31.93   3.18    1.555    28.61   -44.48    7.0    5/5  ✓
   9  bk50d_s15_tr20_v1.2_roc100        91d   460   62.8    +8.05    +36.40    +6.50   +20.45   2.33    1.336    20.19   -36.03    7.0    5/5  ✓
  10  bk50d_s17_tr20_v1.2_roc100        91d   353   63.7    +8.20    +37.15    +7.40   +20.31   2.36    1.335    20.88   -37.79    5.3    5/5  ✓
  11  bk50d_s12_tr20_v1.2_roc100       184d   631   59.7   +13.64    +28.88    +7.51   +27.81   2.72    1.267    28.43   -44.72    9.6    5/5  ✓
  12  bk50d_s12_tr20_v1.2_roc100        91d   631   60.7    +6.62    +29.32    +5.52   +19.83   2.02    1.059    20.19   -36.93    9.6    5/5  ✓

Valid combinations: 12  |  Consistent: 12
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_tr20_v1.2_roc100` | `366d` — SR=2.864, Win%=67.1, Med%=+22.32, AnnMean%=+52.33, Q75%=+71.52, MaxDD%=39.71, CVaR%=-57.79, Yrs+=4/4, N=243
- `bk50d_s15_tr20_v1.2_roc100` | `366d` — SR=2.338, Win%=66.3, Med%=+19.23, AnnMean%=+42.06, Q75%=+58.38, MaxDD%=37.68, CVaR%=-57.34, Yrs+=5/5, N=460
- `bk50d_s17_tr20_v1.2_roc100` | `366d` — SR=2.269, Win%=65.2, Med%=+18.17, AnnMean%=+42.32, Q75%=+61.03, MaxDD%=38.87, CVaR%=-58.64, Yrs+=5/5, N=353
- `bk50d_s20_tr20_v1.2_roc100` | `184d` — SR=2.150, Win%=65.0, Med%=+14.07, AnnMean%=+49.94, Q75%=+42.76, MaxDD%=29.90, CVaR%=-47.09, Yrs+=4/4, N=243
- `bk50d_s12_tr20_v1.2_roc100` | `366d` — SR=2.046, Win%=64.5, Med%=+15.57, AnnMean%=+36.81, Q75%=+53.48, MaxDD%=37.09, CVaR%=-56.60, Yrs+=5/5, N=631
- `bk50d_s20_tr20_v1.2_roc100` | `91d` — SR=1.629, Win%=64.6, Med%=+7.42, AnnMean%=+45.56, Q75%=+22.38, MaxDD%=21.41, CVaR%=-38.24, Yrs+=4/4, N=243
- `bk50d_s17_tr20_v1.2_roc100` | `184d` — SR=1.603, Win%=62.0, Med%=+10.94, AnnMean%=+36.86, Q75%=+33.80, MaxDD%=29.53, CVaR%=-46.31, Yrs+=4/4, N=353
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=1.555, Win%=61.7, Med%=+9.61, AnnMean%=+35.19, Q75%=+31.93, MaxDD%=28.61, CVaR%=-44.48, Yrs+=5/5, N=460
- `bk50d_s15_tr20_v1.2_roc100` | `91d` — SR=1.336, Win%=62.8, Med%=+6.50, AnnMean%=+36.40, Q75%=+20.45, MaxDD%=20.19, CVaR%=-36.03, Yrs+=5/5, N=460
- `bk50d_s17_tr20_v1.2_roc100` | `91d` — SR=1.335, Win%=63.7, Med%=+7.40, AnnMean%=+37.15, Q75%=+20.31, MaxDD%=20.88, CVaR%=-37.79, Yrs+=5/5, N=353
- `bk50d_s12_tr20_v1.2_roc100` | `184d` — SR=1.267, Win%=59.7, Med%=+7.51, AnnMean%=+28.88, Q75%=+27.81, MaxDD%=28.43, CVaR%=-44.72, Yrs+=5/5, N=631
- `bk50d_s12_tr20_v1.2_roc100` | `91d` — SR=1.059, Win%=60.7, Med%=+5.52, AnnMean%=+29.32, Q75%=+19.83, MaxDD%=20.19, CVaR%=-36.93, Yrs+=5/5, N=631

## Rankings — Max 30 Concurrent Positions

Same signals, but a trade is skipped if 30 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```
Period: 2021-01-01 – 2026-07-05  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 30

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s17_tr20_v1.2_roc100       366d   127   75.6   +58.74    +58.54   +26.70   +78.65   9.70    3.652    36.37   -53.19    1.9    1/1   
   2  bk50d_s20_tr20_v1.2_roc100       366d   126   72.2   +53.58    +53.40   +23.81   +74.34   8.28    3.215    37.86   -53.44    1.9    1/1   
   3  bk50d_s15_tr20_v1.2_roc100       366d   130   72.3   +47.13    +46.97   +27.21   +77.33   7.14    2.744    37.13   -55.07    2.0    1/1   
   4  bk50d_s20_tr20_v1.2_roc100       184d   182   65.4   +21.80    +47.87   +12.70   +40.11   4.09    2.024    30.44   -48.77    2.8    3/3  ✓
   5  bk50d_s17_tr20_v1.2_roc100       184d   195   64.6   +20.08    +43.77   +11.56   +33.57   3.86    1.950    29.60   -45.00    3.0    3/3  ✓
   6  bk50d_s15_tr20_v1.2_roc100       184d   202   61.4   +19.38    +42.11    +8.35   +34.87   3.56    1.807    28.94   -45.61    3.1    4/4  ✓
   7  bk50d_s12_tr20_v1.2_roc100       366d   140   68.6   +32.10    +32.00   +21.74   +59.40   4.95    1.800    37.31   -58.67    2.1    1/2   
   8  bk50d_s20_tr20_v1.2_roc100        91d   205   61.5    +9.07    +41.65    +6.01   +20.57   2.50    1.447    21.78   -39.50    3.1    3/3  ✓
   9  bk50d_s17_tr20_v1.2_roc100        91d   257   63.4    +8.38    +38.08    +6.02   +20.09   2.43    1.390    20.93   -38.04    3.9    3/3  ✓
  10  bk50d_s15_tr20_v1.2_roc100        91d   286   62.6    +8.17    +37.04    +5.44   +20.33   2.37    1.363    20.62   -36.93    4.3    4/4  ✓
  11  bk50d_s12_tr20_v1.2_roc100       184d   221   57.9   +13.13    +27.74    +6.56   +26.66   2.54    1.153    29.18   -45.64    3.3    5/5  ✓
  12  bk50d_s12_tr20_v1.2_roc100        91d   331   58.6    +5.85    +25.63    +3.56   +17.39   1.86    0.913    21.32   -37.60    5.0    5/5  ✓

Valid combinations: 12  |  Consistent: 8
```

## Consistent Combinations (Max 30 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_tr20_v1.2_roc100` | `184d` — SR=2.024, Win%=65.4, Med%=+12.70, AnnMean%=+47.87, Q75%=+40.11, MaxDD%=30.44, CVaR%=-48.77, Yrs+=3/3, N=182
- `bk50d_s17_tr20_v1.2_roc100` | `184d` — SR=1.950, Win%=64.6, Med%=+11.56, AnnMean%=+43.77, Q75%=+33.57, MaxDD%=29.60, CVaR%=-45.00, Yrs+=3/3, N=195
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=1.807, Win%=61.4, Med%=+8.35, AnnMean%=+42.11, Q75%=+34.87, MaxDD%=28.94, CVaR%=-45.61, Yrs+=4/4, N=202
- `bk50d_s20_tr20_v1.2_roc100` | `91d` — SR=1.447, Win%=61.5, Med%=+6.01, AnnMean%=+41.65, Q75%=+20.57, MaxDD%=21.78, CVaR%=-39.50, Yrs+=3/3, N=205
- `bk50d_s17_tr20_v1.2_roc100` | `91d` — SR=1.390, Win%=63.4, Med%=+6.02, AnnMean%=+38.08, Q75%=+20.09, MaxDD%=20.93, CVaR%=-38.04, Yrs+=3/3, N=257
- `bk50d_s15_tr20_v1.2_roc100` | `91d` — SR=1.363, Win%=62.6, Med%=+5.44, AnnMean%=+37.04, Q75%=+20.33, MaxDD%=20.62, CVaR%=-36.93, Yrs+=4/4, N=286
- `bk50d_s12_tr20_v1.2_roc100` | `184d` — SR=1.153, Win%=57.9, Med%=+6.56, AnnMean%=+27.74, Q75%=+26.66, MaxDD%=29.18, CVaR%=-45.64, Yrs+=5/5, N=221
- `bk50d_s12_tr20_v1.2_roc100` | `91d` — SR=0.913, Win%=58.6, Med%=+3.56, AnnMean%=+25.63, Q75%=+17.39, MaxDD%=21.32, CVaR%=-37.60, Yrs+=5/5, N=331

## Rankings — Max 20 Concurrent Positions

Same signals, but a trade is skipped if 20 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```
Period: 2021-01-01 – 2026-07-05  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 20

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_tr20_v1.2_roc100       366d    86   70.9   +52.17    +52.00   +26.60   +77.33   7.18    2.850    38.66   -57.73    1.3    0/0   
   2  bk50d_s20_tr20_v1.2_roc100       184d   132   67.4   +24.74    +55.03   +11.11   +40.85   4.82    2.401    30.41   -47.72    2.0    2/2   
   3  bk50d_s15_tr20_v1.2_roc100       366d    90   71.1   +37.03    +36.91   +25.68   +75.13   5.76    2.147    38.21   -56.60    1.4    0/0   
   4  bk50d_s17_tr20_v1.2_roc100       366d    87   71.3   +34.36    +34.25   +22.86   +66.99   5.23    1.936    38.85   -57.64    1.3    0/0   
   5  bk50d_s17_tr20_v1.2_roc100       184d   135   63.0   +20.17    +43.99   +10.29   +36.06   3.79    1.886    29.44   -47.97    2.0    3/3  ✓
   6  bk50d_s15_tr20_v1.2_roc100       184d   142   59.9   +18.13    +39.17    +9.88   +33.78   3.45    1.727    29.20   -44.12    2.2    3/3  ✓
   7  bk50d_s12_tr20_v1.2_roc100       366d   100   66.0   +30.52    +30.42   +14.11   +50.35   4.21    1.560    38.87   -64.15    1.5    0/1   
   8  bk50d_s17_tr20_v1.2_roc100        91d   198   64.6    +8.58    +39.12    +6.01   +18.86   2.52    1.480    21.37   -36.33    3.0    3/3  ✓
   9  bk50d_s15_tr20_v1.2_roc100        91d   218   61.0    +8.37    +38.03    +5.46   +20.35   2.39    1.433    21.21   -34.57    3.3    3/4  ✓
  10  bk50d_s20_tr20_v1.2_roc100        91d   163   62.0    +8.91    +40.80    +5.45   +20.33   2.49    1.428    22.19   -39.82    2.5    3/3  ✓
  11  bk50d_s12_tr20_v1.2_roc100       184d   152   57.2   +12.53    +26.39    +6.43   +26.44   2.42    1.081    29.87   -44.97    2.3    4/4  ✓
  12  bk50d_s12_tr20_v1.2_roc100        91d   250   56.8    +5.40    +23.47    +2.94   +17.38   1.72    0.791    22.11   -38.41    3.8    4/5  ✓

Valid combinations: 12  |  Consistent: 7
```

## Consistent Combinations (Max 20 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s17_tr20_v1.2_roc100` | `184d` — SR=1.886, Win%=63.0, Med%=+10.29, AnnMean%=+43.99, Q75%=+36.06, MaxDD%=29.44, CVaR%=-47.97, Yrs+=3/3, N=135
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=1.727, Win%=59.9, Med%=+9.88, AnnMean%=+39.17, Q75%=+33.78, MaxDD%=29.20, CVaR%=-44.12, Yrs+=3/3, N=142
- `bk50d_s17_tr20_v1.2_roc100` | `91d` — SR=1.480, Win%=64.6, Med%=+6.01, AnnMean%=+39.12, Q75%=+18.86, MaxDD%=21.37, CVaR%=-36.33, Yrs+=3/3, N=198
- `bk50d_s15_tr20_v1.2_roc100` | `91d` — SR=1.433, Win%=61.0, Med%=+5.46, AnnMean%=+38.03, Q75%=+20.35, MaxDD%=21.21, CVaR%=-34.57, Yrs+=3/4, N=218
- `bk50d_s20_tr20_v1.2_roc100` | `91d` — SR=1.428, Win%=62.0, Med%=+5.45, AnnMean%=+40.80, Q75%=+20.33, MaxDD%=22.19, CVaR%=-39.82, Yrs+=3/3, N=163
- `bk50d_s12_tr20_v1.2_roc100` | `184d` — SR=1.081, Win%=57.2, Med%=+6.43, AnnMean%=+26.39, Q75%=+26.44, MaxDD%=29.87, CVaR%=-44.97, Yrs+=4/4, N=152
- `bk50d_s12_tr20_v1.2_roc100` | `91d` — SR=0.791, Win%=56.8, Med%=+2.94, AnnMean%=+23.47, Q75%=+17.38, MaxDD%=22.11, CVaR%=-38.41, Yrs+=4/5, N=250

## Findings & Caveats

**Fixed**: `close`/`high`/`low` are now split/dividend-adjusted (scaled by `adjusted_close/close`). The prior version used raw `close`, which shows a fake ~90% one-day move on a stock's split date (e.g. NVDA's 2024-06-10 10:1 split) — this corrupted rolling indicators for ~50 days around any split and could make a real winning trade compute as a huge loss (or vice versa for a reverse split). 13.1% of the qualifying universe (254/1,943 tickers) had at least one such split event since 2020. The MIN_PRICE/MAX_PRICE band still uses raw (unadjusted) close, since that's the real price a trader would have paid on the entry date — adjusting it would leak knowledge of future splits into a point-in-time filter.

**Unresolved — survivorship bias**: every ticker in the qualifying universe has `status='active'`; the pipeline retains no delisted/bankrupt/acquired tickers. `company.market_cap` is also a single current-day snapshot applied retroactively to all history, not a point-in-time value. A momentum-breakout strategy specifically targets stocks that sometimes blow up afterward (fraud, failed trial, acquisition below entry) — those trades are structurally impossible to appear in this backtest. This likely explains part of the unusually high win rate/profit factor and should be treated as a ceiling on how much to trust the absolute return numbers.

**Partially addressed — overlapping trades**: at several signals/month with 6-12 month holds, most trades are open concurrently and share the same regime exposure, so the unconstrained N overstates the number of independent bets and the Sortino/consistency stats overstate statistical confidence. The 'Max 30 and 20 Concurrent Positions' tables above cap the portfolio at that many simultaneous positions (FIFO signal acceptance) as a rough realism check — comparing the tables shows how much each combination's apparent edge depends on taking every single signal versus a capital-constrained subset. This doesn't fix the underlying correlation between trades still held concurrently within a cap, and it uses an arbitrary FIFO rule rather than a real signal-quality ranking for which trade to take when capacity is full.

**Unresolved — regime concentration**: the SPY>200d SMA filter concentrates trades in bull years. The Yrs+ denominator silently drops any complete calendar year with <10 losing trades from its count (see the Yrs+ column above, e.g. a stricter signal with fewer total trades may show fewer valid years than the number of complete calendar years in the eval period), which can exclude harder regimes rather than prove the strategy survived them.

**Unresolved — no execution costs**: entry is assumed fillable at the same close that generated the signal, with no slippage, spread, commissions, or gap risk — unrealistic for breakout-day fills on high-ADR names.

**Ideas to improve**: source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot; source a delisted-ticker history if available to address survivorship; shift entry to next-day open (+ slippage assumption) for realistic fills; replace the FIFO acceptance rule in the capacity-constrained table with a real signal-quality ranking (e.g. ADR%, breakout strength) to pick which trade to take when capacity is full; account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence.
