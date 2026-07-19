# Qullamaggie Backtest v4 — Results

Run date: 2026-07-19

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
| RSI | RSI(14) < 70 or > 80 (70-80 band excluded) |
| ADR | mean((high-low)/low, last 20d, shift-1) ≥ 3.0% |
| ADR change | ADR%(10d) / ADR%(50d) < 90% |
| SMA alignment | disabled (commented out) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | ≥ 500K |
| Min history | ≥ 300 trading days |
| Cooldown | 30 calendar days |
| Eval period | 2021-01-01 – 2026-07-19 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```text
Period: 2021-01-01 – 2026-07-19  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70 or >80, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.3_roc100            366d   532   65.4   +54.72    +54.53   +20.88   +77.29   6.68    2.765    40.09   -61.58    8.1    5/5  ✓
   2  bk50d_s17_v1.3_roc100            366d   760   63.0   +44.75    +44.60   +15.53   +64.92   5.45    2.251    39.59   -59.95   11.5    5/5  ✓
   3  bk50d_s15_v1.3_roc100            366d   948   63.5   +41.50    +41.37   +17.56   +60.76   5.15    2.082    38.89   -60.38   14.4    5/5  ✓
   4  bk50d_s12_v1.3_roc100            366d  1247   63.0   +37.44    +37.32   +14.72   +56.95   4.70    1.862    38.26   -61.18   18.9    5/5  ✓
   5  bk50d_s20_v1.3_roc100            184d   532   61.1   +20.39    +44.51   +10.41   +40.08   3.47    1.771    30.69   -48.39    8.1    5/5  ✓
   6  bk50d_s17_v1.3_roc100            184d   760   59.3   +16.13    +34.53    +8.23   +34.22   2.82    1.354    30.30   -49.10   11.5    4/5  ✓
   7  bk50d_s20_v1.3_roc100             91d   532   62.0    +9.17    +42.16    +6.42   +23.93   2.33    1.321    21.95   -43.16    8.1    5/5  ✓
   8  bk50d_s15_v1.3_roc100            184d   948   58.4   +14.44    +30.68    +7.12   +32.43   2.60    1.199    29.92   -49.53   14.4    4/5  ✓
   9  bk50d_s12_v1.3_roc100            184d  1247   57.7   +12.99    +27.42    +6.82   +30.71   2.46    1.087    29.28   -49.22   18.9    4/5  ✓
  10  bk50d_s17_v1.3_roc100             91d   760   60.7    +7.62    +34.24    +6.05   +22.30   2.05    1.078    21.53   -43.23   11.5    4/5  ✓
  11  bk50d_s15_v1.3_roc100             91d   948   59.4    +7.15    +31.90    +5.33   +22.26   1.98    1.018    21.24   -42.08   14.4    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d  1247   58.9    +6.27    +27.63    +4.73   +20.84   1.87    0.912    20.80   -41.03   18.9    4/5  ✓

Valid combinations: 12  |  Consistent: 12
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v1.3_roc100` | `366d` — SR=2.765, Win%=65.4, Med%=+20.88, AnnMean%=+54.53, Q75%=+77.29, MaxDD%=40.09, CVaR%=-61.58, Yrs+=5/5, N=532
- `bk50d_s17_v1.3_roc100` | `366d` — SR=2.251, Win%=63.0, Med%=+15.53, AnnMean%=+44.60, Q75%=+64.92, MaxDD%=39.59, CVaR%=-59.95, Yrs+=5/5, N=760
- `bk50d_s15_v1.3_roc100` | `366d` — SR=2.082, Win%=63.5, Med%=+17.56, AnnMean%=+41.37, Q75%=+60.76, MaxDD%=38.89, CVaR%=-60.38, Yrs+=5/5, N=948
- `bk50d_s12_v1.3_roc100` | `366d` — SR=1.862, Win%=63.0, Med%=+14.72, AnnMean%=+37.32, Q75%=+56.95, MaxDD%=38.26, CVaR%=-61.18, Yrs+=5/5, N=1247
- `bk50d_s20_v1.3_roc100` | `184d` — SR=1.771, Win%=61.1, Med%=+10.41, AnnMean%=+44.51, Q75%=+40.08, MaxDD%=30.69, CVaR%=-48.39, Yrs+=5/5, N=532
- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.354, Win%=59.3, Med%=+8.23, AnnMean%=+34.53, Q75%=+34.22, MaxDD%=30.30, CVaR%=-49.10, Yrs+=4/5, N=760
- `bk50d_s20_v1.3_roc100` | `91d` — SR=1.321, Win%=62.0, Med%=+6.42, AnnMean%=+42.16, Q75%=+23.93, MaxDD%=21.95, CVaR%=-43.16, Yrs+=5/5, N=532
- `bk50d_s15_v1.3_roc100` | `184d` — SR=1.199, Win%=58.4, Med%=+7.12, AnnMean%=+30.68, Q75%=+32.43, MaxDD%=29.92, CVaR%=-49.53, Yrs+=4/5, N=948
- `bk50d_s12_v1.3_roc100` | `184d` — SR=1.087, Win%=57.7, Med%=+6.82, AnnMean%=+27.42, Q75%=+30.71, MaxDD%=29.28, CVaR%=-49.22, Yrs+=4/5, N=1247
- `bk50d_s17_v1.3_roc100` | `91d` — SR=1.078, Win%=60.7, Med%=+6.05, AnnMean%=+34.24, Q75%=+22.30, MaxDD%=21.53, CVaR%=-43.23, Yrs+=4/5, N=760
- `bk50d_s15_v1.3_roc100` | `91d` — SR=1.018, Win%=59.4, Med%=+5.33, AnnMean%=+31.90, Q75%=+22.26, MaxDD%=21.24, CVaR%=-42.08, Yrs+=4/5, N=948
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.912, Win%=58.9, Med%=+4.73, AnnMean%=+27.63, Q75%=+20.84, MaxDD%=20.80, CVaR%=-41.03, Yrs+=4/5, N=1247

## Rankings — Max 30 Concurrent Positions

Same signals, but a trade is skipped if 30 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-19  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70 or >80, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 30

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.3_roc100            366d   150   63.3   +45.53    +45.38   +20.65   +68.02   5.15    2.085    40.63   -68.32    2.3    3/4  ✓
   2  bk50d_s20_v1.3_roc100            366d   139   64.7   +43.53    +43.38   +19.20   +72.88   4.83    1.888    41.60   -71.21    2.1    1/2   
   3  bk50d_s12_v1.3_roc100            366d   150   62.7   +35.74    +35.62   +14.15   +61.64   4.52    1.797    39.43   -63.65    2.3    3/3  ✓
   4  bk50d_s17_v1.3_roc100            366d   148   61.5   +41.91    +41.77   +14.30   +74.05   4.26    1.739    41.55   -69.43    2.2    3/4  ✓
   5  bk50d_s20_v1.3_roc100            184d   208   56.7   +16.26    +34.83    +6.53   +37.71   2.65    1.212    32.59   -57.03    3.2    2/3   
   6  bk50d_s17_v1.3_roc100            184d   218   56.9   +13.47    +28.49    +6.16   +30.91   2.49    1.073    31.50   -56.44    3.3    4/5  ✓
   7  bk50d_s15_v1.3_roc100            184d   220   53.6   +11.50    +24.09    +3.86   +31.13   2.13    0.864    31.45   -54.19    3.3    4/5  ✓
   8  bk50d_s12_v1.3_roc100            184d   233   53.6   +11.14    +23.32    +5.92   +26.56   2.09    0.843    32.02   -52.30    3.5    5/5  ✓
   9  bk50d_s20_v1.3_roc100             91d   283   54.8    +5.29    +22.95    +3.03   +23.83   1.62    0.664    23.93   -49.05    4.3    4/5  ✓
  10  bk50d_s17_v1.3_roc100             91d   334   54.5    +3.98    +16.97    +2.72   +18.86   1.44    0.494    23.47   -47.26    5.1    4/5  ✓
  11  bk50d_s15_v1.3_roc100             91d   367   53.7    +3.77    +15.99    +1.80   +18.99   1.41    0.464    23.15   -46.91    5.6    4/5  ✓
  12  bk50d_s12_v1.3_roc100             91d   402   54.2    +3.05    +12.82    +2.34   +17.03   1.34    0.381    22.57   -45.98    6.1    4/5  ✓

Valid combinations: 12  |  Consistent: 10
```

## Consistent Combinations (Max 30 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s15_v1.3_roc100` | `366d` — SR=2.085, Win%=63.3, Med%=+20.65, AnnMean%=+45.38, Q75%=+68.02, MaxDD%=40.63, CVaR%=-68.32, Yrs+=3/4, N=150
- `bk50d_s12_v1.3_roc100` | `366d` — SR=1.797, Win%=62.7, Med%=+14.15, AnnMean%=+35.62, Q75%=+61.64, MaxDD%=39.43, CVaR%=-63.65, Yrs+=3/3, N=150
- `bk50d_s17_v1.3_roc100` | `366d` — SR=1.739, Win%=61.5, Med%=+14.30, AnnMean%=+41.77, Q75%=+74.05, MaxDD%=41.55, CVaR%=-69.43, Yrs+=3/4, N=148
- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.073, Win%=56.9, Med%=+6.16, AnnMean%=+28.49, Q75%=+30.91, MaxDD%=31.50, CVaR%=-56.44, Yrs+=4/5, N=218
- `bk50d_s15_v1.3_roc100` | `184d` — SR=0.864, Win%=53.6, Med%=+3.86, AnnMean%=+24.09, Q75%=+31.13, MaxDD%=31.45, CVaR%=-54.19, Yrs+=4/5, N=220
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.843, Win%=53.6, Med%=+5.92, AnnMean%=+23.32, Q75%=+26.56, MaxDD%=32.02, CVaR%=-52.30, Yrs+=5/5, N=233
- `bk50d_s20_v1.3_roc100` | `91d` — SR=0.664, Win%=54.8, Med%=+3.03, AnnMean%=+22.95, Q75%=+23.83, MaxDD%=23.93, CVaR%=-49.05, Yrs+=4/5, N=283
- `bk50d_s17_v1.3_roc100` | `91d` — SR=0.494, Win%=54.5, Med%=+2.72, AnnMean%=+16.97, Q75%=+18.86, MaxDD%=23.47, CVaR%=-47.26, Yrs+=4/5, N=334
- `bk50d_s15_v1.3_roc100` | `91d` — SR=0.464, Win%=53.7, Med%=+1.80, AnnMean%=+15.99, Q75%=+18.99, MaxDD%=23.15, CVaR%=-46.91, Yrs+=4/5, N=367
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.381, Win%=54.2, Med%=+2.34, AnnMean%=+12.82, Q75%=+17.03, MaxDD%=22.57, CVaR%=-45.98, Yrs+=4/5, N=402

## Rankings — Max 20 Concurrent Positions

Same signals, but a trade is skipped if 20 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-19  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70 or >80, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 20

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.3_roc100            366d   100   64.0   +45.60    +45.45   +20.65   +63.64   5.43    2.155    39.95   -69.83    1.5    0/1   
   2  bk50d_s20_v1.3_roc100            366d    99   63.6   +49.05    +48.89   +21.28   +90.31   4.81    1.948    43.11   -74.88    1.5    0/1   
   3  bk50d_s12_v1.3_roc100            366d   100   60.0   +35.87    +35.75   +10.45   +61.23   4.56    1.886    39.44   -58.51    1.5    1/1   
   4  bk50d_s17_v1.3_roc100            366d   100   63.0   +41.94    +41.80   +17.80   +75.20   4.39    1.783    41.48   -70.16    1.5    0/1   
   5  bk50d_s20_v1.3_roc100            184d   145   56.6   +17.94    +38.71    +7.07   +40.82   2.89    1.339    32.55   -60.29    2.2    2/3   
   6  bk50d_s17_v1.3_roc100            184d   148   58.1   +17.14    +36.85    +6.82   +35.44   2.88    1.305    31.93   -59.32    2.2    3/4  ✓
   7  bk50d_s15_v1.3_roc100            184d   150   50.0   +10.76    +22.47    -0.08   +26.36   1.98    0.776    32.87   -56.41    2.3    4/5  ✓
   8  bk50d_s12_v1.3_roc100            184d   163   52.1   +10.01    +20.83    +1.69   +26.48   1.88    0.707    33.74   -55.32    2.5    4/5  ✓
   9  bk50d_s12_v1.3_roc100             91d   273   56.0    +4.02    +17.13    +3.11   +17.28   1.49    0.544    22.15   -42.97    4.1    4/4  ✓
  10  bk50d_s20_v1.3_roc100             91d   217   51.6    +4.47    +19.16    +1.80   +22.80   1.46    0.516    24.42   -52.40    3.3    4/5  ✓
  11  bk50d_s17_v1.3_roc100             91d   242   53.7    +3.69    +15.64    +2.39   +18.46   1.39    0.434    23.75   -49.89    3.7    4/5  ✓
  12  bk50d_s15_v1.3_roc100             91d   260   52.3    +3.06    +12.85    +0.99   +17.83   1.32    0.361    23.92   -49.63    3.9    3/5   

Valid combinations: 12  |  Consistent: 6
```

## Consistent Combinations (Max 20 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s17_v1.3_roc100` | `184d` — SR=1.305, Win%=58.1, Med%=+6.82, AnnMean%=+36.85, Q75%=+35.44, MaxDD%=31.93, CVaR%=-59.32, Yrs+=3/4, N=148
- `bk50d_s15_v1.3_roc100` | `184d` — SR=0.776, Win%=50.0, Med%=-0.08, AnnMean%=+22.47, Q75%=+26.36, MaxDD%=32.87, CVaR%=-56.41, Yrs+=4/5, N=150
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.707, Win%=52.1, Med%=+1.69, AnnMean%=+20.83, Q75%=+26.48, MaxDD%=33.74, CVaR%=-55.32, Yrs+=4/5, N=163
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.544, Win%=56.0, Med%=+3.11, AnnMean%=+17.13, Q75%=+17.28, MaxDD%=22.15, CVaR%=-42.97, Yrs+=4/4, N=273
- `bk50d_s20_v1.3_roc100` | `91d` — SR=0.516, Win%=51.6, Med%=+1.80, AnnMean%=+19.16, Q75%=+22.80, MaxDD%=24.42, CVaR%=-52.40, Yrs+=4/5, N=217
- `bk50d_s17_v1.3_roc100` | `91d` — SR=0.434, Win%=53.7, Med%=+2.39, AnnMean%=+15.64, Q75%=+18.46, MaxDD%=23.75, CVaR%=-49.89, Yrs+=4/5, N=242

## Findings & Caveats

**Changed in v1.3**: the RSI filter now follows the spec formula `RSI(14) < 70 OR RSI(14) > 80` — only the 70-80 band is excluded, re-admitting extreme-momentum entries. All v1.2 artifacts (cohort docs, QullamaggieStrategy) used plain RSI < 70, so v1.3 numbers are not directly comparable to them.

**Fixed**: `close`/`high`/`low` are now split/dividend-adjusted (scaled by `adjusted_close/close`). The prior version used raw `close`, which shows a fake ~90% one-day move on a stock's split date (e.g. NVDA's 2024-06-10 10:1 split) — this corrupted rolling indicators for ~50 days around any split and could make a real winning trade compute as a huge loss (or vice versa for a reverse split). 13.1% of the qualifying universe (254/1,943 tickers) had at least one such split event since 2020. The MIN_PRICE/MAX_PRICE band still uses raw (unadjusted) close, since that's the real price a trader would have paid on the entry date — adjusting it would leak knowledge of future splits into a point-in-time filter.

**Unresolved — survivorship bias**: every ticker in the qualifying universe has `status='active'`; the pipeline retains no delisted/bankrupt/acquired tickers. `company.market_cap` is also a single current-day snapshot applied retroactively to all history, not a point-in-time value. A momentum-breakout strategy specifically targets stocks that sometimes blow up afterward (fraud, failed trial, acquisition below entry) — those trades are structurally impossible to appear in this backtest. This likely explains part of the unusually high win rate/profit factor and should be treated as a ceiling on how much to trust the absolute return numbers.

**Partially addressed — overlapping trades**: at several signals/month with 6-12 month holds, most trades are open concurrently and share the same regime exposure, so the unconstrained N overstates the number of independent bets and the Sortino/consistency stats overstate statistical confidence. The 'Max 30 and 20 Concurrent Positions' tables above cap the portfolio at that many simultaneous positions (FIFO signal acceptance) as a rough realism check — comparing the tables shows how much each combination's apparent edge depends on taking every single signal versus a capital-constrained subset. This doesn't fix the underlying correlation between trades still held concurrently within a cap, and it uses an arbitrary FIFO rule rather than a real signal-quality ranking for which trade to take when capacity is full.

**Unresolved — regime concentration**: the SPY>200d SMA filter concentrates trades in bull years. The Yrs+ denominator silently drops any complete calendar year with <10 losing trades from its count (see the Yrs+ column above, e.g. a stricter signal with fewer total trades may show fewer valid years than the number of complete calendar years in the eval period), which can exclude harder regimes rather than prove the strategy survived them.

**Unresolved — no execution costs**: entry is assumed fillable at the same close that generated the signal, with no slippage, spread, commissions, or gap risk — unrealistic for breakout-day fills on high-ADR names.

**Ideas to improve**: source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot; source a delisted-ticker history if available to address survivorship; shift entry to next-day open (+ slippage assumption) for realistic fills; replace the FIFO acceptance rule in the capacity-constrained table with a real signal-quality ranking (e.g. ADR%, breakout strength) to pick which trade to take when capacity is full; account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence.
