# Qullamaggie Backtest v4 — Results

Run date: 2026-07-14

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
| Eval period | 2021-01-01 – 2026-07-14 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```text
Period: 2021-01-01 – 2026-07-14  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.2_roc100            366d   361   66.8   +55.34    +55.15   +23.53   +80.68   7.41    3.020    40.34   -58.76    5.5    5/5  ✓
   2  bk50d_s17_v1.2_roc100            366d   522   65.1   +46.39    +46.24   +18.84   +69.19   6.05    2.466    39.61   -58.38    7.9    5/5  ✓
   3  bk50d_s15_v1.2_roc100            366d   679   65.4   +42.33    +42.20   +19.77   +61.63   5.69    2.276    38.60   -58.08   10.3    5/5  ✓
   4  bk50d_s12_v1.2_roc100            366d   927   63.5   +36.79    +36.67   +16.14   +55.30   4.97    1.968    38.01   -57.19   14.0    5/5  ✓
   5  bk50d_s20_v1.2_roc100            184d   361   61.5   +21.14    +46.29   +11.00   +42.25   3.51    1.789    31.40   -49.65    5.5    5/5  ✓
   6  bk50d_s17_v1.2_roc100            184d   522   59.6   +17.06    +36.69    +8.38   +36.30   2.89    1.405    30.77   -50.20    7.9    5/5  ✓
   7  bk50d_s20_v1.2_roc100             91d   361   62.6    +9.54    +44.13    +6.59   +23.95   2.45    1.396    22.38   -42.44    5.5    5/5  ✓
   8  bk50d_s15_v1.2_roc100            184d   679   59.1   +15.11    +32.19    +7.54   +32.57   2.69    1.258    29.97   -49.55   10.3    4/5  ✓
   9  bk50d_s17_v1.2_roc100             91d   522   61.3    +7.82    +35.23    +6.17   +21.77   2.10    1.112    21.83   -43.06    7.9    5/5  ✓
  10  bk50d_s12_v1.2_roc100            184d   927   56.9   +12.89    +27.19    +6.19   +29.73   2.43    1.085    29.48   -48.36   14.0    4/5  ✓
  11  bk50d_s15_v1.2_roc100             91d   679   59.9    +7.41    +33.19    +5.43   +21.39   2.05    1.081    21.18   -41.09   10.3    4/5  ✓
  12  bk50d_s12_v1.2_roc100             91d   927   58.3    +6.16    +27.10    +4.45   +20.03   1.86    0.906    20.87   -40.40   14.0    4/5  ✓

Valid combinations: 12  |  Consistent: 12
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v1.2_roc100` | `366d` — SR=3.020, Win%=66.8, Med%=+23.53, AnnMean%=+55.15, Q75%=+80.68, MaxDD%=40.34, CVaR%=-58.76, Yrs+=5/5, N=361
- `bk50d_s17_v1.2_roc100` | `366d` — SR=2.466, Win%=65.1, Med%=+18.84, AnnMean%=+46.24, Q75%=+69.19, MaxDD%=39.61, CVaR%=-58.38, Yrs+=5/5, N=522
- `bk50d_s15_v1.2_roc100` | `366d` — SR=2.276, Win%=65.4, Med%=+19.77, AnnMean%=+42.20, Q75%=+61.63, MaxDD%=38.60, CVaR%=-58.08, Yrs+=5/5, N=679
- `bk50d_s12_v1.2_roc100` | `366d` — SR=1.968, Win%=63.5, Med%=+16.14, AnnMean%=+36.67, Q75%=+55.30, MaxDD%=38.01, CVaR%=-57.19, Yrs+=5/5, N=927
- `bk50d_s20_v1.2_roc100` | `184d` — SR=1.789, Win%=61.5, Med%=+11.00, AnnMean%=+46.29, Q75%=+42.25, MaxDD%=31.40, CVaR%=-49.65, Yrs+=5/5, N=361
- `bk50d_s17_v1.2_roc100` | `184d` — SR=1.405, Win%=59.6, Med%=+8.38, AnnMean%=+36.69, Q75%=+36.30, MaxDD%=30.77, CVaR%=-50.20, Yrs+=5/5, N=522
- `bk50d_s20_v1.2_roc100` | `91d` — SR=1.396, Win%=62.6, Med%=+6.59, AnnMean%=+44.13, Q75%=+23.95, MaxDD%=22.38, CVaR%=-42.44, Yrs+=5/5, N=361
- `bk50d_s15_v1.2_roc100` | `184d` — SR=1.258, Win%=59.1, Med%=+7.54, AnnMean%=+32.19, Q75%=+32.57, MaxDD%=29.97, CVaR%=-49.55, Yrs+=4/5, N=679
- `bk50d_s17_v1.2_roc100` | `91d` — SR=1.112, Win%=61.3, Med%=+6.17, AnnMean%=+35.23, Q75%=+21.77, MaxDD%=21.83, CVaR%=-43.06, Yrs+=5/5, N=522
- `bk50d_s12_v1.2_roc100` | `184d` — SR=1.085, Win%=56.9, Med%=+6.19, AnnMean%=+27.19, Q75%=+29.73, MaxDD%=29.48, CVaR%=-48.36, Yrs+=4/5, N=927
- `bk50d_s15_v1.2_roc100` | `91d` — SR=1.081, Win%=59.9, Med%=+5.43, AnnMean%=+33.19, Q75%=+21.39, MaxDD%=21.18, CVaR%=-41.09, Yrs+=4/5, N=679
- `bk50d_s12_v1.2_roc100` | `91d` — SR=0.906, Win%=58.3, Med%=+4.45, AnnMean%=+27.10, Q75%=+20.03, MaxDD%=20.87, CVaR%=-40.40, Yrs+=4/5, N=927

## Rankings — Max 30 Concurrent Positions

Same signals, but a trade is skipped if 30 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-14  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 30

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.2_roc100            366d   131   67.9   +55.11    +54.92   +25.62   +80.31   6.75    2.658    39.97   -69.36    2.0    2/2   
   2  bk50d_s15_v1.2_roc100            366d   145   63.4   +40.67    +40.54   +18.08   +71.01   5.24    2.070    40.01   -64.76    2.2    3/3  ✓
   3  bk50d_s17_v1.2_roc100            366d   135   68.1   +35.45    +35.34   +21.15   +68.21   4.97    1.849    39.41   -66.86    2.0    1/2   
   4  bk50d_s17_v1.2_roc100            184d   204   60.3   +20.02    +43.62   +10.11   +37.71   3.40    1.680    30.39   -52.41    3.1    3/4  ✓
   5  bk50d_s12_v1.2_roc100            366d   150   61.3   +31.09    +30.99   +12.14   +60.49   4.13    1.580    40.16   -63.89    2.3    3/3  ✓
   6  bk50d_s20_v1.2_roc100            184d   198   59.1   +18.68    +40.47    +7.02   +38.69   2.99    1.437    32.41   -57.38    3.0    3/3  ✓
   7  bk50d_s15_v1.2_roc100            184d   218   54.6   +14.96    +31.86    +6.21   +33.78   2.46    1.130    31.68   -53.90    3.3    4/5  ✓
   8  bk50d_s20_v1.2_roc100             91d   242   59.5    +7.20    +32.15    +5.19   +23.03   2.00    0.982    23.04   -47.09    3.7    3/3  ✓
   9  bk50d_s17_v1.2_roc100             91d   298   58.7    +5.96    +26.12    +4.11   +19.36   1.77    0.804    22.79   -45.95    4.5    4/5  ✓
  10  bk50d_s15_v1.2_roc100             91d   338   55.6    +5.84    +25.58    +2.94   +19.29   1.73    0.792    22.38   -43.90    5.1    4/5  ✓
  11  bk50d_s12_v1.2_roc100            184d   230   51.7    +9.19    +19.05    +1.58   +26.52   1.83    0.666    32.30   -53.68    3.5    4/5  ✓
  12  bk50d_s12_v1.2_roc100             91d   389   53.2    +3.32    +14.01    +1.52   +16.01   1.39    0.432    22.89   -44.82    5.9    4/5  ✓

Valid combinations: 12  |  Consistent: 10
```

## Consistent Combinations (Max 30 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s15_v1.2_roc100` | `366d` — SR=2.070, Win%=63.4, Med%=+18.08, AnnMean%=+40.54, Q75%=+71.01, MaxDD%=40.01, CVaR%=-64.76, Yrs+=3/3, N=145
- `bk50d_s17_v1.2_roc100` | `184d` — SR=1.680, Win%=60.3, Med%=+10.11, AnnMean%=+43.62, Q75%=+37.71, MaxDD%=30.39, CVaR%=-52.41, Yrs+=3/4, N=204
- `bk50d_s12_v1.2_roc100` | `366d` — SR=1.580, Win%=61.3, Med%=+12.14, AnnMean%=+30.99, Q75%=+60.49, MaxDD%=40.16, CVaR%=-63.89, Yrs+=3/3, N=150
- `bk50d_s20_v1.2_roc100` | `184d` — SR=1.437, Win%=59.1, Med%=+7.02, AnnMean%=+40.47, Q75%=+38.69, MaxDD%=32.41, CVaR%=-57.38, Yrs+=3/3, N=198
- `bk50d_s15_v1.2_roc100` | `184d` — SR=1.130, Win%=54.6, Med%=+6.21, AnnMean%=+31.86, Q75%=+33.78, MaxDD%=31.68, CVaR%=-53.90, Yrs+=4/5, N=218
- `bk50d_s20_v1.2_roc100` | `91d` — SR=0.982, Win%=59.5, Med%=+5.19, AnnMean%=+32.15, Q75%=+23.03, MaxDD%=23.04, CVaR%=-47.09, Yrs+=3/3, N=242
- `bk50d_s17_v1.2_roc100` | `91d` — SR=0.804, Win%=58.7, Med%=+4.11, AnnMean%=+26.12, Q75%=+19.36, MaxDD%=22.79, CVaR%=-45.95, Yrs+=4/5, N=298
- `bk50d_s15_v1.2_roc100` | `91d` — SR=0.792, Win%=55.6, Med%=+2.94, AnnMean%=+25.58, Q75%=+19.29, MaxDD%=22.38, CVaR%=-43.90, Yrs+=4/5, N=338
- `bk50d_s12_v1.2_roc100` | `184d` — SR=0.666, Win%=51.7, Med%=+1.58, AnnMean%=+19.05, Q75%=+26.52, MaxDD%=32.30, CVaR%=-53.68, Yrs+=4/5, N=230
- `bk50d_s12_v1.2_roc100` | `91d` — SR=0.432, Win%=53.2, Med%=+1.52, AnnMean%=+14.01, Q75%=+16.01, MaxDD%=22.89, CVaR%=-44.82, Yrs+=4/5, N=389

## Rankings — Max 20 Concurrent Positions

Same signals, but a trade is skipped if 20 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2021-01-01 – 2026-07-14  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 20

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.2_roc100            366d   100   61.0   +39.45    +39.32   +16.88   +71.80   4.62    1.837    42.00   -71.15    1.5    1/2   
   2  bk50d_s20_v1.2_roc100            366d    91   63.7   +35.57    +35.45   +22.32   +76.88   4.34    1.604    41.94   -73.93    1.4    0/1   
   3  bk50d_s17_v1.2_roc100            366d    95   65.3   +34.72    +34.61   +17.53   +66.48   4.20    1.588    42.08   -73.93    1.4    0/1   
   4  bk50d_s17_v1.2_roc100            184d   144   58.3   +19.42    +42.19    +9.21   +39.08   3.15    1.550    31.72   -54.78    2.2    1/2   
   5  bk50d_s20_v1.2_roc100            184d   138   57.2   +18.98    +41.16    +6.82   +41.39   3.06    1.447    32.74   -61.00    2.1    2/3   
   6  bk50d_s12_v1.2_roc100            366d   100   56.0   +24.03    +23.96    +4.59   +42.33   3.20    1.189    41.13   -63.68    1.5    2/3   
   7  bk50d_s15_v1.2_roc100            184d   148   53.4   +14.69    +31.25    +5.04   +35.17   2.38    1.067    32.28   -56.23    2.2    3/4  ✓
   8  bk50d_s20_v1.2_roc100             91d   191   56.0    +6.27    +27.64    +3.40   +21.88   1.79    0.811    24.06   -49.96    2.9    2/3   
   9  bk50d_s17_v1.2_roc100             91d   222   56.8    +6.08    +26.71    +3.48   +20.35   1.72    0.780    23.57   -47.52    3.4    3/4  ✓
  10  bk50d_s12_v1.2_roc100            184d   160   54.4   +10.50    +21.91    +5.66   +26.59   1.98    0.756    33.32   -56.53    2.4    4/5  ✓
  11  bk50d_s15_v1.2_roc100             91d   250   53.2    +4.30    +18.40    +1.81   +17.38   1.49    0.543    23.34   -47.06    3.8    4/5  ✓
  12  bk50d_s12_v1.2_roc100             91d   272   54.0    +3.42    +14.45    +1.60   +16.60   1.41    0.456    22.59   -43.72    4.1    4/5  ✓

Valid combinations: 12  |  Consistent: 5
```

## Consistent Combinations (Max 20 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s15_v1.2_roc100` | `184d` — SR=1.067, Win%=53.4, Med%=+5.04, AnnMean%=+31.25, Q75%=+35.17, MaxDD%=32.28, CVaR%=-56.23, Yrs+=3/4, N=148
- `bk50d_s17_v1.2_roc100` | `91d` — SR=0.780, Win%=56.8, Med%=+3.48, AnnMean%=+26.71, Q75%=+20.35, MaxDD%=23.57, CVaR%=-47.52, Yrs+=3/4, N=222
- `bk50d_s12_v1.2_roc100` | `184d` — SR=0.756, Win%=54.4, Med%=+5.66, AnnMean%=+21.91, Q75%=+26.59, MaxDD%=33.32, CVaR%=-56.53, Yrs+=4/5, N=160
- `bk50d_s15_v1.2_roc100` | `91d` — SR=0.543, Win%=53.2, Med%=+1.81, AnnMean%=+18.40, Q75%=+17.38, MaxDD%=23.34, CVaR%=-47.06, Yrs+=4/5, N=250
- `bk50d_s12_v1.2_roc100` | `91d` — SR=0.456, Win%=54.0, Med%=+1.60, AnnMean%=+14.45, Q75%=+16.60, MaxDD%=22.59, CVaR%=-43.72, Yrs+=4/5, N=272

## Findings & Caveats

**Fixed**: `close`/`high`/`low` are now split/dividend-adjusted (scaled by `adjusted_close/close`). The prior version used raw `close`, which shows a fake ~90% one-day move on a stock's split date (e.g. NVDA's 2024-06-10 10:1 split) — this corrupted rolling indicators for ~50 days around any split and could make a real winning trade compute as a huge loss (or vice versa for a reverse split). 13.1% of the qualifying universe (254/1,943 tickers) had at least one such split event since 2020. The MIN_PRICE/MAX_PRICE band still uses raw (unadjusted) close, since that's the real price a trader would have paid on the entry date — adjusting it would leak knowledge of future splits into a point-in-time filter.

**Unresolved — survivorship bias**: every ticker in the qualifying universe has `status='active'`; the pipeline retains no delisted/bankrupt/acquired tickers. `company.market_cap` is also a single current-day snapshot applied retroactively to all history, not a point-in-time value. A momentum-breakout strategy specifically targets stocks that sometimes blow up afterward (fraud, failed trial, acquisition below entry) — those trades are structurally impossible to appear in this backtest. This likely explains part of the unusually high win rate/profit factor and should be treated as a ceiling on how much to trust the absolute return numbers.

**Partially addressed — overlapping trades**: at several signals/month with 6-12 month holds, most trades are open concurrently and share the same regime exposure, so the unconstrained N overstates the number of independent bets and the Sortino/consistency stats overstate statistical confidence. The 'Max 30 and 20 Concurrent Positions' tables above cap the portfolio at that many simultaneous positions (FIFO signal acceptance) as a rough realism check — comparing the tables shows how much each combination's apparent edge depends on taking every single signal versus a capital-constrained subset. This doesn't fix the underlying correlation between trades still held concurrently within a cap, and it uses an arbitrary FIFO rule rather than a real signal-quality ranking for which trade to take when capacity is full.

**Unresolved — regime concentration**: the SPY>200d SMA filter concentrates trades in bull years. The Yrs+ denominator silently drops any complete calendar year with <10 losing trades from its count (see the Yrs+ column above, e.g. a stricter signal with fewer total trades may show fewer valid years than the number of complete calendar years in the eval period), which can exclude harder regimes rather than prove the strategy survived them.

**Unresolved — no execution costs**: entry is assumed fillable at the same close that generated the signal, with no slippage, spread, commissions, or gap risk — unrealistic for breakout-day fills on high-ADR names.

**Ideas to improve**: source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot; source a delisted-ticker history if available to address survivorship; shift entry to next-day open (+ slippage assumption) for realistic fills; replace the FIFO acceptance rule in the capacity-constrained table with a real signal-quality ranking (e.g. ADR%, breakout strength) to pick which trade to take when capacity is full; account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence.
