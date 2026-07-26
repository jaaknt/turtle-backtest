# Qullamaggie Backtest v4 — Results

Run date: 2026-07-26

## Configuration

| Parameter | Value |
|---|---|
| Breakout | 50d high |
| SMA thresh sweep | 12%, 15%, 17%, 20% |
| Tight range | disabled (commented out) |
| Hold sweep | 91d, 184d, 366d (calendar) |
| Capacity limits | unconstrained, 30, 20 concurrent (FIFO) |
| vol_dry_up | avg_vol_10 < 90% × avg_vol_50 |
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
| Eval period | 2021-01-01 – 2026-07-26 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```text
Period: 2021-01-01 – 2026-07-26  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.3_roc100            366d   397   66.0   +54.71    +54.53   +22.32   +79.59   6.88    2.820    40.83   -62.03    6.0    5/5  ✓
   2  bk50d_s17_v1.3_roc100            366d   571   64.3   +46.66    +46.50   +18.14   +66.73   5.78    2.368    40.08   -60.69    8.7    5/5  ✓
   3  bk50d_s15_v1.3_roc100            366d   741   64.6   +42.74    +42.60   +18.99   +60.77   5.47    2.192    38.97   -60.22   11.2    5/5  ✓
   4  bk50d_s12_v1.3_roc100            366d  1008   62.9   +37.14    +37.02   +14.86   +55.19   4.78    1.889    38.44   -60.28   15.3    5/5  ✓
   5  bk50d_s20_v1.3_roc100            184d   397   61.2   +21.21    +46.45   +11.23   +41.76   3.52    1.786    31.71   -50.71    6.0    5/5  ✓
   6  bk50d_s17_v1.3_roc100            184d   571   59.0   +16.64    +35.71    +8.48   +35.47   2.79    1.336    31.26   -51.49    8.7    5/5  ✓
   7  bk50d_s20_v1.3_roc100             91d   397   62.2    +9.50    +43.89    +6.35   +23.95   2.37    1.330    22.67   -45.51    6.0    5/5  ✓
   8  bk50d_s15_v1.3_roc100            184d   741   58.4   +14.90    +31.72    +7.46   +32.57   2.62    1.212    30.43   -50.64   11.2    5/5  ✓
   9  bk50d_s12_v1.3_roc100            184d  1008   56.4   +12.74    +26.85    +6.20   +29.86   2.38    1.051    29.87   -49.54   15.3    5/5  ✓
  10  bk50d_s15_v1.3_roc100             91d   741   59.6    +7.33    +32.79    +5.17   +21.37   1.99    1.031    21.55   -42.51   11.2    4/5  ✓
  11  bk50d_s17_v1.3_roc100             91d   571   60.6    +7.42    +33.27    +5.52   +21.36   1.99    1.011    22.26   -45.16    8.7    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d  1008   58.3    +6.21    +27.35    +4.31   +20.04   1.84    0.892    21.13   -41.61   15.3    4/5  ✓

Valid combinations: 12  |  Consistent: 12
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v1.3_roc100` | `366d` — SR=2.820, Win%=66.0, Med%=+22.32, AnnMean%=+54.53, Q75%=+79.59, MaxDD%=40.83, CVaR%=-62.03, Yrs+=5/5, N=397
- `bk50d_s17_v1.3_roc100` | `366d` — SR=2.368, Win%=64.3, Med%=+18.14, AnnMean%=+46.50, Q75%=+66.73, MaxDD%=40.08, CVaR%=-60.69, Yrs+=5/5, N=571
- `bk50d_s15_v1.3_roc100` | `366d` — SR=2.192, Win%=64.6, Med%=+18.99, AnnMean%=+42.60, Q75%=+60.77, MaxDD%=38.97, CVaR%=-60.22, Yrs+=5/5, N=741
- `bk50d_s12_v1.3_roc100` | `366d` — SR=1.889, Win%=62.9, Med%=+14.86, AnnMean%=+37.02, Q75%=+55.19, MaxDD%=38.44, CVaR%=-60.28, Yrs+=5/5, N=1008
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.786, Win%=61.2, Med%=+11.23, AnnMean%=+46.45, Q75%=+41.76, MaxDD%=31.71, CVaR%=-50.71, Yrs+=5/5, N=397
- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.336, Win%=59.0, Med%=+8.48, AnnMean%=+35.71, Q75%=+35.47, MaxDD%=31.26, CVaR%=-51.49, Yrs+=5/5, N=571
- `bk50d_s20_v1.3_roc100` | `91d` — SR=1.330, Win%=62.2, Med%=+6.35, AnnMean%=+43.89, Q75%=+23.95, MaxDD%=22.67, CVaR%=-45.51, Yrs+=5/5, N=397
- `bk50d_s15_v1.3_roc100` | `184d` — SR=1.212, Win%=58.4, Med%=+7.46, AnnMean%=+31.72, Q75%=+32.57, MaxDD%=30.43, CVaR%=-50.64, Yrs+=5/5, N=741
- `bk50d_s12_v1.3_roc100` | `184d` — SR=1.051, Win%=56.4, Med%=+6.20, AnnMean%=+26.85, Q75%=+29.86, MaxDD%=29.87, CVaR%=-49.54, Yrs+=5/5, N=1008
- `bk50d_s15_v1.3_roc100` | `91d` — SR=1.031, Win%=59.6, Med%=+5.17, AnnMean%=+32.79, Q75%=+21.37, MaxDD%=21.55, CVaR%=-42.51, Yrs+=4/5, N=741
- `bk50d_s17_v1.3_roc100` | `91d` — SR=1.011, Win%=60.6, Med%=+5.52, AnnMean%=+33.27, Q75%=+21.36, MaxDD%=22.26, CVaR%=-45.16, Yrs+=4/5, N=571
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.892, Win%=58.3, Med%=+4.31, AnnMean%=+27.35, Q75%=+20.04, MaxDD%=21.13, CVaR%=-41.61, Yrs+=4/5, N=1008

## Rankings — Max 30 Concurrent Positions

Same signals, but a trade is skipped if 30 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-26  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Max concurrent positions: 30

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.3_roc100            366d   133   65.4   +45.76    +45.61   +22.32   +77.36   5.36    2.103    41.19   -69.82    2.0    1/2   
   2  bk50d_s15_v1.3_roc100            366d   147   63.3   +40.11    +39.98   +17.48   +70.03   4.99    1.962    40.29   -67.29    2.2    2/3   
   3  bk50d_s12_v1.3_roc100            366d   150   64.0   +33.92    +33.81   +14.11   +60.15   4.57    1.752    39.36   -64.18    2.3    3/3  ✓
   4  bk50d_s17_v1.3_roc100            366d   137   68.6   +35.34    +35.23   +18.38   +61.84   4.72    1.749    39.83   -69.82    2.1    0/1   
   5  bk50d_s17_v1.3_roc100            184d   209   57.9   +16.61    +35.63    +7.17   +32.04   2.86    1.328    31.10   -55.86    3.2    4/5  ✓
   6  bk50d_s20_v1.3_roc100            184d   202   56.4   +16.97    +36.47    +6.21   +37.12   2.69    1.250    33.48   -58.13    3.1    4/4  ✓
   7  bk50d_s15_v1.3_roc100            184d   222   52.7   +13.73    +29.08    +3.14   +32.37   2.32    1.024    31.82   -55.22    3.4    4/5  ✓
   8  bk50d_s20_v1.3_roc100             91d   249   57.4    +6.36    +28.06    +4.14   +22.80   1.80    0.810    23.64   -50.18    3.8    3/4  ✓
   9  bk50d_s12_v1.3_roc100            184d   236   51.7    +9.59    +19.91    +1.58   +26.44   1.88    0.697    32.38   -55.85    3.6    5/5  ✓
  10  bk50d_s17_v1.3_roc100             91d   305   56.4    +4.86    +20.97    +3.23   +18.24   1.57    0.612    23.32   -48.28    4.6    4/5  ✓
  11  bk50d_s15_v1.3_roc100             91d   345   53.9    +4.61    +19.83    +2.09   +17.56   1.53    0.588    23.05   -46.18    5.2    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d   394   51.0    +1.98     +8.20    +0.30   +15.35   1.21    0.244    23.47   -46.56    6.0    4/5  ✓

Valid combinations: 12  |  Consistent: 9
```

## Consistent Combinations (Max 30 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s12_v1.3_roc100` | `366d` — SR=1.752, Win%=64.0, Med%=+14.11, AnnMean%=+33.81, Q75%=+60.15, MaxDD%=39.36, CVaR%=-64.18, Yrs+=3/3, N=150
- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.328, Win%=57.9, Med%=+7.17, AnnMean%=+35.63, Q75%=+32.04, MaxDD%=31.10, CVaR%=-55.86, Yrs+=4/5, N=209
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.250, Win%=56.4, Med%=+6.21, AnnMean%=+36.47, Q75%=+37.12, MaxDD%=33.48, CVaR%=-58.13, Yrs+=4/4, N=202
- `bk50d_s15_v1.3_roc100` | `184d` — SR=1.024, Win%=52.7, Med%=+3.14, AnnMean%=+29.08, Q75%=+32.37, MaxDD%=31.82, CVaR%=-55.22, Yrs+=4/5, N=222
- `bk50d_s20_v1.3_roc100` | `91d` — SR=0.810, Win%=57.4, Med%=+4.14, AnnMean%=+28.06, Q75%=+22.80, MaxDD%=23.64, CVaR%=-50.18, Yrs+=3/4, N=249
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.697, Win%=51.7, Med%=+1.58, AnnMean%=+19.91, Q75%=+26.44, MaxDD%=32.38, CVaR%=-55.85, Yrs+=5/5, N=236
- `bk50d_s17_v1.3_roc100` | `91d` — SR=0.612, Win%=56.4, Med%=+3.23, AnnMean%=+20.97, Q75%=+18.24, MaxDD%=23.32, CVaR%=-48.28, Yrs+=4/5, N=305
- `bk50d_s15_v1.3_roc100` | `91d` — SR=0.588, Win%=53.9, Med%=+2.09, AnnMean%=+19.83, Q75%=+17.56, MaxDD%=23.05, CVaR%=-46.18, Yrs+=4/5, N=345
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.244, Win%=51.0, Med%=+0.30, AnnMean%=+8.20, Q75%=+15.35, MaxDD%=23.47, CVaR%=-46.56, Yrs+=4/5, N=394

## Rankings — Max 20 Concurrent Positions

Same signals, but a trade is skipped if 20 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-26  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Max concurrent positions: 20

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.3_roc100            366d   100   62.0   +40.40    +40.27   +16.88   +71.80   4.71    1.859    41.74   -71.55    1.5    1/2   
   2  bk50d_s17_v1.3_roc100            366d    97   66.0   +37.88    +37.76   +18.08   +61.84   4.30    1.654    41.89   -73.93    1.5    0/1   
   3  bk50d_s20_v1.3_roc100            366d    93   63.4   +35.50    +35.39   +16.28   +77.27   4.06    1.516    43.47   -73.93    1.4    0/1   
   4  bk50d_s17_v1.3_roc100            184d   149   55.7   +17.46    +37.62    +6.29   +35.54   2.90    1.384    32.33   -56.05    2.3    3/4  ✓
   5  bk50d_s12_v1.3_roc100            366d   100   58.0   +25.98    +25.90    +6.58   +42.32   3.45    1.294    40.54   -63.68    1.5    1/2   
   6  bk50d_s20_v1.3_roc100            184d   142   54.9   +17.22    +37.06    +5.66   +38.52   2.81    1.290    33.27   -60.01    2.2    3/4  ✓
   7  bk50d_s15_v1.3_roc100            184d   152   50.0   +11.74    +24.63    -0.08   +26.79   2.09    0.853    32.55   -55.91    2.3    4/5  ✓
   8  bk50d_s20_v1.3_roc100             91d   194   54.6    +5.72    +24.98    +3.13   +20.86   1.65    0.683    24.47   -53.31    2.9    3/4  ✓
   9  bk50d_s12_v1.3_roc100            184d   166   51.8    +8.88    +18.38    +1.44   +26.15   1.76    0.606    34.04   -59.12    2.5    4/5  ✓
  10  bk50d_s17_v1.3_roc100             91d   226   54.9    +4.52    +19.42    +2.65   +18.50   1.49    0.547    24.26   -48.62    3.4    4/5  ✓
  11  bk50d_s15_v1.3_roc100             91d   254   50.8    +2.80    +11.72    +0.18   +16.09   1.29    0.333    24.15   -50.03    3.8    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d   272   52.6    +2.38     +9.91    +1.04   +15.87   1.26    0.300    23.22   -45.39    4.1    4/5  ✓

Valid combinations: 12  |  Consistent: 8
```

## Consistent Combinations (Max 20 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.384, Win%=55.7, Med%=+6.29, AnnMean%=+37.62, Q75%=+35.54, MaxDD%=32.33, CVaR%=-56.05, Yrs+=3/4, N=149
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.290, Win%=54.9, Med%=+5.66, AnnMean%=+37.06, Q75%=+38.52, MaxDD%=33.27, CVaR%=-60.01, Yrs+=3/4, N=142
- `bk50d_s15_v1.3_roc100` | `184d` — SR=0.853, Win%=50.0, Med%=-0.08, AnnMean%=+24.63, Q75%=+26.79, MaxDD%=32.55, CVaR%=-55.91, Yrs+=4/5, N=152
- `bk50d_s20_v1.3_roc100` | `91d` — SR=0.683, Win%=54.6, Med%=+3.13, AnnMean%=+24.98, Q75%=+20.86, MaxDD%=24.47, CVaR%=-53.31, Yrs+=3/4, N=194
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.606, Win%=51.8, Med%=+1.44, AnnMean%=+18.38, Q75%=+26.15, MaxDD%=34.04, CVaR%=-59.12, Yrs+=4/5, N=166
- `bk50d_s17_v1.3_roc100` | `91d` — SR=0.547, Win%=54.9, Med%=+2.65, AnnMean%=+19.42, Q75%=+18.50, MaxDD%=24.26, CVaR%=-48.62, Yrs+=4/5, N=226
- `bk50d_s15_v1.3_roc100` | `91d` — SR=0.333, Win%=50.8, Med%=+0.18, AnnMean%=+11.72, Q75%=+16.09, MaxDD%=24.15, CVaR%=-50.03, Yrs+=4/5, N=254
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.300, Win%=52.6, Med%=+1.04, AnnMean%=+9.91, Q75%=+15.87, MaxDD%=23.22, CVaR%=-45.39, Yrs+=4/5, N=272

## Findings & Caveats

**RSI filter reverted to plain RSI<70**: v1.3 briefly widened the RSI filter to `RSI(14) < 70 OR RSI(14) > 80` (re-admitting extreme-momentum reentries; an A/B test on identical data showed the wider rule flat-to-better across every combination). The methodology doc has since reverted to plain `RSI(14) < 70` and this script, `QullamaggieStrategy`, and their docs/tests were reverted to match, so the reentry variant is no longer implemented anywhere in this pipeline.

**Fixed**: `close`/`high`/`low` are now split/dividend-adjusted (scaled by `adjusted_close/close`). The prior version used raw `close`, which shows a fake ~90% one-day move on a stock's split date (e.g. NVDA's 2024-06-10 10:1 split) — this corrupted rolling indicators for ~50 days around any split and could make a real winning trade compute as a huge loss (or vice versa for a reverse split). 13.1% of the qualifying universe (254/1,943 tickers) had at least one such split event since 2020. The MIN_PRICE/MAX_PRICE band still uses raw (unadjusted) close, since that's the real price a trader would have paid on the entry date — adjusting it would leak knowledge of future splits into a point-in-time filter.

**Unresolved — survivorship bias**: every ticker in the qualifying universe has `status='active'`; the pipeline retains no delisted/bankrupt/acquired tickers. `company.market_cap` is also a single current-day snapshot applied retroactively to all history, not a point-in-time value. A momentum-breakout strategy specifically targets stocks that sometimes blow up afterward (fraud, failed trial, acquisition below entry) — those trades are structurally impossible to appear in this backtest. This likely explains part of the unusually high win rate/profit factor and should be treated as a ceiling on how much to trust the absolute return numbers.

**Partially addressed — overlapping trades**: at several signals/month with 6-12 month holds, most trades are open concurrently and share the same regime exposure, so the unconstrained N overstates the number of independent bets and the Sortino/consistency stats overstate statistical confidence. The 'Max 30 and 20 Concurrent Positions' tables above cap the portfolio at that many simultaneous positions (FIFO signal acceptance) as a rough realism check — comparing the tables shows how much each combination's apparent edge depends on taking every single signal versus a capital-constrained subset. This doesn't fix the underlying correlation between trades still held concurrently within a cap, and it uses an arbitrary FIFO rule rather than a real signal-quality ranking for which trade to take when capacity is full.

**Unresolved — regime concentration**: the SPY>200d SMA filter concentrates trades in bull years. The Yrs+ denominator silently drops any complete calendar year with <10 losing trades from its count (see the Yrs+ column above, e.g. a stricter signal with fewer total trades may show fewer valid years than the number of complete calendar years in the eval period), which can exclude harder regimes rather than prove the strategy survived them.

**Unresolved — no execution costs**: entry is assumed fillable at the same close that generated the signal, with no slippage, spread, commissions, or gap risk — unrealistic for breakout-day fills on high-ADR names.

**Ideas to improve**: source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot; source a delisted-ticker history if available to address survivorship; shift entry to next-day open (+ slippage assumption) for realistic fills; replace the FIFO acceptance rule in the capacity-constrained table with a real signal-quality ranking (e.g. ADR%, breakout strength) to pick which trade to take when capacity is full; account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence.
