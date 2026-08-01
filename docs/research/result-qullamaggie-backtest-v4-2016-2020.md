# Qullamaggie Backtest v4 — Results

Run date: 2026-08-01 10:07:25 Tallinn time

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
| Eval period | 2016-01-01 – 2020-12-31 |
| Burn-in (indicators only) | 2014-01-01 – 2016-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings — No Ranking Condition

```text
Period: 2016-01-01 – 2020-12-31  |  HOLD_MAX_CAL=366d
Fixed: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0                   366d   813   82.3   +56.67    +56.48   +46.40   +82.13  13.75    4.199    32.89   -51.87   13.8   55.9     58    5/5  ✓
   2  bk50d_s16_v2.0                   366d  1200   79.2   +49.82    +49.66   +41.53   +76.65  10.80    3.496    32.47   -52.96   20.3   45.2     43    5/5  ✓
   3  bk50d_s12_v2.0                   366d  1681   77.8   +45.17    +45.02   +37.45   +72.77   9.18    3.003    32.38   -54.73   28.5   39.6     33    4/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0` | `366d` — SR=4.199, Win%=82.3, Med%=+46.40, AnnMean%=+56.48, Q75%=+82.13, MaxDD%=32.89, CVaR%=-51.87, Yrs+=5/5, N=813
- `bk50d_s16_v2.0` | `366d` — SR=3.496, Win%=79.2, Med%=+41.53, AnnMean%=+49.66, Q75%=+76.65, MaxDD%=32.47, CVaR%=-52.96, Yrs+=5/5, N=1200
- `bk50d_s12_v2.0` | `366d` — SR=3.003, Win%=77.8, Med%=+37.45, AnnMean%=+45.02, Q75%=+72.77, MaxDD%=32.38, CVaR%=-54.73, Yrs+=4/5, N=1681

## Rankings — Ranking Gate Sweep (R ≥ 40)

Same signals, but a trade is taken only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over 40 (40 is the `--min-signal-ranking` default). The score is computed from the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead.

```text
Period: 2016-01-01 – 2020-12-31  |  HOLD_MAX_CAL=366d
Fixed: roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Ranking gate sweep: QullamaggieRanking ≥ 40

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s16_v2.0 R≥40              366d   674   82.9   +64.14    +63.92   +52.48   +96.02  17.12    5.203    34.20   -48.26   11.4   60.9     60    3/3  ✓
   2  bk50d_s20_v2.0 R≥40              366d   634   83.8   +63.90    +63.68   +51.86   +94.79  17.09    5.111    33.90   -49.11   10.7   62.0     60    3/3  ✓
   3  bk50d_s12_v2.0 R≥40              366d   745   80.7   +60.27    +60.06   +48.84   +91.27  13.46    4.374    34.65   -51.26   12.6   59.4     60    5/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations (Ranking ≥ 40)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s16_v2.0 R≥40` | `366d` — SR=5.203, Win%=82.9, Med%=+52.48, AnnMean%=+63.92, Q75%=+96.02, MaxDD%=34.20, CVaR%=-48.26, Yrs+=3/3, N=674
- `bk50d_s20_v2.0 R≥40` | `366d` — SR=5.111, Win%=83.8, Med%=+51.86, AnnMean%=+63.68, Q75%=+94.79, MaxDD%=33.90, CVaR%=-49.11, Yrs+=3/3, N=634
- `bk50d_s12_v2.0 R≥40` | `366d` — SR=4.374, Win%=80.7, Med%=+48.84, AnnMean%=+60.06, Q75%=+91.27, MaxDD%=34.65, CVaR%=-51.26, Yrs+=5/5, N=745

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40      1681       745        936     55.7%
bk50d_s16_v2.0               40      1200       674        526     43.8%
bk50d_s20_v2.0               40       813       634        179     22.0%
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
