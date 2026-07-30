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
| Ranking gate sweep | ungated, ≥ 40 |
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
| Eval period | 2010-01-01 – 2015-12-31 |
| Burn-in (indicators only) | 2008-01-02 – 2010-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings — No Ranking Condition

```text
Period: 2010-01-01 – 2015-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s16_v2.0                   366d   233   60.5   +18.08    +18.03   +10.68   +41.78   2.60    0.847    38.30   -62.59    3.3   38.2     34    3/4  ✓
   2  bk50d_s20_v2.0                   366d   107   57.9   +16.95    +16.90    +6.13   +40.95   2.27    0.706    40.94   -65.04    1.5   51.6     49    2/3   
   3  bk50d_s12_v2.0                   366d   450   57.1   +13.11    +13.07    +7.17   +35.52   2.16    0.613    38.10   -62.79    6.3   31.6     24    4/5  ✓

Valid combinations: 3  |  Consistent: 2
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s16_v2.0` | `366d` — SR=0.847, Win%=60.5, Med%=+10.68, AnnMean%=+18.03, Q75%=+41.78, MaxDD%=38.30, CVaR%=-62.59, Yrs+=3/4, N=233
- `bk50d_s12_v2.0` | `366d` — SR=0.613, Win%=57.1, Med%=+7.17, AnnMean%=+13.07, Q75%=+35.52, MaxDD%=38.10, CVaR%=-62.79, Yrs+=4/5, N=450

## Rankings — Ranking Gate Sweep (R ≥ 40)

Same signals, but a trade is taken only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over 40 (40 is the `--min-signal-ranking` default). The score is computed from the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead.

```text
Period: 2010-01-01 – 2015-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Ranking gate sweep: QullamaggieRanking ≥ 40

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s16_v2.0 R≥40              366d    91   54.9   +17.99    +17.93   +10.38   +47.86   2.42    0.799    42.05   -63.05    1.3   58.2     57    0/1   
   2  bk50d_s20_v2.0 R≥40              366d    71   57.7   +17.12    +17.07   +11.04   +44.46   2.24    0.716    43.28   -62.20    1.0   60.1     60    0/0   
   3  bk50d_s12_v2.0 R≥40              366d   119   56.3   +15.47    +15.42   +10.38   +43.53   2.21    0.670    42.50   -66.98    1.7   55.3     52    1/2   

Valid combinations: 3  |  Consistent: 0
```

## Consistent Combinations (Ranking ≥ 40)

No combinations met the consistency criteria.

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40       450       119        331     73.6%
bk50d_s16_v2.0               40       233        91        142     60.9%
bk50d_s20_v2.0               40       107        71         36     33.6%
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

### Window notes (hand-written, 2026-07-30 run)

- **This is the weakest of the three windows by a wide margin** — ungated Sortino 0.61-0.85 against
  1.85-2.72 in 2021-2026 and 3.23-4.60 in 2016-2020, on identical rules. SPY returned +13.1 / +0.9 /
  +14.2 / +29.0 / +14.6 / +1.3 % over 2010-2015 (mean +12.2%/yr), the flattest tape of the three.
- **s16 beats s20 here, reversing the other two windows.** On 107 s20 trades against 233 s16 trades
  that ordering is inside sampling noise; it is not evidence that a lower threshold is better in
  chop.
- **The ranking gate is a wash in this window** (+0.06 / −0.05 / +0.01 Sortino on s12 / s16 / s20),
  and it destroys the consistency flag: gated, no combination is flagged consistent, because gating
  leaves fewer than 10 losing trades in nearly every year and those years fall out of the `Yrs+`
  denominator (`0/0` for s20, `0/1` for s16). The ✓ column is uninformative on the gated table here.
- **Signal frequency is 1.5-6.3/mo against 9.9-20.9/mo in 2016-2020.** Most of that gap is the
  universe thinning backwards in time: the market-cap filter is a 2026 snapshot, so far fewer names
  qualify in 2010 — 1,000 of the 2,272 sector-eligible US common stocks that traded in 2010 are
  excluded by a threshold measured 16 years later. This window is the one where that bias bites
  hardest, and it biases results *upward*, which makes the weak numbers here more damning, not less.
