# Qullamaggie Backtest v4 — Results

Run date: 2026-08-01 10:08:42 Tallinn time

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
| Ranking gate sweep | ungated, ≥ 40 |
| vol_dry_up | disabled (commented out) |
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
| Eval period | 2021-01-01 – 2026-08-01 |
| Burn-in (indicators only) | 2019-01-02 – 2021-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings — No Ranking Condition

```text
Period: 2021-01-01 – 2026-08-01  |  HOLD_MAX_CAL=366d
Fixed: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0                   366d   520   65.4   +56.35    +56.16   +26.37   +85.40   7.07    2.941    41.35   -60.06    7.8   55.9     58    5/5  ✓
   2  bk50d_s16_v2.0                   366d   870   63.4   +45.20    +45.05   +20.43   +71.54   5.58    2.289    39.88   -60.44   13.0   44.3     41    5/5  ✓
   3  bk50d_s12_v2.0                   366d  1346   62.1   +38.26    +38.14   +15.80   +60.18   4.89    1.953    38.63   -60.18   20.1   38.0     33    5/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0` | `366d` — SR=2.941, Win%=65.4, Med%=+26.37, AnnMean%=+56.16, Q75%=+85.40, MaxDD%=41.35, CVaR%=-60.06, Yrs+=5/5, N=520
- `bk50d_s16_v2.0` | `366d` — SR=2.289, Win%=63.4, Med%=+20.43, AnnMean%=+45.05, Q75%=+71.54, MaxDD%=39.88, CVaR%=-60.44, Yrs+=5/5, N=870
- `bk50d_s12_v2.0` | `366d` — SR=1.953, Win%=62.1, Med%=+15.80, AnnMean%=+38.14, Q75%=+60.18, MaxDD%=38.63, CVaR%=-60.18, Yrs+=5/5, N=1346

## Rankings — Ranking Gate Sweep (R ≥ 40)

Same signals, but a trade is taken only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over 40 (40 is the `--min-signal-ranking` default). The score is computed from the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead.

```text
Period: 2021-01-01 – 2026-08-01  |  HOLD_MAX_CAL=366d
Fixed: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Ranking gate sweep: QullamaggieRanking ≥ 40

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0 R≥40              366d   379   65.4   +58.69    +58.49   +27.84   +91.06   6.85    2.846    44.07   -64.15    5.7   64.0     64    5/5  ✓
   2  bk50d_s12_v2.0 R≥40              366d   552   64.7   +55.51    +55.32   +25.60   +86.27   6.53    2.718    42.90   -63.14    8.2   58.9     58    5/5  ✓
   3  bk50d_s16_v2.0 R≥40              366d   454   63.9   +53.96    +53.78   +25.17   +84.67   6.08    2.546    44.12   -63.92    6.8   61.3     60    5/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations (Ranking ≥ 40)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0 R≥40` | `366d` — SR=2.846, Win%=65.4, Med%=+27.84, AnnMean%=+58.49, Q75%=+91.06, MaxDD%=44.07, CVaR%=-64.15, Yrs+=5/5, N=379
- `bk50d_s12_v2.0 R≥40` | `366d` — SR=2.718, Win%=64.7, Med%=+25.60, AnnMean%=+55.32, Q75%=+86.27, MaxDD%=42.90, CVaR%=-63.14, Yrs+=5/5, N=552
- `bk50d_s16_v2.0 R≥40` | `366d` — SR=2.546, Win%=63.9, Med%=+25.17, AnnMean%=+53.78, Q75%=+84.67, MaxDD%=44.12, CVaR%=-63.92, Yrs+=5/5, N=454

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40      1851       763       1088     58.8%
bk50d_s16_v2.0               40      1196       630        566     47.3%
bk50d_s20_v2.0               40       713       534        179     25.1%
```

## Findings & Caveats

### Ideas to improve

- source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot
- source a delisted-ticker history if available to address survivorship
- add a slippage/commission assumption on top of the next-day-open fill
- widen the gate sweep past 40 to find where the score stops separating outcomes
- report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold
- account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence
- re-run all three windows (2010-2015, 2016-2020, 2021-present) before accepting any parameter change — a change that only improves the window it was chosen on is fitted to that window
- pick the ranking gate per SMA threshold rather than one R≥40 across s12/s16/s20; the same score rejects a very different share of each, so it is not the same filter at each
- report each year's negative-trade count next to its Sortino — under the gate a thin window can fall below the 10-loser bar and silently drop out of the Yrs+ denominator
