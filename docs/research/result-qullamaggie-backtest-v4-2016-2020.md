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
| Eval period | 2016-01-01 – 2020-12-31 |
| Burn-in (indicators only) | 2014-01-01 – 2016-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings — No Ranking Condition

```text
Period: 2016-01-01 – 2020-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0                   366d   584   84.8   +59.26    +59.06   +49.37   +85.96  16.27    4.597    31.95   -50.55    9.9   54.8     56    3/3  ✓
   2  bk50d_s16_v2.0                   366d   868   80.9   +50.89    +50.72   +42.59   +77.61  12.04    3.733    32.24   -51.60   14.7   44.3     43    5/5  ✓
   3  bk50d_s12_v2.0                   366d  1235   79.5   +46.37    +46.22   +38.75   +73.18  10.14    3.234    32.00   -52.79   20.9   38.5     33    5/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0` | `366d` — SR=4.597, Win%=84.8, Med%=+49.37, AnnMean%=+59.06, Q75%=+85.96, MaxDD%=31.95, CVaR%=-50.55, Yrs+=3/3, N=584
- `bk50d_s16_v2.0` | `366d` — SR=3.733, Win%=80.9, Med%=+42.59, AnnMean%=+50.72, Q75%=+77.61, MaxDD%=32.24, CVaR%=-51.60, Yrs+=5/5, N=868
- `bk50d_s12_v2.0` | `366d` — SR=3.234, Win%=79.5, Med%=+38.75, AnnMean%=+46.22, Q75%=+73.18, MaxDD%=32.00, CVaR%=-52.79, Yrs+=5/5, N=1235

## Rankings — Ranking Gate Sweep (R ≥ 40)

Same signals, but a trade is taken only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over 40 (40 is the `--min-signal-ranking` default). The score is computed from the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead.

```text
Period: 2016-01-01 – 2020-12-31  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Ranking gate sweep: QullamaggieRanking ≥ 40

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0 R≥40              366d   447   86.4   +67.49    +67.25   +56.34   +97.68  21.25    5.685    33.03   -47.85    7.6   61.2     60    2/2   
   2  bk50d_s16_v2.0 R≥40              366d   478   84.9   +66.96    +66.73   +56.61   +97.75  20.18    5.619    33.48   -47.99    8.1   60.2     60    2/2   
   3  bk50d_s12_v2.0 R≥40              366d   521   83.3   +63.60    +63.38   +54.42   +95.13  16.09    4.839    33.90   -49.97    8.8   59.0     60    3/3  ✓

Valid combinations: 3  |  Consistent: 1
```

## Consistent Combinations (Ranking ≥ 40)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s12_v2.0 R≥40` | `366d` — SR=4.839, Win%=83.3, Med%=+54.42, AnnMean%=+63.38, Q75%=+95.13, MaxDD%=33.90, CVaR%=-49.97, Yrs+=3/3, N=521

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40      1235       521        714     57.8%
bk50d_s16_v2.0               40       868       478        390     44.9%
bk50d_s20_v2.0               40       584       447        137     23.5%
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

- **Treat these figures as an upper bound, not a result.** Win rates of 79.5-84.8%, profit factors of
  10-21 and ungated Sortino of 3.23-4.60 are the highest of the three windows by a factor of ~2 over
  2021-2026 and ~5 over 2010-2015, on identical rules.
- **A third of the return is earned outside the window.** A 366-day hold on a 2020 signal exits in
  2021 (SPY +30.5%, QQQ +29.2%). The window's own tape was also the strongest of the three: QQQ
  averaged +24.7%/yr over 2016-2020 (+46.2% in 2020 alone) against +16.4%/yr over 2010-2015.
- **The gate helps every configuration here, uniquely.** Gated-minus-ungated Sortino is +1.61 (s12),
  +1.89 (s16), +1.09 (s20) — the only window where s20 improves under the gate. In 2021-2026 s20
  *loses* 0.34 under the same gate, so this is not a stable property of the score.
- **The consistency flag thins under the gate**: only s12 keeps ≥3 valid years, because gating drops
  s16 and s20 below 10 losing trades in most years (`Yrs+` = `2/2` for both). Ungated, s16 and s12
  are 5/5 and s20 is 3/3 — s20's own 2 missing years also failed the 10-loser bar, not the Sortino
  test.
- **Survivorship applies here too.** The universe is fixed by a 2026 market-cap snapshot, so a 2016
  signal only exists if the company was ≥$1.5B ten years later. Combined with the bull tape, this is
  the window least suited to validating a rule and most likely to flatter one.
