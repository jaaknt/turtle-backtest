# Qullamaggie Backtest v4 — Results

Run date: 2026-07-22

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
| Eval period | 2021-01-01 – 2026-07-22 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```text
Period: 2021-01-01 – 2026-07-22  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.3_roc100            366d   398   65.6   +53.43    +53.25   +20.88   +77.33   6.69    2.730    40.93   -62.90    6.0    5/5  ✓
   2  bk50d_s17_v1.3_roc100            366d   572   63.8   +45.74    +45.59   +18.08   +65.49   5.64    2.306    40.20   -61.28    8.7    5/5  ✓
   3  bk50d_s15_v1.3_roc100            366d   739   64.3   +42.19    +42.05   +18.45   +60.62   5.38    2.150    39.10   -61.08   11.2    5/5  ✓
   4  bk50d_s12_v1.3_roc100            366d  1002   62.7   +36.83    +36.71   +14.61   +55.04   4.71    1.859    38.57   -60.64   15.2    5/5  ✓
   5  bk50d_s20_v1.3_roc100            184d   398   60.6   +20.47    +44.68   +10.19   +40.92   3.42    1.729    31.72   -49.83    6.0    5/5  ✓
   6  bk50d_s20_v1.3_roc100             91d   398   62.3    +9.29    +42.80    +6.27   +23.90   2.34    1.311    22.66   -44.76    6.0    5/5  ✓
   7  bk50d_s17_v1.3_roc100            184d   572   58.6   +16.14    +34.56    +7.85   +34.67   2.74    1.300    31.31   -50.91    8.7    5/5  ✓
   8  bk50d_s15_v1.3_roc100            184d   739   58.1   +14.55    +30.93    +7.32   +32.44   2.58    1.185    30.53   -50.49   11.2    5/5  ✓
   9  bk50d_s12_v1.3_roc100            184d  1002   56.2   +12.58    +26.50    +6.07   +29.95   2.36    1.039    29.98   -49.20   15.2    5/5  ✓
  10  bk50d_s15_v1.3_roc100             91d   739   59.5    +7.22    +32.25    +5.17   +21.36   1.97    1.018    21.63   -42.21   11.2    4/5  ✓
  11  bk50d_s17_v1.3_roc100             91d   572   60.5    +7.22    +32.25    +5.51   +21.10   1.96    0.985    22.31   -44.63    8.7    3/5   
  12  bk50d_s12_v1.3_roc100             91d  1002   58.1    +6.10    +26.81    +4.26   +20.03   1.82    0.875    21.24   -41.18   15.2    4/5  ✓

Valid combinations: 12  |  Consistent: 11
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v1.3_roc100` | `366d` — SR=2.730, Win%=65.6, Med%=+20.88, AnnMean%=+53.25, Q75%=+77.33, MaxDD%=40.93, CVaR%=-62.90, Yrs+=5/5, N=398
- `bk50d_s17_v1.3_roc100` | `366d` — SR=2.306, Win%=63.8, Med%=+18.08, AnnMean%=+45.59, Q75%=+65.49, MaxDD%=40.20, CVaR%=-61.28, Yrs+=5/5, N=572
- `bk50d_s15_v1.3_roc100` | `366d` — SR=2.150, Win%=64.3, Med%=+18.45, AnnMean%=+42.05, Q75%=+60.62, MaxDD%=39.10, CVaR%=-61.08, Yrs+=5/5, N=739
- `bk50d_s12_v1.3_roc100` | `366d` — SR=1.859, Win%=62.7, Med%=+14.61, AnnMean%=+36.71, Q75%=+55.04, MaxDD%=38.57, CVaR%=-60.64, Yrs+=5/5, N=1002
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.729, Win%=60.6, Med%=+10.19, AnnMean%=+44.68, Q75%=+40.92, MaxDD%=31.72, CVaR%=-49.83, Yrs+=5/5, N=398
- `bk50d_s20_v1.3_roc100` | `91d` — SR=1.311, Win%=62.3, Med%=+6.27, AnnMean%=+42.80, Q75%=+23.90, MaxDD%=22.66, CVaR%=-44.76, Yrs+=5/5, N=398
- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.300, Win%=58.6, Med%=+7.85, AnnMean%=+34.56, Q75%=+34.67, MaxDD%=31.31, CVaR%=-50.91, Yrs+=5/5, N=572
- `bk50d_s15_v1.3_roc100` | `184d` — SR=1.185, Win%=58.1, Med%=+7.32, AnnMean%=+30.93, Q75%=+32.44, MaxDD%=30.53, CVaR%=-50.49, Yrs+=5/5, N=739
- `bk50d_s12_v1.3_roc100` | `184d` — SR=1.039, Win%=56.2, Med%=+6.07, AnnMean%=+26.50, Q75%=+29.95, MaxDD%=29.98, CVaR%=-49.20, Yrs+=5/5, N=1002
- `bk50d_s15_v1.3_roc100` | `91d` — SR=1.018, Win%=59.5, Med%=+5.17, AnnMean%=+32.25, Q75%=+21.36, MaxDD%=21.63, CVaR%=-42.21, Yrs+=4/5, N=739
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.875, Win%=58.1, Med%=+4.26, AnnMean%=+26.81, Q75%=+20.03, MaxDD%=21.24, CVaR%=-41.18, Yrs+=4/5, N=1002

## Rankings — Max 30 Concurrent Positions

Same signals, but a trade is skipped if 30 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-22  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 30

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.3_roc100            366d   133   65.4   +46.03    +45.88   +22.32   +77.36   5.49    2.140    41.30   -69.82    2.0    1/2   
   2  bk50d_s17_v1.3_roc100            366d   138   68.1   +36.48    +36.36   +18.29   +64.17   4.92    1.831    39.98   -69.82    2.1    0/1   
   3  bk50d_s15_v1.3_roc100            366d   148   60.8   +38.30    +38.18   +14.30   +69.53   4.50    1.800    40.74   -67.29    2.2    2/3   
   4  bk50d_s12_v1.3_roc100            366d   150   64.0   +33.78    +33.68   +14.11   +60.15   4.51    1.731    39.46   -64.18    2.3    3/3  ✓
   5  bk50d_s17_v1.3_roc100            184d   210   56.7   +16.53    +35.45    +6.43   +34.33   2.81    1.312    31.46   -55.86    3.2    4/5  ✓
   6  bk50d_s20_v1.3_roc100            184d   201   55.2   +16.42    +35.19    +5.20   +36.58   2.63    1.219    33.56   -56.95    3.0    4/4  ✓
   7  bk50d_s15_v1.3_roc100            184d   221   52.5   +13.77    +29.17    +1.99   +32.04   2.33    1.038    31.77   -53.83    3.3    4/5  ✓
   8  bk50d_s20_v1.3_roc100             91d   249   57.0    +6.29    +27.71    +3.39   +22.80   1.79    0.809    23.70   -48.99    3.8    3/4  ✓
   9  bk50d_s12_v1.3_roc100            184d   235   51.9   +10.24    +21.34    +1.69   +26.48   1.98    0.772    32.17   -52.47    3.6    5/5  ✓
  10  bk50d_s15_v1.3_roc100             91d   345   53.9    +4.63    +19.91    +2.09   +17.56   1.54    0.596    23.11   -44.90    5.2    4/5  ✓
  11  bk50d_s17_v1.3_roc100             91d   306   55.9    +4.60    +19.79    +3.13   +18.05   1.53    0.582    23.43   -47.16    4.6    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d   393   51.1    +2.11     +8.75    +0.39   +15.37   1.23    0.264    23.45   -45.12    6.0    4/5  ✓

Valid combinations: 12  |  Consistent: 9
```

## Consistent Combinations (Max 30 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s12_v1.3_roc100` | `366d` — SR=1.731, Win%=64.0, Med%=+14.11, AnnMean%=+33.68, Q75%=+60.15, MaxDD%=39.46, CVaR%=-64.18, Yrs+=3/3, N=150
- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.312, Win%=56.7, Med%=+6.43, AnnMean%=+35.45, Q75%=+34.33, MaxDD%=31.46, CVaR%=-55.86, Yrs+=4/5, N=210
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.219, Win%=55.2, Med%=+5.20, AnnMean%=+35.19, Q75%=+36.58, MaxDD%=33.56, CVaR%=-56.95, Yrs+=4/4, N=201
- `bk50d_s15_v1.3_roc100` | `184d` — SR=1.038, Win%=52.5, Med%=+1.99, AnnMean%=+29.17, Q75%=+32.04, MaxDD%=31.77, CVaR%=-53.83, Yrs+=4/5, N=221
- `bk50d_s20_v1.3_roc100` | `91d` — SR=0.809, Win%=57.0, Med%=+3.39, AnnMean%=+27.71, Q75%=+22.80, MaxDD%=23.70, CVaR%=-48.99, Yrs+=3/4, N=249
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.772, Win%=51.9, Med%=+1.69, AnnMean%=+21.34, Q75%=+26.48, MaxDD%=32.17, CVaR%=-52.47, Yrs+=5/5, N=235
- `bk50d_s15_v1.3_roc100` | `91d` — SR=0.596, Win%=53.9, Med%=+2.09, AnnMean%=+19.91, Q75%=+17.56, MaxDD%=23.11, CVaR%=-44.90, Yrs+=4/5, N=345
- `bk50d_s17_v1.3_roc100` | `91d` — SR=0.582, Win%=55.9, Med%=+3.13, AnnMean%=+19.79, Q75%=+18.05, MaxDD%=23.43, CVaR%=-47.16, Yrs+=4/5, N=306
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.264, Win%=51.1, Med%=+0.39, AnnMean%=+8.75, Q75%=+15.37, MaxDD%=23.45, CVaR%=-45.12, Yrs+=4/5, N=393

## Rankings — Max 20 Concurrent Positions

Same signals, but a trade is skipped if 20 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-22  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 20

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.3_roc100            366d   100   62.0   +40.21    +40.08   +16.88   +71.80   4.63    1.831    41.88   -71.55    1.5    1/2   
   2  bk50d_s17_v1.3_roc100            366d    98   64.3   +37.81    +37.69   +17.51   +68.80   4.25    1.652    42.20   -73.93    1.5    0/1   
   3  bk50d_s20_v1.3_roc100            366d    93   63.4   +35.84    +35.73   +16.28   +77.27   4.19    1.553    43.34   -73.93    1.4    0/1   
   4  bk50d_s17_v1.3_roc100            184d   149   55.7   +17.55    +37.82    +6.29   +35.54   2.90    1.383    32.44   -56.05    2.3    3/4  ✓
   5  bk50d_s12_v1.3_roc100            366d   100   58.0   +26.08    +26.00    +6.58   +42.32   3.49    1.313    40.43   -62.71    1.5    1/2   
   6  bk50d_s20_v1.3_roc100            184d   141   53.9   +16.80    +36.08    +5.20   +38.93   2.76    1.274    33.25   -58.33    2.1    3/4  ✓
   7  bk50d_s15_v1.3_roc100            184d   151   50.3   +12.20    +25.65    +0.13   +26.91   2.16    0.910    32.51   -54.53    2.3    4/5  ✓
   8  bk50d_s20_v1.3_roc100             91d   194   54.6    +5.79    +25.33    +3.13   +20.86   1.66    0.702    24.42   -51.73    2.9    3/4  ✓
   9  bk50d_s12_v1.3_roc100            184d   165   51.5    +9.40    +19.51    +1.19   +26.24   1.83    0.669    33.85   -55.32    2.5    4/5  ✓
  10  bk50d_s17_v1.3_roc100             91d   228   54.4    +4.11    +17.54    +2.39   +18.26   1.43    0.485    24.51   -49.11    3.5    4/5  ✓
  11  bk50d_s15_v1.3_roc100             91d   254   50.8    +2.95    +12.39    +0.18   +16.25   1.31    0.355    24.13   -48.22    3.8    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d   272   52.6    +2.49    +10.39    +1.04   +15.87   1.28    0.321    23.20   -43.38    4.1    4/5  ✓

Valid combinations: 12  |  Consistent: 8
```

## Consistent Combinations (Max 20 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.383, Win%=55.7, Med%=+6.29, AnnMean%=+37.82, Q75%=+35.54, MaxDD%=32.44, CVaR%=-56.05, Yrs+=3/4, N=149
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.274, Win%=53.9, Med%=+5.20, AnnMean%=+36.08, Q75%=+38.93, MaxDD%=33.25, CVaR%=-58.33, Yrs+=3/4, N=141
- `bk50d_s15_v1.3_roc100` | `184d` — SR=0.910, Win%=50.3, Med%=+0.13, AnnMean%=+25.65, Q75%=+26.91, MaxDD%=32.51, CVaR%=-54.53, Yrs+=4/5, N=151
- `bk50d_s20_v1.3_roc100` | `91d` — SR=0.702, Win%=54.6, Med%=+3.13, AnnMean%=+25.33, Q75%=+20.86, MaxDD%=24.42, CVaR%=-51.73, Yrs+=3/4, N=194
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.669, Win%=51.5, Med%=+1.19, AnnMean%=+19.51, Q75%=+26.24, MaxDD%=33.85, CVaR%=-55.32, Yrs+=4/5, N=165
- `bk50d_s17_v1.3_roc100` | `91d` — SR=0.485, Win%=54.4, Med%=+2.39, AnnMean%=+17.54, Q75%=+18.26, MaxDD%=24.51, CVaR%=-49.11, Yrs+=4/5, N=228
- `bk50d_s15_v1.3_roc100` | `91d` — SR=0.355, Win%=50.8, Med%=+0.18, AnnMean%=+12.39, Q75%=+16.25, MaxDD%=24.13, CVaR%=-48.22, Yrs+=4/5, N=254
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.321, Win%=52.6, Med%=+1.04, AnnMean%=+10.39, Q75%=+15.87, MaxDD%=23.20, CVaR%=-43.38, Yrs+=4/5, N=272

## Findings & Caveats

**RSI filter reverted to plain RSI<70**: v1.3 briefly widened the RSI filter to `RSI(14) < 70 OR RSI(14) > 80` (re-admitting extreme-momentum reentries; an A/B test on identical data showed the wider rule flat-to-better across every combination). The methodology doc has since reverted to plain `RSI(14) < 70` and this script, `QullamaggieStrategy`, and their docs/tests were reverted to match, so the reentry variant is no longer implemented anywhere in this pipeline.

**Fixed**: `close`/`high`/`low` are now split/dividend-adjusted (scaled by `adjusted_close/close`). The prior version used raw `close`, which shows a fake ~90% one-day move on a stock's split date (e.g. NVDA's 2024-06-10 10:1 split) — this corrupted rolling indicators for ~50 days around any split and could make a real winning trade compute as a huge loss (or vice versa for a reverse split). 13.1% of the qualifying universe (254/1,943 tickers) had at least one such split event since 2020. The MIN_PRICE/MAX_PRICE band still uses raw (unadjusted) close, since that's the real price a trader would have paid on the entry date — adjusting it would leak knowledge of future splits into a point-in-time filter.

**Unresolved — survivorship bias**: every ticker in the qualifying universe has `status='active'`; the pipeline retains no delisted/bankrupt/acquired tickers. `company.market_cap` is also a single current-day snapshot applied retroactively to all history, not a point-in-time value. A momentum-breakout strategy specifically targets stocks that sometimes blow up afterward (fraud, failed trial, acquisition below entry) — those trades are structurally impossible to appear in this backtest. This likely explains part of the unusually high win rate/profit factor and should be treated as a ceiling on how much to trust the absolute return numbers.

**Partially addressed — overlapping trades**: at several signals/month with 6-12 month holds, most trades are open concurrently and share the same regime exposure, so the unconstrained N overstates the number of independent bets and the Sortino/consistency stats overstate statistical confidence. The 'Max 30 and 20 Concurrent Positions' tables above cap the portfolio at that many simultaneous positions (FIFO signal acceptance) as a rough realism check — comparing the tables shows how much each combination's apparent edge depends on taking every single signal versus a capital-constrained subset. This doesn't fix the underlying correlation between trades still held concurrently within a cap, and it uses an arbitrary FIFO rule rather than a real signal-quality ranking for which trade to take when capacity is full.

**Unresolved — regime concentration**: the SPY>200d SMA filter concentrates trades in bull years. The Yrs+ denominator silently drops any complete calendar year with <10 losing trades from its count (see the Yrs+ column above, e.g. a stricter signal with fewer total trades may show fewer valid years than the number of complete calendar years in the eval period), which can exclude harder regimes rather than prove the strategy survived them.

**Unresolved — no execution costs**: entry is assumed fillable at the same close that generated the signal, with no slippage, spread, commissions, or gap risk — unrealistic for breakout-day fills on high-ADR names.

**Ideas to improve**: source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot; source a delisted-ticker history if available to address survivorship; shift entry to next-day open (+ slippage assumption) for realistic fills; replace the FIFO acceptance rule in the capacity-constrained table with a real signal-quality ranking (e.g. ADR%, breakout strength) to pick which trade to take when capacity is full; account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence.
