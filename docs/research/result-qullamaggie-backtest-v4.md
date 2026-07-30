# Qullamaggie Backtest v4 — Results

Run date: 2026-07-30

## Configuration

| Parameter | Value |
|---|---|
| Algorithm version | 2.0 (encoded as `_v2.0` in the names below) |
| Breakout | 50d high |
| Entry | next trading day's adjusted open (within 7 cal days of the signal) |
| Exit | close of the first bar at or after entry + hold |
| SMA thresh sweep | 12%, 16%, 20% |
| Tight range | disabled (commented out) |
| Hold sweep | 366d (calendar) |
| Ranking | QullamaggieRanking (ADR 40 / SMA50 35 / price 25) |
| Ranking gate sweep | ungated, ≥ 40, 45, 50 |
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
| Eval period | 2021-01-01 – 2026-07-30 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings — No Ranking Condition

```text
Period: 2021-01-01 – 2026-07-30  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0                   366d   397   65.7   +53.91    +53.73   +24.05   +75.32   6.77    2.762    40.88   -62.50    6.0   54.3     52    5/5  ✓
   2  bk50d_s16_v2.0                   366d   653   63.9   +43.78    +43.64   +18.24   +65.23   5.44    2.198    39.48   -61.69    9.9   43.6     40    5/5  ✓
   3  bk50d_s12_v2.0                   366d  1009   62.3   +36.80    +36.69   +14.89   +55.96   4.73    1.864    38.47   -60.61   15.3   37.3     33    5/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0` | `366d` — SR=2.762, Win%=65.7, Med%=+24.05, AnnMean%=+53.73, Q75%=+75.32, MaxDD%=40.88, CVaR%=-62.50, Yrs+=5/5, N=397
- `bk50d_s16_v2.0` | `366d` — SR=2.198, Win%=63.9, Med%=+18.24, AnnMean%=+43.64, Q75%=+65.23, MaxDD%=39.48, CVaR%=-61.69, Yrs+=5/5, N=653
- `bk50d_s12_v2.0` | `366d` — SR=1.864, Win%=62.3, Med%=+14.89, AnnMean%=+36.69, Q75%=+55.96, MaxDD%=38.47, CVaR%=-60.61, Yrs+=5/5, N=1009

## Rankings — Ranking Gate Sweep (R ≥ 40, 45, 50)

Same signals, but a trade is taken only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over 40, 45, 50 (40 is the `--min-signal-ranking` default). The score is computed from the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead.

```text
Period: 2021-01-01 – 2026-07-30  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Ranking gate sweep: QullamaggieRanking ≥ 40, 45, 50

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0 R≥45              366d   232   62.9   +57.12    +56.93   +20.82   +85.52   6.04    2.548    45.11   -69.48    3.5   67.1     64    3/4  ✓
   2  bk50d_s12_v2.0 R≥50              366d   255   63.9   +53.83    +53.65   +25.49   +81.16   6.05    2.518    45.05   -67.70    3.9   67.1     64    4/4  ✓
   3  bk50d_s12_v2.0 R≥40              366d   399   62.7   +51.20    +51.03   +22.06   +72.47   5.89    2.466    42.73   -63.50    6.0   58.5     57    5/5  ✓
   4  bk50d_s20_v2.0 R≥50              366d   203   62.1   +56.07    +55.88   +25.86   +86.80   5.80    2.443    46.07   -70.44    3.1   70.0     66    3/4  ✓
   5  bk50d_s20_v2.0 R≥40              366d   277   63.2   +52.99    +52.81   +22.09   +76.17   5.87    2.434    44.13   -67.21    4.2   63.1     62    4/4  ✓
   6  bk50d_s12_v2.0 R≥45              366d   298   63.4   +51.92    +51.75   +21.90   +75.96   5.76    2.405    44.45   -66.96    4.5   64.2     64    4/4  ✓
   7  bk50d_s16_v2.0 R≥50              366d   230   61.3   +53.77    +53.59   +23.71   +84.64   5.65    2.404    45.73   -69.00    3.5   68.3     66    4/4  ✓
   8  bk50d_s16_v2.0 R≥45              366d   272   61.8   +52.10    +51.93   +18.83   +76.27   5.49    2.323    44.91   -67.66    4.1   65.0     64    4/4  ✓
   9  bk50d_s16_v2.0 R≥40              366d   329   61.7   +50.02    +49.85   +19.23   +72.85   5.40    2.268    43.97   -65.60    5.0   61.1     60    4/4  ✓

Valid combinations: 9  |  Consistent: 9
```

## Consistent Combinations (Ranking ≥ 40, 45, 50)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0 R≥45` | `366d` — SR=2.548, Win%=62.9, Med%=+20.82, AnnMean%=+56.93, Q75%=+85.52, MaxDD%=45.11, CVaR%=-69.48, Yrs+=3/4, N=232
- `bk50d_s12_v2.0 R≥50` | `366d` — SR=2.518, Win%=63.9, Med%=+25.49, AnnMean%=+53.65, Q75%=+81.16, MaxDD%=45.05, CVaR%=-67.70, Yrs+=4/4, N=255
- `bk50d_s12_v2.0 R≥40` | `366d` — SR=2.466, Win%=62.7, Med%=+22.06, AnnMean%=+51.03, Q75%=+72.47, MaxDD%=42.73, CVaR%=-63.50, Yrs+=5/5, N=399
- `bk50d_s20_v2.0 R≥50` | `366d` — SR=2.443, Win%=62.1, Med%=+25.86, AnnMean%=+55.88, Q75%=+86.80, MaxDD%=46.07, CVaR%=-70.44, Yrs+=3/4, N=203
- `bk50d_s20_v2.0 R≥40` | `366d` — SR=2.434, Win%=63.2, Med%=+22.09, AnnMean%=+52.81, Q75%=+76.17, MaxDD%=44.13, CVaR%=-67.21, Yrs+=4/4, N=277
- `bk50d_s12_v2.0 R≥45` | `366d` — SR=2.405, Win%=63.4, Med%=+21.90, AnnMean%=+51.75, Q75%=+75.96, MaxDD%=44.45, CVaR%=-66.96, Yrs+=4/4, N=298
- `bk50d_s16_v2.0 R≥50` | `366d` — SR=2.404, Win%=61.3, Med%=+23.71, AnnMean%=+53.59, Q75%=+84.64, MaxDD%=45.73, CVaR%=-69.00, Yrs+=4/4, N=230
- `bk50d_s16_v2.0 R≥45` | `366d` — SR=2.323, Win%=61.8, Med%=+18.83, AnnMean%=+51.93, Q75%=+76.27, MaxDD%=44.91, CVaR%=-67.66, Yrs+=4/4, N=272
- `bk50d_s16_v2.0 R≥40` | `366d` — SR=2.268, Win%=61.7, Med%=+19.23, AnnMean%=+49.85, Q75%=+72.85, MaxDD%=43.97, CVaR%=-65.60, Yrs+=4/4, N=329

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40      1385       548        837     60.4%
bk50d_s12_v2.0               45      1385       402        983     71.0%
bk50d_s12_v2.0               50      1385       344       1041     75.2%
bk50d_s16_v2.0               40       894       458        436     48.8%
bk50d_s16_v2.0               45       894       371        523     58.5%
bk50d_s16_v2.0               50       894       308        586     65.5%
bk50d_s20_v2.0               40       536       389        147     27.4%
bk50d_s20_v2.0               45       536       323        213     39.7%
bk50d_s20_v2.0               50       536       277        259     48.3%
```

## Findings & Caveats

### Ideas to improve

- source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot
- source a delisted-ticker history if available to address survivorship
- add a slippage/commission assumption on top of the next-day-open fill
- widen the gate sweep past 50 to find where the score stops separating outcomes
- report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold
- account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence
