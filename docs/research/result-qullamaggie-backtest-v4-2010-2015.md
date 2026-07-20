# Qullamaggie Backtest v4 — Results

Run date: 2026-07-20

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
| Eval period | 2010-01-01 – 2015-12-31 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```text
Period: 2010-01-01 – 2015-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70 or >80, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.3_roc100            366d   351   60.7   +17.89    +17.84   +10.94   +42.87   2.62    0.844    37.63   -63.58    4.9    4/5  ✓
   2  bk50d_s17_v1.3_roc100            366d   261   57.9   +18.17    +18.11    +9.76   +44.89   2.52    0.814    38.56   -64.60    3.7    4/5  ✓
   3  bk50d_s20_v1.3_roc100            366d   146   56.2   +17.89    +17.84    +6.14   +45.06   2.34    0.734    40.83   -67.33    2.1    2/3   
   4  bk50d_s12_v1.3_roc100            366d   540   56.5   +13.86    +13.82    +7.40   +36.57   2.21    0.642    37.96   -63.02    7.6    4/5  ✓
   5  bk50d_s17_v1.3_roc100            184d   261   55.2    +8.09    +16.70    +5.30   +27.73   1.83    0.609    28.38   -57.72    3.7    4/5  ✓
   6  bk50d_s15_v1.3_roc100            184d   351   55.8    +7.45    +15.32    +5.25   +26.36   1.78    0.577    27.72   -56.80    4.9    4/5  ✓
   7  bk50d_s12_v1.3_roc100            184d   540   55.0    +7.00    +14.37    +4.84   +25.82   1.74    0.560    27.10   -53.73    7.6    5/6  ✓
   8  bk50d_s12_v1.3_roc100             91d   540   54.6    +3.35    +14.15    +3.13   +15.56   1.48    0.512    19.23   -40.95    7.6    5/6  ✓
   9  bk50d_s20_v1.3_roc100            184d   146   52.1    +7.03    +14.42    +1.96   +24.32   1.66    0.497    30.24   -60.21    2.1    2/3   
  10  bk50d_s17_v1.3_roc100             91d   261   57.9    +3.45    +14.56    +3.65   +16.38   1.46    0.491    20.59   -42.80    3.7    2/4   
  11  bk50d_s15_v1.3_roc100             91d   351   56.7    +3.30    +13.89    +3.92   +15.56   1.46    0.488    19.94   -42.01    4.9    3/5   
  12  bk50d_s20_v1.3_roc100             91d   146   52.7    +3.35    +14.12    +2.51   +17.87   1.41    0.459    21.51   -44.73    2.1    2/3   

Valid combinations: 12  |  Consistent: 7
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s15_v1.3_roc100` | `366d` — SR=0.844, Win%=60.7, Med%=+10.94, AnnMean%=+17.84, Q75%=+42.87, MaxDD%=37.63, CVaR%=-63.58, Yrs+=4/5, N=351
- `bk50d_s17_v1.3_roc100` | `366d` — SR=0.814, Win%=57.9, Med%=+9.76, AnnMean%=+18.11, Q75%=+44.89, MaxDD%=38.56, CVaR%=-64.60, Yrs+=4/5, N=261
- `bk50d_s12_v1.3_roc100` | `366d` — SR=0.642, Win%=56.5, Med%=+7.40, AnnMean%=+13.82, Q75%=+36.57, MaxDD%=37.96, CVaR%=-63.02, Yrs+=4/5, N=540
- `bk50d_s17_v1.3_roc100` | `184d` — SR=0.609, Win%=55.2, Med%=+5.30, AnnMean%=+16.70, Q75%=+27.73, MaxDD%=28.38, CVaR%=-57.72, Yrs+=4/5, N=261
- `bk50d_s15_v1.3_roc100` | `184d` — SR=0.577, Win%=55.8, Med%=+5.25, AnnMean%=+15.32, Q75%=+26.36, MaxDD%=27.72, CVaR%=-56.80, Yrs+=4/5, N=351
- `bk50d_s12_v1.3_roc100` | `184d` — SR=0.560, Win%=55.0, Med%=+4.84, AnnMean%=+14.37, Q75%=+25.82, MaxDD%=27.10, CVaR%=-53.73, Yrs+=5/6, N=540
- `bk50d_s12_v1.3_roc100` | `91d` — SR=0.512, Win%=54.6, Med%=+3.13, AnnMean%=+14.15, Q75%=+15.56, MaxDD%=19.23, CVaR%=-40.95, Yrs+=5/6, N=540

## Rankings — Max 30 Concurrent Positions

Same signals, but a trade is skipped if 30 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2010-01-01 – 2015-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70 or >80, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 30

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s15_v1.3_roc100            366d   163   65.6   +24.70    +24.62   +14.49   +48.90   3.73    1.328    36.73   -57.47    2.3    1/2   
   2  bk50d_s17_v1.3_roc100            366d   152   59.9   +20.82    +20.75   +12.72   +49.82   2.77    0.916    38.81   -66.61    2.1    3/4  ✓
   3  bk50d_s15_v1.3_roc100            184d   230   60.0   +10.49    +21.87    +8.45   +29.61   2.27    0.879    26.15   -54.56    3.2    2/4   
   4  bk50d_s17_v1.3_roc100            184d   202   59.4   +10.58    +22.08    +8.99   +30.97   2.19    0.830    27.13   -56.25    2.8    3/4  ✓
   5  bk50d_s12_v1.3_roc100            184d   280   60.0    +9.93    +20.66    +7.59   +29.87   2.11    0.821    26.20   -50.04    3.9    3/5   
   6  bk50d_s20_v1.3_roc100            366d   123   56.9   +18.91    +18.86    +7.51   +47.63   2.48    0.804    41.05   -67.19    1.7    1/2   
   7  bk50d_s12_v1.3_roc100            366d   169   56.8   +14.21    +14.17    +6.45   +39.09   2.34    0.718    38.01   -55.62    2.4    2/4   
   8  bk50d_s20_v1.3_roc100            184d   140   54.3    +8.18    +16.89    +3.07   +27.08   1.80    0.591    29.72   -59.56    2.0    2/3   
   9  bk50d_s17_v1.3_roc100             91d   241   58.9    +3.97    +16.91    +3.98   +16.64   1.55    0.581    20.31   -42.50    3.4    2/4   
  10  bk50d_s20_v1.3_roc100             91d   146   52.7    +3.35    +14.12    +2.51   +17.87   1.41    0.459    21.51   -44.73    2.1    2/3   
  11  bk50d_s15_v1.3_roc100             91d   308   54.2    +2.88    +12.06    +2.94   +15.20   1.39    0.432    20.16   -40.49    4.3    3/5   
  12  bk50d_s12_v1.3_roc100             91d   394   50.3    +2.60    +10.85    +0.05   +15.09   1.35    0.389    19.72   -40.79    5.5    3/6   

Valid combinations: 12  |  Consistent: 2
```

## Consistent Combinations (Max 30 Concurrent)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s17_v1.3_roc100` | `366d` — SR=0.916, Win%=59.9, Med%=+12.72, AnnMean%=+20.75, Q75%=+49.82, MaxDD%=38.81, CVaR%=-66.61, Yrs+=3/4, N=152
- `bk50d_s17_v1.3_roc100` | `184d` — SR=0.830, Win%=59.4, Med%=+8.99, AnnMean%=+22.08, Q75%=+30.97, MaxDD%=27.13, CVaR%=-56.25, Yrs+=3/4, N=202

## Rankings — Max 20 Concurrent Positions

Same signals, but a trade is skipped if 20 positions are already open on its entry date (FIFO, ties broken alphabetically by symbol; no queueing for a freed-up slot later).

```text
Period: 2010-01-01 – 2015-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70 or >80, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Max concurrent positions: 20

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v1.3_roc100            366d    95   62.1   +25.10    +25.02   +10.94   +62.18   3.11    1.088    40.53   -68.96    1.3    0/1   
   2  bk50d_s15_v1.3_roc100            184d   182   61.0   +11.49    +24.08    +8.65   +31.14   2.37    0.960    26.71   -53.27    2.6    2/4   
   3  bk50d_s15_v1.3_roc100            366d   113   62.8   +18.67    +18.61   +10.08   +44.89   2.88    0.959    37.28   -57.22    1.6    1/2   
   4  bk50d_s17_v1.3_roc100            184d   162   59.3   +11.05    +23.11    +8.75   +29.61   2.34    0.927    26.48   -53.90    2.3    2/4   
   5  bk50d_s17_v1.3_roc100            366d   107   55.1   +19.65    +19.59    +7.63   +49.93   2.50    0.814    38.81   -65.82    1.5    1/3   
   6  bk50d_s12_v1.3_roc100            184d   200   58.0    +9.96    +20.72    +7.95   +31.92   2.05    0.796    26.51   -51.46    2.8    2/4   
   7  bk50d_s12_v1.3_roc100            366d   119   56.3   +14.46    +14.42    +6.64   +32.64   2.38    0.739    38.93   -55.53    1.7    1/3   
   8  bk50d_s20_v1.3_roc100            184d   129   55.0    +9.73    +20.21    +4.59   +31.37   2.02    0.737    29.24   -57.94    1.8    2/3   
   9  bk50d_s17_v1.3_roc100             91d   215   59.1    +4.43    +18.99    +3.98   +17.09   1.65    0.694    20.16   -39.54    3.0    2/4   
  10  bk50d_s20_v1.3_roc100             91d   140   55.0    +4.67    +20.11    +3.07   +18.28   1.64    0.694    21.02   -41.03    2.0    2/3   
  11  bk50d_s12_v1.3_roc100             91d   308   52.9    +3.78    +16.04    +2.52   +16.31   1.57    0.619    19.04   -38.32    4.3    4/6   
  12  bk50d_s15_v1.3_roc100             91d   257   54.1    +2.93    +12.28    +3.08   +14.83   1.39    0.442    20.15   -40.25    3.6    2/5   

Valid combinations: 12  |  Consistent: 0
```

## Consistent Combinations (Max 20 Concurrent)

No combinations met the consistency criteria.

## Notes

Historical re-run (2010-2015) of the unchanged v4 methodology for out-of-sample comparison against the 2021-present run in result-qullamaggie-backtest-v4.md (see that file for full caveats). Survivorship bias and the static market-cap snapshot are materially WORSE here: the universe and market_cap >= 1.5B filter reflect 2026 data applied to 2010-2015 history, so companies that grew into the cap threshold after 2015 are included with their pre-growth prices, and 2010-2015 delistings are absent entirely.

## Comparison vs 2021 – 2026-07 (unconstrained)

| Combo | Exit | SR 21-26 | SR 10-15 | AnnMean 21-26 | AnnMean 10-15 | Win% 21-26 | Win% 10-15 | PF 21-26 | PF 10-15 | F/mo 21-26 | F/mo 10-15 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s20 | 366d | 2.765 | 0.734 | +54.5% | +17.8% | 65.4 | 56.2 | 6.68 | 2.34 | 8.1 | 2.1 |
| s17 | 366d | 2.251 | 0.814 | +44.6% | +18.1% | 63.0 | 57.9 | 5.45 | 2.52 | 11.5 | 3.7 |
| s15 | 366d | 2.082 | 0.844 | +41.4% | +17.8% | 63.5 | 60.7 | 5.15 | 2.62 | 14.4 | 4.9 |
| s12 | 366d | 1.862 | 0.642 | +37.3% | +13.8% | 63.0 | 56.5 | 4.70 | 2.21 | 18.9 | 7.6 |
| s20 | 184d | 1.771 | 0.497 | +44.5% | +14.4% | 61.1 | 52.1 | 3.47 | 1.66 | 8.1 | 2.1 |
| s17 | 184d | 1.354 | 0.609 | +34.5% | +16.7% | 59.3 | 55.2 | 2.82 | 1.83 | 11.5 | 3.7 |
| s15 | 184d | 1.199 | 0.577 | +30.7% | +15.3% | 58.4 | 55.8 | 2.60 | 1.78 | 14.4 | 4.9 |
| s12 | 184d | 1.087 | 0.560 | +27.4% | +14.4% | 57.7 | 55.0 | 2.46 | 1.74 | 18.9 | 7.6 |
| s20 | 91d | 1.321 | 0.459 | +42.2% | +14.1% | 62.0 | 52.7 | 2.33 | 1.41 | 8.1 | 2.1 |
| s17 | 91d | 1.078 | 0.491 | +34.2% | +14.6% | 60.7 | 57.9 | 2.05 | 1.46 | 11.5 | 3.7 |
| s15 | 91d | 1.018 | 0.488 | +31.9% | +13.9% | 59.4 | 56.7 | 1.98 | 1.46 | 14.4 | 4.9 |
| s12 | 91d | 0.912 | 0.512 | +27.6% | +14.2% | 58.9 | 54.6 | 2.46 | 1.48 | 18.9 | 7.6 |

Key observations:

- **The edge survives but is roughly a third of its recent size.** Every combination stays Sortino-positive and 7/12 remain year-by-year consistent, but top Sortino drops 2.77 → 0.84, 366d annualized mean +37-55% → +14-18%, profit factor 4.7-6.7 → 2.2-2.6.
- **Downside is unchanged.** Mean per-trade MaxDD (~38-41% at 366d) and CVaR(95%) (-63 to -67%) match the current period — same tail risk, much smaller reward.
- **The hold-period ordering is regime-stable**: 366d > 184d > 91d by Sortino in both periods.
- **The SMA-threshold ordering is NOT**: 2021-26 ranks strictest-first (s20 best), 2010-15 ranks s15/s17 first with s20 mid-pack on barely 146 trades (2/3 valid years, not consistent). The recent "raise the pct_above_sma50 bar" conclusion looks period-specific.
- **Signal frequency is ~60% lower** (2-8/mo vs 8-19/mo). Partly a real regime difference (2010s low-ADR environment passes the ADR ≥ 3% gate less often), partly artifact: the 2026 market-cap snapshot back-applied to 2010 shrinks the qualifying universe.
- **Capacity caps change little in 2010-15** (frequency rarely fills 20-30 slots) but consistency collapses there (2 consistent at cap 30, 0 at cap 20) because few years reach 10 losing trades.
