# Qullamaggie Backtest v4 — Results

Run date: 2026-08-02 01:21:04 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Algorithm version | 2.0 (encoded as `_v2.0` in the names below) |
| Breakout | 50d high |
| Entry | next trading day's adjusted open (within 7 cal days of the signal) |
| Exit | close of the first bar at or after entry + hold |
| SMA thresh sweep | 12%, 16%, 20% |
| Tight range | disabled (commented out) |
| Hold sweep | 366d (calendar); entries without 366d of forward data are skipped |
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
| Eval period | 2010-01-01 – 2015-12-31 |
| Burn-in (indicators only) | 2008-01-02 – 2010-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Rankings

Each algorithm appears twice on adjacent rows, distinguished by the `Gate` column: `R>=40` takes a trade only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) clears the gate, `ungated` takes every signal. The two rows come from the same signals, sized and exited identically, so the difference isolates the gate. The score uses the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead. Groups are ordered by the gated run's Sortino.

```text
Entry Signal      Gate        Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
bk50d_s20_v2.0    R>=40      366d   116   56.9   +17.92    +17.86    +9.62   +47.21   2.30    0.729    42.73   -66.48    1.6   61.0     60    1/2   
bk50d_s20_v2.0    ungated    366d   178   56.2   +16.49    +16.44    +4.94   +44.22   2.23    0.682    41.13   -66.45    2.5   52.0     49    3/4  ✓
bk50d_s16_v2.0    R>=40      366d   150   56.7   +16.27    +16.22   +10.71   +46.37   2.24    0.677    42.02   -68.77    2.1   58.8     57    3/4  ✓
bk50d_s16_v2.0    ungated    366d   359   59.3   +17.07    +17.02    +8.71   +43.21   2.47    0.777    38.71   -64.50    5.1   39.5     37    4/5  ✓
bk50d_s12_v2.0    R>=40      366d   194   57.2   +15.27    +15.22   +10.56   +43.42   2.16    0.626    41.98   -70.79    2.7   55.6     52    4/5  ✓
bk50d_s12_v2.0    ungated    366d   661   57.3   +13.76    +13.72    +7.20   +36.94   2.24    0.651    37.53   -62.75    9.3   32.7     27    5/6  ✓

Valid combinations: 6  |  Consistent: 5
```

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40       661       194        467     70.7%
bk50d_s16_v2.0               40       359       150        209     58.2%
bk50d_s20_v2.0               40       178       116         62     34.8%
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
